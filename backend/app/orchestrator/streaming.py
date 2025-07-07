"""
Streaming Handler - Manages OpenAI streaming responses
"""

import logging
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional, Callable
from datetime import datetime
import json

import openai
from openai import AsyncOpenAI
from app.core.config import settings
from .models import Agent, Message, StreamChunk, SessionState

logger = logging.getLogger(__name__)


class StreamingHandler:
    """Handles streaming responses from OpenAI"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.active_streams: Dict[str, bool] = {}
        logger.info("Streaming Handler initialized")
    
    async def stream_response(
        self,
        agent: Agent,
        messages: list[Dict[str, str]],
        session_id: str,
        on_transfer_suggestion: Optional[Callable] = None
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Stream response from OpenAI
        Yields StreamChunk objects for real-time delivery
        """
        stream_id = f"{session_id}:{datetime.now().timestamp()}"
        self.active_streams[stream_id] = True
        
        try:
            # Create streaming completion
            stream = await self.client.chat.completions.create(
                model=agent.openai_model,
                messages=messages,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens,
                stream=True,
                stream_options={"include_usage": True}
            )
            
            full_response = ""
            
            async for chunk in stream:
                # Check if stream was cancelled
                if not self.active_streams.get(stream_id, False):
                    logger.info(f"Stream {stream_id} cancelled")
                    break
                
                # Process chunk
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    
                    # Yield content chunk
                    yield StreamChunk(
                        type="content",
                        content=content,
                        agent_id=agent.slug,
                        metadata={"stream_id": stream_id}
                    )
                    
                    # Check for transfer suggestions in the response
                    if on_transfer_suggestion and self._check_transfer_suggestion(full_response):
                        transfer_info = await on_transfer_suggestion(full_response)
                        if transfer_info:
                            yield StreamChunk(
                                type="transfer",
                                agent_id=agent.slug,
                                metadata={
                                    "suggested_agent": transfer_info[0],
                                    "reason": transfer_info[1]
                                }
                            )
                
                # Check for usage info (final chunk)
                if hasattr(chunk, 'usage') and chunk.usage:
                    yield StreamChunk(
                        type="metadata",
                        agent_id=agent.slug,
                        metadata={
                            "usage": {
                                "prompt_tokens": chunk.usage.prompt_tokens,
                                "completion_tokens": chunk.usage.completion_tokens,
                                "total_tokens": chunk.usage.total_tokens
                            }
                        }
                    )
            
            # Log completion
            logger.info(f"Stream {stream_id} completed, response length: {len(full_response)}")
            
        except asyncio.CancelledError:
            logger.info(f"Stream {stream_id} cancelled")
            yield StreamChunk(
                type="error",
                content="Stream cancelled",
                agent_id=agent.slug
            )
        except Exception as e:
            logger.error(f"Stream {stream_id} error: {e}")
            yield StreamChunk(
                type="error",
                content=f"Stream error: {str(e)}",
                agent_id=agent.slug
            )
        finally:
            # Cleanup
            self.active_streams.pop(stream_id, None)
    
    def _check_transfer_suggestion(self, response: str) -> bool:
        """Check if response contains transfer suggestion"""
        transfer_phrases = [
            "suggest transfer to",
            "would benefit from talking to",
            "recommend switching to",
            "might want to speak with",
            "connect you with"
        ]
        
        response_lower = response.lower()
        return any(phrase in response_lower for phrase in transfer_phrases)
    
    async def cancel_stream(self, session_id: str):
        """Cancel active streams for a session"""
        cancelled = 0
        for stream_id in list(self.active_streams.keys()):
            if stream_id.startswith(f"{session_id}:"):
                self.active_streams[stream_id] = False
                cancelled += 1
        
        if cancelled:
            logger.info(f"Cancelled {cancelled} streams for session {session_id}")
    
    async def generate_transfer_notification(
        self,
        from_agent: Agent,
        to_agent: Agent,
        reason: str
    ) -> StreamChunk:
        """Generate a transfer notification chunk"""
        return StreamChunk(
            type="transfer",
            content=f"I'm connecting you with {to_agent.name} who specializes in {to_agent.description}. "
                   f"They'll be better equipped to help you with this.",
            agent_id=to_agent.slug,
            metadata={
                "from_agent": from_agent.slug,
                "to_agent": to_agent.slug,
                "reason": reason
            }
        )
    
    def format_messages_for_api(
        self,
        agent: Agent,
        messages: list[Message],
        include_system: bool = True
    ) -> list[Dict[str, str]]:
        """Format messages for OpenAI API"""
        formatted = []
        
        # Add system prompt
        if include_system:
            formatted.append({
                "role": "system",
                "content": agent.system_prompt
            })
        
        # Add conversation messages
        for msg in messages:
            formatted.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return formatted
    
    async def generate_summary(
        self,
        messages: list[Message],
        focus: str = "key points"
    ) -> str:
        """Generate summary of conversation"""
        try:
            summary_prompt = f"Summarize the following conversation, focusing on {focus}:"
            
            # Format messages for summary
            conversation = "\n".join([
                f"{msg.role}: {msg.content}" 
                for msg in messages 
                if msg.role in ["user", "assistant"]
            ])
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": summary_prompt},
                    {"role": "user", "content": conversation}
                ],
                temperature=0.5,
                max_tokens=200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Summary generation failed"