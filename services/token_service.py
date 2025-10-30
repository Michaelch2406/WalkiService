# =====================================================
# Archivo: services/token_service.py
# Propósito: Generar y validar tokens de recuperación
# =====================================================

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple
from app_config.firebase_config import firebase_config

class TokenService:
    """Servicio para manejar tokens de recuperación"""
    
    TOKEN_LENGTH = 32  # Longitud del token en bytes
    TOKEN_EXPIRATION_MINUTES = 15  # Expiración en 15 minutos
    COLLECTION_NAME = "solicitudes_recuperacion"
    
    @staticmethod
    def generate_token() -> str:
        """
        Generar token criptográficamente seguro
        
        Returns:
            str: Token hex de 64 caracteres
        """
        return secrets.token_hex(TokenService.TOKEN_LENGTH)
    
    @staticmethod
    def create_recovery_request(user_uid: str, user_email: str) -> Tuple[str, datetime]:
        """
        Crear solicitud de recuperación en Firestore
        
        Args:
            user_uid: UID del usuario en Firebase Auth
            user_email: Correo del usuario
            
        Returns:
            Tuple[str, datetime]: (token generado, fecha de expiración)
            
        Raises:
            Exception: Si falla al crear el documento
        """
        try:
            # Generar token
            token = TokenService.generate_token()
            
            # Calcular fecha de expiración
            now = datetime.utcnow()
            expiration_date = now + timedelta(
                minutes=TokenService.TOKEN_EXPIRATION_MINUTES
            )
            
            # Hashear el token para seguridad adicional
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            # Crear documento en Firestore
            db = firebase_config.firestore
            db.collection(TokenService.COLLECTION_NAME).add({
                'uid': user_uid,
                'email': user_email,
                'token_hash': token_hash,
                'fecha_creacion': now,
                'fecha_expiracion': expiration_date,
                'estado': 'ACTIVO',
                'usado': False
            })
            
            print(f"✅ Solicitud de recuperación creada para {user_email}")
            return token, expiration_date
            
        except Exception as e:
            print(f"Error creando solicitud de recuperación: {str(e)}")
            raise
    
    @staticmethod
    def validate_token(token: str) -> Optional[dict]:
        """
        Validar token y obtener información de recuperación
        
        Args:
            token: Token a validar
            
        Returns:
            dict: Información de recuperación si es válido, None si no lo es
        """
        try:
            # Hashear el token recibido
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            # Buscar en Firestore
            db = firebase_config.firestore
            query = db.collection(TokenService.COLLECTION_NAME)\
                .where('token_hash', '==', token_hash)\
                .where('estado', '==', 'ACTIVO')\
                .where('usado', '==', False)
            
            docs = query.stream()
            docs_list = list(docs)
            
            if not docs_list:
                print("Token no encontrado o ya fue utilizado")
                return None
            
            doc = docs_list[0]
            recovery_data = doc.to_dict()
            
            # Validar que no haya expirado
            if datetime.utcnow() > recovery_data['fecha_expiracion']:
                print("Token expirado")
                # Marcar como expirado
                doc.reference.update({'estado': 'EXPIRADO'})
                return None
            
            # Agregar el ID del documento para actualizaciones posteriores
            recovery_data['doc_id'] = doc.id
            
            return recovery_data
            
        except Exception as e:
            print(f"Error validando token: {str(e)}")
            return None
    
    @staticmethod
    def invalidate_token(doc_id: str):
        """
        Invalidar token después de su uso
        
        Args:
            doc_id: ID del documento en Firestore
        """
        try:
            db = firebase_config.firestore
            db.collection(TokenService.COLLECTION_NAME)\
                .document(doc_id).update({
                'usado': True,
                'estado': 'COMPLETADO',
                'fecha_uso': datetime.utcnow()
            })
            print(f"✅ Token invalidado: {doc_id}")
        except Exception as e:
            print(f"Error invalidando token: {str(e)}")
            raise
