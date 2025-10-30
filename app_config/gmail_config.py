# =====================================================
# Archivo: config/gmail_config.py
# Propósito: Configurar Gmail API con OAuth2
# =====================================================

from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
import os
from dotenv import load_dotenv

load_dotenv()

GMAIL_CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
GMAIL_SENDER_EMAIL = os.getenv("GMAIL_SENDER_EMAIL", "michael.chasiguano734@ist17dejulio.edu.ec")

class GmailConfig:
    """Configuración centralizada de Gmail API"""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    
    @staticmethod
    def get_gmail_credentials():
        """Obtener credenciales autenticadas para Gmail"""
        try:
            # Usar credentials.json para autenticación
            credentials = Credentials.from_service_account_file(
                GMAIL_CREDENTIALS_PATH,
                scopes=GmailConfig.SCOPES
            )
            return credentials
        except FileNotFoundError:
            raise Exception(f"Archivo de credenciales Gmail no encontrado: {GMAIL_CREDENTIALS_PATH}")
        except Exception as e:
            raise Exception(f"Error al obtener credenciales Gmail: {str(e)}")
    
    @staticmethod
    def get_sender_email():
        """Obtener email remitente"""
        return GMAIL_SENDER_EMAIL
