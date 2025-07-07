"""
Chat API endpoints with Multi-Agent Orchestrator
"""

import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from app.orchestrator.orchestrator import orchestrator
from app.orchestrator.models import StreamChunk
from app.core.security import get_current_user_optional, get_current_user
from app.database.connection import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    try:
        await orchestrator.initialize()
        logger.info("Orchestrator initialized on chat API startup")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
        # Don't fail startup, orchestrator will initialize on first request
    
    yield
    
    # Shutdown
    try:
        await orchestrator.cleanup_sessions()
        logger.info("Orchestrator cleanup completed")
    except Exception as e:
        logger.error(f"Error during orchestrator cleanup: {e}")


router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    agent_slug: Optional[str] = None  # For manual agent selection


class TransferRequest(BaseModel):
    session_id: str
    target_agent: str
    reason: Optional[str] = "User requested transfer"


@router.post("/chat/stream")
async def stream_chat(
    request: ChatMessage,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """
    Stream chat response using orchestrator
    Supports anonymous and authenticated users
    """
    try:
        # Get user ID if authenticated
        logger.info(f"stream_chat: current_user = {current_user}")
        user_id = current_user.get("id") if current_user else None
        logger.info(f"stream_chat: extracted user_id = {user_id}")
        
        # Process message through orchestrator
        async def generate():
            async for chunk in orchestrator.process_message(
                session_id=request.session_id or "anonymous",
                message=request.message,
                user_id=user_id
            ):
                # Convert chunk to SSE format
                data = {
                    "type": chunk.type,
                    "content": chunk.content,
                    "agent_id": chunk.agent_id,
                    "metadata": chunk.metadata,
                    "timestamp": chunk.timestamp.isoformat()
                }
                yield f"data: {json.dumps(data)}\n\n"
            
            # Send end of stream
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        logger.error(f"Chat stream error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/session/{session_id}")
async def get_session_status(
    session_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Get current session status"""
    status = await orchestrator.get_session_status(session_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check access (only authenticated users can see user_id sessions)
    if status.get("user_id") and not current_user:
        raise HTTPException(status_code=403, detail="Authentication required")
    
    if status.get("user_id") and current_user and status["user_id"] != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return status


@router.post("/chat/transfer")
async def transfer_agent(
    request: TransferRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """Manually transfer to a different agent"""
    result = await orchestrator.manual_transfer(
        session_id=request.session_id,
        target_agent=request.target_agent,
        reason=request.reason
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.get("/chat/agents")
async def list_available_agents():
    """List all available agents"""
    agents = await orchestrator.registry.get_all_agents()
    
    return {
        "agents": [
            {
                "slug": agent.slug,
                "name": agent.name,
                "description": agent.description
            }
            for agent in agents
        ],
        "total": len(agents)
    }


@router.get("/orchestrator/status")
async def get_orchestrator_status():
    """Get orchestrator health and metrics"""
    status = await orchestrator.get_status()
    return status.dict()


@router.post("/orchestrator/reload")
async def reload_agents(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Reload agents from database (admin only)"""
    # Check if user is admin
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await orchestrator.reload_agents()
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


# Note: Startup and shutdown are now handled by lifespan context manager above