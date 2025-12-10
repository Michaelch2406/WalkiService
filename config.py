# =====================================================
# Archivo: config.py (AUTO-DETECTA RED - MULTIPLATAFORMA)
# =====================================================

import socket
import os
import platform
import subprocess
import re
from typing import Tuple, Optional, Dict
from dotenv import load_dotenv
import httpx

load_dotenv()

# Mapeo de redes: SSID o rango de IP → nombre de red
NETWORKS = {
    "CASA": {
        "ssid": "INNO_FLIA_CHASIGUANO_5G",
        "ip_prefix": "192.168.0",
        "ip": "192.168.0.147"
    },
    "INSTITUTO": {
        "ssid": "ESTUDIANTES_IST",
        "ip_prefix": "10.10.0",
        "ip": "10.10.0.142"
    },
    "HOSTPOST": {
        "ssid": "POCO X5 PRO 5G",
        "ip_prefix": "10.246.204",
        "ip": "10.246.204.132"
    },
}

PORT = int(os.getenv("API_PORT", 8000))
TOKEN_EXPIRATION = int(os.getenv("TOKEN_EXPIRATION_MINUTES", 15))
DEFAULT_NETWORK = os.getenv("DEFAULT_NETWORK", "CASA")
APP_ENV = os.getenv("APP_ENV", "DEV") # Por defecto a DEV si no está definida
# Overrides opcionales para enlaces externos (no rompen la detección actual)
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")
DEEP_LINK_BASE_ENV = os.getenv("DEEP_LINK_BASE")

def get_public_ip() -> Optional[str]:
    """
    Obtiene la IP pública del servidor usando un servicio externo.
    
    Returns:
        Optional[str]: La dirección IP pública o None si falla.
    """
    try:
        with httpx.Client(timeout=5) as client:
            response = client.get("https://api.ipify.org?format=json")
            response.raise_for_status()
            ip = response.json()["ip"]
            if _is_valid_ip(ip):
                print(f"✅ IP pública detectada: {ip}")
                return ip
    except httpx.RequestError as e:
        print(f"❌ Error al contactar el servicio de IP: {e}")
    except Exception as e:
        print(f"❌ Error inesperado al obtener IP pública: {e}")
    return None


def get_local_ip() -> str:
    """
    Obtener IP local del servidor con múltiples fallbacks.
    
    Returns:
        str: Dirección IP local o 127.0.0.1 si falla
    """
    methods = [
        _get_ip_via_socket,
        _get_ip_via_hostname,
        _get_ip_from_interfaces
    ]
    
    for method in methods:
        try:
            ip = method()
            if ip and ip != "127.0.0.1" and _is_valid_ip(ip):
                return ip
        except Exception as e:
            # Silenciado para no ensuciar logs de producción
            # print(f"⚠️  Método {method.__name__} falló: {e}")
            continue
    
    print("⚠️ No se pudo detectar IP local, usando localhost")
    return "127.0.0.1"


def _get_ip_via_socket() -> str:
    """Método principal: conectar a servidor externo para obtener IP"""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(2)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]


def _get_ip_via_hostname() -> str:
    """Método alternativo: resolver hostname"""
    hostname = socket.gethostname()
    return socket.gethostbyname(hostname)


def _get_ip_from_interfaces() -> str:
    """Método de respaldo: leer interfaces de red"""
    system = platform.system()
    
    if system == "Linux":
        return _get_ip_linux()
    elif system == "Windows":
        return _get_ip_windows()
    elif system == "Darwin":  # macOS
        return _get_ip_macos()
    
    raise RuntimeError(f"Sistema operativo no soportado: {system}")


