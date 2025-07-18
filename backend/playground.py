"""
Playground endpoint for testing agent prompts
Completely standalone - doesn't affect production
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import time
import logging
import json
import asyncio
from openai import AsyncOpenAI
import tiktoken

from database import get_db
from agent_parser import extract_agent_slug, remove_agent_json
from config import settings
logger = logging.getLogger(__name__)

# Router
playground_router = APIRouter()

# OpenAI client
openai = AsyncOpenAI(api_key=settings.openai_api_key)

# Token encoding cache
try:
    encoding = tiktoken.encoding_for_model("gpt-4")
except:
    encoding = tiktoken.get_encoding("cl100k_base")  # Fallback


class PlaygroundSettings(BaseModel):
    model: str = "gpt-4"
    temperature: float = 0.7
    show_json: bool = True
    enable_fallback: bool = True


class ChatMessage(BaseModel):
    role: str
    content: str


class PlaygroundRequest(BaseModel):
    agent_slug: str
    system_prompt: str
    message: str
    settings: PlaygroundSettings


class PlaygroundResponse(BaseModel):
    clean_response: str
    raw_response: str
    detected_json: Optional[str] = None
    agent_switch: Optional[str] = None
    debug_info: Dict[str, Any]




@playground_router.post("/chat", response_model=PlaygroundResponse)
async def playground_chat(
    request: PlaygroundRequest,
    db: Session = Depends(get_db)
):
    """
    Test agent prompts without affecting production
    Returns detailed debug information
    """
    start_time = time.time()
    
    try:
        logger.info(f"[PLAYGROUND] Testing agent: {request.agent_slug}")
        logger.info(f"[PLAYGROUND] Model: {request.settings.model}, Temp: {request.settings.temperature}")
        
        # Build messages
        messages = [
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": request.message}
        ]
        
        # Get response from OpenAI
        response = await openai.chat.completions.create(
            model=request.settings.model,
            messages=messages,
            temperature=request.settings.temperature,
            max_tokens=1000
        )
        
        raw_response = response.choices[0].message.content
        logger.info(f"[PLAYGROUND] Raw response length: {len(raw_response)}")
        logger.info(f"[PLAYGROUND] Last 200 chars: {raw_response[-200:]}")
        
        # Detect JSON
        detected_json = extract_agent_slug(raw_response)
        agent_switch = None
        fallback_triggered = False
        
        if detected_json:
            agent_switch = detected_json
            logger.info(f"[PLAYGROUND] JSON detected: {detected_json}")
        elif request.settings.enable_fallback:
            # Simulate fallback logic
            logger.info(f"[PLAYGROUND] No JSON detected, fallback enabled but not triggered in playground")
            fallback_triggered = True
        
        # Clean response
        clean_response = remove_agent_json(raw_response)
        
        # Calculate processing time
        processing_time = f"{(time.time() - start_time):.2f}s"
        
        # Token count (approximate)
        token_count = response.usage.total_tokens if response.usage else 0
        
        # Build debug info
        debug_info = {
            "detected_json": f'{{"agent": "{detected_json}"}}' if detected_json else None,
            "agent_switch": agent_switch,
            "token_count": token_count,
            "processing_time": processing_time,
            "model_used": request.settings.model,
            "fallback_triggered": fallback_triggered,
            "json_in_response": '{"agent"' in raw_response,
            "response_length": len(raw_response)
        }
        
        return PlaygroundResponse(
            clean_response=clean_response,
            raw_response=raw_response,
            detected_json=f'{{"agent": "{detected_json}"}}' if detected_json else None,
            agent_switch=agent_switch,
            debug_info=debug_info
        )
        
    except Exception as e:
        logger.error(f"[PLAYGROUND] Error: {e}")
        return PlaygroundResponse(
            clean_response=f"Error: {str(e)}",
            raw_response=f"Error: {str(e)}",
            detected_json=None,
            agent_switch=None,
            debug_info={
                "error": str(e),
                "processing_time": f"{(time.time() - start_time):.2f}s"
            }
        )


@playground_router.get("/sse")
async def playground_sse(
    agent_slug: str = Query(...),
    system_prompt: str = Query(...),
    message: str = Query(...),
    history: str = Query("[]"),  # JSON array of messages
    model: str = Query("gpt-4"),
    temperature: float = Query(0.7),
    db: Session = Depends(get_db)
):
    """
    SSE endpoint for streaming playground responses
    """
    async def generate():
        try:
            # Safe parse history
            try:
                message_history = json.loads(history) if history and history != "[]" else []
            except:
                message_history = []
                logger.warning(f"[PLAYGROUND SSE] Failed to parse history: {history}")
            
            # Build messages with system prompt and history
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(message_history)
            messages.append({"role": "user", "content": message})
            
            logger.info(f"[PLAYGROUND SSE] Agent: {agent_slug}, Model: {model}")
            logger.info(f"[PLAYGROUND SSE] Message count: {len(messages)}")
            
            # Count input tokens
            input_tokens = sum(len(encoding.encode(str(msg))) for msg in messages)
            
            # Stream from OpenAI
            stream = await openai.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=1000,
                stream=True
            )
            
            full_response = ""
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    
                    # Send chunk (without fake tokens)
                    data = {"chunk": content}
                    yield f"data: {json.dumps(data)}\n\n"
            
            # Count output tokens
            output_tokens = len(encoding.encode(full_response))
            
            # Detect JSON in full response
            detected_json = extract_agent_slug(full_response)
            
            # Send final metadata with real tokens
            final_data = {
                "detected_json": f'{{"agent": "{detected_json}"}}' if detected_json else None,
                "agent_switch": detected_json,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            
            # Send done signal
            yield f"data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"[PLAYGROUND SSE] Error: {e}")
            error_data = {"error": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
