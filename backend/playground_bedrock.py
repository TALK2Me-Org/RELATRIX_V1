"""
Playground with AWS Bedrock integration
Ultra simple - just SSE streaming with AWS Claude
"""
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import json
import logging
from typing import AsyncGenerator
from anthropic import AsyncAnthropicBedrock

from config import settings

logger = logging.getLogger(__name__)

# Router
bedrock_router = APIRouter()

# Initialize Bedrock client (only if AWS credentials are provided)
bedrock_client = None
if getattr(settings, 'aws_access_key_id', None) and getattr(settings, 'aws_secret_access_key', None):
    try:
        bedrock_client = AsyncAnthropicBedrock(
            aws_region=getattr(settings, 'aws_default_region', 'eu-central-1'),
            aws_access_key=settings.aws_access_key_id,
            aws_secret_key=settings.aws_secret_access_key
        )
        logger.info("[BEDROCK] AsyncAnthropicBedrock client initialized")
    except Exception as e:
        logger.error(f"[BEDROCK] Failed to initialize: {e}")


async def generate_bedrock_stream(
    agent_slug: str,
    system_prompt: str, 
    message: str,
    user_id: str,
    model: str = "claude-3-5-sonnet-20241022",
    temperature: float = 0.7
) -> AsyncGenerator[str, None]:
    """Generate SSE stream with AWS Bedrock Claude"""
    
    if not bedrock_client:
        yield f"data: {json.dumps({'error': 'AWS Bedrock not configured'})}\n\n"
        return
    
    try:
        # Always use Claude 3.5 Sonnet for Bedrock
        actual_model = "claude-3-5-sonnet-20241022"
        
        logger.info(f"[BEDROCK] Invoking model: {actual_model}")
        
        # Create streaming response with AsyncAnthropicBedrock
        stream = await bedrock_client.messages.create(
            model=actual_model,
            max_tokens=4000,
            temperature=temperature,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": message
                }
            ],
            stream=True
        )
        
        # Stream the response
        full_response = ""
        input_tokens = 0
        output_tokens = 0
        
        async for event in stream:
            # Handle content blocks
            if event.type == 'content_block_delta':
                text = event.delta.text
                if text:
                    full_response += text
                    yield f"data: {json.dumps({'chunk': text})}\n\n"
            
            # Handle message start (contains usage info)
            elif event.type == 'message_start':
                if hasattr(event.message, 'usage'):
                    input_tokens = event.message.usage.input_tokens
            
            # Handle message delta (contains final usage)
            elif event.type == 'message_delta':
                if hasattr(event, 'usage'):
                    output_tokens = event.usage.output_tokens
        
        logger.info(f"[BEDROCK] Response completed for user: {user_id}")
        
        # Send token counts
        token_data = {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens
        }
        yield f"data: {json.dumps(token_data)}\n\n"
        
        # Done
        yield f"data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"[BEDROCK] Stream error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


@bedrock_router.get("/sse")
async def playground_bedrock_sse(
    agent_slug: str = Query(...),
    system_prompt: str = Query(...),
    message: str = Query(...),
    user_id: str = Query(...),
    model: str = Query(default="anthropic.claude-3-5-sonnet-20240620-v1:0"),
    temperature: float = Query(default=0.7)
):
    """Playground SSE endpoint with AWS Bedrock"""
    return StreamingResponse(
        generate_bedrock_stream(
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