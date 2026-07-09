import time
import asyncio
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
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

class AlertRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=25, description="Título centrado de la alerta RPG.")
    text: str = Field(..., min_length=1, max_length=120, description="Texto del cuerpo de la alerta RPG.")
    image_id: int = Field(..., ge=1, le=5, description="ID de la imagen pixel art a mostrar (1: Knight, 2: Mage, 3: Slime, 4: Robot, 5: Heart).")
    duration: int = Field(..., ge=5, le=86400, description="Duración en segundos para mostrar la alerta.")
    footer: Optional[str] = Field(None, max_length=40, description="Texto personalizado para el footer de la alerta RPG (opcional).")

class AlertResponse(BaseModel):
    status: str
    message: str
    title: str
    text: str
    image_id: int
    duration: int
    expires_at: float
    footer: Optional[str] = None

class StatusResponse(BaseModel):
    status: str
    custom_message: Optional[str] = None
    custom_message_expires_in: Optional[float] = None
    alert_active: bool = False
    alert_title: Optional[str] = None
    alert_text: Optional[str] = None
    alert_image_id: Optional[int] = None
    alert_expires_in: Optional[float] = None
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
        
        # RPG Alert state fields
        self.alert_title: Optional[str] = None
        self.alert_text: Optional[str] = None
        self.alert_image_id: Optional[int] = None
        self.alert_footer: Optional[str] = None
        self.alert_expiry: Optional[float] = None

    def clear_alert(self):
        self.alert_title = None
        self.alert_text = None
        self.alert_image_id = None
        self.alert_footer = None
        self.alert_expiry = None

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

@router.post("/alert", response_model=AlertResponse)
async def post_alert(req: AlertRequest):
    """
    Publica una alerta a pantalla completa con estilo RPG retro y un retrato de pixel art.
    Si ya hay una alerta activa en pantalla, se rechaza con código 409 Conflict.
    """
    now = time.time()
    if state.alert_expiry and now < state.alert_expiry:
        logger.warning("API: Intento de publicar alerta rechazado (ya hay una alerta activa).")
        raise HTTPException(
            status_code=409,
            detail="Ya hay una alerta activa en pantalla. Espere a que expire o bórrela manualmente."
        )

    logger.info(f"API: Recibida alerta RPG: '{req.title}' - '{req.text}' (duración={req.duration}s)")
    
    state.alert_title = req.title
    state.alert_text = req.text
    state.alert_image_id = req.image_id
    state.alert_footer = req.footer
    state.alert_expiry = now + req.duration

    # Trigger immediate display refresh
    state.force_refresh_event.set()

    return AlertResponse(
        status="success",
        message="Alerta recibida. Actualizando pantalla...",
        title=req.title,
        text=req.text,
        image_id=req.image_id,
        duration=req.duration,
        expires_at=state.alert_expiry,
        footer=req.footer
    )

@router.post("/alert/clear")
async def clear_alert_endpoint():
    """
    Limpia cualquier alerta RPG activa y vuelve a mostrar el estado por defecto.
    """
    logger.info("API: Solicitud de limpieza de alerta RPG.")
    state.clear_alert()
    
    # Trigger immediate display refresh
    state.force_refresh_event.set()
    
    return {"status": "success", "message": "Alerta RPG borrada. Actualizando pantalla..."}

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
    now = time.time()
    
    expires_in = None
    if state.custom_message_expiry:
        expires_in = max(0.0, state.custom_message_expiry - now)
        if expires_in == 0:
            # Clean up if expired
            state.custom_message = None
            state.custom_message_expiry = None
            expires_in = None

    # Clean up alert if expired
    alert_expires_in = None
    alert_active = False
    if state.alert_expiry:
        alert_expires_in = max(0.0, state.alert_expiry - now)
        if alert_expires_in == 0:
            state.clear_alert()
            alert_expires_in = None
        else:
            alert_active = True

    return StatusResponse(
        status="online",
        custom_message=state.custom_message,
        custom_message_expires_in=expires_in,
        alert_active=alert_active,
        alert_title=state.alert_title,
        alert_text=state.alert_text,
        alert_image_id=state.alert_image_id,
        alert_expires_in=alert_expires_in,
        refresh_count=state.refresh_count,
        last_full_refresh=state.last_full_refresh,
        last_partial_refresh=state.last_partial_refresh,
        system=state.system_metrics,
        weather=state.weather_metrics
    )
