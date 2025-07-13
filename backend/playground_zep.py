"""
Playground with Zep memory integration
Ultra simple - just SSE streaming + Zep sessions
"""
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
import json
import logging
import time
import uuid
from typing import AsyncGenerator

from config import settings

logger = logging.getLogger(__name__)

# Router
zep_router = APIRouter()

# OpenAI client
openai = AsyncOpenAI(api_key=settings.openai_api_key)

# Zep client
zep_client = None
try:
    from zep_cloud.client import AsyncZep
    from zep_cloud import Message as ZepMessage
    
    if settings.zep_api_key:
        zep_client = AsyncZep(api_key=settings.zep_api_key)
        logger.info("[ZEP] Client initialized")
except ImportError:
    logger.warning("[ZEP] zep-cloud package not installed")
except Exception as e:
    logger.error(f"[ZEP] Init failed: {e}")


async def generate_zep_stream(
    session_id: str,
    agent_slug: str,
    system_prompt: str,
    message: str,
    user_id: str,
    model: str = "gpt-4",
    temperature: float = 0.7
) -> AsyncGenerator[str, None]:
    """Generate SSE stream with Zep memory"""
    
    if not zep_client:
        yield f"data: {json.dumps({'error': 'Zep not configured'})}\n\n"
        return
    
    try:
        # 1. Ensure user exists
        try:
            await zep_client.user.get(user_id=user_id)
        except:
            await zep_client.user.add(
                user_id=user_id,
                metadata={"source": "playground"}
            )
            logger.info(f"[ZEP] Created user: {user_id}")
        
        # 2. Create session if doesn't exist
        try:
            await zep_client.memory.get_session(session_id)
            logger.info(f"[ZEP] Using existing session: {session_id}")
        except:
            # Session doesn't exist, create it
            await zep_client.memory.add_session(
                session_id=session_id,
                user_id=user_id
            )
            logger.info(f"[ZEP] Created new session: {session_id}")
        
        # 3. Get user memory context
        memory_context = ""
        memory_count = 0
        
        try:
            # Get memory for this specific session (will be empty for new session)
            # For user context across sessions, we'd need different approach
            memories = await zep_client.memory.get(
                session_id=session_id
            )
            
            if memories:
                # Add context (facts from user's entire history)
                if memories.context:
                    memory_context += f"\n\n{memories.context}"
                    memory_count = len(memories.facts) if hasattr(memories, 'facts') and memories.facts else 0
                    logger.info(f"[ZEP] Found context with {memory_count} facts")
                
                # Also add recent messages from this session (if any)
                if memories.messages and len(memories.messages) > 0:
                    memory_context += "\n\nRecent messages in this session:\n"
                    for msg in memories.messages:  # All messages
                        memory_context += f"{msg.role}: {msg.content}\n"
                    logger.info(f"[ZEP] Added {len(memories.messages)} session messages")
                
        except Exception as e:
            logger.debug(f"[ZEP] No memory yet: {e}")
        
        # 4. Build messages
        messages = [
            {"role": "system", "content": system_prompt + memory_context},
            {"role": "user", "content": message}
        ]
        
        # 5. Stream from OpenAI
        stream = await openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True
        )
        
        full_response = ""
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                yield f"data: {json.dumps({'chunk': content, 'memory_count': memory_count})}\n\n"
        
        # 6. Save to Zep
        try:
            zep_messages = [
                ZepMessage(
                    role="human",
                    content=message,
                    role_type="user"
                ),
                ZepMessage(
                    role="ai",
                    content=full_response,
                    role_type="assistant"
                )
            ]
            
            await zep_client.memory.add(
                session_id=session_id,
                messages=zep_messages
            )
            logger.info(f"[ZEP] Saved to session: {session_id}")
            
        except Exception as e:
            logger.error(f"[ZEP] Failed to save: {e}")
        
        # Done
        yield f"data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"[ZEP] Stream error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


@zep_router.get("/sse")
async def playground_zep_sse(
    session_id: str = Query(...),
    agent_slug: str = Query(...),
    system_prompt: str = Query(...),
    message: str = Query(...),
    user_id: str = Query(...),
    model: str = Query(default="gpt-4"),
    temperature: float = Query(default=0.7)
):
    """Playground SSE endpoint with Zep memory"""
    return StreamingResponse(
        generate_zep_stream(
            session_id=session_id,
            agent_slug=agent_slug,
            system_prompt=system_prompt,
            message=message,
            user_id=user_id,
            model=model,
            temperature=temperature
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


@zep_router.get("/sessions")
async def get_user_sessions(user_id: str = Query(...)):
    """Get all sessions for a user"""
    if not zep_client:
        return {"error": "Zep not configured"}
    
    try:
        sessions = await zep_client.user.get_sessions(user_id=user_id)
        return sessions
    except Exception as e:
        logger.error(f"[ZEP] Failed to get sessions: {e}")
        return {"error": str(e)}


@zep_router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Get all messages from a session"""
    if not zep_client:
        return {"error": "Zep not configured"}
    
    try:
        messages = await zep_client.memory.get_session_messages(session_id=session_id)
        return messages
    except Exception as e:
        logger.error(f"[ZEP] Failed to get messages: {e}")
        return {"error": str(e)}