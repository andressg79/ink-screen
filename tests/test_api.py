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
    state.force_refresh_event.clear()
    state.refresh_count = 0
    yield
    # Teardown: Reset shared state
    state.custom_message = None
    state.custom_message_expiry = None
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
