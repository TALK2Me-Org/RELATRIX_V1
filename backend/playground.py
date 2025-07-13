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

from database import get_db
from agent_parser import extract_agent_slug, remove_agent_json
from config import settings
from memory_service import search_memories, add_memory

logger = logging.getLogger(__name__)

# Zep imports
import uuid
try:
    from zep_cloud.client import AsyncZep
    from zep_cloud import Message as ZepMessage, Session
    HAS_ZEP = True
except ImportError:
    HAS_ZEP = False
    logger.warning("[ZEP] zep-cloud package not installed")

# Router
playground_router = APIRouter()

# OpenAI client
openai = AsyncOpenAI(api_key=settings.openai_api_key)

# Zep client - prosty, bez wrapperów
zep_client = None
if HAS_ZEP and settings.zep_api_key:
    try:
        zep_client = AsyncZep(api_key=settings.zep_api_key)
        logger.info("[ZEP] Client initialized")
    except Exception as e:
        logger.error(f"[ZEP] Init failed: {e}")


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


@playground_router.get("/models")
async def get_available_models():
    """
    Get list of available OpenAI models
    """
    try:
        # Fetch models from OpenAI API
        models_response = await openai.models.list()
        
        # Filter and format chat models
        chat_models = []
        model_descriptions = {
            "gpt-4-turbo": "Najnowszy i najszybszy GPT-4 (128k kontekst)",
            "gpt-4-turbo-preview": "GPT-4 Turbo z wiedzą do kwietnia 2023",
            "gpt-4-turbo-2024-04-09": "GPT-4 Turbo - stabilna wersja",
            "gpt-4": "Klasyczny GPT-4 (8k kontekst)",
            "gpt-4-32k": "GPT-4 z dużym kontekstem (32k)",
            "gpt-4-0125-preview": "GPT-4 Preview - styczniowa wersja",
            "gpt-4-1106-preview": "GPT-4 Preview - listopadowa wersja",
            "gpt-4o": "GPT-4 Optimized - szybszy i tańszy",
            "gpt-4o-mini": "GPT-4 Optimized Mini - najszybszy",
            "gpt-3.5-turbo": "Szybki i ekonomiczny (16k kontekst)",
            "gpt-3.5-turbo-0125": "Najnowszy GPT-3.5",
            "gpt-3.5-turbo-1106": "GPT-3.5 - stabilna wersja",
            "gpt-3.5-turbo-16k": "GPT-3.5 z dużym kontekstem"
        }
        
        for model in models_response.data:
            # Only include chat models
            if model.id.startswith(('gpt-4', 'gpt-3.5')):
                chat_models.append({
                    "id": model.id,
                    "name": model.id.replace('-', ' ').title(),
                    "description": model_descriptions.get(model.id, "Model dostępny w OpenAI")
                })
        
        # Sort by model name (GPT-4 first, then GPT-3.5)
        chat_models.sort(key=lambda x: (not x['id'].startswith('gpt-4'), x['id']))
        
        logger.info(f"[PLAYGROUND] Found {len(chat_models)} chat models")
        return {"models": chat_models}
        
    except Exception as e:
        logger.error(f"[PLAYGROUND] Error fetching models from OpenAI: {e}")
        # Return comprehensive fallback list
        return {
            "models": [
                {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "description": "Najnowszy i najszybszy GPT-4"},
                {"id": "gpt-4-turbo-preview", "name": "GPT-4 Turbo Preview", "description": "GPT-4 z wiedzą do kwietnia 2023"},
                {"id": "gpt-4", "name": "GPT-4", "description": "Klasyczny GPT-4 (8k kontekst)"},
                {"id": "gpt-4-32k", "name": "GPT-4 32K", "description": "GPT-4 z dużym kontekstem"},
                {"id": "gpt-4o", "name": "GPT-4 Optimized", "description": "Szybszy i tańszy GPT-4"},
                {"id": "gpt-4o-mini", "name": "GPT-4 Optimized Mini", "description": "Najszybszy wariant GPT-4"},
                {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "description": "Szybki i ekonomiczny"},
                {"id": "gpt-3.5-turbo-16k", "name": "GPT-3.5 Turbo 16K", "description": "GPT-3.5 z dużym kontekstem"}
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
            # Parse history
            message_history = json.loads(history)
            
            # Build messages with system prompt and history
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(message_history)
            messages.append({"role": "user", "content": message})
            
            logger.info(f"[PLAYGROUND SSE] Agent: {agent_slug}, Model: {model}")
            logger.info(f"[PLAYGROUND SSE] Message count: {len(messages)}")
            
            # Stream from OpenAI
            stream = await openai.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=1000,
                stream=True
            )
            
            full_response = ""
            total_tokens = 0
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    
                    # Send chunk
                    data = {
                        "chunk": content,
                        "tokens": len(content.split()) // 4  # Approximate
                    }
                    yield f"data: {json.dumps(data)}\n\n"
            
            # Detect JSON in full response
            detected_json = extract_agent_slug(full_response)
            
            # Send final metadata
            final_data = {
                "detected_json": f'{{"agent": "{detected_json}"}}' if detected_json else None,
                "agent_switch": detected_json,
                "total_tokens": len(full_response.split()) // 4  # Approximate
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


@playground_router.get("/mem0-sse")
async def playground_mem0_sse(
    agent_slug: str = Query(...),
    system_prompt: str = Query(...),
    message: str = Query(...),
    user_id: str = Query(...),  # Playground test user ID
    model: str = Query("gpt-4"),
    temperature: float = Query(0.7),
    db: Session = Depends(get_db)
):
    """
    SSE endpoint for Mem0-enabled chat in playground
    Uses only the last message + Mem0 context
    """
    async def generate():
        start_time = time.time()
        
        try:
            logger.info(f"[PLAYGROUND MEM0] User: {user_id}, Agent: {agent_slug}")
            
            # Search memories first
            memories = await search_memories(message, user_id)
            memory_context = ""
            
            if memories:
                logger.info(f"[PLAYGROUND MEM0] Found {len(memories)} memories")
                memory_texts = [m.get('memory', '') for m in memories[:5]]  # Limit to 5
                memory_context = f"\n\nRelevant memories:\n" + "\n".join(f"- {m}" for m in memory_texts)
            
            # Build messages with system prompt and memory context
            enhanced_prompt = system_prompt + memory_context
            messages = [
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": message}
            ]
            
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
                    
                    # Send chunk
                    data = {
                        "chunk": content,
                        "memory_count": len(memories)
                    }
                    yield f"data: {json.dumps(data)}\n\n"
            
            # Save to memory
            await add_memory(
                messages=[
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": full_response}
                ],
                user_id=user_id
            )
            
            # Detect JSON in full response
            detected_json = extract_agent_slug(full_response)
            
            # Send final metadata
            final_data = {
                "detected_json": f'{{"agent": "{detected_json}"}}' if detected_json else None,
                "agent_switch": detected_json,
                "memory_count": len(memories),
                "processing_time": f"{(time.time() - start_time):.2f}s"
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            
            # Send done signal
            yield f"data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"[PLAYGROUND MEM0] Error: {e}")
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
    )# This file will be appended to playground.py

@playground_router.get("/zep-sse")
async def playground_zep_sse(
    agent_slug: str = Query(...),
    system_prompt: str = Query(...),
    message: str = Query(...),
    user_id: str = Query(...),  # Test user ID
    model: str = Query("gpt-4"),
    temperature: float = Query(0.7),
    db: Session = Depends(get_db)
):
    """
    SSE endpoint for Zep memory testing
    Each conversation gets a new session, but same user
    """
    async def generate():
        if not zep_client:
            yield f"data: {json.dumps({'error': 'Zep not configured'})}\n\n"
            return
            
        start_time = time.time()
        session_id = f"session_{uuid.uuid4()}"  # Nowa sesja dla każdej rozmowy
        
        try:
            logger.info(f"[PLAYGROUND ZEP] User: {user_id}, Session: {session_id}, Agent: {agent_slug}")
            
            # 1. Najpierw upewnij się że user istnieje
            try:
                await zep_client.user.get(user_id=user_id)
            except:
                # Twórz nowego usera jeśli nie istnieje
                await zep_client.user.add(
                    user_id=user_id,
                    metadata={"source": "playground", "created_at": time.time()}
                )
                logger.info(f"[PLAYGROUND ZEP] Created new user: {user_id}")
            
            # 2. Stwórz nową sesję dla tej rozmowy
            session = Session(
                session_id=session_id,
                user_id=user_id,
                metadata={"agent": agent_slug, "started_at": time.time()}
            )
            await zep_client.memory.add_session(session)
            logger.info(f"[PLAYGROUND ZEP] Created new session: {session_id}")
            
            # 3. Pobierz kontekst z pamięci usera (nie sesji!)
            memory_context = ""
            memory_count = 0
            
            try:
                # memory.get używa user_id, nie session_id
                result = await zep_client.memory.get(
                    user_id=user_id,
                    min_rating=0.5  # Tylko ważne fakty
                )
                
                if result and result.context:
                    memory_context = f"\n\nRelevant context:\n{result.context}"
                    memory_count = len(result.facts) if result.facts else 0
                    logger.info(f"[PLAYGROUND ZEP] Found context with {memory_count} facts")
                    
            except Exception as e:
                logger.info(f"[PLAYGROUND ZEP] No context yet for user: {e}")
            
            # 4. Build messages with memory context
            enhanced_prompt = system_prompt + memory_context
            messages = [
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": message}
            ]
            
            # 5. Stream from OpenAI
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
                    
                    # Send chunk
                    data = {
                        "chunk": content,
                        "memory_count": memory_count
                    }
                    yield f"data: {json.dumps(data)}\n\n"
            
            # 6. Save conversation to Zep session
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
                logger.info("[PLAYGROUND ZEP] Messages saved to session")
                
            except Exception as e:
                logger.error(f"[PLAYGROUND ZEP] Failed to save messages: {e}")
            
            # Detect JSON
            detected_json = extract_agent_slug(full_response)
            
            # Send final metadata
            final_data = {
                "detected_json": f'{{"agent": "{detected_json}"}}' if detected_json else None,
                "agent_switch": detected_json,
                "memory_count": memory_count,
                "processing_time": f"{(time.time() - start_time):.2f}s",
                "session_id": session_id  # Może się przydać do debugowania
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            
            # Done signal
            yield f"data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"[PLAYGROUND ZEP] Error: {e}")
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