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

def test_render_miner_normal():
    renderer = ScreenRenderer()
    mock_system = {"cpu": 15.0, "temp": 32.5}
    mock_miner = {
        "status": "MINANDO",
        "hashrate_10s": 125.4,
        "hashrate_60s": 120.0,
        "hashrate_max": 145.0,
        "shares_good": 15,
        "shares_rejected": 0,
        "diff_formatted": "1.28M",
        "pool": "gulf.moneroocean.stream:20128",
        "uptime": "2h 30m",
        "algo": "rx/0",
        "threads": 8,
        "hugepages": "100%"
    }
    carousel_info = {
        "rotation_enabled": True,
        "total_screens": 2,
        "current_index": 2,
        "next_title": "Sistema",
        "time_remaining_sec": 20
    }

    img = renderer.render_miner(mock_miner, mock_system, carousel_info=carousel_info)
    assert isinstance(img, Image.Image)
    assert img.size == (296, 128)
    assert img.mode == "1"

def test_render_miner_paused_and_offline():
    renderer = ScreenRenderer()
    mock_system = {"cpu": 50.0, "temp": 45.0}
    
    # Pausado
    paused_miner = {"status": "PAUSADO (Watchdog)", "hashrate_10s": 0.0}
    img_paused = renderer.render_miner(paused_miner, mock_system)
    assert img_paused.size == (296, 128)

    # Offline
    offline_miner = {"status": "OFFLINE", "hashrate_10s": 0.0}
    img_offline = renderer.render_miner(offline_miner, mock_system)
    assert img_offline.size == (296, 128)

def test_render_miner_with_custom_message():
    renderer = ScreenRenderer()
    mock_system = {}
    mock_miner = {"status": "MINANDO", "hashrate_10s": 100.0}
    msg = "Alerta: Reinicio de servidor"
    
    img = renderer.render_miner(mock_miner, mock_system, custom_message=msg)
    assert img.size == (296, 128)

