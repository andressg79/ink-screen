from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
from PIL import Image

@dataclass
class ScreenContext:
    """Contexto de ejecución compartido provisto por el ciclo principal."""
    custom_message: Optional[str] = None
    carousel_info: Optional[Dict[str, Any]] = None

class BaseScreen(ABC):
    """
    Interfaz base que cualquier módulo de pantalla debe implementar
    para conectarse al ciclo de visualización de forma Plug and Play.
    """
    name: str = "base"
    title: str = "Pantalla Base"
    duration: int = 30

    def __init__(self, name: Optional[str] = None, title: Optional[str] = None, duration: Optional[int] = None):
        if name:
            self.name = name
        if title:
            self.title = title
        if duration is not None:
            self.duration = max(5, duration)

    @abstractmethod
    def fetch_data(self) -> dict:
        """
        Recupera las métricas o datos requeridos por la pantalla.
        Puede implementar su propia estrategia interna de caché.
        """
        pass

    @abstractmethod
    def render(self, data: dict, toolkit: Any, context: ScreenContext) -> Image.Image:
        """
        Renderiza el lienzo (296x128 píxeles en modo '1') usando
        las utilidades de dibujo del toolkit provisto.
        """
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__} name='{self.name}' duration={self.duration}s>"
