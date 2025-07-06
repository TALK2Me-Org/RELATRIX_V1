"""
Memory Coordinator - Integrates Mem0 and Redis for memory management
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

from mem0 import Memory
from redis import asyncio as aioredis
from app.core.config import settings
from .models import SessionState, Message

logger = logging.getLogger(__name__)


class MemoryCoordinator:
    """Coordinates memory between Mem0 and Redis"""
    
    def __init__(self):
        # Initialize Mem0
        self.mem0_config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": settings.qdrant_host,
                    "port": settings.qdrant_port,
                    "collection_name": settings.qdrant_collection,
                    "api_key": settings.qdrant_api_key if hasattr(settings, 'qdrant_api_key') else None
                }
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "api_key": settings.openai_api_key,
                    "model": "gpt-4-turbo-preview"
                }
            }
        }
        
        self.memory = Memory.from_config(self.mem0_config)
        self.redis_client = None
        self._initialized = False
        logger.info("Memory Coordinator initialized")
    
    async def initialize(self):
        """Initialize Redis connection"""
        if self._initialized:
            return
        
        try:
            self.redis_client = await aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            self._initialized = True
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def save_session_state(self, session_state: SessionState):
        """Save session state to Redis"""
        if not self._initialized:
            await self.initialize()
        
        key = f"session:{session_state.session_id}"
        value = session_state.json()
        
        # Set with 24 hour expiration
        await self.redis_client.setex(key, 86400, value)
        logger.debug(f"Saved session state: {session_state.session_id}")
    
    async def load_session_state(self, session_id: str) -> Optional[SessionState]:
        """Load session state from Redis"""
        if not self._initialized:
            await self.initialize()
        
        key = f"session:{session_id}"
        value = await self.redis_client.get(key)
        
        if value:
            return SessionState.parse_raw(value)
        
        return None
    
    async def add_memory(
        self, 
        user_id: str, 
        message: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add memory to Mem0"""
        try:
            result = self.memory.add(
                message,
                user_id=user_id,
                metadata=metadata or {}
            )
            
            # Extract memory ID
            memory_id = result.get('id', '') if isinstance(result, dict) else str(result)
            logger.debug(f"Added memory for user {user_id}: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            return ""
    
    async def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search user memories"""
        try:
            results = self.memory.search(
                query=query,
                user_id=user_id,
                limit=limit
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    async def get_context_window(
        self,
        session_state: SessionState,
        max_messages: int = 10
    ) -> List[Message]:
        """Get relevant context window for current conversation"""
        # Get recent messages
        recent_messages = session_state.conversation_history[-max_messages:]
        
        # If user_id available, search for relevant memories
        if session_state.user_id:
            # Get last user message for context
            last_user_msg = None
            for msg in reversed(recent_messages):
                if msg.role == "user":
                    last_user_msg = msg.content
                    break
            
            if last_user_msg:
                # Search relevant memories
                memories = await self.search_memories(
                    session_state.user_id,
                    last_user_msg,
                    limit=3
                )
                
                # Add memories as system messages if found
                if memories:
                    memory_msg = Message(
                        role="system",
                        content=f"Relevant user history: {json.dumps(memories)}",
                        metadata={"type": "memory_context"}
                    )
                    recent_messages.insert(0, memory_msg)
        
        return recent_messages
    
    async def save_conversation_memory(
        self,
        session_state: SessionState,
        summary: Optional[str] = None
    ):
        """Save conversation summary to long-term memory"""
        if not session_state.user_id:
            return
        
        # Create conversation summary if not provided
        if not summary:
            # Get key points from conversation
            key_points = []
            for transfer in session_state.transfer_history:
                key_points.append(f"Discussed with {transfer.to_agent}: {transfer.trigger}")
            
            summary = f"Conversation on {datetime.now().strftime('%Y-%m-%d')}: " + \
                     f"Talked with {len(set(t.to_agent for t in session_state.transfer_history)) + 1} agents. " + \
                     "Topics: " + ", ".join(key_points[:3])
        
        # Save to Mem0
        memory_id = await self.add_memory(
            session_state.user_id,
            summary,
            metadata={
                "session_id": session_state.session_id,
                "agents_involved": list(set(t.to_agent for t in session_state.transfer_history)),
                "message_count": len(session_state.conversation_history)
            }
        )
        
        # Add to session memory refs
        if memory_id:
            session_state.memory_refs.append(memory_id)
            await self.save_session_state(session_state)
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile from memories"""
        memories = await self.search_memories(user_id, "user profile relationship", limit=10)
        
        profile = {
            "user_id": user_id,
            "conversation_count": 0,
            "common_topics": [],
            "relationship_status": "unknown",
            "communication_style": "unknown"
        }
        
        # Extract profile info from memories
        for memory in memories:
            # This would parse memories to build profile
            pass
        
        return profile
    
    async def cleanup_old_sessions(self, days: int = 7):
        """Clean up old session data"""
        if not self._initialized:
            await self.initialize()
        
        # Get all session keys
        cursor = 0
        while True:
            cursor, keys = await self.redis_client.scan(
                cursor, 
                match="session:*",
                count=100
            )
            
            for key in keys:
                # Check TTL
                ttl = await self.redis_client.ttl(key)
                if ttl < 0:  # No expiration set
                    await self.redis_client.expire(key, days * 86400)
            
            if cursor == 0:
                break
        
        logger.info("Cleaned up old sessions")