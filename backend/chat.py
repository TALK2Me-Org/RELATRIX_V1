"""
Chat endpoint with SSE streaming
Core logic for agent switching
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import logging
import json
from openai import AsyncOpenAI

from database import get_db, Agent
from auth import get_current_user, security
from memory_service import search_memories, add_memory
from agent_parser import extract_agent_slug, remove_agent_json
from config import settings

logger = logging.getLogger(__name__)

# Router
chat_router = APIRouter()

# Test endpoint for agent switching
@chat_router.get("/test-switch")
async def test_agent_switch():
    """Test endpoint to verify agent switching logic"""
    
    # Test JSON detection
    test_response = 'Hello, I understand you need help. {"agent": "emotional_vomit"} Let me help you.'
    detected = extract_agent_slug(test_response)
    cleaned = remove_agent_json(test_response)
    
    # Test fallback
    fallback_test = await should_switch_agent(
        "I'm feeling very angry and need to vent",
        "misunderstanding_protector"
    )
    
    return {
        "json_detection": {
            "test_response": test_response,
            "detected_agent": detected,
            "cleaned_response": cleaned
        },
        "fallback_test": {
            "message": "I'm feeling very angry and need to vent",
            "current_agent": "misunderstanding_protector",
            "suggested_agent": fallback_test
        }
    }

# OpenAI client
openai = AsyncOpenAI(api_key=settings.openai_api_key)


async def get_current_user_sse(
    token: Optional[str] = Query(None, description="JWT token for SSE"),
    credentials = Depends(security)
) -> Optional[dict]:
    """Get current user from JWT token - supports both header and query param"""
    import jwt
    from fastapi.security import HTTPAuthorizationCredentials
    
    # Try header first (standard auth)
    if credentials:
        try:
            payload = jwt.decode(
                credentials.credentials,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            logger.info(f"[AUTH] User authenticated via header: {payload['email']}")
            return {"id": payload["sub"], "email": payload["email"]}
        except jwt.PyJWTError as e:
            logger.error(f"[AUTH] Header token decode error: {e}")
    
    # Try query param (for SSE)
    if token:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            logger.info(f"[AUTH] User authenticated via query param: {payload['email']}")
            return {"id": payload["sub"], "email": payload["email"]}
        except jwt.PyJWTError as e:
            logger.error(f"[AUTH] Query token decode error: {e}")
    
    logger.warning("[AUTH] No valid authentication found")
    return None


async def should_switch_agent(message: str, current_agent: str) -> Optional[str]:
    """
    Fallback agent switching logic
    Used when agent doesn't include JSON in response
    """
    try:
        prompt = f"""Current agent: {current_agent}
User message: {message}

Should we switch to a different agent? Reply ONLY with the agent slug or "no":
- emotional_vomit (for venting emotions)
- solution_finder (for action plans)
- conflict_solver (for mediation)
- communication_simulator (for practice)
- misunderstanding_protector (for understanding)
- no (stay with current agent)

