"""
Memory Coordinator - Integrates Mem0 and Redis for memory management
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import time

from redis import asyncio as aioredis
from app.core.config import settings
from .models import SessionState, Message
from .memory_modes import (
    MemoryMode, MemoryConfig, MemoryMetrics, 
    TriggerType, DEFAULT_CONFIGS
)

logger = logging.getLogger(__name__)

# Lazy import Mem0 to avoid initialization issues
try:
    from mem0 import MemoryClient
    HAS_MEM0 = True
except ImportError:
    logger.warning("Mem0 not available, memory features will be limited")
    HAS_MEM0 = False


class MemoryCoordinator:
    """Coordinates memory between Mem0 and Redis with configurable modes"""
    
    def __init__(self):
        # Mem0 client will be initialized lazily
        self.mem0_client = None
        self.redis_client = None
        self._initialized = False
        self._mem0_initialized = False
        self._using_mock = False
        
        # Memory mode configuration
        self.global_config = DEFAULT_CONFIGS["premium"]
        self.session_configs: Dict[str, MemoryConfig] = {}
        self.session_metrics: Dict[str, MemoryMetrics] = {}
        
        logger.info("Memory Coordinator initialized with premium mode")
    
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
            self._using_mock = False
            logger.info("Mem0 Cloud API client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Mem0: {e}")
            # Don't crash if Mem0 fails
            self.mem0_client = None
    
    async def save_session_state(self, session_state: SessionState):
        """Save session state to Redis"""
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
    
    async def add_memory(
        self, 
        user_id: str, 
        messages: List[Dict[str, str]],
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add memory to Mem0 Cloud"""
        # Initialize Mem0 if needed
        self._init_mem0()
        
        if not self.mem0_client:
            logger.debug("Mem0 not available, skipping memory storage")
            return ""
        
        try:
            # Prepare parameters for Mem0 API
            params = {
                "user_id": user_id,
                "metadata": metadata or {}
            }
            
            # Add optional parameters
            if agent_id:
                params["agent_id"] = agent_id
            if run_id:
                params["run_id"] = run_id
            
            # Use Mem0 Cloud API with async mode for better performance
            logger.info(f"Mem0 add called with {len(messages)} messages for user {user_id}")
            result = self.mem0_client.add(
                messages,
                async_mode=True,  # Process in background to avoid blocking
                **params
            )
            
            # Extract memory ID from Cloud API response
            if isinstance(result, dict):
                # Mem0 returns {"results": [{"id": "...", ...}]}
                results = result.get('results', [])
                if results:
                    memory_id = results[0].get('id', '')
                    logger.debug(f"Added memory for user {user_id}: {memory_id}")
                    return memory_id
            
            return ""
            
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            return ""
    
    async def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        agent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search user memories"""
        # Initialize Mem0 if needed
        self._init_mem0()
        
        if not self.mem0_client:
            logger.debug("Mem0 not available, returning empty results")
            return []
        
        try:
            # Use Mem0 Cloud API search - simplified to match documentation
            results = self.mem0_client.search(
                query=query,
                user_id=user_id,
                limit=limit
            )
            
            # Log search results for debugging
            logger.info(f"Mem0 search for user {user_id} with query '{query}' returned {len(results) if isinstance(results, list) else 0} memories")
            if results and len(results) > 0:
                logger.debug(f"First memory sample: {results[0]}")
            
            # Mem0 returns a list directly
            return results if isinstance(results, list) else []
            
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
        
        # Check if this is first message in session (always refresh for new sessions)
        is_first_message = len(session_state.conversation_history) <= 1
        
        # Check if we should refresh memory based on mode and triggers
        last_user_msg = None
        if recent_messages:
            for msg in reversed(recent_messages):
                if msg.role == "user":
                    last_user_msg = msg.content
                    break
        
        should_refresh = await self.should_refresh_memory(session_state, last_user_msg)
        
        # Force refresh for first message or if triggers say so
        if session_state.user_id and (is_first_message or should_refresh):
            if is_first_message:
                logger.info(f"First message in session, forcing Mem0 retrieval for user {session_state.user_id}")
            else:
                logger.info(f"Refreshing memory context for user {session_state.user_id}")
            
            context = await self.retrieve_user_context(session_state, force_refresh=is_first_message)
            
            # Add context as system message if found
            if context.get("memories"):
                # Format memories for better readability
                memories_text = "Previous context from user memories:\n"
                for i, memory in enumerate(context["memories"][:5], 1):  # Limit to top 5
                    if isinstance(memory, dict):
                        memory_content = memory.get("memory", memory.get("content", str(memory)))
                        memories_text += f"{i}. {memory_content}\n"
                
                memory_msg = Message(
                    role="system",
                    content=memories_text,
                    metadata={"type": "memory_context", "source": "mem0"}
                )
                recent_messages.insert(0, memory_msg)
                logger.info(f"Added {len(context['memories'])} memories to context")
            else:
                logger.info(f"No memories found for user {session_state.user_id}")
        
        return recent_messages
    
    def format_messages_for_mem0(
        self, 
        messages: List[Message], 
        limit: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """Format conversation messages for Mem0 API"""
        formatted = []
        
        # Get messages to format
        messages_to_format = messages[-limit:] if limit else messages
        
        for msg in messages_to_format:
            formatted.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return formatted
    
    async def save_conversation_memory(
        self,
        session_state: SessionState,
        current_agent: Optional[str] = None,
        force: bool = False
    ):
        """Save conversation to long-term memory based on mode"""
        logger.info(f"save_conversation_memory called for session {session_state.session_id}, user_id: {session_state.user_id}")
        if not session_state.user_id:
            logger.warning(f"No user_id for session {session_state.session_id}, skipping memory save")
            return
        
        config = self.get_session_config(session_state.session_id)
        metrics = self.get_session_metrics(session_state.session_id)
        
        # Check if we should save based on mode
        should_save = force
        
        if config.mode == MemoryMode.ALWAYS_FRESH:
            # Always save in this mode
            should_save = True
        elif config.mode == MemoryMode.CACHE_FIRST:
            # Only save at session end
            should_save = force or config.save_on_session_end
        elif config.mode in [MemoryMode.SMART_TRIGGERS, MemoryMode.TEST_MODE]:
            # Save based on configuration
            should_save = force or config.save_on_session_end
            
            # Check for important info trigger
            if config.save_on_important_info and metrics:
                if "important_info" in metrics.triggers_fired:
                    should_save = True
        
        if not should_save:
            logger.debug(f"Skipping memory save for session {session_state.session_id}")
            return
        
        # Prepare messages based on mode
        messages_to_save = []
        
        if config.mode == MemoryMode.ALWAYS_FRESH:
            # For ALWAYS_FRESH: save only the last user-assistant pair
            if len(session_state.conversation_history) >= 2:
                # Get last 2 messages (should be user + assistant)
                messages_to_save = self.format_messages_for_mem0(
                    session_state.conversation_history,
                    limit=2
                )
            elif session_state.conversation_history:
                # If only 1 message, save it
                messages_to_save = self.format_messages_for_mem0(
                    session_state.conversation_history,
                    limit=1
                )
        else:
            # For other modes: save batch of messages
            # CACHE_FIRST: all messages (called at session end)
            # SMART_TRIGGERS: last N messages (called periodically)
            if config.mode == MemoryMode.CACHE_FIRST:
                # Save all messages
                messages_to_save = self.format_messages_for_mem0(
                    session_state.conversation_history
                )
            else:
                # Save last 10 messages for SMART_TRIGGERS
                messages_to_save = self.format_messages_for_mem0(
                    session_state.conversation_history,
                    limit=10
                )
        
        if not messages_to_save:
            logger.warning(f"No messages to save for session {session_state.session_id}")
            return
        
        # Prepare metadata
        metadata = {
            "session_id": session_state.session_id,
            "agents_involved": list(set(t.to_agent for t in session_state.transfer_history)) if session_state.transfer_history else [],
            "message_count": len(session_state.conversation_history),
            "memory_mode": config.mode.value,
            "triggers_fired": metrics.triggers_fired if metrics else {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Add current agent to agents_involved
        if current_agent and current_agent not in metadata["agents_involved"]:
            metadata["agents_involved"].append(current_agent)
        
        # Save to Mem0
        memory_id = await self.add_memory(
            user_id=session_state.user_id,
            messages=messages_to_save,
            agent_id=current_agent,
            run_id=session_state.session_id if config.mode != MemoryMode.ALWAYS_FRESH else None,
            metadata=metadata
        )
        
        # Add to session memory refs
        if memory_id:
            session_state.memory_refs.append(memory_id)
            await self.save_session_state(session_state)
            logger.info(f"Saved {len(messages_to_save)} messages to Mem0 for session {session_state.session_id}")
            
        if config.log_all_operations:
            logger.info(f"[TEST MODE] Saved memory: {memory_id} with {len(messages_to_save)} messages")
    
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
    
    # Memory Mode Management Methods
    
    def set_global_mode(self, config: MemoryConfig):
        """Set global memory configuration"""
        self.global_config = config
        logger.info(f"Global memory mode set to: {config.mode}")
    
    def set_session_mode(self, session_id: str, config: MemoryConfig):
        """Set memory configuration for specific session"""
        self.session_configs[session_id] = config
        
        # Initialize metrics for this session
        if session_id not in self.session_metrics:
            self.session_metrics[session_id] = MemoryMetrics(
                session_id=session_id,
                mode=config.mode
            )
        
        logger.info(f"Session {session_id} memory mode set to: {config.mode}")
    
    def get_session_config(self, session_id: str) -> MemoryConfig:
        """Get memory configuration for session (fallback to global)"""
        return self.session_configs.get(session_id, self.global_config)
    
    def get_session_metrics(self, session_id: str) -> Optional[MemoryMetrics]:
        """Get metrics for a session"""
        return self.session_metrics.get(session_id)
    
    async def should_refresh_memory(
        self, 
        session_state: SessionState,
        message: Optional[str] = None
    ) -> bool:
        """Check if memory should be refreshed based on triggers"""
        config = self.get_session_config(session_state.session_id)
        
        # Always refresh mode
        if config.mode == MemoryMode.ALWAYS_FRESH:
            logger.debug(f"Memory mode is ALWAYS_FRESH, should refresh: True")
            return True
        
        # Cache first mode - only on session start
        if config.mode == MemoryMode.CACHE_FIRST:
            # Check if we have cached context
            cache_key = f"context:{session_state.session_id}"
            cached = await self.redis_client.get(cache_key)
            should_refresh = cached is None
            logger.debug(f"Memory mode is CACHE_FIRST, cache exists: {cached is not None}, should refresh: {should_refresh}")
            return should_refresh
        
        # Smart triggers mode
        if config.mode == MemoryMode.SMART_TRIGGERS:
            return await self._check_smart_triggers(session_state, message, config)
        
        # Test mode - follow smart triggers but log everything
        if config.mode == MemoryMode.TEST_MODE:
            should_refresh = await self._check_smart_triggers(session_state, message, config)
            if config.log_all_operations:
                logger.info(f"[TEST MODE] Should refresh: {should_refresh}")
            return should_refresh
        
        return False
    
    async def _check_smart_triggers(
        self,
        session_state: SessionState,
        message: Optional[str],
        config: MemoryConfig
    ) -> bool:
        """Check if any smart trigger is activated"""
        triggers = config.triggers
        metrics = self.get_session_metrics(session_state.session_id)
        
        # Message count trigger
        if triggers.message_count.enabled and triggers.message_count.threshold:
            msg_count = len(session_state.conversation_history)
            if msg_count % triggers.message_count.threshold == 0:
                if metrics:
                    metrics.add_trigger("message_count")
                logger.debug(f"Message count trigger fired: {msg_count}")
                return True
        
        # Time elapsed trigger
        if triggers.time_elapsed.enabled and triggers.time_elapsed.minutes:
            if metrics and metrics.started_at:
                elapsed = (datetime.now() - metrics.started_at).total_seconds() / 60
                if elapsed >= triggers.time_elapsed.minutes:
                    metrics.add_trigger("time_elapsed")
                    logger.debug(f"Time elapsed trigger fired: {elapsed:.1f} minutes")
                    return True
        
        # Agent transfer trigger
        if triggers.agent_transfer.enabled:
            # Check if agent changed in last transfer
            if session_state.transfer_history:
                last_transfer = session_state.transfer_history[-1]
                # Check if this is a recent transfer (within last 2 messages)
                recent_messages = session_state.conversation_history[-2:]
                if any(msg.metadata.get("transfer_event") for msg in recent_messages):
                    if metrics:
                        metrics.add_trigger("agent_transfer")
                    logger.debug("Agent transfer trigger fired")
                    return True
        
        # Keyword-based triggers (emotion, topic, important info)
        if message:
            message_lower = message.lower()
            
            # Emotion spike trigger
            if triggers.emotion_spike.enabled and triggers.emotion_spike.keywords:
                if any(keyword in message_lower for keyword in triggers.emotion_spike.keywords):
                    if metrics:
                        metrics.add_trigger("emotion_spike")
                    logger.debug("Emotion spike trigger fired")
                    return True
            
            # Topic change trigger
            if triggers.topic_change.enabled and triggers.topic_change.keywords:
                if any(keyword in message_lower for keyword in triggers.topic_change.keywords):
                    if metrics:
                        metrics.add_trigger("topic_change")
                    logger.debug("Topic change trigger fired")
                    return True
            
            # Important info trigger (for immediate save)
            if triggers.important_info.enabled and triggers.important_info.keywords:
                if any(keyword in message_lower for keyword in triggers.important_info.keywords):
                    if metrics:
                        metrics.add_trigger("important_info")
                    logger.debug("Important info trigger fired")
                    # Note: This trigger might also trigger immediate save
                    return True
        
        return False
    
    async def retrieve_user_context(
        self,
        session_state: SessionState,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Retrieve user context based on memory mode"""
        config = self.get_session_config(session_state.session_id)
        metrics = self.get_session_metrics(session_state.session_id)
        cache_key = f"context:{session_state.session_id}"
        
        # Check cache first (unless forced or in always fresh mode)
        if not force_refresh and config.mode != MemoryMode.ALWAYS_FRESH:
            cached = await self.redis_client.get(cache_key)
            if cached:
                if metrics:
                    metrics.add_cache_hit()
                logger.debug(f"Cache hit for session {session_state.session_id}")
                cached_data = json.loads(cached)
                logger.info(f"Retrieved {len(cached_data.get('memories', []))} memories from Redis cache")
                return cached_data
        
        # Cache miss - retrieve from Mem0
        if metrics:
            metrics.add_cache_miss()
        
        logger.info(f"Cache miss for session {session_state.session_id}, retrieving from Mem0")
        start_time = time.time()
        context = await self._retrieve_from_mem0(session_state, config)
        retrieval_time = (time.time() - start_time) * 1000  # Convert to ms
        logger.info(f"Mem0 retrieval took {retrieval_time:.2f}ms, got {len(context.get('memories', []))} memories")
        
        # Update metrics
        if metrics:
            token_count = len(json.dumps(context)) // 4  # Rough estimate
            metrics.add_retrieval(token_count, retrieval_time)
        
        # Cache the context
        await self.redis_client.setex(
            cache_key,
            config.cache_ttl,
            json.dumps(context)
        )
        
        logger.debug(f"Retrieved and cached context for session {session_state.session_id}")
        return context
    
    async def _retrieve_from_mem0(
        self,
        session_state: SessionState,
        config: MemoryConfig
    ) -> Dict[str, Any]:
        """Retrieve memories from Mem0 with config limits"""
        if not session_state.user_id:
            return {"memories": [], "profile": {}}
        
        # Initialize Mem0 if needed
        self._init_mem0()
        
        if not self.mem0_client:
            return {"memories": [], "profile": {}}
        
        # Get last user message for context
        last_user_msg = None
        for msg in reversed(session_state.conversation_history[-10:]):
            if msg.role == "user":
                last_user_msg = msg.content
                break
        
        if not last_user_msg:
            last_user_msg = "user conversation history"
        
        # Search memories with limit
        logger.info(f"Searching Mem0 for user {session_state.user_id} with query: {last_user_msg[:50]}...")
        memories = await self.search_memories(
            session_state.user_id,
            last_user_msg,
            limit=config.max_memories_per_retrieval
        )
        logger.info(f"Found {len(memories)} memories for user {session_state.user_id}")
        
        # Truncate if exceeds token limit
        context = {
            "memories": memories,
            "profile": await self.get_user_profile(session_state.user_id)
        }
        
        # Simple token estimation and truncation
        context_str = json.dumps(context)
        if len(context_str) > config.max_context_tokens * 4:  # Rough char to token ratio
            # Truncate memories
            while len(json.dumps(context)) > config.max_context_tokens * 4 and context["memories"]:
                context["memories"].pop()
        
        return context