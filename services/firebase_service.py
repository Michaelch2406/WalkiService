# =====================================================
# Archivo: services/firebase_service.py
# Propósito: Servicios generales de Firebase
# =====================================================

from app_config.firebase_config import firebase_config
from typing import Optional, Dict, Any
from datetime import datetime

class FirebaseService:
    """Servicio centralizado para operaciones Firebase"""
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """
        Obtener usuario de Firebase Auth por email
        
        Args:
            email: Correo del usuario
            
        Returns:
            Dict con datos del usuario o None
        """
        try:
            auth = firebase_config.auth
            user = auth.get_user_by_email(email)
            
            return {
                'uid': user.uid,
                'email': user.email,
                'email_verified': user.email_verified,
                'display_name': user.display_name,
                'disabled': user.disabled
            }
        except auth.UserNotFoundError:
            return None
        except Exception as e:
            print(f"Error obteniendo usuario: {str(e)}")
            raise
    
    @staticmethod
    def update_user_password(uid: str, new_password: str) -> bool:
        """
        Actualizar contraseña de usuario
        
        Args:
            uid: UID del usuario
            new_password: Nueva contraseña
            
        Returns:
            bool: True si fue exitoso
        """
        try:
            auth = firebase_config.auth
            auth.update_user(uid, password=new_password)
            print(f"✅ Contraseña actualizada para usuario {uid}")
            return True
        except Exception as e:
            print(f"Error actualizando contraseña: {str(e)}")
            raise
    
    @staticmethod
    def get_firestore_document(collection: str, document_id: str) -> Optional[Dict]:
        """
        Obtener documento de Firestore
        
        Args:
            collection: Nombre de colección
            document_id: ID del documento
            
        Returns:
            Dict con datos del documento o None
        """
        try:
            db = firebase_config.firestore
            doc = db.collection(collection).document(document_id).get()
            
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error obteniendo documento: {str(e)}")
            raise
    
    @staticmethod
    def update_firestore_document(
        collection: str,
        document_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Actualizar documento de Firestore
        
        Args:
            collection: Nombre de colección
            document_id: ID del documento
            data: Datos a actualizar
            
        Returns:
            bool: True si fue exitoso
        """
        try:
            db = firebase_config.firestore
            db.collection(collection).document(document_id).update(data)
            print(f"✅ Documento actualizado: {collection}/{document_id}")
            return True
        except Exception as e:
            print(f"Error actualizando documento: {str(e)}")
            raise
    
    @staticmethod
    def create_firestore_document(
        collection: str,
        data: Dict[str, Any],
        document_id: Optional[str] = None
    ) -> str:
        """
        Crear documento en Firestore
        
        Args:
            collection: Nombre de colección
            data: Datos del documento
            document_id: ID del documento (opcional)
            
        Returns:
            str: ID del documento creado
        """
        try:
            db = firebase_config.firestore
            
            if document_id:
                db.collection(collection).document(document_id).set(data)
                return document_id
            else:
                doc_ref = db.collection(collection).add(data)
                return doc_ref[1].id
        except Exception as e:
            print(f"Error creando documento: {str(e)}")
            raise
    
    @staticmethod
    def delete_firestore_document(collection: str, document_id: str) -> bool:
        """
        Eliminar documento de Firestore
        
        Args:
            collection: Nombre de colección
            document_id: ID del documento
            
        Returns:
            bool: True si fue exitoso
        """
        try:
            db = firebase_config.firestore
            db.collection(collection).document(document_id).delete()
            print(f"✅ Documento eliminado: {collection}/{document_id}")
            return True
        except Exception as e:
            print(f"Error eliminando documento: {str(e)}")
            raise