Reply with just the slug or "no"."""

        response = await openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=20,
            temperature=0
        )
        
        result = response.choices[0].message.content.strip().lower()
        if result != "no" and result in [
            "emotional_vomit", "solution_finder", "conflict_solver",
            "communication_simulator", "misunderstanding_protector",
            "empathy_amplifier", "attachment_analyzer", "relationship_upgrader"
        ]:
            logger.info(f"Fallback switch to: {result}")
            return result
        return None
        
    except Exception as e:
        logger.error(f"Fallback switch error: {e}")
        return None


@chat_router.get("/sse")
async def stream_chat(
    message: str = Query(..., description="User message"),
    agent_slug: str = Query("misunderstanding_protector", description="Current agent"),
    user: Optional[dict] = Depends(get_current_user_sse),
    db: Session = Depends(get_db)
):
    """
    SSE endpoint for streaming chat responses
    Handles agent switching via JSON detection
    """
    async def generate():
        try:
            # Get agent
            agent = db.query(Agent).filter(Agent.slug == agent_slug).first()
            if not agent:
                yield f"data: {json.dumps({'error': 'Agent not found'})}\n\n"
                return
            
            # Get user ID (use session ID if not authenticated)
            user_id = user["id"] if user else "anonymous"
            logger.info(f"[CHAT] Processing message for user: {user_id}, agent: {agent_slug}")
            logger.debug(f"[CHAT] User object: {user}")
            logger.debug(f"[CHAT] User type: {type(user)}")
            if user:
                logger.debug(f"[CHAT] User keys: {user.keys() if hasattr(user, 'keys') else 'not a dict'}")
            
            # Log why user might be anonymous
            if user_id == "anonymous":
                logger.warning("[CHAT] User is anonymous - no memory will be saved/retrieved")
            
            # Search memories
            memories = []
            if user_id != "anonymous":
                logger.info(f"[CHAT] Searching memories for authenticated user: {user_id}")
                memories = await search_memories(message, user_id)
                logger.info(f"[CHAT] Memory search complete, found {len(memories)} memories")
            
            # Build messages for OpenAI
            messages = [
                {"role": "system", "content": agent.system_prompt}
            ]
            
            # Add memories as context
            if memories:
                context = "Previous context:\n"
                for mem in memories:
                    context += f"- {mem.get('memory', mem.get('content', ''))}\n"
                messages.append({"role": "system", "content": context})
            
            messages.append({"role": "user", "content": message})
            
            # Stream from OpenAI
            stream = await openai.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                stream=True,
                temperature=0.7
            )
            
            full_response = ""
            new_agent = None
            chunk_buffer = ""
            
            # Stream chunks to client
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    chunk_buffer += content
                    
                    # Check if buffer might contain JSON pattern
                    if '{"agent"' in chunk_buffer:
                        # Check for complete JSON pattern
                        agent_match = extract_agent_slug(chunk_buffer)
                        if agent_match:
                            # Found complete JSON, extract agent and clean buffer
                            if not new_agent:
                                new_agent = agent_match
                                logger.info(f"[AGENT_SWITCH] JSON detection found: {new_agent}")
                                logger.debug(f"[AGENT_SWITCH] Original buffer: {chunk_buffer}")
                            # Remove JSON from buffer
                            chunk_buffer = remove_agent_json(chunk_buffer)
                            logger.debug(f"[AGENT_SWITCH] Cleaned buffer: {chunk_buffer}")
                        elif not chunk_buffer.strip().endswith('}'):
                            # Partial JSON, wait for more content
                            logger.debug(f"[AGENT_SWITCH] Partial JSON detected, waiting for more: {chunk_buffer}")
                            continue
                    
                    # Send whatever is in buffer (already cleaned if needed)
                    if chunk_buffer:
                        yield f"data: {json.dumps({'chunk': chunk_buffer})}\n\n"
                        chunk_buffer = ""
            
            # Log full response for debugging
            logger.debug(f"[CHAT] Full response length: {len(full_response)}")
            if new_agent:
                logger.info(f"[CHAT] Agent switch detected in response: {new_agent}")
            
            # Clean response and save to memory
            clean_response = remove_agent_json(full_response)
            
            if user_id != "anonymous":
                logger.info(f"[CHAT] Saving memory for user: {user_id}")
                memory_result = await add_memory(
                    messages=[
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": clean_response}
                    ],
                    user_id=user_id
                )
                logger.info(f"[CHAT] Memory save result: {memory_result}")
            
            # Check fallback only if enabled and no JSON agent switch was detected
            from main import system_settings
            if not new_agent and system_settings.get("enable_fallback", True):
                logger.info(f"[AGENT_SWITCH] No JSON detected, trying fallback GPT-3.5")
                new_agent = await should_switch_agent(message, agent_slug)
                if new_agent:
                    logger.info(f"[AGENT_SWITCH] Fallback suggested: {new_agent}")
            elif not new_agent:
                logger.info(f"[AGENT_SWITCH] Fallback disabled by system settings")
            else:
                logger.info(f"[AGENT_SWITCH] Skipping fallback - JSON detection already found: {new_agent}")
            
            # Send switch signal
            logger.info(f"[AGENT_SWITCH] Final decision: {new_agent or 'none'}")
            yield f"data: {json.dumps({'switch': new_agent or 'none'})}\n\n"
            
            # End stream
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )