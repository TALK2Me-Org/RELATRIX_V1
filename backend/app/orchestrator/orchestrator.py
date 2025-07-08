"""
Simple Orchestrator - Direct integration with Mem0 and OpenAI
No unnecessary abstractions!
"""

import logging
from typing import AsyncGenerator, Optional, Dict, Any
import json

from openai import AsyncOpenAI
from mem0 import MemoryClient

from .registry import AgentRegistry
from .models import Agent
from app.core.config import settings

logger = logging.getLogger(__name__)


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
        
        # Initialize Mem0 if API key is configured
        if hasattr(settings, 'mem0_api_key') and not settings.mem0_api_key.startswith('m0-placeholder'):
            try:
                self.mem0 = MemoryClient(api_key=settings.mem0_api_key)
                logger.info("Mem0 client initialized")
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
                memories = self.mem0.search(
                    query=message,
                    user_id=user_id,
                    limit=5
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
                    result = self.mem0.add(
                        messages=[
                            {"role": "user", "content": message},
                            {"role": "assistant", "content": full_response}
                        ],
                        user_id=user_id,
                        version="v2",  # Use v2 for automatic context management
                        output_format="v1.1"
                        # NO run_id - we want cross-session memory!
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
        return await self.registry.get_all_agents()
    
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