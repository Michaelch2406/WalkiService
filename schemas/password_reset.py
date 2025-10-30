# =====================================================
# Archivo: schemas/password_reset.py
# Propósito: Definir estructuras de datos con Pydantic
# =====================================================

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# ========== SOLICITUD DE RECUPERACIÓN ==========

class RequestPasswordResetRequest(BaseModel):
    """Schema para solicitud de recuperación de contraseña"""
    email: EmailStr = Field(..., description="Correo electrónico del usuario")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "usuario@example.com"
            }
        }

class RequestPasswordResetResponse(BaseModel):
    """Schema para respuesta de solicitud de recuperación"""
    success: bool
    message: str
    timestamp: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Correo de recuperación enviado a usuario@example.com",
                "timestamp": "2025-10-26T12:00:00Z"
            }
        }

# ========== CONFIRMACIÓN DE RECUPERACIÓN ==========

class ConfirmPasswordResetRequest(BaseModel):
    """Schema para confirmar recuperación de contraseña"""
    token: str = Field(..., min_length=32, description="Token único de recuperación")
    new_password: str = Field(..., min_length=8, description="Nueva contraseña")
    confirm_password: str = Field(..., description="Confirmación de nueva contraseña")
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123def456ghi789jkl012mno345pqr",
                "new_password": "NewSecurePassword123!",
                "confirm_password": "NewSecurePassword123!"
            }
        }

class ConfirmPasswordResetResponse(BaseModel):
    """Schema para respuesta de confirmación"""
    success: bool
    message: str
    timestamp: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Contraseña actualizada correctamente",
                "timestamp": "2025-10-26T12:00:00Z"
            }
        }

# ========== VALIDAR TOKEN ==========

class ValidateTokenResponse(BaseModel):
    """Schema para validación de token"""
    valid: bool
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "message": "Token válido"
            }
        }

# ========== ERROR RESPONSE ==========

class ErrorResponse(BaseModel):
    """Schema para respuestas de error"""
    success: bool = False
    error: str
    details: Optional[str] = None
    timestamp: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Usuario no encontrado",
                "details": "No existe cuenta con ese correo electrónico",
                "timestamp": "2025-10-26T12:00:00Z"
            }
        }
