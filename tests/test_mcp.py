"""
Pruebas automatizadas para el Servidor MCP (SSE y HTTP RPC) de ink-screen.
"""

import json
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.api import state

client = TestClient(app)


def test_mcp_info_endpoint():
    resp = client.get("/mcp/info")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"
    assert data["protocol"] == "Model Context Protocol (MCP)"
    assert data["tools_count"] == 7
    tool_names = [t["name"] for t in data["tools"]]
    assert "get_screen_status" in tool_names
    assert "post_rpg_alert" in tool_names
    assert "clear_rpg_alert" in tool_names
    assert "switch_screen" in tool_names
    assert "post_custom_message" in tool_names
    assert "clear_custom_message" in tool_names
    assert "force_screen_refresh" in tool_names


def test_mcp_rpc_initialize():
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        }
    }
    resp = client.post("/mcp", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert "result" in data
    res = data["result"]
    assert res["serverInfo"]["name"] == "ink-screen"
    assert "tools" in res["capabilities"]


def test_mcp_rpc_notifications():
    req = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }
    resp = client.post("/mcp", json=req)
    assert resp.status_code == 204


def test_mcp_rpc_ping():
    req = {
        "jsonrpc": "2.0",
        "id": "ping-123",
        "method": "ping"
    }
    resp = client.post("/mcp", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "ping-123"
    assert data["result"] == {}


def test_mcp_rpc_tools_list():
    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    }
    resp = client.post("/mcp", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert "tools" in data["result"]
    tools = data["result"]["tools"]
    assert len(tools) == 7


def test_mcp_tool_get_screen_status():
    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "get_screen_status",
            "arguments": {}
        }
    }
    resp = client.post("/mcp", json=req)
    assert resp.status_code == 200
    data = resp.json()
    result = data["result"]
    assert result["isError"] is False
    content = result["content"][0]["text"]
    parsed = json.loads(content)
    assert parsed["status"] == "online"
    assert "screen" in parsed
    assert "system" in parsed


def test_mcp_tool_switch_screen():
    # 1. Switch to 'miner'
    req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "switch_screen",
            "arguments": {"screen": "miner"}
        }
    }
    resp = client.post("/mcp", json=req)
    assert resp.status_code == 200
    result = resp.json()["result"]
    assert result["isError"] is False
    assert "miner" in result["content"][0]["text"]

    # 2. Switch back to 'auto'
    req["params"]["arguments"] = {"screen": "auto"}
    resp = client.post("/mcp", json=req)
    assert resp.status_code == 200
    assert "auto" in resp.json()["result"]["content"][0]["text"]

    # 3. Invalid screen
    req["params"]["arguments"] = {"screen": "invalid_xyz"}
    resp = client.post("/mcp", json=req)
    assert resp.status_code == 200
    assert resp.json()["result"]["isError"] is True


def test_mcp_tool_rpg_alert():
    state.clear_alert()
    # 1. Post alert
    req = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "post_rpg_alert",
            "arguments": {
                "title": "Misión Urgente",
                "text": "Los goblins atacan la aldea.",
                "avatar": "caballero",
                "duration": 15
            }
        }
    }
    resp = client.post("/mcp", json=req)
    assert resp.status_code == 200
    result = resp.json()["result"]
    assert result["isError"] is False
    assert "caballero" in result["content"][0]["text"]
    assert state.alert_title == "Misión Urgente"

    # 2. Duplicate alert while active should error gracefully
    resp_dup = client.post("/mcp", json=req)
    assert resp_dup.json()["result"]["isError"] is True

    # 3. Clear alert
    req_clear = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "clear_rpg_alert",
            "arguments": {}
        }
    }
    resp_clear = client.post("/mcp", json=req_clear)
    assert resp_clear.status_code == 200
    assert resp_clear.json()["result"]["isError"] is False
    assert state.alert_title is None


def test_mcp_tool_custom_message():
    # 1. Post message
    req = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {
            "name": "post_custom_message",
            "arguments": {
                "text": "Hola Antigravity!",
                "duration": 20
            }
        }
    }
    resp = client.post("/mcp", json=req)
    assert resp.status_code == 200
    assert resp.json()["result"]["isError"] is False
    assert state.custom_message == "Hola Antigravity!"

    # 2. Clear message
    req_clear = {
        "jsonrpc": "2.0",
        "id": 8,
        "method": "tools/call",
        "params": {
            "name": "clear_custom_message",
            "arguments": {}
        }
    }
    resp_clear = client.post("/mcp", json=req_clear)
    assert resp_clear.status_code == 200
    assert resp_clear.json()["result"]["isError"] is False
    assert state.custom_message is None


def test_mcp_tool_force_refresh():
    req = {
        "jsonrpc": "2.0",
        "id": 9,
        "method": "tools/call",
        "params": {
            "name": "force_screen_refresh",
            "arguments": {}
        }
    }
    resp = client.post("/mcp", json=req)
    assert resp.status_code == 200
    assert resp.json()["result"]["isError"] is False


def test_mcp_unknown_tool():
    req = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {
            "name": "herramienta_fantasma",
            "arguments": {}
        }
    }
    resp = client.post("/mcp", json=req)
    assert resp.status_code == 200
    assert "error" in resp.json()
    assert resp.json()["error"]["code"] == -32601


def test_mcp_sse_lifecycle():
    from src.mcp.router import mcp_server

    # 1. Crear sesión de prueba directamente en el servidor
    session_id = mcp_server.create_session()
    queue = mcp_server.get_session_queue(session_id)
    assert queue is not None

    # 2. Enviar mensaje a /messages?session_id=...
    req = {
        "jsonrpc": "2.0",
        "id": 99,
        "method": "ping"
    }
    msg_resp = client.post(f"/messages?session_id={session_id}", json=req)
    assert msg_resp.status_code == 202

    # 3. Verificar que la respuesta se encoló para el stream SSE
    assert not queue.empty()
    queued_msg = queue.get_nowait()
    parsed_msg = json.loads(queued_msg)
    assert parsed_msg["id"] == 99
    assert parsed_msg["result"] == {}

    # 4. Limpiar sesión
    mcp_server.close_session(session_id)
    assert mcp_server.get_session_queue(session_id) is None

    # 5. Verificar 404 para sesión inexistente
    msg_fail = client.post("/messages?session_id=sesion_fantasma", json=req)
    assert msg_fail.status_code == 404


