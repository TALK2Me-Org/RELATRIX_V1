"""
Simple Orchestrator - Direct integration with Mem0 and OpenAI
No unnecessary abstractions!
"""

import logging
from typing import AsyncGenerator, Optional, Dict, Any
import json
import httpx

from openai import AsyncOpenAI

from .registry import AgentRegistry
from .models import Agent
from app.core.config import settings

logger = logging.getLogger(__name__)


class AsyncMem0Client:
    """Async client for Mem0 API using httpx"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.mem0.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def search(self, query: str, user_id: str, limit: int = 20):
        """Async search memories"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/memories/search/",
                headers=self.headers,
                json={
                    "query": query,
                    "user_id": user_id,
                    "limit": limit,
                    "output_format": "v1.1"
                },
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            # Extract memories from response
            if "results" in data:
                return data["results"]
            return data
    
    async def add(self, messages: list, user_id: str, **kwargs):
        """Async add memories"""
        async with httpx.AsyncClient() as client:
            payload = {
                "messages": messages,
                "user_id": user_id,
                "version": "v2",
                "output_format": "v1.1"
            }
            payload.update(kwargs)
            
            response = await client.post(
                f"{self.base_url}/memories/",
                headers=self.headers,
                json=payload,
                timeout=10.0
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Mem0 add response: {json.dumps(result, indent=2)}")
            return result


class SimpleOrchestrator:
    """Ultra simple orchestrator - just connects the pieces"""
    
    def __init__(self):
        self.registry = AgentRegistry()
        self.mem0 = None
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self._initialized = False
        logger.info("Simple Orchestrator initialized")
    
    async def initialize(self):
        """Initialize components"""
        if self._initialized:
            return
            
        # Load agents from database
        await self.registry.load_agents()
        
        # Initialize Async Mem0 if API key is configured
        if hasattr(settings, 'mem0_api_key') and not settings.mem0_api_key.startswith('m0-placeholder'):
            try:
                self.mem0 = AsyncMem0Client(api_key=settings.mem0_api_key)
                logger.info("Async Mem0 client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Mem0: {e}")
                self.mem0 = None
        
        self._initialized = True
        logger.info("Orchestrator ready")
    
    async def process_message(
        self,
        message: str,
        user_id: Optional[str] = None,
        agent_slug: str = "misunderstanding_protector"
    ) -> AsyncGenerator[str, None]:
        """
        Process user message and stream response
        Super simple: get agent → get memories → call OpenAI → save to Mem0
        """
        if not self._initialized:
            await self.initialize()
        
        # 1. Get agent
        agent = await self.registry.get_agent(agent_slug)
        if not agent:
            logger.error(f"Agent {agent_slug} not found")
            yield f"Error: Agent {agent_slug} not found"
            return
        
        # 2. Get memories from Mem0 (if user is logged in)
        memories = []
        if user_id and self.mem0:
            try:
                logger.info(f"Searching Mem0 for user {user_id}")
                # Let Mem0 decide what's relevant for this message
                memories = await self.mem0.search(
                    query=message,
                    user_id=user_id,
                    limit=20  # Increased from 5 to get more context
                )
                logger.info(f"Found {len(memories)} memories")
            except Exception as e:
                logger.error(f"Mem0 search failed: {e}")
        
        # 3. Build messages for OpenAI
        messages = [
            {"role": "system", "content": agent.system_prompt}
        ]
        
        # Add memories as context if available
        if memories:
            context = "Relevant user context:\n"
            for mem in memories:
                # Handle different memory formats
                memory_content = mem.get('memory', mem.get('content', str(mem)))
                context += f"- {memory_content}\n"
            messages.append({"role": "system", "content": context})
            logger.debug(f"Added context: {context}")
        
        messages.append({"role": "user", "content": message})
        
        # 4. Stream response from OpenAI
        try:
            stream = await self.openai.chat.completions.create(
                model=agent.openai_model,
                messages=messages,
                temperature=agent.temperature,
                max_tokens=agent.max_tokens,
                stream=True
            )
            
            full_response = ""
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            # 5. Save to Mem0 (if user is logged in)
            if user_id and self.mem0 and full_response:
                try:
                    # Save the conversation pair
                    result = await self.mem0.add(
                        messages=[
                            {"role": "user", "content": message},
                            {"role": "assistant", "content": full_response}
                        ],
                        user_id=user_id
                        # version and output_format already set in AsyncMem0Client
                    )
                    logger.info(f"Saved to Mem0: {result}")
                except Exception as e:
                    logger.error(f"Failed to save to Mem0: {e}")
            
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield f"Error: {str(e)}"
    
    async def get_agents(self) -> Dict[str, Agent]:
        """Get all available agents"""
        if not self._initialized:
            await self.initialize()
        # Convert list to dict
        agents_list = await self.registry.get_all_agents()
        return {agent.slug: agent for agent in agents_list}
    
    async def reload_agents(self) -> int:
        """Reload agents from database"""
        agents = await self.registry.reload_agents()
        return len(agents)


# Global instance
_orchestrator = None

def get_orchestrator() -> SimpleOrchestrator:
    """Get or create orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SimpleOrchestrator()
    return _orchestrator

# For backward compatibility
orchestrator = get_orchestrator()