"""
HTTP wrapper for MCP Server
Provides HTTP endpoints to interact with MCP server
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import json

from server import RelatrixMCPServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RELATRIX MCP Server HTTP API")

# Initialize MCP server
mcp_server = None

class ToolCallRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any]

class ToolCallResponse(BaseModel):
    result: Any
    success: bool
    error: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Initialize MCP server on startup"""
    global mcp_server
    try:
        mcp_server = RelatrixMCPServer()
        logger.info("MCP Server initialized via HTTP wrapper")
    except Exception as e:
        logger.error(f"Failed to initialize MCP server: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "RELATRIX MCP Server",
        "transport": "http"
    }

@app.get("/tools")
async def list_tools():
    """List available tools"""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    # Get tool information from MCP server
    tools = []
    # This would need to be implemented to extract tool info from FastMCP
    # For now, return hardcoded list
    tools = [
        {"name": "switch_agent", "description": "Switch to a different agent"},
        {"name": "get_agent_info", "description": "Get agent information"},
        {"name": "list_agents", "description": "List all available agents"},
        {"name": "process_message", "description": "Process a message"},
        {"name": "get_transfer_history", "description": "Get transfer history"},
        {"name": "get_session_context", "description": "Get session context"}
    ]
    
    return {"tools": tools, "total": len(tools)}

@app.post("/tools/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    """Call a specific tool"""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    try:
        # This would need proper implementation to call MCP tools
        # For now, return placeholder response
        result = f"Called {request.tool} with args: {request.arguments}"
        
        return ToolCallResponse(
            result=result,
            success=True
        )
    except Exception as e:
        logger.error(f"Error calling tool {request.tool}: {e}")
        return ToolCallResponse(
            result=None,
            success=False,
            error=str(e)
        )

@app.get("/agents")
async def list_agents():
    """List all available agents"""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    agents = mcp_server.agent_registry.get_all_agents()
    return {"agents": agents, "total": len(agents)}

@app.get("/agents/current")
async def get_current_agent():
    """Get current active agent"""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")
    
    current = mcp_server.agent_registry.get_current_agent()
    agent_info = mcp_server.agent_registry.get_agent_info(current)
    
    return {
        "current_agent": current,
        "agent_info": agent_info
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)