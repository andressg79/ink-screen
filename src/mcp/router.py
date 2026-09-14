"""
Router FastAPI para el Servidor MCP (Model Context Protocol).
Implementa transporte SSE (GET /sse + POST /messages) y HTTP RPC directo (POST /mcp).
"""

import asyncio
import json
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse

from .schemas import (
    JSONRPCErrorCode,
    JSONRPCError,
    JSONRPCRequest,
    JSONRPCResponse,
)
from .server import MCPServer

logger = logging.getLogger("mcp_router")

mcp_router = APIRouter(tags=["MCP"])
mcp_server = MCPServer()


@mcp_router.get("/sse")
async def handle_sse(request: Request):
    """
    Endpoint SSE (Server-Sent Events) del protocolo MCP.
    Inicia la conexión de eventos y emite el evento 'endpoint' con la URL para POST /messages.
    """
    session_id = mcp_server.create_session()
    queue = mcp_server.get_session_queue(session_id)

    async def event_generator():
        try:
            # 1. Evento inicial con la URL de retorno para mensajes
            endpoint_url = f"/messages?session_id={session_id}"
            yield f"event: endpoint\ndata: {endpoint_url}\n\n"

            # 2. Bucle de escucha de respuestas
            while True:
                if await request.is_disconnected():
                    break
                try:
                    # Espera con timeout para emitir keep-alives periódicos
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"event: message\ndata: {msg}\n\n"
                except asyncio.TimeoutError:
                    # Keep-alive SSE (comentario)
                    yield ": ping\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            mcp_server.close_session(session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@mcp_router.post("/messages")
async def handle_messages(request: Request, session_id: str = Query(..., description="ID de sesión MCP")):
    """
    Endpoint para recibir mensajes JSON-RPC 2.0 de clientes MCP conectados por SSE.
    """
    queue = mcp_server.get_session_queue(session_id)
    if not queue:
        raise HTTPException(
            status_code=404,
            detail=f"Sesión MCP '{session_id}' no encontrada o ya finalizada."
        )

    try:
        body_bytes = await request.body()
        body_json = json.loads(body_bytes.decode("utf-8"))
        req = JSONRPCRequest.model_validate(body_json)
    except Exception as e:
        err_resp = JSONRPCResponse(
            error=JSONRPCError(
                code=JSONRPCErrorCode.PARSE_ERROR,
                message=f"JSON-RPC inválido: {str(e)}"
            )
        )
        await queue.put(err_resp.model_dump_json(exclude_none=True))
        return Response(status_code=202)

    response = await mcp_server.dispatch_request(req)
    if response is not None:
        await queue.put(response.model_dump_json(exclude_none=True))

    return Response(status_code=202)


@mcp_router.post("/mcp", response_model=Optional[JSONRPCResponse])
async def handle_mcp_rpc(req: JSONRPCRequest):
    """
    Endpoint directo HTTP JSON-RPC 2.0 (alternativa sin SSE para pruebas o clientes directos).
    """
    response = await mcp_server.dispatch_request(req)
    if response is None:
        return Response(status_code=204)
    return response


@mcp_router.get("/mcp/info")
async def handle_mcp_info():
    """
    Devuelve información del servidor MCP y catálogo de herramientas disponibles.
    """
    return {
        "status": "online",
        "protocol": "Model Context Protocol (MCP)",
        "transport": "SSE (Server-Sent Events) + HTTP RPC",
        "endpoints": {
            "sse": "/sse",
            "messages": "/messages?session_id={id}",
            "rpc": "/mcp"
        },
        "tools_count": len(mcp_server.registry.tools),
        "tools": mcp_server.registry.list_tools()
    }
