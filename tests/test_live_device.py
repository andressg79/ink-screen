import time
import sys
import requests

DEVICE_URL = "http://orangepirv2.local:8000"

def run_live_tests():
    print(f"--- Iniciando pruebas de integración en el dispositivo: {DEVICE_URL} ---")
    
    # 1. Verificar estado inicial
    print("\n1. Obteniendo estado inicial...")
    try:
        res = requests.get(f"{DEVICE_URL}/api/status")
        if res.status_code != 200:
            print(f"❌ Error: El dispositivo retornó status code {res.status_code}")
            sys.exit(1)
        data = res.json()
        print(f"✅ Dispositivo responde correctamente (status: {data.get('status')})")
        print(f"   Alerta activa inicial: {data.get('alert_active')}")
    except Exception as e:
        print(f"❌ Error de conexión con el dispositivo: {e}")
        sys.exit(1)

    # Si hay una alerta activa remanente, limpiarla primero
    if data.get('alert_active'):
        print("   Limpiando alerta previa activa...")
        requests.post(f"{DEVICE_URL}/api/alert/clear")
        time.sleep(1)

    # 2. Publicar una nueva alerta RPG
    print("\n2. Publicando nueva alerta RPG a pantalla completa...")
    payload = {
        "title": "Alerta de Red",
        "text": "Prueba de integración remota en ejecución. Todo marcha perfecto.",
        "image_id": 4,  # Robot
        "duration": 60,
        "footer": "⌛ [ PROBANDO RED... ]"
    }
    res = requests.post(f"{DEVICE_URL}/api/alert", json=payload)
    if res.status_code != 200:
        print(f"❌ Error al publicar alerta: {res.status_code} - {res.text}")
        sys.exit(1)
    
    data = res.json()
    print("✅ Alerta publicada con éxito:")
    print(f"   Mensaje de respuesta: '{data.get('message')}'")
    print(f"   Expira en timestamp: {data.get('expires_at')}")

    # 3. Verificar estado actual (debe reportar alerta activa)
    print("\n3. Verificando estado tras publicar la alerta...")
    res = requests.get(f"{DEVICE_URL}/api/status")
    data = res.json()
    if not data.get("alert_active"):
        print("❌ Error: La alerta debería estar activa, pero alert_active es False")
        sys.exit(1)
    
    print("✅ Alerta activa en estado:")
    print(f"   Título en pantalla: '{data.get('alert_title')}'")
    print(f"   Texto en pantalla: '{data.get('alert_text')}'")
    print(f"   ID de imagen: {data.get('alert_image_id')}")
    print(f"   Tiempo restante: {data.get('alert_expires_in') or 0.0:.2f}s")

    # 4. Probar manejo de conflictos (superposición de alertas)
    print("\n4. Intentando superponer una segunda alerta (debe retornar 409 Conflict)...")
    conflict_payload = {
        "title": "Alerta Conflicto",
        "text": "Este texto no debería mostrarse.",
        "image_id": 1,
        "duration": 10
    }
    res = requests.post(f"{DEVICE_URL}/api/alert", json=conflict_payload)
    if res.status_code == 409:
        print("✅ Conflicto detectado correctamente. Respuesta HTTP 409 Conflict:")
        print(f"   Mensaje detallado: '{res.json().get('detail')}'")
    else:
        print(f"❌ Error: Se esperaba HTTP 409 Conflict, pero se obtuvo {res.status_code}")
        sys.exit(1)

    # 5. Limpieza manual de la alerta
    print("\n5. Limpiando la alerta manualmente antes de que expire...")
    res = requests.post(f"{DEVICE_URL}/api/alert/clear")
    if res.status_code != 200:
        print(f"❌ Error al limpiar alerta: {res.status_code} - {res.text}")
        sys.exit(1)
    
    # 6. Verificar que la pantalla haya vuelto a la normalidad
    print("\n6. Verificando estado tras la limpieza...")
    res = requests.get(f"{DEVICE_URL}/api/status")
    data = res.json()
    if data.get("alert_active"):
        print("❌ Error: La alerta sigue activa tras llamar a /api/alert/clear")
        sys.exit(1)
    
    print("✅ Alerta inactiva en estado. La pantalla vuelve a mostrar el dashboard por defecto.")
    print("\n🎉 --- ¡Pruebas de integración finalizadas exitosamente! ---")

if __name__ == "__main__":
    run_live_tests()
