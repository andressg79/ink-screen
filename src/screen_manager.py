import os
import time
import logging
from typing import List, Optional, Dict, Any
from src.screens.base import BaseScreen
from src.screens.system_screen import SystemScreen
from src.screens.miner_screen import MinerScreen
from src.screens.calendar_screen import CalendarScreen

logger = logging.getLogger(__name__)

class Screen(BaseScreen):
    """
    Clase de pantalla genérica para retrocompatibilidad y pantallas ad-hoc.
    """
    def __init__(self, name: str, title: str, duration: int):
        super().__init__(name=name, title=title, duration=duration)

    def fetch_data(self) -> dict:
        return {}

    def render(self, data: dict, toolkit: Any, context: Any) -> Any:
        return None

class ScreenManager:
    """
    Gestor de pantallas y carrusel extensible con duraciones configurables
    y control de transiciones en el ciclo de visualización.
    """
    def __init__(self):
        # Duraciones configurables por entorno
        system_duration = int(os.getenv("SCREEN_SYSTEM_DURATION", "60"))
        miner_duration = int(os.getenv("SCREEN_MINER_DURATION", "30"))
        calendar_duration = int(os.getenv("SCREEN_CALENDAR_DURATION", "30"))
        rotation_env = os.getenv("SCREEN_ROTATION_ENABLED", "1").lower()
        self.rotation_enabled = rotation_env in ("1", "true", "yes")

        # Registro de módulos de pantalla por defecto
        self.screens: List[BaseScreen] = [
            SystemScreen(duration=system_duration),
            MinerScreen(duration=miner_duration),
            CalendarScreen(duration=calendar_duration)
        ]
        
        self.current_index: int = 0
        self.last_switch_time: float = time.time()
        self.forced_screen: Optional[str] = None

    def register_screen(self, screen: BaseScreen):
        """Permite registrar nuevas pantallas dinámicamente para futuros monitores Plug & Play."""
        self.screens.append(screen)
        logger.info(f"ScreenManager: Registrada nueva pantalla '{screen.name}' ({screen.duration}s)")

    def get_current_screen(self) -> Screen:
        """Devuelve la pantalla que corresponde mostrar en este momento."""
        if self.forced_screen:
            for s in self.screens:
                if s.name == self.forced_screen:
                    return s
        if not self.screens:
            return Screen("system", "Sistema", 60)
        return self.screens[self.current_index % len(self.screens)]

    def get_remaining_time(self, now: Optional[float] = None) -> float:
        """Devuelve los segundos restantes de la pantalla actual antes de rotar."""
        if now is None:
            now = time.time()
        curr = self.get_current_screen()

        # Si la pantalla está fijada o la rotación deshabilitada, calcula el intervalo cíclico normal
        if not self.rotation_enabled or self.forced_screen is not None:
            elapsed = (now - self.last_switch_time) % curr.duration
            return max(5.0, curr.duration - elapsed)

        elapsed = now - self.last_switch_time
        remaining = max(0.0, curr.duration - elapsed)
        return remaining

    def reset_timer(self, now: Optional[float] = None):
        """Reinicia el temporizador de la pantalla activa tras completarse la actualización física."""
        if now is None:
            now = time.time()
        self.last_switch_time = now

    def should_switch(self, now: Optional[float] = None) -> bool:
        """Evalúa si ha transcurrido la duración de la pantalla actual."""
        if not self.rotation_enabled or self.forced_screen is not None:
            return False
        return self.get_remaining_time(now) <= 0.0

    def switch_next(self, now: Optional[float] = None) -> Screen:
        """Avanza a la siguiente pantalla del carrusel y reinicia el temporizador."""
        if now is None:
            now = time.time()
        self.current_index = (self.current_index + 1) % len(self.screens)
        self.last_switch_time = now
        curr = self.get_current_screen()
        logger.info(f"ScreenManager: Rotando a pantalla '{curr.name}' ({curr.duration}s)")
        return curr

    def set_forced_screen(self, name: Optional[str]) -> bool:
        """Fija una pantalla específica o reanuda la rotación si se pasa None."""
        if name is None:
            self.forced_screen = None
            self.last_switch_time = time.time()
            logger.info("ScreenManager: Reanudada rotación automática.")
            return True

        name_clean = name.lower().strip()
        for s in self.screens:
            if s.name == name_clean:
                self.forced_screen = name_clean
                self.last_switch_time = time.time()
                logger.info(f"ScreenManager: Pantalla fijada a '{name_clean}'.")
                return True

        logger.warning(f"ScreenManager: Intento de fijar pantalla inexistente '{name}'.")
        return False

    def get_carousel_info(self) -> Dict[str, Any]:
        """Devuelve información estructurada del carrusel para el footer y la API."""
        now = time.time()
        curr = self.get_current_screen()
        idx = self.current_index % len(self.screens)
        next_idx = (idx + 1) % len(self.screens)
        next_screen = self.screens[next_idx]
        remaining = int(self.get_remaining_time(now))

        return {
            "current_name": curr.name,
            "current_title": curr.title,
            "current_index": idx + 1,
            "total_screens": len(self.screens),
            "next_name": next_screen.name,
            "next_title": next_screen.title,
            "time_remaining_sec": remaining,
            "rotation_enabled": self.rotation_enabled,
            "is_forced": self.forced_screen is not None
        }

# Instancia singleton
screen_manager = ScreenManager()
