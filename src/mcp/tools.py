"""
Registro e implementación de herramientas MCP para ink-screen.
Interactúa directamente en memoria con el estado del servidor (state, screen_manager).
"""

import time
import json
import logging
from typing import Any, Dict, List, Optional
from src.api import state
from src.screen_manager import screen_manager
from src.pixel_art import SPRITES, load_sprites
from .schemas import MCPToolDefinition

logger = logging.getLogger("mcp_tools")

VALID_AVATARS = [
    "caballero", "brujo", "bruja", "nigromante",
    "elfo", "ogro", "enano", "doncella", "paisano"
]

VALID_SCREENS = ["system", "miner", "calendar", "auto"]


class MCPToolsRegistry:
    def __init__(self):
        self.tools: Dict[str, MCPToolDefinition] = {}
        self._register_tools()

    def _register_tools(self):
        # 1. get_screen_status
        self.tools["get_screen_status"] = MCPToolDefinition(
            name="get_screen_status",
            description=(
                "Obtiene el estado completo actual del sistema y de la pantalla E-Ink, "
                "incluyendo la pantalla activa en pantalla, estado de rotación del carrusel, "
                "métricas del hardware (CPU, Temp, RAM, Disco, IP, Uptime), estado de minería XMRig, "
                "clima local y estado de alertas."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )

        # 2. post_rpg_alert
        self.tools["post_rpg_alert"] = MCPToolDefinition(
            name="post_rpg_alert",
            description=(
                "Muestra una alerta visual a pantalla completa con estética RPG retro de 8-bits "
                "en la pantalla E-Ink. Incluye un retrato pixel art monocromático a la izquierda "
                "y texto de diálogo con recuadro temático."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Título centrado superior de la alerta (1 a 25 caracteres).",
                        "minLength": 1,
                        "maxLength": 25
                    },
                    "text": {
                        "type": "string",
                        "description": "Mensaje principal o diálogo de la alerta RPG (1 a 120 caracteres).",
                        "minLength": 1,
                        "maxLength": 120
                    },
                    "avatar": {
                        "type": "string",
                        "description": "Personaje pixel art a mostrar.",
                        "enum": VALID_AVATARS,
                        "default": "paisano"
                    },
                    "duration": {
                        "type": "integer",
                        "description": "Duración de visualización en pantalla en segundos (mínimo 5, máximo 86400). Por defecto 30.",
                        "default": 30,
                        "minimum": 5,
                        "maximum": 86400
                    },
                    "footer": {
                        "type": "string",
                        "description": "Texto personalizado opcional para la franja inferior (máximo 40 caracteres).",
                        "maxLength": 40
                    }
                },
                "required": ["title", "text"],
                "additionalProperties": False
            }
        )

        # 3. clear_rpg_alert
        self.tools["clear_rpg_alert"] = MCPToolDefinition(
            name="clear_rpg_alert",
            description="Limpia de inmediato cualquier alerta RPG activa en pantalla y reanuda el carrusel normal.",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )

        # 4. switch_screen
        self.tools["switch_screen"] = MCPToolDefinition(
            name="switch_screen",
            description=(
                "Fija la pantalla E-Ink a un módulo específico ('system', 'miner', 'calendar') "
                "o reanuda la rotación automática del carrusel ('auto')."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "screen": {
                        "type": "string",
                        "description": "Nombre de la pantalla destino o 'auto' para reanudar rotación.",
                        "enum": VALID_SCREENS
                    }
                },
                "required": ["screen"],
                "additionalProperties": False
            }
        )

        # 5. post_custom_message
        self.tools["post_custom_message"] = MCPToolDefinition(
            name="post_custom_message",
            description="Publica un mensaje personalizado en el sistema con duración opcional en segundos.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Texto del mensaje (1 a 100 caracteres).",
                        "minLength": 1,
                        "maxLength": 100
                    },
                    "duration": {
                        "type": "integer",
                        "description": "Duración opcional en segundos.",
                        "minimum": 5,
                        "maximum": 86400
                    }
                },
                "required": ["text"],
                "additionalProperties": False
            }
        )

        # 6. clear_custom_message
        self.tools["clear_custom_message"] = MCPToolDefinition(
            name="clear_custom_message",
            description="Elimina cualquier mensaje personalizado activo en el sistema.",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )

        # 7. force_screen_refresh
        self.tools["force_screen_refresh"] = MCPToolDefinition(
            name="force_screen_refresh",
            description="Dispara una actualización inmediata del hardware E-Ink.",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        )

    def list_tools(self) -> List[Dict[str, Any]]:
        return [tool.model_dump() for tool in self.tools.values()]

    async def execute_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        arguments = arguments or {}
        handler_name = f"_handle_{name}"
        handler = getattr(self, handler_name, None)
        if not handler:
            raise ValueError(f"Herramienta desconocida: '{name}'")
        return await handler(arguments)

    # --- Tool Handlers ---

    async def _handle_get_screen_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        now = time.time()
        expires_in = None
        if state.custom_message_expiry:
            expires_in = max(0.0, state.custom_message_expiry - now)
            if expires_in == 0:
                state.custom_message = None
                state.custom_message_expiry = None
                expires_in = None

        alert_expires_in = None
        alert_active = False
        if state.alert_expiry:
            alert_expires_in = max(0.0, state.alert_expiry - now)
            if alert_expires_in == 0:
                state.clear_alert()
                alert_expires_in = None
            else:
                alert_active = True

        carousel_info = screen_manager.get_carousel_info()

        status_data = {
            "status": "online",
            "screen": carousel_info,
            "alert": {
                "active": alert_active,
                "title": state.alert_title,
                "text": state.alert_text,
                "avatar": state.alert_avatar,
                "expires_in_sec": round(alert_expires_in, 1) if alert_expires_in else None
            },
            "custom_message": {
                "text": state.custom_message,
                "expires_in_sec": round(expires_in, 1) if expires_in else None
            },
            "system": state.system_metrics,
            "weather": state.weather_metrics,
            "miner": state.miner_metrics,
            "refresh_stats": {
                "refresh_count": state.refresh_count,
                "last_full_refresh": state.last_full_refresh,
                "last_partial_refresh": state.last_partial_refresh
            }
        }
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(status_data, indent=2, ensure_ascii=False)
                }
            ],
            "isError": False
        }

    async def _handle_post_rpg_alert(self, args: Dict[str, Any]) -> Dict[str, Any]:
        now = time.time()
        if state.alert_expiry and now < state.alert_expiry:
            rem = round(state.alert_expiry - now, 1)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Ya hay una alerta activa ('{state.alert_title}') expira en {rem}s. Use 'clear_rpg_alert' primero si desea sobreescribirla."
                    }
                ],
                "isError": True
            }

        title = str(args.get("title", "")).strip()
        text = str(args.get("text", "")).strip()
        avatar = str(args.get("avatar", "paisano")).lower().strip()
        duration = int(args.get("duration", 30))
        footer = args.get("footer")

        if not SPRITES:
            load_sprites()

        if avatar not in SPRITES:
            avatar = "paisano"

        state.alert_title = title
        state.alert_text = text
        state.alert_avatar = avatar
        state.alert_footer = footer
        state.alert_expiry = now + duration

        # Disparar actualización inmediata
        state.force_refresh_event.set()

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Alerta RPG '{title}' activada con avatar '{avatar}' por {duration} segundos. Pantalla E-Ink actualizándose."
                }
            ],
            "isError": False
        }

    async def _handle_clear_rpg_alert(self, args: Dict[str, Any]) -> Dict[str, Any]:
        state.clear_alert()
        state.force_refresh_event.set()
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Alerta RPG limpiada con éxito. Carrusel normal reanudado."
                }
            ],
            "isError": False
        }

    async def _handle_switch_screen(self, args: Dict[str, Any]) -> Dict[str, Any]:
        screen_target = args.get("screen", "auto").lower().strip()
        target = None if screen_target in ("auto", "none", "clear") else screen_target

        success = screen_manager.set_forced_screen(target)
        if not success:
            avail = [s.name for s in screen_manager.screens] + ["auto"]
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Pantalla '{screen_target}' no válida. Opciones: {', '.join(avail)}"
                    }
                ],
                "isError": True
            }

        state.force_refresh_event.set()
        msg = f"Pantalla fijada a '{target}'." if target else "Rotación automática reanudada ('auto')."
        return {
            "content": [
                {
                    "type": "text",
                    "text": msg
                }
            ],
            "isError": False
        }

    async def _handle_post_custom_message(self, args: Dict[str, Any]) -> Dict[str, Any]:
        msg_text = str(args.get("text", "")).strip()
        dur = args.get("duration")

        state.custom_message = msg_text
        if dur:
            state.custom_message_expiry = time.time() + int(dur)
        else:
            state.custom_message_expiry = None

        state.force_refresh_event.set()
        exp_info = f" (expira en {dur}s)" if dur else ""
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Mensaje personalizado publicado: '{msg_text}'{exp_info}."
                }
            ],
            "isError": False
        }

    async def _handle_clear_custom_message(self, args: Dict[str, Any]) -> Dict[str, Any]:
        state.custom_message = None
        state.custom_message_expiry = None
        state.force_refresh_event.set()
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Mensaje personalizado eliminado."
                }
            ],
            "isError": False
        }

    async def _handle_force_screen_refresh(self, args: Dict[str, Any]) -> Dict[str, Any]:
        state.force_refresh_event.set()
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Señal de refresco inmediato enviada al hardware E-Ink."
                }
            ],
            "isError": False
        }
