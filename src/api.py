import time
import asyncio
import logging
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Router definition
router = APIRouter()

# Pydantic schemas
class MessageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=100, description="Texto a mostrar en el footer de la pantalla.")
    duration: Optional[int] = Field(None, ge=5, le=86400, description="Duración en segundos para mostrar el mensaje (opcional).")

class MessageResponse(BaseModel):
    status: str
    message: str
    text: str
    expires_at: Optional[float] = None

class StatusResponse(BaseModel):
    status: str
    custom_message: Optional[str] = None
    custom_message_expires_in: Optional[float] = None
    refresh_count: int
    last_full_refresh: Optional[str] = None
    last_partial_refresh: Optional[str] = None
    system: dict
    weather: dict

# Shared State Class for Thread-Safe & Async Coordination
class DisplayState:
    def __init__(self):
        self.custom_message: Optional[str] = None
        self.custom_message_expiry: Optional[float] = None
        self.force_refresh_event = asyncio.Event()
        self.system_metrics: dict = {}
        self.weather_metrics: dict = {}
        self.refresh_count: int = 0
        self.last_full_refresh: Optional[str] = None
        self.last_partial_refresh: Optional[str] = None
        self.previous_image_buffer: Optional[list] = None

# Singleton state instance
state = DisplayState()

@router.post("/message", response_model=MessageResponse)
async def post_message(req: MessageRequest):
    """
    Publica un mensaje personalizado para mostrar en la sección inferior de la pantalla.
    Opcionalmente se puede definir una duración tras la cual expirará el mensaje.
    """
    logger.info(f"API: Recibido mensaje personalizado: '{req.text}' (duración={req.duration}s)")
    
    state.custom_message = req.text
    if req.duration:
        state.custom_message_expiry = time.time() + req.duration
    else:
        state.custom_message_expiry = None

    # Trigger immediate display refresh
    state.force_refresh_event.set()
    
    return MessageResponse(
        status="success",
        message="Mensaje recibido. Actualizando pantalla...",
        text=req.text,
        expires_at=state.custom_message_expiry
    )

@router.post("/clear")
async def clear_message():
    """
    Limpia cualquier mensaje personalizado activo en pantalla y vuelve a mostrar el estado por defecto.
    """
    logger.info("API: Solicitud de limpieza de mensaje personalizado.")
    state.custom_message = None
    state.custom_message_expiry = None
    
    # Trigger immediate display refresh
    state.force_refresh_event.set()
    
    return {"status": "success", "message": "Mensaje personalizado borrado. Actualizando pantalla..."}

@router.post("/refresh")
async def force_refresh():
    """
    Fuerza una actualización inmediata de la pantalla con datos de clima y sistema frescos.
    """
    logger.info("API: Solicitud de actualización de pantalla forzada.")
    state.force_refresh_event.set()
    return {"status": "success", "message": "Actualización forzada en cola."}

@router.get("/status", response_model=StatusResponse)
async def get_status():
    """
    Devuelve el estado actual de la pantalla, clima almacenado en caché y métricas del sistema.
    """
    expires_in = None
    if state.custom_message_expiry:
        expires_in = max(0.0, state.custom_message_expiry - time.time())
        if expires_in == 0:
            # Clean up if expired
            state.custom_message = None
            state.custom_message_expiry = None
            expires_in = None

    return StatusResponse(
        status="online",
        custom_message=state.custom_message,
        custom_message_expires_in=expires_in,
        refresh_count=state.refresh_count,
        last_full_refresh=state.last_full_refresh,
        last_partial_refresh=state.last_partial_refresh,
        system=state.system_metrics,
        weather=state.weather_metrics
    )
