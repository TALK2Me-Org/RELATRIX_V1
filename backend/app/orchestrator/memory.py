"""
Memory Coordinator - Simple Mem0 v2 integration
Philosophy: Let Mem0 handle all the complexity
"""

import logging
import json
from typing import Dict, Any, List, Optional
from redis import asyncio as aioredis
from app.core.config import settings
from .models import SessionState

logger = logging.getLogger(__name__)

# Lazy import Mem0 to avoid initialization issues
try:
    from mem0 import MemoryClient
    HAS_MEM0 = True
except ImportError:
    logger.warning("Mem0 not available, memory features will be limited")
    HAS_MEM0 = False


class MemoryCoordinator:
    """Simple coordinator for Mem0 v2 and Redis session state"""
    
    def __init__(self):
        self.mem0_client = None
        self.redis_client = None
        self._initialized = False
        self._mem0_initialized = False
        logger.info("Memory Coordinator initialized")
    
    async def initialize(self):
        """Initialize Redis connection for session state only"""
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
    
    def _init_mem0(self):
        """Initialize Mem0 client lazily"""
        if self._mem0_initialized or not HAS_MEM0:
            return
        
        try:
            # Check if API key is configured
            if not hasattr(settings, 'mem0_api_key') or settings.mem0_api_key.startswith('m0-placeholder'):
                logger.warning("Mem0 API key not configured, skipping initialization")
                return
            
            # Initialize Mem0 Cloud API client
            self.mem0_client = MemoryClient(api_key=settings.mem0_api_key)
            self._mem0_initialized = True
            logger.info("Mem0 Cloud API client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Mem0: {e}")
            self.mem0_client = None
    
    async def add(
        self, 
        messages: List[Dict[str, str]],
        user_id: str,
        run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add messages to Mem0 v2 - let it handle all the complexity"""
        self._init_mem0()
        
        if not self.mem0_client or not user_id:
            logger.debug("Mem0 not available or no user_id, skipping memory storage")
            return ""
        
        try:
            # Prepare parameters for Mem0 API v2
            params = {
                "user_id": user_id,
                "version": "v2",  # Always use v2 for automatic context management
                "output_format": "v1.1",  # Latest format
                "async_mode": True  # Don't block the response
            }
            
            # Add optional parameters
            if run_id:
                params["run_id"] = run_id
            if metadata:
                params["metadata"] = metadata
            
            # Let Mem0 v2 handle everything
            logger.info(f"Mem0 add called with params: user_id={user_id}, run_id={run_id}")
            logger.info(f"Messages being saved: {json.dumps(messages, indent=2)}")
            
            result = self.mem0_client.add(messages, **params)
            
            # Extract memory ID if available
            if isinstance(result, dict) and 'results' in result:
                results = result.get('results', [])
                if results and 'id' in results[0]:
                    memory_id = results[0]['id']
                    logger.info(f"Mem0 created memory {memory_id} for user {user_id}")
                    logger.debug(f"Full Mem0 response: {json.dumps(result, indent=2)}")
                    return memory_id
            
            return ""
            
        except Exception as e:
            logger.error(f"Error adding to Mem0: {e}")
            return ""
    
    async def search(
        self,
        query: str,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search memories - Mem0 knows what's relevant"""
        self._init_mem0()
        
        if not self.mem0_client or not user_id:
            logger.debug("Mem0 not available or no user_id, returning empty results")
            return []
        
        try:
            # Simple search - let Mem0 handle relevance
            logger.info(f"Searching Mem0 for user {user_id} with query: '{query[:50]}...'")
            results = self.mem0_client.search(
                query=query,
                user_id=user_id,
                limit=limit
            )
            
            # Return results as-is
            memories = results if isinstance(results, list) else []
            logger.info(f"Found {len(memories)} memories for user {user_id}")
            if memories:
                logger.debug(f"First memory: {json.dumps(memories[0], indent=2)}")
            return memories
            
        except Exception as e:
            logger.error(f"Error searching Mem0: {e}")
            return []
    
    async def save_session_state(self, session_state: SessionState):
        """Save session state to Redis - only for temporary session data"""
        if not self._initialized:
            await self.initialize()
        
        key = f"session:{session_state.session_id}"
        value = session_state.model_dump_json()
        
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
            return SessionState.model_validate_json(value)
        
        return None
    
    async def cleanup_old_sessions(self, days: int = 7):
        """Clean up old session data from Redis"""
        if not self._initialized:
            await self.initialize()
        
        # Get all session keys
        cursor = 0
        cleaned = 0
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
                    cleaned += 1
            
            if cursor == 0:
                break
        
        logger.info(f"Set expiration for {cleaned} old sessions")