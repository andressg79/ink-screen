import pytest
from PIL import Image
from src.renderer import ScreenRenderer

def test_renderer_initialization():
    renderer = ScreenRenderer()
    assert renderer is not None

def test_renderer_output_dimensions():
    renderer = ScreenRenderer()
    
    mock_system = {
        "cpu": 10.0,
        "temp": 40.0,
        "ram": 50.0,
        "disk": 20.0,
        "ip": "127.0.0.1",
        "uptime": "1h"
    }
    mock_weather = {
        "temp": "20.0",
        "condition": "Despejado",
        "icon": "☀️",
        "humidity": "50%",
        "wind": "10.0"
    }
    
    img = renderer.render(mock_system, mock_weather)
    
    # Assert type, size, and mode
    assert isinstance(img, Image.Image)
    assert img.size == (296, 128)
    assert img.mode == "1"

def test_renderer_with_custom_message():
    renderer = ScreenRenderer()
    
    mock_system = {}
    mock_weather = {}
    msg = "Mensaje Corto"
    
    img = renderer.render(mock_system, mock_weather, custom_message=msg)
    assert img.size == (296, 128)
    
    # Render with long message to check handling
    long_msg = "Este es un mensaje extremadamente largo para probar el truncamiento en el footer"
    img_long = renderer.render(mock_system, mock_weather, custom_message=long_msg)
    assert img_long.size == (296, 128)

def test_renderer_with_alert():
    renderer = ScreenRenderer()
    
    mock_system = {}
    mock_weather = {}
    alert = {
        "title": "Alerta de Prueba",
        "text": "Este es un texto para verificar el renderizado de la alerta RPG retro a pantalla completa.",
        "avatar": "caballero",
        "footer": "[A] Continuar"
    }
    
    img = renderer.render(mock_system, mock_weather, alert=alert)
    assert img.size == (296, 128)
    assert img.mode == "1"

def test_renderer_with_4shade_character_names():
    renderer = ScreenRenderer()
    mock_system = {}
    mock_weather = {}
    
    # Render with string-based avatar "elfo"
    alert = {
        "title": "Elf talking",
        "text": "The elf winks and says hello.",
        "avatar": "elfo"
    }
    img = renderer.render(mock_system, mock_weather, alert=alert)
    assert img.size == (296, 128)
    assert img.mode == "1"
