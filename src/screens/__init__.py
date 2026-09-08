from .base import BaseScreen, ScreenContext
from .system_screen import SystemScreen
from .miner_screen import MinerScreen

__all__ = [
    "BaseScreen",
    "ScreenContext",
    "SystemScreen",
    "MinerScreen",
    "get_default_screens",
]

def get_default_screens():
    """Retorna las instancias de pantalla por defecto configuradas."""
    return [
        SystemScreen(),
        MinerScreen()
    ]
