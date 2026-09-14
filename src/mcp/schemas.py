"""
Esquemas Pydantic para el protocolo JSON-RPC 2.0 y la especificación MCP (Model Context Protocol).
"""

from enum import IntEnum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class JSONRPCErrorCode(IntEnum):
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603


class JSONRPCError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None


class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any] = Field(default_factory=lambda: {"type": "object", "properties": {}})


class MCPInitializeResult(BaseModel):
    protocolVersion: str = "2024-11-05"
    capabilities: Dict[str, Any] = Field(
        default_factory=lambda: {
            "tools": {
                "listChanged": False
            }
        }
    )
    serverInfo: Dict[str, Any] = Field(
        default_factory=lambda: {
            "name": "ink-screen",
            "version": "1.0.0"
        }
    )
