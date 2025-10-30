# =====================================================
# Archivo: utils/constants.py
# Propósito: Constantes de la aplicación
# =====================================================

# Configuración de tokens
TOKEN_LENGTH = 32  # Bytes para generador de tokens
TOKEN_EXPIRATION_MINUTES = 15  # Minutos de expiración

# Configuración de contraseña
MIN_PASSWORD_LENGTH = 8
PASSWORD_REQUIRES_UPPERCASE = True
PASSWORD_REQUIRES_LOWERCASE = True
PASSWORD_REQUIRES_NUMBERS = True
PASSWORD_REQUIRES_SPECIAL_CHARS = True

# Colecciones de Firestore
COLLECTION_USUARIOS = "usuarios"
COLLECTION_PASEADORES = "paseadores"
COLLECTION_RECUPERACIONES = "solicitudes_recuperacion"
COLLECTION_DUEÑOS = "dueños"

# Estados de recuperación
STATUS_ACTIVO = "ACTIVO"
STATUS_EXPIRADO = "EXPIRADO"
STATUS_COMPLETADO = "COMPLETADO"

# Mensajes
MSG_EMAIL_SENT = "Correo de recuperación enviado"
MSG_PASSWORD_UPDATED = "Contraseña actualizada correctamente"
MSG_INVALID_TOKEN = "Token inválido o expirado"
MSG_USER_NOT_FOUND = "Usuario no encontrado"
MSG_PASSWORD_MISMATCH = "Las contraseñas no coinciden"

# Códigos de error
ERROR_USER_NOT_FOUND = 404
ERROR_INVALID_TOKEN = 401
ERROR_VALIDATION_ERROR = 422
ERROR_INTERNAL_SERVER = 500
