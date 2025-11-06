# ====================================================
# Archivo: main.py (COMPLETAMENTE CORREGIDO)
# ====================================================

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
import secrets
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import firebase_admin
from firebase_admin import credentials, firestore, auth
from config import get_deep_link_base, get_base_url, get_token_expiration, get_current_network, print_network_info

load_dotenv()

# ========== INICIALIZAR FIREBASE ==========

try:
    cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH", "credentials.json"))
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase inicializado correctamente")
except Exception as e:
    print(f"❌ Error inicializando Firebase: {e}")
    db = None

# ========== CREAR APP ==========

app = FastAPI(title="WalkiService API", version="1.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== SCHEMAS ==========

class RequestPasswordResetRequest(BaseModel):
    email: EmailStr

class RequestPasswordResetResponse(BaseModel):
    success: bool
    message: str
    timestamp: datetime

class ConfirmPasswordResetRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

class ConfirmPasswordResetResponse(BaseModel):
    success: bool
    message: str
    timestamp: datetime

# ========== CONFIGURACIÓN AUTO-DETECTADA ==========

GMAIL_SENDER_EMAIL = os.getenv("GMAIL_SENDER_EMAIL", "tu-correo@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "tu-password")

print_network_info()
base_url, network_name = get_base_url()
DEEP_LINK_BASE = get_deep_link_base()
TOKEN_EXPIRATION_MINUTES = get_token_expiration()

print(f"\n{'='*60}")
print(f"🌐 Red detectada: {network_name}")
print(f"📍 URL base: {base_url}")
print(f"🔗 Deep link base: {DEEP_LINK_BASE}")
print(f"⏱️  Token expira en: {TOKEN_EXPIRATION_MINUTES} minutos")
print(f"{'='*60}\n")

EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; background: #f9f9f9; border-radius: 8px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
        .content { background: white; padding: 30px; border-radius: 0 0 8px 8px; }
        .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .button:hover { background: #764ba2; }
        .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #666; border-top: 1px solid #ddd; padding-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Walki - Servicio Canino</h1>
            <p>Recuperación de Contraseña</p>
        </div>
        <div class="content">
            <h2>¡Hola {{ user_name }}!</h2>
            <p>Recibimos una solicitud para recuperar tu contraseña.</p>
            <p><strong>Para cambiar tu contraseña, haz clic en el botón:</strong></p>
            <div style="text-align: center;">
                <a href="{{ reset_link }}" class="button">Recuperar Contraseña</a>
            </div>
            <p>O copia esta URL:</p>
            <p style="background: #f0f0f0; padding: 10px; word-break: break-all; font-size: 12px;">{{ reset_link }}</p>
            <p style="background: #fff3cd; border: 1px solid #ffc107; color: #856404; padding: 10px; border-radius: 5px; font-size: 12px;">
                <strong>⚠️</strong> Este enlace expira en {{ expiration_minutes }} minutos.
            </p>
            <div class="footer">
                <p>Walki - Equipo de Soporte</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

# ========== FUNCIONES AUXILIARES ==========

def get_utc_now() -> datetime:
    """Obtener datetime actual CON zona horaria UTC"""
    return datetime.now(timezone.utc)

def generate_token() -> str:
    """Generar token seguro de 64 caracteres"""
    return secrets.token_hex(32)

def send_email(recipient_email: str, user_name: str, token: str) -> bool:
    """Enviar correo de recuperación"""
    try:
        reset_link = f"{DEEP_LINK_BASE}?token={token}"
        
        template = Template(EMAIL_TEMPLATE)
        html_content = template.render(
            user_name=user_name,
            reset_link=reset_link,
            expiration_minutes=TOKEN_EXPIRATION_MINUTES
        )
        
        message = MIMEMultipart('alternative')
        message['From'] = GMAIL_SENDER_EMAIL
        message['To'] = recipient_email
        message['Subject'] = 'Walki - Recuperación de Contraseña'
        
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_SENDER_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(message)
        
        print(f"✅ Correo enviado a {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ Error enviando correo: {e}")
        return False

def save_recovery_request(uid: str, email: str, token: str) -> bool:
    """Guardar solicitud de recuperación en Firestore"""
    try:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        now = get_utc_now()
        expiration = now + timedelta(minutes=TOKEN_EXPIRATION_MINUTES)
        
        db.collection("solicitudes_recuperacion").add({
            'uid': uid,
            'email': email,
            'token_hash': token_hash,
            'fecha_creacion': now,
            'fecha_expiracion': expiration,
            'estado': 'ACTIVO',
            'usado': False
        })
        
        print(f"✅ Solicitud guardada: {email}")
        return True
    except Exception as e:
        print(f"❌ Error guardando: {e}")
        return False

def validate_recovery_token(token: str) -> dict:
    """Validar token de recuperación"""
    try:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        now = get_utc_now()
        
        docs = db.collection("solicitudes_recuperacion").where(
            filter=firestore.FieldFilter('token_hash', '==', token_hash)
        ).where(
            filter=firestore.FieldFilter('estado', '==', 'ACTIVO')
        ).where(
            filter=firestore.FieldFilter('usado', '==', False)
        ).stream()
        
        docs_list = list(docs)
        
        if not docs_list:
            print("❌ Token no encontrado")
            return None
        
        doc = docs_list[0]
        recovery_data = doc.to_dict()
        
        # Asegurar que fecha_expiracion tiene zona horaria
        fecha_expiracion = recovery_data.get('fecha_expiracion')
        
        if fecha_expiracion and fecha_expiracion.tzinfo is None:
            fecha_expiracion = fecha_expiracion.replace(tzinfo=timezone.utc)
            recovery_data['fecha_expiracion'] = fecha_expiracion
        
        # Comparar datetimes con zona horaria
        if fecha_expiracion and now > fecha_expiracion:
            print(f"❌ Token expirado: {now} > {fecha_expiracion}")
            doc.reference.update({'estado': 'EXPIRADO'})
            return None
        
        recovery_data['doc_id'] = doc.id
        print(f"✅ Token válido")
        return recovery_data
        
    except Exception as e:
        print(f"❌ Error validando: {e}")
        import traceback
        traceback.print_exc()
        return None

# ========== ENDPOINTS ==========

@app.get("/")
async def root():
    return {"message": "WalkiService API", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "OK"}

@app.post("/api/v1/auth/request-password-reset", response_model=RequestPasswordResetResponse)
async def request_password_reset(request: RequestPasswordResetRequest):
    """Solicitar recuperación de contraseña"""
    try:
        try:
            user = auth.get_user_by_email(request.email)
            user_uid = user.uid
        except auth.UserNotFoundError:
            return RequestPasswordResetResponse(
                success=True,
                message=f"Si la cuenta existe, recibirás un correo",
                timestamp=get_utc_now()
            )
        
        token = generate_token()
        
        if not save_recovery_request(user_uid, request.email, token):
            raise Exception("Error guardando en Firestore")
        
        try:
            user_doc = db.collection('usuarios').document(user_uid).get()
            user_name = user_doc.get('nombre_display') if user_doc.exists else "Usuario"
        except:
            user_name = "Usuario"
        
        if send_email(request.email, user_name, token):
            return RequestPasswordResetResponse(
                success=True,
                message=f"Correo enviado a {request.email}",
                timestamp=get_utc_now()
            )
        else:
            raise Exception("Error enviando correo")
    
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": str(e)}
        )

@app.get("/api/v1/auth/validate-token/{token}")
async def validate_token(token: str):
    """Validar token"""
    recovery_data = validate_recovery_token(token)
    
    if recovery_data:
        return {"valid": True, "message": "Token válido"}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"valid": False, "message": "Token inválido"}
        )

