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

from config import settings

logger = logging.getLogger(__name__)

# Router
bedrock_router = APIRouter()

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
        # Prepare request body for Claude (using the correct format)
        body = json.dumps({
            "prompt": f"\n\nHuman: {system_prompt}\n\n{message}\n\nAssistant:",
            "max_tokens_to_sample": 4000,
            "temperature": temperature,
            "stop_sequences": ["\n\nHuman:"]
        })
        
        # Invoke the model with streaming
        logger.info(f"[BEDROCK] Invoking model: {model}")
        response = bedrock_runtime.invoke_model_with_response_stream(
            modelId=model,
            contentType="application/json",
            accept="application/json",
            body=body
        )
        
        # Stream the response
        full_response = ""
        stream = response.get('body')
        
        if stream:
            for event in stream:
                chunk = event.get('chunk')
                if chunk:
                    try:
                        chunk_data = json.loads(chunk.get('bytes', b'{}').decode())
                        
                        # Claude v1 format - simple completion field
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
        prompt_text = f"\n\nHuman: {system_prompt}\n\n{message}\n\nAssistant:"
        input_tokens = len(prompt_text.split()) * 1.3  # Rough estimate
        output_tokens = len(full_response.split()) * 1.3
        
        # Send token counts
        yield f"data: {json.dumps({
            'input_tokens': int(input_tokens),
            'output_tokens': int(output_tokens),
            'total_tokens': int(input_tokens + output_tokens)
        })}\n\n"
        
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