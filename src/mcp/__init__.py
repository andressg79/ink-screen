"""
Módulo del Servidor MCP (Model Context Protocol) para ink-screen.
Soporta transporte SSE nativo para integración con Antigravity y otros clientes MCP.
"""

from .router import mcp_router

__all__ = ["mcp_router"]
