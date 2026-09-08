import pytest
from PIL import Image
from src.screens.base import BaseScreen, ScreenContext
from src.screens.system_screen import SystemScreen
from src.screens.miner_screen import MinerScreen
from src.screen_manager import ScreenManager
from src.renderer import ScreenRenderer

def test_screen_context():
    ctx = ScreenContext(custom_message="Hola Mundo", carousel_info={"current_index": 1, "total_screens": 3})
    assert ctx.custom_message == "Hola Mundo"
    assert ctx.carousel_info["total_screens"] == 3

def test_system_screen():
    screen = SystemScreen(duration=45)
    assert screen.name == "system"
    assert screen.title == "Sistema y Clima"
    assert screen.duration == 45

    data = screen.fetch_data()
    assert "system" in data
    assert "weather" in data

    renderer = ScreenRenderer()
    ctx = ScreenContext(custom_message="Testing System", carousel_info={"current_index": 1, "total_screens": 2, "rotation_enabled": True})
    img = screen.render(data, toolkit=renderer, context=ctx)
    assert isinstance(img, Image.Image)
    assert img.size == (296, 128)
    assert img.mode == "1"

def test_miner_screen():
    screen = MinerScreen(duration=25)
    assert screen.name == "miner"
    assert screen.title == "Nodo Minero XMRig"
    assert screen.duration == 25

    data = screen.fetch_data()
    assert "miner" in data
    assert "system" in data

    renderer = ScreenRenderer()
    ctx = ScreenContext(custom_message="Mining test", carousel_info={"current_index": 2, "total_screens": 2, "rotation_enabled": True})
    img = screen.render(data, toolkit=renderer, context=ctx)
    assert isinstance(img, Image.Image)
    assert img.size == (296, 128)
    assert img.mode == "1"

def test_plug_and_play_custom_screen():
    class BitcoinTickerScreen(BaseScreen):
        name = "bitcoin"
        title = "Bitcoin Price"
        duration = 15

        def fetch_data(self):
            return {"price_usd": 65432.10, "change_24h": "+3.4%"}

        def render(self, data, toolkit, context):
            img = Image.new("1", (296, 128), 255)
            # Custom screen can render anything
            return img

    sm = ScreenManager()
    btc_screen = BitcoinTickerScreen()
    sm.register_screen(btc_screen)

    assert any(s.name == "bitcoin" for s in sm.screens)
    
    # Force or rotate to bitcoin
    assert sm.set_forced_screen("bitcoin") is True
    curr = sm.get_current_screen()
    assert curr.name == "bitcoin"
    assert curr.title == "Bitcoin Price"
    
    # Test fetch and render
    data = curr.fetch_data()
    assert data["price_usd"] == 65432.10
    
    renderer = ScreenRenderer()
    ctx = ScreenContext()
    img = curr.render(data, toolkit=renderer, context=ctx)
    assert isinstance(img, Image.Image)
    assert img.size == (296, 128)
