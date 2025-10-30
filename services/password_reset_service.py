# =====================================================
# Archivo: services/password_reset_service.py
# Propósito: Servicios de recuperación de contraseña
# =====================================================

from typing import Tuple
from datetime import datetime, timedelta, timezone
import hashlib
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import auth, firestore
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from app_config import get_deep_link_base, get_token_expiration

load_dotenv()

# ========== CONFIGURACIÓN ==========

GMAIL_SENDER_EMAIL = os.getenv("GMAIL_SENDER_EMAIL", "tu-correo@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "tu-password")
TOKEN_EXPIRATION_MINUTES = get_token_expiration()

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


class PasswordResetService:
    """Servicio para recuperación de contraseña"""

    @staticmethod
    def _validate_password(password: str) -> Tuple[bool, str]:
        """Validar fortaleza de contraseña"""
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        if not any(char.isupper() for char in password):
            return False, "Debe contener al menos una mayúscula"
        if not any(char.isdigit() for char in password):
            return False, "Debe contener al menos un número"
        return True, "Contraseña válida"

    @staticmethod
    def _send_recovery_email(recipient_email: str, user_name: str, token: str) -> bool:
        """Enviar correo de recuperación"""
        try:
            reset_link = f"{get_deep_link_base()}?token={token}"
            
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
            
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(GMAIL_SENDER_EMAIL, GMAIL_APP_PASSWORD)
                server.send_message(message)
            
            print(f"✅ Correo enviado a {recipient_email}")
            return True
        except Exception as e:
            print(f"❌ Error enviando correo: {e}")
            return False

    @staticmethod
    def request_password_reset(email: str) -> Tuple[bool, str]:
        """
        Solicitar recuperación de contraseña
        
        Args:
            email: Email del usuario
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        try:
            # Verificar que el usuario existe
            try:
                user = auth.get_user_by_email(email)
                user_uid = user.uid
            except auth.UserNotFoundError:
                return True, "Si la cuenta existe, recibirás un correo"
            
            # Generar token
            import secrets
            token = secrets.token_hex(32)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            # Guardar en Firestore
            db = firestore.client()
            now = datetime.now(timezone.utc)
            expiration = now + timedelta(minutes=TOKEN_EXPIRATION_MINUTES)
            
            db.collection("solicitudes_recuperacion").add({
                'uid': user_uid,
                'email': email,
                'token_hash': token_hash,
                'fecha_creacion': now,
                'fecha_expiracion': expiration,
                'estado': 'ACTIVO',
                'usado': False
            })
            
            print(f"✅ Solicitud guardada: {email}")
            
            # Obtener nombre del usuario
            try:
                user_doc = db.collection('usuarios').document(user_uid).get()
                user_name = user_doc.get('nombre_display') if user_doc.exists else "Usuario"
            except:
                user_name = "Usuario"
            
            # Enviar correo
            if PasswordResetService._send_recovery_email(email, user_name, token):
                return True, f"Correo enviado a {email}"
            else:
                return False, "Error enviando correo"
        
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return False, f"Error: {str(e)}"

    @staticmethod
    def confirm_password_reset(
        token: str,
        new_password: str,
        confirm_password: str
    ) -> Tuple[bool, str]:
        """
        Confirmar y aplicar nueva contraseña
        
        Args:
            token: Token de recuperación
            new_password: Nueva contraseña
            confirm_password: Confirmación de nueva contraseña
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        try:
            # Validar que las contraseñas coincidan
            if new_password != confirm_password:
                return False, "Las contraseñas no coinciden"
            
            # Validar fortaleza de contraseña
            is_valid, message = PasswordResetService._validate_password(new_password)
            if not is_valid:
                return False, message
            
            # Validar token
            db = firestore.client()
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            now = datetime.now(timezone.utc)
            
            docs = db.collection("solicitudes_recuperacion").where(
                filter=firestore.FieldFilter('token_hash', '==', token_hash)
            ).where(
                filter=firestore.FieldFilter('estado', '==', 'ACTIVO')
            ).where(
                filter=firestore.FieldFilter('usado', '==', False)
            ).stream()
            
            docs_list = list(docs)
            
            if not docs_list:
                return False, "Token inválido o expirado"
            
            doc = docs_list[0]
            recovery_data = doc.to_dict()
            
            # Verificar expiración
            fecha_expiracion = recovery_data.get('fecha_expiracion')
            if fecha_expiracion and fecha_expiracion.tzinfo is None:
                fecha_expiracion = fecha_expiracion.replace(tzinfo=timezone.utc)
            
            if fecha_expiracion and now > fecha_expiracion:
                return False, "Token expirado"
            
            # Actualizar contraseña en Firebase Auth
            try:
                auth.update_user(
                    uid=recovery_data['uid'],
                    password=new_password
                )
                print(f"✅ Contraseña actualizada para {recovery_data['uid']}")
            except Exception as e:
                return False, f"Error actualizando contraseña: {str(e)}"
            
            # 🔴 ELIMINAR EL DOCUMENTO DE RECUPERACIÓN INMEDIATAMENTE
            try:
                db.collection("solicitudes_recuperacion").document(doc.id).delete()
                print(f"✅ Solicitud de recuperación eliminada del servidor")
            except Exception as e:
                print(f"⚠️  Advertencia: Error eliminando solicitud: {e}")
                # No fallar si no se puede eliminar, la contraseña ya cambió
            
            # Registrar el cambio en Firestore (opcional, para auditoría)
            try:
                db.collection('usuarios').document(
                    recovery_data['uid']
                ).update({
                    'ultima_actualizacion_password': db.server_timestamp()
                })
            except:
                pass
            
            return True, "Contraseña actualizada correctamente"
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return False, f"Error confirmando recuperación: {str(e)}"
