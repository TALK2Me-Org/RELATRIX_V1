"""
Playground with AWS Bedrock integration
Ultra simple - just SSE streaming with AWS Claude
"""
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import json
import logging
from typing import AsyncGenerator
import boto3
from botocore.exceptions import ClientError
import asyncio
from concurrent.futures import ThreadPoolExecutor

from config import settings

logger = logging.getLogger(__name__)

# Router
bedrock_router = APIRouter()

# Thread pool for blocking boto3 calls
executor = ThreadPoolExecutor(max_workers=3)

# Initialize Bedrock client (only if AWS credentials are provided)
bedrock_runtime = None
if getattr(settings, 'aws_access_key_id', None) and getattr(settings, 'aws_secret_access_key', None):
    try:
        bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=getattr(settings, 'aws_default_region', 'eu-central-1'),
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        logger.info("[BEDROCK] AWS Bedrock client initialized")
    except Exception as e:
        logger.error(f"[BEDROCK] Failed to initialize: {e}")


async def generate_bedrock_stream(
    agent_slug: str,
    system_prompt: str, 
    message: str,
    user_id: str,
    model: str = "anthropic.claude-3-5-sonnet-20240620-v1:0",
    temperature: float = 0.7
) -> AsyncGenerator[str, None]:
    """Generate SSE stream with AWS Bedrock Claude"""
    
    if not bedrock_runtime:
        yield f"data: {json.dumps({'error': 'AWS Bedrock not configured'})}\n\n"
        return
    
    try:
        # Always use Claude 3.5 Sonnet for Bedrock (ignore frontend model)
        actual_model = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        
        # Detect which API format to use based on model
        use_messages_api = "claude-3" in actual_model or "claude-4" in actual_model or "sonnet" in actual_model
        
        if use_messages_api:
            # New Messages API format for Claude 3+
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4000,
                "temperature": temperature,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            })
        else:
            # Old format for Claude Instant and v2
            body = json.dumps({
                "prompt": f"\n\nHuman: {system_prompt}\n\n{message}\n\nAssistant:",
                "max_tokens_to_sample": 4000,
                "temperature": temperature,
                "stop_sequences": ["\n\nHuman:"]
            })
        
        # Invoke the model with streaming (async to not block)
        logger.info(f"[BEDROCK] Invoking model: {actual_model}")
        loop = asyncio.get_event_loop()
        
        # Create a lambda function that calls invoke_model with all parameters
        invoke_func = lambda: bedrock_runtime.invoke_model_with_response_stream(
            modelId=actual_model,
            contentType="application/json",
            accept="application/json",
            body=body
        )
        
        response = await loop.run_in_executor(executor, invoke_func)
        
        # Stream the response
        full_response = ""
        stream = response.get('body')
        
        if stream:
            for event in stream:
                chunk = event.get('chunk')
                if chunk:
                    try:
                        chunk_data = json.loads(chunk.get('bytes', b'{}').decode())
                        
                        if use_messages_api:
                            # New Messages API format
                            if chunk_data.get('type') == 'content_block_delta':
                                delta = chunk_data.get('delta', {})
                                text = delta.get('text', '')
                                if text:
                                    full_response += text
                                    yield f"data: {json.dumps({'chunk': text})}\n\n"
                            elif chunk_data.get('type') == 'message_stop':
                                logger.info(f"[BEDROCK] Response completed for user: {user_id}")
                        else:
                            # Old format - simple completion field
                            if 'completion' in chunk_data:
                                text = chunk_data['completion']
                                # Extract only the new part (Claude sends cumulative)
                                new_text = text[len(full_response):]
                                if new_text:
                                    full_response = text
                                    yield f"data: {json.dumps({'chunk': new_text})}\n\n"
                            
                            # Check for stop reason
                            if chunk_data.get('stop_reason'):
                                logger.info(f"[BEDROCK] Response completed for user: {user_id}")
                            
                    except json.JSONDecodeError:
                        logger.warning(f"[BEDROCK] Failed to parse chunk: {chunk}")
        
        # Estimate tokens (rough approximation for Claude)
        if use_messages_api:
            prompt_text = f"{system_prompt} {message}"
        else:
            prompt_text = f"\n\nHuman: {system_prompt}\n\n{message}\n\nAssistant:"
        
        input_tokens = len(prompt_text.split()) * 1.3  # Rough estimate
        output_tokens = len(full_response.split()) * 1.3
        
        # Send token counts
        token_data = {
            'input_tokens': int(input_tokens),
            'output_tokens': int(output_tokens),
            'total_tokens': int(input_tokens + output_tokens)
        }
        yield f"data: {json.dumps(token_data)}\n\n"
        
        # Done
        yield f"data: [DONE]\n\n"
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        logger.error(f"[BEDROCK] AWS error ({error_code}): {error_msg}")
        yield f"data: {json.dumps({'error': f'AWS Error: {error_msg}'})}\n\n"
        
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