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
import tiktoken

from config import settings

logger = logging.getLogger(__name__)

# Router
zep_router = APIRouter()

# OpenAI client
openai = AsyncOpenAI(api_key=settings.openai_api_key)

# Token encoding cache
try:
    encoding = tiktoken.encoding_for_model("gpt-4")
except:
    encoding = tiktoken.get_encoding("cl100k_base")  # Fallback

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
    user_name: str = "User",
    model: str = "gpt-4",
    temperature: float = 0.7
) -> AsyncGenerator[str, None]:
    """Generate SSE stream with Zep memory"""
    
    if not zep_client:
        yield f"data: {json.dumps({'error': 'Zep not configured'})}\n\n"
        return
    
    try:
        # 1. Ensure user exists and has current name
        try:
            await zep_client.user.get(user_id=user_id)
            # User exists - update name
            await zep_client.user.update(
                user_id=user_id,
                first_name=user_name
            )
            logger.info(f"[ZEP] Updated user: {user_id} with name: {user_name}")
        except:
            # User doesn't exist - create
            await zep_client.user.add(
                user_id=user_id,
                first_name=user_name,
                metadata={"source": "playground"}
            )
            logger.info(f"[ZEP] Created user: {user_id} with name: {user_name}")
        
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
        
        # 3. Get user memory context (facts only, Zep handles history!)
        memory_count = 0
        
        try:
            memories = await zep_client.memory.get(session_id=session_id)
            
            # Debug logging for memory retrieval
            logger.info(f"[ZEP] Raw memories object: {memories}")
            logger.info(f"[ZEP] Has context: {bool(memories and memories.context)}")
            logger.info(f"[ZEP] Context content: {memories.context if memories and memories.context else 'EMPTY'}")
            if memories and hasattr(memories, 'messages'):
                logger.info(f"[ZEP] Messages count: {len(memories.messages) if memories.messages else 0}")
            
            # Build clean messages structure
            # Combine system prompt with context if available
            system_content = system_prompt
            memory_count = 0
            
            # Add user context/facts if available (NOT the message history!)
            if memories and memories.context:
                system_content += f"\n\nUser context and facts:\n{memories.context}"
                memory_count = len(memories.facts) if hasattr(memories, 'facts') and memories.facts else 0
                logger.info(f"[ZEP] Found context with {memory_count} facts")
            
            messages = [
                {"role": "system", "content": system_content}
            ]
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
        except Exception as e:
            logger.debug(f"[ZEP] No memory yet: {e}")
            # Fallback - simple messages without context
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        
        # Count input tokens
        input_tokens = sum(len(encoding.encode(msg.get('content', ''))) for msg in messages)
        
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
                yield f"data: {json.dumps({'chunk': content})}\n\n"
        
        # Count output tokens
        output_tokens = len(encoding.encode(full_response))
        
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
        
        # Send token counts
        yield f"data: {json.dumps({
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'memory_count': memory_count
        })}\n\n"
        
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
    user_name: str = Query(default="User"),
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
            user_name=user_name,
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
        # Zep doesn't return message count directly, so we need to enhance the response
        enhanced_sessions = []
        for session in sessions:
            session_dict = session.dict() if hasattr(session, 'dict') else session
            # Try to get message count for each session
            try:
                messages = await zep_client.memory.get_session_messages(session_id=session_dict.get('session_id', session_dict.get('id')))
                message_count = len(messages.messages) if hasattr(messages, 'messages') else 0
            except:
                message_count = 0
            
            session_dict['message_count'] = message_count
            enhanced_sessions.append(session_dict)
        
        return enhanced_sessions
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