# =====================================================
# Archivo: services/email_service.py
# Propósito: Enviar correos de recuperación vía Gmail
# =====================================================

import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from jinja2 import Template
from typing import Optional
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

GMAIL_SENDER_EMAIL = os.getenv("GMAIL_SENDER_EMAIL", "michael.chasiguano734@ist17dejulio.edu.ec")
CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
# Deep Link de Firebase para la app (reemplazar con tu dominio)
DEEP_LINK_BASE = os.getenv("DEEP_LINK_BASE", "https://walki.page.link/reset-password")
APP_NAME = os.getenv("APP_NAME", "Walki")

class EmailService:
    """Servicio para enviar correos de recuperación"""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    
    EMAIL_TEMPLATE = """
    <!DOCTYPE html>
<html lang="es">
<head>
    <title>Recuperación de Contraseña - Walki</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            line-height: 1.6; 
            color: #333; 
            margin: 0; 
            padding: 0;
        }
        .container { 
            max-width: 600px; 
            margin: 20px auto; /* Añadido margen para vista de email */
            padding: 0; /* Removido padding para que el header y content se alineen */
            background: #f9f9f9; 
            border-radius: 8px; 
            overflow: hidden; /* Para contener los border-radius hijos */
            border: 1px solid #ddd; /* Un borde sutil */
        }
        /* Color actualizado a #12A3ED */
        .header { 
            background: #12A3ED; 
            color: white; 
            padding: 20px; 
            text-align: center; 
        }
        .header h1 {
            margin: 0 0 5px 0;
            font-size: 24px;
        }
        .header p {
            margin: 0;
            font-size: 16px;
        }
        .content { 
            background: white; 
            padding: 30px; 
        }
        /* Color actualizado a #12A3ED */
        .button { 
            display: inline-block; 
            background: #12A3ED; 
            color: white !important; /* Importante para anular estilos de cliente de email */
            padding: 12px 30px; 
            text-decoration: none; 
            border-radius: 5px; 
            margin: 20px 0; 
            font-weight: bold;
        }
        .footer { 
            text-align: center; 
            margin-top: 20px; 
            font-size: 12px; 
            color: #666; 
            border-top: 1px solid #ddd; 
            padding-top: 20px; 
        }
        .url-box {
            background: #f0f0f0; 
            padding: 10px; 
            word-break: break-all; 
            font-size: 12px; 
            border-radius: 4px;
        }
        .warning-box {
            background: #fff3cd; 
            border: 1px solid #ffeeba; /* Color más suave */
            color: #856404; 
            padding: 10px; 
            border-radius: 5px; 
            font-size: 12px;
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Walki - Servicio Canino</h1>
            <p>Recuperación de Contraseña</p>
        </div>
        <div class="content">
            <h2 style="color: #12A3ED;">¡Hola {{ user_name }}!</h2>
            <p>Recibimos una solicitud para recuperar tu contraseña.</p>
            <p><strong>Para cambiar tu contraseña, haz clic en el botón:</strong></p>
            <div style="text-align: center;">
                <a href="{{ reset_link }}" class="button">Recuperar Contraseña</a>
            </div>
            <p>Si el botón no funciona, copia y pega esta URL en tu navegador:</p>
            <p class="url-box">{{ reset_link }}</p>
            <p class="warning-box">
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
    
    @staticmethod
    def get_gmail_service():
        """
        Obtener servicio autenticado de Gmail
        
        Returns:
            googleapiclient.discovery.Resource: Servicio de Gmail
        """
        try:
            credentials = Credentials.from_service_account_file(
                CREDENTIALS_PATH,
                scopes=EmailService.SCOPES
            )
            service = build('gmail', 'v1', credentials=credentials)
            return service
        except Exception as e:
            print(f"Error al obtener servicio Gmail: {str(e)}")
            raise
    
    @staticmethod
    def send_password_reset_email(
        recipient_email: str,
        user_name: str,
        token: str,
        expiration_minutes: int = 15
    ) -> bool:
        """
        Enviar correo de recuperación de contraseña
        
        Args:
            recipient_email: Correo del usuario
            user_name: Nombre del usuario
            token: Token de recuperación
            expiration_minutes: Minutos hasta expiración
            
        Returns:
            bool: True si se envió correctamente, False en caso contrario
        """
        try:
            # Construir deep link
            reset_link = f"{DEEP_LINK_BASE}?token={token}"
            
            # Preparar datos para el template
            template_data = {
                'app_name': APP_NAME,
                'user_name': user_name,
                'reset_link': reset_link,
                'token': token,
                'expiration_minutes': expiration_minutes,
                'current_date': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            }
            
            # Renderizar template
            template = Template(EmailService.EMAIL_TEMPLATE)
            html_content = template.render(**template_data)
            
            # Crear mensaje
            message = MIMEMultipart('alternative')
            message['to'] = recipient_email
            message['from'] = GMAIL_SENDER_EMAIL
            message['subject'] = f'{APP_NAME} - Recuperación de Contraseña'
            
            # Agregar versión de texto plano
            text_content = f"""
            Hola {user_name},
            
            Recibimos una solicitud para recuperar tu contraseña.
            
            Para cambiar tu contraseña, abre tu app Walki y usa el siguiente token:
            {token}
            
            Este token expira en {expiration_minutes} minutos.
            
            Si no solicitaste esto, ignora este correo.
            
            Saludos,
            {APP_NAME}
            """
            
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            
            message.attach(part1)
            message.attach(part2)
            
            # Codificar mensaje
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode()
            
            # Enviar vía Gmail API
            service = EmailService.get_gmail_service()
            send_message = {
                'raw': raw_message
            }
            
            result = service.users().messages().send(
                userId='me',
                body=send_message
            ).execute()
            
            print(f"✅ Correo de recuperación enviado a {recipient_email}")
            return True
            
        except Exception as e:
            print(f"Error enviando correo: {str(e)}")
            return False
