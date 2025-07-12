"""
Playground endpoint for testing agent prompts
Completely standalone - doesn't affect production
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import time
import logging
from openai import AsyncOpenAI

from database import get_db
from agent_parser import extract_agent_slug, remove_agent_json
from config import settings

logger = logging.getLogger(__name__)

# Router
playground_router = APIRouter()

# OpenAI client
openai = AsyncOpenAI(api_key=settings.openai_api_key)


class PlaygroundSettings(BaseModel):
    model: str = "gpt-4"
    temperature: float = 0.7
    show_json: bool = True
    enable_fallback: bool = True


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


@playground_router.get("/models")
async def get_available_models():
    """
    Get list of available OpenAI models
    """
    try:
        # Common models with descriptions
        models = [
            {
                "id": "gpt-4-turbo-preview",
                "name": "GPT-4 Turbo",
                "description": "Najnowszy model GPT-4 z wiedzą do kwietnia 2023"
            },
            {
                "id": "gpt-4",
                "name": "GPT-4",
                "description": "Najbardziej zaawansowany model, najlepsza jakość"
            },
            {
                "id": "gpt-4-32k",
                "name": "GPT-4 32K",
                "description": "GPT-4 z większym kontekstem (32k tokenów)"
            },
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "description": "Szybki i tani, dobry do większości zadań"
            },
            {
                "id": "gpt-3.5-turbo-16k",
                "name": "GPT-3.5 Turbo 16K",
                "description": "GPT-3.5 z większym kontekstem (16k tokenów)"
            }
        ]
        
        return {"models": models}
        
    except Exception as e:
        logger.error(f"[PLAYGROUND] Error fetching models: {e}")
        # Return default models if API fails
        return {
            "models": [
                {"id": "gpt-4", "name": "GPT-4", "description": "Default"},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "Default"}
            ]
        }


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