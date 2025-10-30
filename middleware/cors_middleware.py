# =====================================================
# Archivo: middleware/cors_middleware.py
# Propósito: Configuración personalizada de CORS
# =====================================================

from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost:5000",
    "http://192.168.0.147:5000",
    "http://192.168.0.147:8000",
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
]

async def cors_middleware(request: Request, call_next):
    """Middleware CORS personalizado"""
    
    # Manejar preflight requests
    if request.method == "OPTIONS":
        return JSONResponse(
            status_code=200,
            content="OK",
            headers={
                "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Max-Age": "600",
            }
        )
    
    # Procesar request normal
    response = await call_next(request)
    
    # Agregar headers CORS
    origin = request.headers.get("origin")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    return response
