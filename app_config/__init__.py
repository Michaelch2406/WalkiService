# =====================================================
# Archivo: config/__init__.py
# Propósito: Inicializar módulo config
# =====================================================

from .firebase_config import firebase_config, FirebaseConfig
from .gmail_config import GmailConfig

__all__ = [
    'firebase_config',
    'FirebaseConfig',
    'GmailConfig'
]
