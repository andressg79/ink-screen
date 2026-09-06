import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.api import state

client = TestClient(app)

@pytest.fixture(autouse=True)
def run_before_and_after_tests():
    # Setup: Reset shared state
    state.custom_message = None
    state.custom_message_expiry = None
    state.clear_alert()
    state.force_refresh_event.clear()
    state.refresh_count = 0
    yield
    # Teardown: Reset shared state
    state.custom_message = None
    state.custom_message_expiry = None
    state.clear_alert()
    state.force_refresh_event.clear()

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Ink Screen REST API activa" in response.json()["message"]

def test_api_status():
    state.system_metrics = {"cpu": 5.0}
    state.weather_metrics = {"temp": "25.0"}
    state.custom_message = "Prueba de estado"
    
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["custom_message"] == "Prueba de estado"
    assert data["system"]["cpu"] == 5.0
    assert data["weather"]["temp"] == "25.0"

def test_post_message_without_duration():
    payload = {"text": "Hola Mundo"}
    response = client.post("/api/message", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["text"] == "Hola Mundo"
    assert data["expires_at"] is None
    
    # Assert state updated
    assert state.custom_message == "Hola Mundo"
    assert state.custom_message_expiry is None
    assert state.force_refresh_event.is_set()

def test_post_message_with_duration():
    payload = {"text": "Mensaje Temporal", "duration": 30}
    response = client.post("/api/message", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["text"] == "Mensaje Temporal"
    assert data["expires_at"] is not None
    
    # Assert state updated
    assert state.custom_message == "Mensaje Temporal"
    assert state.custom_message_expiry is not None
    assert state.force_refresh_event.is_set()

def test_clear_message():
    state.custom_message = "Mensaje a borrar"
    state.custom_message_expiry = 1234567.0
    state.force_refresh_event.clear()
    
    response = client.post("/api/clear")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Assert state cleared
    assert state.custom_message is None
    assert state.custom_message_expiry is None
    assert state.force_refresh_event.is_set()

def test_force_refresh():
    state.force_refresh_event.clear()
    
    response = client.post("/api/refresh")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Assert refresh event triggered
    assert state.force_refresh_event.is_set()

def test_post_alert_success():
    payload = {
        "title": "Alerta de Fuego",
        "text": "Se detectó humo en el sector 4.",
        "avatar": "caballero",
        "duration": 30,
        "footer": "[A] Silenciar"
    }
    response = client.post("/api/alert", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["title"] == "Alerta de Fuego"
    assert data["text"] == "Se detectó humo en el sector 4."
    assert data["avatar"] == "caballero"
    assert data["duration"] == 30
    assert data["footer"] == "[A] Silenciar"
    
    # Assert state is updated
    assert state.alert_title == "Alerta de Fuego"
    assert state.alert_text == "Se detectó humo en el sector 4."
    assert state.alert_avatar == "caballero"
    assert state.alert_footer == "[A] Silenciar"
    assert state.alert_expiry is not None
    assert state.force_refresh_event.is_set()

def test_post_alert_conflict():
    payload1 = {
        "title": "Alerta 1",
        "text": "Mensaje 1",
        "avatar": "bruja",
        "duration": 10
    }
    response1 = client.post("/api/alert", json=payload1)
    assert response1.status_code == 200
    
    # Attempt to post a second alert while first is active
    payload2 = {
        "title": "Alerta 2",
        "text": "Mensaje 2",
        "avatar": "nigromante",
        "duration": 15
    }
    response2 = client.post("/api/alert", json=payload2)
    assert response2.status_code == 409
    assert "Ya hay una alerta activa" in response2.json()["detail"]

def test_clear_alert():
    # Setup active alert
    state.alert_title = "Alerta temporal"
    state.alert_text = "Se va a borrar"
    state.alert_avatar = "brujo"
    state.alert_expiry = 9999999999.0
    state.force_refresh_event.clear()
    
    response = client.post("/api/alert/clear")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Assert cleared
    assert state.alert_title is None
    assert state.alert_text is None
    assert state.alert_avatar is None
    assert state.alert_expiry is None
    assert state.force_refresh_event.is_set()

def test_status_with_alert():
    payload = {
        "title": "Status Alert",
        "text": "Alerta activa",
        "avatar": "elfo",
        "duration": 60
    }
    client.post("/api/alert", json=payload)
    
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["alert_active"] is True
    assert data["alert_title"] == "Status Alert"
    assert data["alert_text"] == "Alerta activa"
    assert data["alert_avatar"] == "elfo"
    assert data["alert_expires_in"] > 0.0

def test_post_alert_invalid_avatar():
    # Test invalid string name
    payload1 = {
        "title": "Error",
        "text": "Prueba",
        "avatar": "orco",
        "duration": 30
    }
    response1 = client.post("/api/alert", json=payload1)
    assert response1.status_code == 422
    assert "no encontrado" in response1.json()["detail"]

def test_set_screen_endpoint():
    # Set to miner
    res = client.post("/api/screen/miner")
    assert res.status_code == 200
    assert "Pantalla fijada a 'miner'" in res.json()["message"]

    # Check status reports miner as current
    status_res = client.get("/api/status")
    assert status_res.status_code == 200
    data = status_res.json()
    assert data["screen"]["current_name"] == "miner"
    assert data["screen"]["is_forced"] is True

    # Reset to auto
    res_auto = client.post("/api/screen/auto")
    assert res_auto.status_code == 200
    assert "Rotación automática reanudada" in res_auto.json()["message"]

    # Invalid screen
    res_err = client.post("/api/screen/pantalla_fantasma")
    assert res_err.status_code == 400

