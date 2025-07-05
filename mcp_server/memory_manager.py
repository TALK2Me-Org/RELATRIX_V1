"""
RELATRIX Memory Manager
Intelligent memory management using Mem0 for long-term storage and Redis for caching
Optimizes context length and reduces API costs through smart memory compression
"""

import os
import sys
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import tiktoken

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redis_config import get_redis_client, CacheKeys, CacheTTL
from backend.app.config import settings

# Try to import mem0ai
try:
    from mem0 import MemoryClient
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False
    logging.warning("mem0ai not available. Using fallback memory storage.")

logger = logging.getLogger(__name__)

class MemoryType(Enum):
    """Types of memory storage"""
    CONVERSATION = "conversation"
    RELATIONSHIP_PATTERN = "relationship_pattern"
    COMMUNICATION_STYLE = "communication_style"
    EMOTIONAL_STATE = "emotional_state"
    CONFLICT_HISTORY = "conflict_history"
    SOLUTION_HISTORY = "solution_history"
    PREFERENCE = "preference"
    CONTEXT = "context"

@dataclass
class MemoryEntry:
    """Individual memory entry"""
    id: str
    content: str
    memory_type: MemoryType
    timestamp: datetime
    user_id: str
    session_id: str
    agent_id: str
    importance: float = 1.0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "importance": self.importance,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create from dictionary"""
        return cls(
            id=data["id"],
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            user_id=data["user_id"],
            session_id=data["session_id"],
            agent_id=data["agent_id"],
            importance=data.get("importance", 1.0),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )

@dataclass
class ConversationContext:
    """Context for conversation memory"""
    session_id: str
    user_id: str
    current_agent: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    compressed_context: Optional[str] = None
    token_count: int = 0
    last_compression: Optional[datetime] = None
    importance_scores: List[float] = field(default_factory=list)

class MemoryManager:
    """Intelligent memory management system"""
    
    def __init__(self):
        self.redis_client = get_redis_client()
        self.mem0_client = None
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        
        # Initialize Mem0 client if available
        if MEM0_AVAILABLE and not settings.mem0_api_key.startswith("m0-placeholder"):
            try:
                self.mem0_client = MemoryClient(
                    api_key=settings.mem0_api_key,
                    user_id=settings.mem0_user_id
                )
                logger.info("Mem0 client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Mem0 client: {e}")
                self.mem0_client = None
        else:
            logger.info("Using Redis-only memory storage")
        
        # Memory configuration
        self.max_context_length = settings.max_context_length
        self.compression_threshold = settings.context_compression_threshold
        self.max_memory_entries = 1000
        
        logger.info("Memory manager initialized")
    
    def _generate_memory_id(self, content: str, user_id: str, session_id: str) -> str:
        """Generate unique memory ID"""
        data = f"{content}:{user_id}:{session_id}:{datetime.now().isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed: {e}")
            return len(text) // 4  # Rough estimation
    
    def _calculate_importance(self, content: str, memory_type: MemoryType, metadata: Dict[str, Any]) -> float:
        """Calculate importance score for memory entry"""
        base_importance = 1.0
        
        # Memory type weights
        type_weights = {
            MemoryType.RELATIONSHIP_PATTERN: 2.0,
            MemoryType.CONFLICT_HISTORY: 1.8,
            MemoryType.COMMUNICATION_STYLE: 1.5,
            MemoryType.EMOTIONAL_STATE: 1.2,
            MemoryType.SOLUTION_HISTORY: 1.6,
            MemoryType.PREFERENCE: 1.3,
            MemoryType.CONVERSATION: 1.0,
            MemoryType.CONTEXT: 0.8
        }
        
        importance = base_importance * type_weights.get(memory_type, 1.0)
        
        # Emotional intensity boost
        emotional_keywords = ["angry", "hurt", "love", "hate", "devastated", "happy", "excited"]
        for keyword in emotional_keywords:
            if keyword in content.lower():
                importance *= 1.2
                break
        
        # Conflict-related boost
        conflict_keywords = ["fight", "argument", "disagree", "conflict", "problem"]
        for keyword in conflict_keywords:
            if keyword in content.lower():
                importance *= 1.3
                break
        
        # Solution-related boost
        solution_keywords = ["solution", "plan", "fix", "resolve", "improve", "work"]
        for keyword in solution_keywords:
            if keyword in content.lower():
                importance *= 1.2
                break
        
        # Recency boost
        if metadata.get("is_recent", False):
            importance *= 1.1
        
        return min(importance, 3.0)  # Cap at 3.0
    
    async def store_memory(self, content: str, memory_type: MemoryType, user_id: str, 
                          session_id: str, agent_id: str, tags: List[str] = None, 
                          metadata: Dict[str, Any] = None) -> str:
        """Store memory entry"""
        try:
            tags = tags or []
            metadata = metadata or {}
            
            # Generate memory ID
            memory_id = self._generate_memory_id(content, user_id, session_id)
            
            # Calculate importance
            importance = self._calculate_importance(content, memory_type, metadata)
            
            # Create memory entry
            memory_entry = MemoryEntry(
                id=memory_id,
                content=content,
                memory_type=memory_type,
                timestamp=datetime.now(),
                user_id=user_id,
                session_id=session_id,
                agent_id=agent_id,
                importance=importance,
                tags=tags,
                metadata=metadata
            )
            
            # Store in Redis for fast access
            cache_key = CacheKeys.format_key(CacheKeys.AGENT_MEMORY, session_id=session_id)
            await self._store_in_redis(cache_key, memory_entry)
            
            # Store in Mem0 for long-term storage
            if self.mem0_client:
                await self._store_in_mem0(memory_entry)
            
            logger.info(f"Memory stored: {memory_id} (importance: {importance:.2f})")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise
    
    async def _store_in_redis(self, cache_key: str, memory_entry: MemoryEntry):
        """Store memory entry in Redis"""
        try:
            # Get existing memories
            existing_data = self.redis_client.get(cache_key)
            if existing_data:
                memories = json.loads(existing_data)
            else:
                memories = []
            
            # Add new memory
            memories.append(memory_entry.to_dict())
            
            # Keep only the most recent/important memories
            if len(memories) > self.max_memory_entries:
                memories = sorted(memories, key=lambda x: (x["importance"], x["timestamp"]), reverse=True)
                memories = memories[:self.max_memory_entries]
            
            # Store back in Redis
            self.redis_client.setex(
                cache_key,
                CacheTTL.MEMORY,
                json.dumps(memories)
            )
            
        except Exception as e:
            logger.error(f"Failed to store in Redis: {e}")
            raise
    
    async def _store_in_mem0(self, memory_entry: MemoryEntry):
        """Store memory entry in Mem0"""
        try:
            if not self.mem0_client:
                return
            
            # Prepare memory data for Mem0
            memory_data = {
                "content": memory_entry.content,
                "user_id": memory_entry.user_id,
                "agent_id": memory_entry.agent_id,
                "metadata": {
                    "session_id": memory_entry.session_id,
                    "memory_type": memory_entry.memory_type.value,
                    "importance": memory_entry.importance,
                    "tags": memory_entry.tags,
                    "timestamp": memory_entry.timestamp.isoformat(),
                    **memory_entry.metadata
                }
            }
            
            # Store in Mem0
            await asyncio.to_thread(self.mem0_client.add, memory_data)
            
        except Exception as e:
            logger.error(f"Failed to store in Mem0: {e}")
            # Don't raise - Redis storage should work even if Mem0 fails
    
    async def retrieve_memories(self, user_id: str, session_id: str = None, 
                               memory_type: MemoryType = None, limit: int = 10) -> List[MemoryEntry]:
        """Retrieve memories from storage"""
        try:
            memories = []
            
            # Try Redis first for fast access
            if session_id:
                cache_key = CacheKeys.format_key(CacheKeys.AGENT_MEMORY, session_id=session_id)
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    cached_memories = json.loads(cached_data)
                    for memory_data in cached_memories:
                        if memory_type is None or memory_data["memory_type"] == memory_type.value:
                            memories.append(MemoryEntry.from_dict(memory_data))
            
            # If not enough memories, try Mem0
            if len(memories) < limit and self.mem0_client:
                mem0_memories = await self._retrieve_from_mem0(user_id, memory_type, limit - len(memories))
                memories.extend(mem0_memories)
            
            # Sort by importance and recency
            memories.sort(key=lambda x: (x.importance, x.timestamp), reverse=True)
            
            return memories[:limit]
            
        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}")
            return []
    
    async def _retrieve_from_mem0(self, user_id: str, memory_type: MemoryType = None, 
                                 limit: int = 10) -> List[MemoryEntry]:
        """Retrieve memories from Mem0"""
        try:
            if not self.mem0_client:
                return []
            
            # Query Mem0
            query_params = {"user_id": user_id, "limit": limit}
            if memory_type:
                query_params["filters"] = {"memory_type": memory_type.value}
            
            mem0_results = await asyncio.to_thread(self.mem0_client.get_all, **query_params)
            
            # Convert to MemoryEntry objects
            memories = []
            for result in mem0_results:
                metadata = result.get("metadata", {})
                memory_entry = MemoryEntry(
                    id=result.get("id", ""),
                    content=result.get("content", ""),
                    memory_type=MemoryType(metadata.get("memory_type", "context")),
                    timestamp=datetime.fromisoformat(metadata.get("timestamp", datetime.now().isoformat())),
                    user_id=user_id,
                    session_id=metadata.get("session_id", ""),
                    agent_id=metadata.get("agent_id", ""),
                    importance=metadata.get("importance", 1.0),
                    tags=metadata.get("tags", []),
                    metadata=metadata
                )
                memories.append(memory_entry)
            
            return memories
            
        except Exception as e:
            logger.error(f"Failed to retrieve from Mem0: {e}")
            return []
    
    async def get_conversation_context(self, session_id: str, user_id: str) -> ConversationContext:
        """Get conversation context for a session"""
        try:
            cache_key = CacheKeys.format_key(CacheKeys.CONVERSATION_CONTEXT, session_id=session_id)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                return ConversationContext(
                    session_id=session_id,
                    user_id=user_id,
                    current_agent=data.get("current_agent", "misunderstanding_protector"),
                    messages=data.get("messages", []),
                    compressed_context=data.get("compressed_context"),
                    token_count=data.get("token_count", 0),
                    last_compression=datetime.fromisoformat(data["last_compression"]) if data.get("last_compression") else None,
                    importance_scores=data.get("importance_scores", [])
                )
            else:
                # Create new context
                return ConversationContext(
                    session_id=session_id,
                    user_id=user_id,
                    current_agent="misunderstanding_protector"
                )
                
        except Exception as e:
            logger.error(f"Failed to get conversation context: {e}")
            return ConversationContext(session_id=session_id, user_id=user_id, current_agent="misunderstanding_protector")
    
    async def update_conversation_context(self, context: ConversationContext):
        """Update conversation context"""
        try:
            # Check if compression is needed
            if context.token_count > self.compression_threshold:
                await self._compress_context(context)
            
            # Store updated context
            cache_key = CacheKeys.format_key(CacheKeys.CONVERSATION_CONTEXT, session_id=context.session_id)
            context_data = {
                "current_agent": context.current_agent,
                "messages": context.messages,
                "compressed_context": context.compressed_context,
                "token_count": context.token_count,
                "last_compression": context.last_compression.isoformat() if context.last_compression else None,
                "importance_scores": context.importance_scores
            }
            
            self.redis_client.setex(
                cache_key,
                CacheTTL.AGENT_CONTEXT,
                json.dumps(context_data)
            )
            
        except Exception as e:
            logger.error(f"Failed to update conversation context: {e}")
    
    async def _compress_context(self, context: ConversationContext):
        """Compress conversation context to save tokens"""
        try:
            if not context.messages:
                return
            
            # Create summary of conversation
            messages_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context.messages])
            
            # Store important messages based on importance scores
            important_messages = []
            if context.importance_scores:
                for i, score in enumerate(context.importance_scores):
                    if score > 1.5 and i < len(context.messages):
                        important_messages.append(context.messages[i])
            
            # Create compressed context
            compressed_summary = f"Previous conversation summary:\n{messages_text[:500]}..."
            if important_messages:
                compressed_summary += f"\n\nKey moments:\n"
                for msg in important_messages[-5:]:  # Last 5 important messages
                    compressed_summary += f"- {msg['role']}: {msg['content'][:100]}...\n"
            
            # Update context
            context.compressed_context = compressed_summary
            context.messages = context.messages[-5:]  # Keep only last 5 messages
            context.token_count = self._count_tokens(compressed_summary + str(context.messages))
            context.last_compression = datetime.now()
            
            logger.info(f"Context compressed for session {context.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to compress context: {e}")
    
    async def add_message_to_context(self, session_id: str, user_id: str, role: str, 
                                    content: str, importance: float = 1.0):
        """Add message to conversation context"""
        try:
            context = await self.get_conversation_context(session_id, user_id)
            
            # Add message
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "importance": importance
            }
            
            context.messages.append(message)
            context.importance_scores.append(importance)
            context.token_count += self._count_tokens(content)
            
            # Store as memory if important
            if importance > 1.2:
                await self.store_memory(
                    content=content,
                    memory_type=MemoryType.CONVERSATION,
                    user_id=user_id,
                    session_id=session_id,
                    agent_id=context.current_agent,
                    metadata={"role": role, "importance": importance}
                )
            
            # Update context
            await self.update_conversation_context(context)
            
        except Exception as e:
            logger.error(f"Failed to add message to context: {e}")
    
    async def get_relevant_memories(self, query: str, user_id: str, session_id: str = None, 
                                   limit: int = 5) -> List[MemoryEntry]:
        """Get memories relevant to a query"""
        try:
            # First try semantic search with Mem0
            if self.mem0_client:
                try:
                    # Search Mem0
                    search_results = await asyncio.to_thread(
                        self.mem0_client.search,
                        query=query,
                        user_id=user_id,
                        limit=limit
                    )
                    
                    memories = []
                    for result in search_results:
                        metadata = result.get("metadata", {})
                        memory_entry = MemoryEntry(
                            id=result.get("id", ""),
                            content=result.get("content", ""),
                            memory_type=MemoryType(metadata.get("memory_type", "context")),
                            timestamp=datetime.fromisoformat(metadata.get("timestamp", datetime.now().isoformat())),
                            user_id=user_id,
                            session_id=metadata.get("session_id", ""),
                            agent_id=metadata.get("agent_id", ""),
                            importance=metadata.get("importance", 1.0),
                            tags=metadata.get("tags", []),
                            metadata=metadata
                        )
                        memories.append(memory_entry)
                    
                    return memories
                    
                except Exception as e:
                    logger.warning(f"Mem0 search failed: {e}")
            
            # Fallback to keyword search in Redis
            all_memories = await self.retrieve_memories(user_id, session_id, limit=50)
            
            # Simple keyword matching
            query_words = query.lower().split()
            relevant_memories = []
            
            for memory in all_memories:
                relevance_score = 0
                memory_text = memory.content.lower()
                
                for word in query_words:
                    if word in memory_text:
                        relevance_score += 1
                
                if relevance_score > 0:
                    relevant_memories.append((memory, relevance_score))
            
            # Sort by relevance and importance
            relevant_memories.sort(key=lambda x: (x[1], x[0].importance), reverse=True)
            
            return [memory for memory, _ in relevant_memories[:limit]]
            
        except Exception as e:
            logger.error(f"Failed to get relevant memories: {e}")
            return []
    
    async def get_memory_summary(self, user_id: str, session_id: str = None) -> Dict[str, Any]:
        """Get memory summary for user"""
        try:
            memories = await self.retrieve_memories(user_id, session_id, limit=100)
            
            if not memories:
                return {"total_memories": 0}
            
            # Count by type
            type_counts = {}
            for memory in memories:
                type_name = memory.memory_type.value
                type_counts[type_name] = type_counts.get(type_name, 0) + 1
            
            # Calculate average importance
            avg_importance = sum(m.importance for m in memories) / len(memories)
            
            # Recent memories (last 7 days)
            recent_cutoff = datetime.now() - timedelta(days=7)
            recent_memories = [m for m in memories if m.timestamp > recent_cutoff]
            
            return {
                "total_memories": len(memories),
                "memory_types": type_counts,
                "average_importance": avg_importance,
                "recent_memories": len(recent_memories),
                "oldest_memory": min(memories, key=lambda x: x.timestamp).timestamp.isoformat() if memories else None,
                "newest_memory": max(memories, key=lambda x: x.timestamp).timestamp.isoformat() if memories else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory summary: {e}")
            return {"total_memories": 0, "error": str(e)}
    
    async def cleanup_old_memories(self, days_threshold: int = 30):
        """Clean up old memories"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_threshold)
            
            # Clean up Redis cache
            pattern = CacheKeys.AGENT_MEMORY.replace("{session_id}", "*")
            keys = self.redis_client.keys(pattern)
            
            for key in keys:
                try:
                    cached_data = self.redis_client.get(key)
                    if cached_data:
                        memories = json.loads(cached_data)
                        filtered_memories = [
                            m for m in memories 
                            if datetime.fromisoformat(m["timestamp"]) > cutoff_date
                        ]
                        
                        if len(filtered_memories) != len(memories):
                            if filtered_memories:
                                self.redis_client.setex(
                                    key,
                                    CacheTTL.MEMORY,
                                    json.dumps(filtered_memories)
                                )
                            else:
                                self.redis_client.delete(key)
                            
                            logger.info(f"Cleaned {len(memories) - len(filtered_memories)} old memories from {key}")
                        
                except Exception as e:
                    logger.warning(f"Failed to clean key {key}: {e}")
            
            logger.info(f"Memory cleanup completed for memories older than {days_threshold} days")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old memories: {e}")