def _get_ip_linux() -> str:
    """Obtener IP en Linux usando ip o ifconfig"""
    try:
        # Intentar con 'ip' (más moderno)
        result = subprocess.run(
            ["ip", "route", "get", "1"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            match = re.search(r'src\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    try:
        # Fallback a ifconfig
        result = subprocess.run(
            ["ifconfig"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            matches = re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            for ip in matches:
                if not ip.startswith("127."):
                    return ip
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    raise RuntimeError("No se pudo obtener IP en Linux")


def _get_ip_windows() -> str:
    """Obtener IP en Windows usando ipconfig"""
    try:
        result = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            # Buscar IPv4 (evitando 127.x.x.x y direcciones de túneles)
            matches = re.findall(r'IPv4.*?:\s*(\d+\.\d+\.\d+\.\d+)', result.stdout)
            for ip in matches:
                if not ip.startswith(("127.", "169.254.")):
                    return ip
    except subprocess.SubprocessError:
        pass
    
    raise RuntimeError("No se pudo obtener IP en Windows")


def _get_ip_macos() -> str:
    """Obtener IP en macOS"""
    try:
        result = subprocess.run(
            ["ifconfig"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            matches = re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            for ip in matches:
                if not ip.startswith("127."):
                    return ip
    except subprocess.SubprocessError:
        pass
    
    raise RuntimeError("No se pudo obtener IP en macOS")


def _is_valid_ip(ip: str) -> bool:
    """Validar formato de dirección IP"""
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False


def get_current_ssid() -> Optional[str]:
    """
    Detectar SSID de la red WiFi actual (opcional, puede fallar).
    
    Returns:
        Optional[str]: SSID de la red o None si no se puede detectar
    """
    # En producción, no necesitamos SSID
    if APP_ENV == 'PROD':
        return None

    system = platform.system()
    
    try:
        if system == "Linux":
            result = subprocess.run(
                ["iwgetid", "-r"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return result.stdout.strip()
        
        elif system == "Windows":
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                match = re.search(r'SSID\s*:\s*(.+)', result.stdout)
                if match:
                    return match.group(1).strip()
        
        elif system == "Darwin":  # macOS
            result = subprocess.run(
                ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                match = re.search(r'\sSSID:\s*(.+)', result.stdout)
                if match:
                    return match.group(1).strip()
    
    except Exception as e:
        print(f"⚠️  No se pudo detectar SSID: {e}")
    
    return None


def get_current_network() -> Tuple[str, str]:
    """
    Detecta la configuración de red actual basándose en el entorno (PROD/DEV).
    
    Returns:
        Tuple[str, str]: (nombre_de_red, ip_configurada)
    """
    # Entorno de Producción (AWS, etc.)
    if APP_ENV == 'PROD':
        print("🚀 Entorno de Producción detectado.")
        public_ip = get_public_ip()
        if public_ip:
            return "PROD", public_ip
        else:
            print("❌ FATAL: No se pudo obtener la IP pública. Usando localhost como fallback.")
            return "PROD_FALLBACK", "127.0.0.1"

    # Entorno de Desarrollo (Local)
    current_ip = get_local_ip()
    
    # Prioridad 1: Detectar por SSID
    current_ssid = get_current_ssid()
    if current_ssid:
        for network_name, network_config in NETWORKS.items():
            if "ssid" in network_config and network_config["ssid"] == current_ssid:
                print(f"🏠 Red de desarrollo detectada por SSID: {network_name} ({current_ssid})")
                return network_name, network_config["ip"]
    
    # Prioridad 2: Detectar por rango de IP
    for network_name, network_config in NETWORKS.items():
        if "ip_prefix" in network_config and current_ip.startswith(network_config["ip_prefix"]):
            print(f"🏠 Red de desarrollo detectada por IP: {network_name} (IP: {current_ip})")
            return network_name, network_config["ip"]
    
    # Fallback para desarrollo: Usar red por defecto
    if DEFAULT_NETWORK in NETWORKS:
        print(f"⚠️  Red de desarrollo no reconocida (IP: {current_ip}), usando {DEFAULT_NETWORK} por defecto")
        return DEFAULT_NETWORK, NETWORKS[DEFAULT_NETWORK]["ip"]
    else:
        print(f"⚠️  Red de desarrollo no reconocida y sin default. Usando primera red disponible.")
        first_network = next(iter(NETWORKS.keys()))
        return first_network, NETWORKS[first_network]["ip"]


def detect_tailscale_ip() -> Optional[str]:
    """
    Intentar detectar la IP de Tailscale (rango 100.x.x.x) recorriendo interfaces conocidas.
    Usa psutil o netifaces si estan disponibles; si no, retorna None.
    """
    prefixes = ("tailscale", "ts", "tun")

    try:
        import psutil  # type: ignore
        for name, addrs in psutil.net_if_addrs().items():
            lname = name.lower()
            if not any(lname.startswith(p) for p in prefixes):
                continue
            for addr in addrs:
                if getattr(addr, "family", None) == socket.AF_INET:
                    ip = getattr(addr, "address", "")
                    if ip and ip.startswith("100."):
                        return ip
    except ImportError:
        pass
    except Exception as e:
        print(f"Warning: No se pudo detectar Tailscale via psutil: {e}")

    try:
        import netifaces  # type: ignore
        for name in netifaces.interfaces():
            lname = name.lower()
            if not any(lname.startswith(p) for p in prefixes):
                continue
            addrs = netifaces.ifaddresses(name).get(netifaces.AF_INET, [])
            for addr in addrs:
                ip = addr.get("addr")
                if ip and ip.startswith("100."):
                    return ip
    except ImportError:
        pass
    except Exception as e:
        print(f"Warning: No se pudo detectar Tailscale via netifaces: {e}")

    return None

def get_base_url() -> Tuple[str, str]:
    """
    Obtener URL base automáticamente.
    
    Returns:
        Tuple[str, str]: (url_completa, nombre_de_red)
    """
    # Permite forzar una URL pública (ej. Tailscale, dominio o ngrok) sin modificar la
    # detección por red local. Ej: PUBLIC_BASE_URL=http://100.x.x.x:8000
    if PUBLIC_BASE_URL:
        return PUBLIC_BASE_URL, "PUBLIC_BASE_URL"

    ts_ip = detect_tailscale_ip()
    if ts_ip:
        return f"http://{ts_ip}:{PORT}", "TAILSCALE"

    network_name, ip = get_current_network()
    url = f"http://{ip}:{PORT}"
    return url, network_name


def get_deep_link_base() -> str:
    """
    Obtener URL base para deep link.
    
    Returns:
        str: URL completa para reset password
    """
    # Permite fijar el deep link completo (ej. https://mi-dominio/reset-password)
    if DEEP_LINK_BASE_ENV:
        return DEEP_LINK_BASE_ENV

    url, _ = get_base_url()
    return f"{url}/reset-password"


def get_token_expiration() -> int:
    """
    Obtener expiración de token en minutos.
    
    Returns:
        int: Minutos de expiración
    """
    return TOKEN_EXPIRATION


def print_network_info():
    """Imprimir información de red para debugging"""
    print("\n" + "="*50)
    print(f"▶️  Modo de entorno: {APP_ENV}")
    print(f"🖥️  Sistema operativo: {platform.system()} {platform.release()}")
    print(f"💻 Hostname: {socket.gethostname()}")
    
    if APP_ENV != 'PROD':
        current_ip = get_local_ip()
        print(f"📍 IP local detectada: {current_ip}")
        current_ssid = get_current_ssid()
        if current_ssid:
            print(f"📶 SSID actual: {current_ssid}")
        else:
            print(f"📶 SSID: No detectado (conexión Ethernet o permiso denegado)")
    
    url, network = get_base_url()
    print(f"\n🌐 Red configurada: {network}")
    print(f"🔗 URL base: {url}")
    print(f"🔐 Deep link: {get_deep_link_base()}")
    print(f"⏱️  Token expira en: {TOKEN_EXPIRATION} minutos")
    print("="*50 + "\n")


# Ejecutar debugging si se corre directamente
if __name__ == "__main__":
    print_network_info()
