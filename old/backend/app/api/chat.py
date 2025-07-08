"""
Chat API endpoints - simplified version
Direct and simple!
"""

import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from app.orchestrator.orchestrator import orchestrator
from app.core.security import get_current_user_optional

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    """Initialize orchestrator on startup"""
    try:
        await orchestrator.initialize()
        logger.info("Orchestrator initialized")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")
    
    yield
    
    # Cleanup not needed for simple version


router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    agent_slug: str = "misunderstanding_protector"


@router.post("/chat/stream")
async def stream_chat(
    request: ChatMessage,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """
    Stream chat response
    Super simple: message in → response out
    """
    try:
        # Get user ID if authenticated
        user_id = current_user.get("id") if current_user else None
        logger.info(f"Chat request from user: {user_id or 'anonymous'}")
        
        # Stream response
        async def generate():
            async for chunk in orchestrator.process_message(
                message=request.message,
                user_id=user_id,
                agent_slug=request.agent_slug
            ):
                # JSON format for frontend compatibility
                data = {
                    "type": "content",
                    "content": chunk,
                    "agent_id": request.agent_slug
                }
                yield f"data: {json.dumps(data)}\n\n"
            
            # End of stream
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/agents")
async def list_agents():
    """List all available agents"""
    agents = await orchestrator.get_agents()
    
    return {
        "agents": [
            {
                "slug": agent.slug,
                "name": agent.name,
                "description": agent.description
            }
            for agent in agents.values()
        ]
    }


@router.post("/chat/reload-agents")
async def reload_agents():
    """Reload agents from database"""
    count = await orchestrator.reload_agents()
    return {"success": True, "agents_loaded": count}