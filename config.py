# =====================================================
# Archivo: config.py (AUTO-DETECTA RED)
# =====================================================

import socket
import os
from dotenv import load_dotenv

load_dotenv()

# Mapeo de redes: SSID o rango de IP → nombre de red
NETWORKS = {
    "CASA": {
        "ssid": "INNO_FLIA_CHASIGUANO_5G",  # ← Cambiar por tu SSID
        "ip_prefix": "192.168.0",
        "ip": "192.168.0.147"
    },
    "INSTITUTO": {
        "ssid": "ESTUDIANTES_IST",  # ← Cambiar por tu SSID
        "ip_prefix": "10.10.0",
        "ip": "10.10.0.142"
    },
    "HOSTPOST": {
        "ssid": "POCO X5 PRO 5G",  # ← Cambiar por tu SSID
        "ip_prefix": "10.246.204",
        "ip": "10.246.204.132"
    },
}

PORT = int(os.getenv("API_PORT", 8000))
TOKEN_EXPIRATION = int(os.getenv("TOKEN_EXPIRATION_MINUTES", 15))


def get_local_ip():
    """Obtener IP local del servidor"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"❌ Error obteniendo IP: {e}")
        return "127.0.0.1"


def get_current_network():
    """Detectar red actual basándose en IP local"""
    current_ip = get_local_ip()
    
    # Buscar coincidencia por rango de IP
    for network_name, network_config in NETWORKS.items():
        if current_ip.startswith(network_config["ip_prefix"]):
            print(f"🌐 Red detectada: {network_name} (IP: {current_ip})")
            return network_name, network_config["ip"]
    
    # Si no coincide, usar CASA por defecto
    print(f"⚠️  Red no reconocida (IP: {current_ip}), usando CASA por defecto")
    return "CASA", NETWORKS["CASA"]["ip"]


def get_base_url():
    """Obtener URL base automáticamente"""
    network_name, ip = get_current_network()
    url = f"http://{ip}:{PORT}"
    return url, network_name


def get_deep_link_base():
    """Obtener URL base para deep link"""
    url, _ = get_base_url()
    return f"{url}/reset-password"


def get_token_expiration():
    """Obtener expiración de token"""
    return TOKEN_EXPIRATION


# Print para debugging
if __name__ == "__main__":
    url, network = get_base_url()
    print(f"\n🌐 Red actual: {network}")
    print(f"📍 URL base: {url}")
    print(f"🔗 Deep link: {get_deep_link_base()}")
    print(f"⏱️  Token expira en: {TOKEN_EXPIRATION} minutos\n")
