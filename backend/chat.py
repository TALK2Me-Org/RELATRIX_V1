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
from auth import get_current_user
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
            "communication_simulator", "misunderstanding_protector"
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
    user: Optional[dict] = Depends(get_current_user),
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
            
            # Search memories
            memories = []
            if user_id != "anonymous":
                memories = await search_memories(message, user_id)
            
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
            
            # Stream chunks to client
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    
                    # Check for agent switch
                    if not new_agent:
                        new_agent = extract_agent_slug(full_response)
                        if new_agent:
                            logger.info(f"[AGENT_SWITCH] JSON detection found: {new_agent}")
                    
                    # Send chunk
                    yield f"data: {json.dumps({'chunk': content})}\n\n"
            
            # Clean response and save to memory
            clean_response = remove_agent_json(full_response)
            
            if user_id != "anonymous":
                await add_memory(
                    messages=[
                        {"role": "user", "content": message},
                        {"role": "assistant", "content": clean_response}
                    ],
                    user_id=user_id
                )
            
            # Check fallback if no agent switch detected
            if not new_agent:
                logger.info(f"[AGENT_SWITCH] No JSON detected, trying fallback GPT-3.5")
                new_agent = await should_switch_agent(message, agent_slug)
                if new_agent:
                    logger.info(f"[AGENT_SWITCH] Fallback suggested: {new_agent}")
            
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