# Global memory manager instance
memory_manager = MemoryManager()

# Convenience functions
async def store_memory(content: str, memory_type: MemoryType, user_id: str, session_id: str, 
                      agent_id: str, tags: List[str] = None, metadata: Dict[str, Any] = None) -> str:
    """Store memory entry"""
    return await memory_manager.store_memory(content, memory_type, user_id, session_id, agent_id, tags, metadata)

async def retrieve_memories(user_id: str, session_id: str = None, memory_type: MemoryType = None, 
                           limit: int = 10) -> List[MemoryEntry]:
    """Retrieve memories"""
    return await memory_manager.retrieve_memories(user_id, session_id, memory_type, limit)

async def get_relevant_memories(query: str, user_id: str, session_id: str = None, 
                               limit: int = 5) -> List[MemoryEntry]:
    """Get relevant memories for a query"""
    return await memory_manager.get_relevant_memories(query, user_id, session_id, limit)

async def add_message_to_context(session_id: str, user_id: str, role: str, content: str, 
                                importance: float = 1.0):
    """Add message to conversation context"""
    return await memory_manager.add_message_to_context(session_id, user_id, role, content, importance)

if __name__ == "__main__":
    # Test the memory manager
    import asyncio
    
    async def test_memory_manager():
        print("RELATRIX Memory Manager Test")
        print("=" * 40)
        
        # Test storing memory
        memory_id = await store_memory(
            content="We had a fight about money yesterday",
            memory_type=MemoryType.CONFLICT_HISTORY,
            user_id="test_user",
            session_id="test_session",
            agent_id="conflict_solver",
            tags=["money", "conflict"],
            metadata={"severity": "high"}
        )
        print(f"Stored memory: {memory_id}")
        
        # Test retrieving memories
        memories = await retrieve_memories("test_user", "test_session", limit=5)
        print(f"Retrieved {len(memories)} memories")
        
        # Test relevant memories
        relevant = await get_relevant_memories("money problems", "test_user", "test_session")
        print(f"Found {len(relevant)} relevant memories")
        
        # Test memory summary
        summary = await memory_manager.get_memory_summary("test_user", "test_session")
        print(f"Memory summary: {summary}")
        
        print("Memory manager test completed")
    
    asyncio.run(test_memory_manager())