# =====================================================
# Archivo: config/firebase_config.py
# Propósito: Inicializar y configurar Firebase Admin SDK
# =====================================================

import firebase_admin
from firebase_admin import credentials, db, firestore, auth
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Variables de entorno
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "credentials.json")
FIREBASE_DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL", "")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# 🔴 EMULADOR - Variables locales
FIREBASE_EMULATOR_HOST = os.getenv("FIREBASE_EMULATOR_HOST", None)
FIREBASE_AUTH_EMULATOR_HOST = os.getenv("FIREBASE_AUTH_EMULATOR_HOST", None)
FIRESTORE_EMULATOR_HOST = os.getenv("FIRESTORE_EMULATOR_HOST", None)

class FirebaseConfig:
    """Configuración centralizada de Firebase Admin SDK"""
    
    _instance: Optional['FirebaseConfig'] = None
    _app = None
    _firestore_client = None
    _auth_client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicializar Firebase Admin SDK"""
        try:
            # 🔴 EMULADOR: Configurar variables de entorno antes de inicializar
            if ENVIRONMENT == "development":
                if FIRESTORE_EMULATOR_HOST:
                    os.environ["FIRESTORE_EMULATOR_HOST"] = FIRESTORE_EMULATOR_HOST
                if FIREBASE_AUTH_EMULATOR_HOST:
                    os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = FIREBASE_AUTH_EMULATOR_HOST
                
                print(f"🔧 Conectando a emulador Firestore: {FIRESTORE_EMULATOR_HOST}")
                print(f"🔧 Conectando a emulador Auth: {FIREBASE_AUTH_EMULATOR_HOST}")
            
            # Cargar credenciales desde archivo JSON
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            
            # Inicializar app
            self._app = firebase_admin.initialize_app(cred, {
                'databaseURL': FIREBASE_DATABASE_URL
            })
            
            # Inicializar clientes
            self._firestore_client = firestore.client()
            self._auth_client = auth
            
            print("✅ Firebase Admin SDK inicializado correctamente")
            
            # Mostrar estado
            if ENVIRONMENT == "development":
                print("Modo: DESARROLLO (Emulador)")
            else:
                print("Modo: PRODUCCIÓN")
            
        except FileNotFoundError:
            raise Exception(f"Archivo de credenciales no encontrado: {FIREBASE_CREDENTIALS_PATH}")
        except Exception as e:
            raise Exception(f"Error inicializando Firebase: {str(e)}")
    
    @property
    def firestore(self):
        """Obtener cliente Firestore"""
        return self._firestore_client
    
    @property
    def auth(self):
        """Obtener cliente Auth"""
        return self._auth_client
    
    @property
    def app(self):
        """Obtener app Firebase"""
        return self._app

# Instancia global
firebase_config = FirebaseConfig()
