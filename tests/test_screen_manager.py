import pytest
import time
from src.screen_manager import Screen, ScreenManager

def test_screen_manager_defaults():
    sm = ScreenManager()
    assert len(sm.screens) == 3
    assert sm.screens[0].name == "system"
    assert sm.screens[1].name == "miner"
    assert sm.screens[2].name == "calendar"
    assert sm.rotation_enabled is True
    assert sm.forced_screen is None

def test_screen_manager_rotation():
    sm = ScreenManager()
    sm.screens = [
        Screen("system", "Sistema", 10),
        Screen("miner", "Minero", 5)
    ]
    sm.last_switch_time = 1000.0

    # At 1005.0: 5 seconds elapsed on system (remaining 5) -> should NOT switch
    assert sm.get_current_screen().name == "system"
    assert sm.should_switch(now=1005.0) is False
    assert sm.get_remaining_time(now=1005.0) == 5.0

    # At 1010.0: 10 seconds elapsed -> should switch
    assert sm.should_switch(now=1010.0) is True

    # Switch to next -> miner
    next_s = sm.switch_next(now=1010.0)
    assert next_s.name == "miner"
    assert sm.get_current_screen().name == "miner"
    assert sm.get_remaining_time(now=1010.0) == 5.0

    # At 1015.0: 5 seconds elapsed on miner -> should switch back to system
    assert sm.should_switch(now=1015.0) is True
    back_s = sm.switch_next(now=1015.0)
    assert back_s.name == "system"

def test_screen_manager_forced_screen():
    sm = ScreenManager()
    
    # Set forced to miner
    assert sm.set_forced_screen("miner") is True
    assert sm.forced_screen == "miner"
    assert sm.get_current_screen().name == "miner"
    # Even if time elapses, forced screen should not switch
    assert sm.should_switch(now=time.time() + 9999) is False

    # Try invalid screen
    assert sm.set_forced_screen("invalid_screen") is False
    assert sm.forced_screen == "miner"

    # Reset forced screen (return to auto rotation)
    assert sm.set_forced_screen(None) is True
    assert sm.forced_screen is None

def test_screen_manager_register_screen():
    sm = ScreenManager()
    initial_count = len(sm.screens)
    new_screen = Screen("custom_monitor", "Monitor Personalizado", 45)
    sm.register_screen(new_screen)

    assert len(sm.screens) == initial_count + 1
    assert sm.screens[-1].name == "custom_monitor"

def test_screen_manager_carousel_info():
    sm = ScreenManager()
    sm.screens = [
        Screen("system", "Sistema y Clima", 60),
        Screen("miner", "Nodo Minero XMRig", 30)
    ]
    sm.last_switch_time = time.time()
    info = sm.get_carousel_info()

    assert info["current_name"] == "system"
    assert info["current_title"] == "Sistema y Clima"
    assert info["current_index"] == 1
    assert info["total_screens"] == 2
    assert info["next_name"] == "miner"
    assert info["rotation_enabled"] is True
    assert info["is_forced"] is False