@app.post("/api/v1/auth/confirm-password-reset", response_model=ConfirmPasswordResetResponse)
async def confirm_password_reset(request: ConfirmPasswordResetRequest):
    """Confirmar nueva contraseña"""
    try:
        if request.new_password != request.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": "Las contraseñas no coinciden"}
            )
        
        if len(request.new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": "Mínimo 8 caracteres"}
            )
        
        recovery_data = validate_recovery_token(request.token)
        if not recovery_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"success": False, "error": "Token inválido"}
            )
        
        try:
            auth.update_user(recovery_data['uid'], password=request.new_password)
            print(f"✅ Contraseña actualizada")
        except Exception as e:
            raise Exception(f"Error Firebase: {str(e)}")
        
        # 🔴 ELIMINAR EL DOCUMENTO DE RECUPERACIÓN (NO actualizar)
        try:
            db.collection("solicitudes_recuperacion").document(recovery_data['doc_id']).delete()
            print(f"✅ Solicitud de recuperación eliminada del servidor")
        except Exception as e:
            print(f"⚠️  Advertencia: Error eliminando solicitud: {e}")
            # No fallar si no se puede eliminar, la contraseña ya cambió
        
        return ConfirmPasswordResetResponse(
            success=True,
            message="Contraseña actualizada",
            timestamp=get_utc_now()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": str(e)}
        )

@app.get("/reset-password")
async def reset_password_page():
    """Servir la página de recuperación de contraseña"""
    file_path = os.path.join(os.path.dirname(__file__), "static", "reset-password.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        return {"error": "Archivo no encontrado"}

@app.get("/api/v1/test-smtp")
async def test_smtp_connection():
    """Endpoint de prueba para verificar la conexión con smtp.gmail.com"""
    import socket
    host = "smtp.gmail.com"
    port = 587
    timeout_seconds = 10

    try:
        # Crear un socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout_seconds)
        
        # Intentar conectar
        print(f"Intentando conectar a {host}:{port}...")
        result = sock.connect_ex((host, port))
        
        if result == 0:
            print("✅ Conexión exitosa.")
            return {"success": True, "message": f"Conexión a {host}:{port} exitosa."}
        else:
            error_message = os.strerror(result)
            print(f"❌ Falla de conexión con código: {result} ({error_message})")
            raise ConnectionError(f"No se pudo conectar a {host}:{port}. Código: {result} - {error_message}")

    except socket.timeout:
        print("❌ Falla de conexión: Timeout")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": f"Timeout de {timeout_seconds}s esperando a {host}:{port}"}
        )
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": str(e)}
        )
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": f"Error inesperado: {str(e)}"}
        )
    finally:
        if 'sock' in locals() and sock:
            sock.close()

if __name__ == "__main__":
    import uvicorn
    HOST = os.getenv("API_HOST", "0.0.0.0")
    PORT = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host=HOST, port=PORT, reload=True)
