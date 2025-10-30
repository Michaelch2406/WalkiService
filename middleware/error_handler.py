# =====================================================
# Archivo: middleware/error_handler.py
# Propósito: Manejo centralizado de excepciones
# =====================================================

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CustomException(Exception):
    """Excepción personalizada"""
    def __init__(self, status_code: int, message: str, details: str = None):
        self.status_code = status_code
        self.message = message
        self.details = details

async def custom_exception_handler(request: Request, exc: CustomException):
    """Manejador para excepciones personalizadas"""
    logger.error(f"CustomException: {exc.message} - {exc.details}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "details": exc.details,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Manejador para errores de validación Pydantic"""
    logger.warning(f"Validation error: {exc.errors()}")
    
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"][1:]),
            "message": error["msg"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validación de datos fallida",
            "details": errors,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Manejador general de excepciones"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Error interno del servidor",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
