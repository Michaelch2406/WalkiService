# =====================================================
# Archivo: schemas/response.py
# Propósito: Schemas generales de respuesta
# =====================================================

from pydantic import BaseModel
from typing import Optional, Any, List
from datetime import datetime

class SuccessResponse(BaseModel):
    """Schema genérico para respuestas exitosas"""
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None
    timestamp: datetime = datetime.utcnow()
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"id": "123", "name": "Example"},
                "message": "Operación exitosa",
                "timestamp": "2025-10-26T12:00:00Z"
            }
        }

class ErrorResponseGeneral(BaseModel):
    """Schema genérico para errores"""
    success: bool = False
    error: str
    details: Optional[str | List[dict]] = None
    timestamp: datetime = datetime.utcnow()
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Operación fallida",
                "details": "Descripción del error",
                "timestamp": "2025-10-26T12:00:00Z"
            }
        }

class PaginatedResponse(BaseModel):
    """Schema para respuestas paginadas"""
    success: bool = True
    data: List[Any]
    total: int
    page: int
    page_size: int
    timestamp: datetime = datetime.utcnow()
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": [],
                "total": 100,
                "page": 1,
                "page_size": 10,
                "timestamp": "2025-10-26T12:00:00Z"
            }
        }
