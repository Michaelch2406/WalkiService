# =====================================================
# Archivo: utils/logger.py
# Propósito: Configuración centralizada de logging
# =====================================================

import logging
import logging.config
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

# Crear carpeta de logs si no existe
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Obtener logger configurado
    
    Args:
        name: Nombre del logger
        
    Returns:
        logging.Logger: Logger configurado
    """
    
    logger = logging.getLogger(name)
    
    # Solo configurar si no tiene handlers
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Formato de logs
        formatter = logging.Formatter(
            '[%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler: Archivo rotativo
        log_file = os.path.join(
            LOG_DIR,
            f"app_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Handler: Consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Agregar handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger
