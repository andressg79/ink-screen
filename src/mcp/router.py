"""
Router FastAPI para el Servidor MCP (Model Context Protocol).
Implementa transporte dual:
1. Estándar MCP SSE (GET /sse + POST /messages o POST /sse)
2. Endpoint directo JSON-RPC 2.0 HTTP (POST /mcp o POST /rpc o POST /sse)
"""

import asyncio
import json
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

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
            # 1. Evento oficial 'endpoint' con formato estándar de retorno
            endpoint_url = f"/messages?sessionId={session_id}"
            yield f"event: endpoint\r\ndata: {endpoint_url}\r\n\r\n"

            # 2. Bucle de escucha de respuestas
            while True:
                if await request.is_disconnected():
                    break
                try:
                    # Espera con timeout para emitir keep-alives periódicos
                    msg = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"event: message\r\ndata: {msg}\r\n\r\n"
                except asyncio.TimeoutError:
                    # Keep-alive SSE
                    yield ": keepalive\r\n\r\n"
        except asyncio.CancelledError:
            pass
        finally:
            mcp_server.close_session(session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "X-Accel-Buffering": "no"
        }
    )


@mcp_router.post("/sse")
@mcp_router.post("/messages")
@mcp_router.post("/mcp")
@mcp_router.post("/rpc")
async def handle_post_messages_or_rpc(request: Request):
    """
    Manejador unificado para peticiones JSON-RPC 2.0 por POST.
    Soporta:
    - POST /messages?sessionId=... o POST /sse?sessionId=... (asociado a flujo SSE activo)
    - POST /sse, POST /mcp, POST /rpc (modo directo HTTP RPC donde la respuesta viaja en el body)
    """
    session_id = (
        request.query_params.get("sessionId")
        or request.query_params.get("session_id")
        or request.query_params.get("sessionid")
    )

    # Si se especificó una sesión pero no existe o expiró, devolver 404
    if session_id and session_id not in mcp_server.sse_sessions:
        raise HTTPException(
            status_code=404,
            detail=f"Sesión MCP '{session_id}' no encontrada o ya finalizada."
        )

    # El endpoint /messages requiere obligatoriamente una sesión SSE activa
    if request.url.path.rstrip("/").endswith("/messages") and not session_id:
        raise HTTPException(
            status_code=400,
            detail="Se requiere el parámetro 'sessionId' para enviar mensajes al endpoint /messages."
        )

    try:
        body_bytes = await request.body()
        body_json = json.loads(body_bytes.decode("utf-8"))
    except Exception as e:
        err_resp = JSONRPCResponse(
            error=JSONRPCError(
                code=JSONRPCErrorCode.PARSE_ERROR,
                message=f"JSON inválido: {str(e)}"
            )
        )
        if session_id and session_id in mcp_server.sse_sessions:
            queue = mcp_server.sse_sessions[session_id]
            await queue.put(err_resp.model_dump_json(exclude_none=True))
            return Response(status_code=202, content="Accepted")
        return JSONResponse(status_code=400, content=err_resp.model_dump(exclude_none=True))

    # Soporte para single o batch
    if isinstance(body_json, list):
        responses = []
        for item in body_json:
            try:
                rpc_req = JSONRPCRequest.model_validate(item)
                rpc_resp = await mcp_server.dispatch_request(rpc_req)
                if rpc_resp:
                    responses.append(rpc_resp.model_dump(exclude_none=True))
            except Exception as e:
                responses.append(
                    JSONRPCResponse(
                        error=JSONRPCError(code=JSONRPCErrorCode.INVALID_REQUEST, message=str(e))
                    ).model_dump(exclude_none=True)
                )

        if session_id and session_id in mcp_server.sse_sessions:
            queue = mcp_server.sse_sessions[session_id]
            for r in responses:
                await queue.put(json.dumps(r, ensure_ascii=False))
            return Response(status_code=202, content="Accepted")

        return JSONResponse(content=responses)

    # Objeto único JSON-RPC
    try:
        rpc_req = JSONRPCRequest.model_validate(body_json)
    except Exception as e:
        err_resp = JSONRPCResponse(
            error=JSONRPCError(
                code=JSONRPCErrorCode.INVALID_REQUEST,
                message=f"Solicitud JSON-RPC inválida: {str(e)}"
            )
        )
        return JSONResponse(status_code=400, content=err_resp.model_dump(exclude_none=True))

    rpc_resp = await mcp_server.dispatch_request(rpc_req)

    # Si hay una sesión SSE activa registrada, encolamos al stream SSE y devolvemos 202
    if session_id and session_id in mcp_server.sse_sessions:
        if rpc_resp is not None:
            queue = mcp_server.sse_sessions[session_id]
            await queue.put(rpc_resp.model_dump_json(exclude_none=True))
        return Response(status_code=202, content="Accepted")

    # Si no hay sesión SSE (llamada directa como POST /sse o POST /mcp):
    if rpc_resp is None:
        return Response(status_code=204)

    return JSONResponse(content=rpc_resp.model_dump(exclude_none=True))


@mcp_router.get("/mcp/info")
async def handle_mcp_info():
    """
    Devuelve información del servidor MCP y catálogo de herramientas disponibles.
    """
    return {
        "status": "online",
        "protocol": "Model Context Protocol (MCP)",
        "transport": "SSE (Server-Sent Events) + HTTP RPC Directo",
        "endpoints": {
            "sse": "/sse",
            "messages": "/messages?sessionId={id}",
            "rpc": "/mcp"
        },
        "tools_count": len(mcp_server.registry.tools),
        "tools": mcp_server.registry.list_tools()
    }
