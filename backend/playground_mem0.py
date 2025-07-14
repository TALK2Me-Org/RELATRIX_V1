"""
Playground with Mem0 memory integration
Ultra simple - just SSE streaming + memory
"""
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
import json
import logging
from typing import AsyncGenerator
import tiktoken

from config import settings
from memory_service import search_memories, add_memory

logger = logging.getLogger(__name__)

# Router
mem0_router = APIRouter()

# OpenAI client
openai = AsyncOpenAI(api_key=settings.openai_api_key)

# Token encoding cache
try:
    encoding = tiktoken.encoding_for_model("gpt-4")
except:
    encoding = tiktoken.get_encoding("cl100k_base")  # Fallback


async def generate_mem0_stream(
    agent_slug: str,
    system_prompt: str, 
    message: str,
    user_id: str,
    model: str = "gpt-4",
    temperature: float = 0.7
) -> AsyncGenerator[str, None]:
    """Generate SSE stream with Mem0 memory"""
    
    try:
        # 1. Search memories
        logger.info(f"[MEM0] Searching memories for user: {user_id}")
        memories = await search_memories(message, user_id)
        
        # 2. Build context
        memory_context = ""
        if memories:
            memory_context = "\n\nRelevant memories:\n"
            for mem in memories[:5]:  # Top 5
                memory_context += f"- {mem.get('memory', '')}\n"
        
        # 3. Prepare messages
        messages = [
            {"role": "system", "content": system_prompt + memory_context},
            {"role": "user", "content": message}
        ]
        
        # Count input tokens
        input_tokens = sum(len(encoding.encode(str(msg))) for msg in messages)
        
        # 4. Stream from OpenAI
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
        
        # 5. Save to memory (fire and forget)
        try:
            messages.append({"role": "assistant", "content": full_response})
            await add_memory(messages, user_id)
            logger.info(f"[MEM0] Memory saved for user: {user_id}")
        except Exception as e:
            logger.error(f"[MEM0] Failed to save memory: {e}")
        
        # Send token counts
        yield f"data: {json.dumps({
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens
        })}\n\n"
        
        # Done
        yield f"data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"[MEM0] Stream error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


@mem0_router.get("/sse")
async def playground_mem0_sse(
    agent_slug: str = Query(...),
    system_prompt: str = Query(...),
    message: str = Query(...),
    user_id: str = Query(...),
    model: str = Query(default="gpt-4"),
    temperature: float = Query(default=0.7)
):
    """Playground SSE endpoint with Mem0 memory"""
    return StreamingResponse(
        generate_mem0_stream(
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