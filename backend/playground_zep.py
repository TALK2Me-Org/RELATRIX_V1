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
    
    session_id = f"session_{uuid.uuid4()}"
    
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
        
        # 2. Create new session
        await zep_client.memory.add_session(
            session_id=session_id,
            user_id=user_id
        )
        logger.info(f"[ZEP] Created session: {session_id}")
        
        # 3. Get user memory context
        memory_context = ""
        memory_count = 0
        
        try:
            # Get memory for this specific session (will be empty for new session)
            # For user context across sessions, we'd need different approach
            memories = await zep_client.memory.get(
                session_id=session_id
            )
            
            if memories and memories.messages:
                memory_context = "\n\nPrevious conversation:\n"
                for msg in memories.messages[-10:]:  # Last 10 messages
                    memory_context += f"{msg.role}: {msg.content}\n"
                memory_count = len(memories.messages)
                
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