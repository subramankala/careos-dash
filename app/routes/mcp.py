from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from app.config import settings
from app.dependencies import mcp_service
from app.schemas import MCPCallRequest, MCPCallResponse, MCPToolsResponse

router = APIRouter(prefix="/mcp", tags=["mcp"])


def _verify_mcp_api_key(x_mcp_api_key: str | None) -> None:
    configured = settings.mcp_api_key.strip()
    if not configured:
        return
    if x_mcp_api_key != configured:
        raise HTTPException(status_code=401, detail="invalid mcp api key")


@router.get("/tools", response_model=MCPToolsResponse)
def list_tools(x_mcp_api_key: str | None = Header(default=None)) -> MCPToolsResponse:
    _verify_mcp_api_key(x_mcp_api_key)
    return MCPToolsResponse(tools=mcp_service.list_tools())


@router.post("/call", response_model=MCPCallResponse)
def call_tool(payload: MCPCallRequest, x_mcp_api_key: str | None = Header(default=None)) -> MCPCallResponse:
    _verify_mcp_api_key(x_mcp_api_key)
    result = mcp_service.call_tool(payload.tool, payload.arguments)
    return MCPCallResponse(ok=True, result=result)
