# =====================================================
# Archivo: routers/auth_router.py
# =====================================================

from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from schemas.password_reset import (
    RequestPasswordResetRequest,
    RequestPasswordResetResponse,
    ConfirmPasswordResetRequest,
    ConfirmPasswordResetResponse,
    ValidateTokenResponse,
)
from services.password_reset_service import PasswordResetService
from services.token_service import TokenService

# 🔴 SIN PREFIX - Lo ponemos en main.py
router = APIRouter(tags=["Autenticación"])

@router.post(
    "/request-password-reset",
    response_model=RequestPasswordResetResponse,
    status_code=status.HTTP_200_OK,
)
async def request_password_reset(request: RequestPasswordResetRequest):
    """Solicitar recuperación de contraseña"""
    try:
        success, message = PasswordResetService.request_password_reset(
            email=request.email
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": message}
            )
        
        return RequestPasswordResetResponse(
            success=True,
            message=message,
            timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": str(e)}
        )

@router.get("/validate-token/{token}", response_model=ValidateTokenResponse)
async def validate_token(token: str):
    """Validar token"""
    recovery_data = TokenService.validate_token(token)
    if recovery_data:
        return ValidateTokenResponse(valid=True, message="Token válido")
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"valid": False, "message": "Token inválido"}
        )

@router.post(
    "/confirm-password-reset",
    response_model=ConfirmPasswordResetResponse
)
async def confirm_password_reset(request: ConfirmPasswordResetRequest):
    """Confirmar nueva contraseña"""
    try:
        success, message = PasswordResetService.confirm_password_reset(
            token=request.token,
            new_password=request.new_password,
            confirm_password=request.confirm_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "error": message}
            )
        
        return ConfirmPasswordResetResponse(
            success=True,
            message=message,
            timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "error": str(e)}
        )
