"""
Servidor MCP (Model Context Protocol) para ink-screen.
Maneja el protocolo JSON-RPC 2.0 y coordina las sesiones SSE.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, Optional

from .schemas import (
    JSONRPCErrorCode,
    JSONRPCError,
    JSONRPCRequest,
    JSONRPCResponse,
    MCPInitializeResult,
)
from .tools import MCPToolsRegistry

logger = logging.getLogger("mcp_server")


class MCPServer:
    def __init__(self, registry: Optional[MCPToolsRegistry] = None):
        self.registry = registry or MCPToolsRegistry()
        self.sse_sessions: Dict[str, asyncio.Queue] = {}

    def create_session(self) -> str:
        """Crea una nueva sesión SSE con su propia cola de mensajes."""
        session_id = uuid.uuid4().hex
        self.sse_sessions[session_id] = asyncio.Queue()
        logger.info(f"Sesión MCP SSE iniciada: {session_id} (Total activas: {len(self.sse_sessions)})")
        return session_id

    def close_session(self, session_id: str):
        """Cierra y limpia una sesión SSE."""
        if session_id in self.sse_sessions:
            del self.sse_sessions[session_id]
            logger.info(f"Sesión MCP SSE cerrada: {session_id} (Total activas: {len(self.sse_sessions)})")

    def get_session_queue(self, session_id: str) -> Optional[asyncio.Queue]:
        return self.sse_sessions.get(session_id)

    async def dispatch_request(self, req: JSONRPCRequest) -> Optional[JSONRPCResponse]:
        """
        Procesa y enruta peticiones JSON-RPC 2.0 según la especificación MCP.
        """
        method = req.method.strip()

        # 1. Handshake inicial
        if method == "initialize":
            init_result = MCPInitializeResult()
            return JSONRPCResponse(id=req.id, result=init_result.model_dump())

        # 2. Notificaciones del cliente (no retornan respuesta en JSON-RPC)
        if method == "notifications/initialized" or method.startswith("notifications/"):
            logger.debug(f"Notificación MCP recibida: {method}")
            return None

        # 3. Ping
        if method == "ping":
            return JSONRPCResponse(id=req.id, result={})

        # 4. Listado de herramientas
        if method == "tools/list":
            tools_list = self.registry.list_tools()
            return JSONRPCResponse(id=req.id, result={"tools": tools_list})

        # 5. Ejecución de herramientas
        if method == "tools/call":
            params = req.params or {}
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})

            if not tool_name:
                return JSONRPCResponse(
                    id=req.id,
                    error=JSONRPCError(
                        code=JSONRPCErrorCode.INVALID_PARAMS,
                        message="Falta el parámetro 'name' de la herramienta a ejecutar."
                    )
                )

            try:
                result = await self.registry.execute_tool(tool_name, tool_args)
                return JSONRPCResponse(id=req.id, result=result)
            except ValueError as ve:
                return JSONRPCResponse(
                    id=req.id,
                    error=JSONRPCError(
                        code=JSONRPCErrorCode.METHOD_NOT_FOUND,
                        message=str(ve)
                    )
                )
            except Exception as e:
                logger.exception(f"Error ejecutando herramienta MCP '{tool_name}': {e}")
                return JSONRPCResponse(
                    id=req.id,
                    error=JSONRPCError(
                        code=JSONRPCErrorCode.INTERNAL_ERROR,
                        message=f"Error interno al ejecutar '{tool_name}': {str(e)}"
                    )
                )

        # Método no implementado
        return JSONRPCResponse(
            id=req.id,
            error=JSONRPCError(
                code=JSONRPCErrorCode.METHOD_NOT_FOUND,
                message=f"Método MCP desconocido: '{method}'"
            )
        )
