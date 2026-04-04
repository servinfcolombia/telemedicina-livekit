"""
Script de prueba para verificar la conexión con LiveKit
"""
import os
import sys
import jwt
import time

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "APIUTCtpP7uaVRG")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "A3xGzgKfgyMejcdXCtOnyXdSN2dfgDz6T4OeQPNUi0EC")
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "http://localhost:7880")

print("=" * 60)
print("CONFIGURACIÓN")
print("=" * 60)
print(f"LIVEKIT_API_KEY: {LIVEKIT_API_KEY}")
print(f"LIVEKIT_API_SECRET: {LIVEKIT_API_SECRET}")
print(f"LIVEKIT_URL: {LIVEKIT_URL}")

def generate_token(room_name: str, identity: str, name: str) -> str:
    """Genera un token JWT para LiveKit"""
    now = int(time.time())
    exp = now + 3600
    
    # Claims de video grants - permisos completos
    video_grants = {
        "room_join": True,
        "room": room_name,
        "can_publish": True,
        "can_subscribe": True,
        "can_publish_data": True,
        "can_update_metadata": True,
    }
    
    payload = {
        "iss": LIVEKIT_API_KEY,
        "sub": identity,
        "name": name,
        "exp": exp,
        "nbf": now,
        "video": video_grants,
        "metadata": "",
    }
    
    token = jwt.encode(payload, LIVEKIT_API_SECRET, algorithm="HS256")
    return token

def test_token_generation():
    """Prueba la generación de tokens"""
    print("\n" + "=" * 60)
    print("PRUEBA 1: Generación de Token")
    print("=" * 60)
    
    token = generate_token(
        room_name="test_room",
        identity="test_user",
        name="Test User"
    )
    
    print(f"Token generado: {token[:50]}...")
    
    # Decodificar para verificar
    decoded = jwt.decode(token, options={"verify_signature": False})
    print(f"\nToken decodificado:")
    print(f"  - iss (issuer): {decoded.get('iss')}")
    print(f"  - sub (subject): {decoded.get('sub')}")
    print(f"  - name: {decoded.get('name')}")
    print(f"  - video grants: {decoded.get('video')}")
    
    return token

def verify_api_key_match():
    """Verifica que las API keys coincidan"""
    print("\n" + "=" * 60)
    print("PRUEBA 2: Verificación de API Keys")
    print("=" * 60)
    
    # Del .env
    env_key = os.getenv("LIVEKIT_API_KEY")
    env_secret = os.getenv("LIVEKIT_API_SECRET")
    
    print(f"API Key en .env: {env_key}")
    print(f"API Secret en .env: {env_secret}")
    
    # Del contenedor Docker (hardcoded en el comando)
    docker_key = "APIUTCtpP7uaVRG"
    docker_secret = "A3xGzgKfgyMejcdXCtOnyXdSN2dfgDz6T4OeQPNUi0EC"
    
    print(f"\nAPI Key en LiveKit Docker: {docker_key}")
    print(f"API Secret en LiveKit Docker: {docker_secret}")
    
    if env_key == docker_key and env_secret == docker_secret:
        print("\n[OK] Las API keys COINCIDEN")
    else:
        print("\n[ERROR] Las API keys NO COINCIDEN!")
        print("  Actualiza el archivo .env con los valores correctos")

def test_livekit_server():
    """Verifica que el servidor LiveKit esté corriendo"""
    print("\n" + "=" * 60)
    print("PRUEBA 3: Conexión al Servidor LiveKit")
    print("=" * 60)
    
    import urllib.request
    import json
    
    try:
        # Verificar que el servidor esté corriendo
        req = urllib.request.Request(f"{LIVEKIT_URL}/health")
        with urllib.request.urlopen(req, timeout=5) as response:
            print(f"✓ Servidor LiveKit responding: {response.status}")
    except Exception as e:
        print(f"✗ Error conectando al servidor: {e}")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SCRIPT DE PRUEBA PARA LIVEKIT")
    print("=" * 60)
    
    # Ejecutar pruebas
    verify_api_key_match()
    test_livekit_server()
    token = test_token_generation()
    
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Token de prueba: {token}")
    print("\nPara probar en el navegador, llama a:")
    print("POST http://localhost:8000/api/livekit/token")
    print("Con body: {roomName, userName, userIdentity}")
