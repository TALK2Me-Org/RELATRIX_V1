"""
Memory service using official Mem0 AsyncMemoryClient
Ultra simple - no custom wrappers!
"""
from mem0 import AsyncMemoryClient
from config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize AsyncMemoryClient
client = AsyncMemoryClient(api_key=settings.mem0_api_key)


async def search_memories(query: str, user_id: str):
    """Search memories for user"""
    try:
        logger.info(f"[MEM0] Searching memories for user: {user_id}, query: {query[:50]}...")
        results = await client.search(
            query=query,
            user_id=user_id
        )
        logger.info(f"[MEM0] Found {len(results)} memories for user {user_id}")
        if results:
            logger.debug(f"[MEM0] Memory preview: {results[0]}")
        return results
    except Exception as e:
        logger.error(f"[MEM0] Memory search error: {e}")
        return []


async def add_memory(messages: list, user_id: str):
    """Add conversation to memory"""
    try:
        logger.info(f"[MEM0] Adding memory for user: {user_id}")
        logger.debug(f"[MEM0] Messages to save: {messages}")
        result = await client.add(
            messages=messages,
            user_id=user_id,
            version="v2"  # Important for automatic context management
        )
        logger.info(f"[MEM0] Memory saved successfully for user {user_id}")
        logger.debug(f"[MEM0] Save result: {result}")
        return result
    except Exception as e:
        logger.error(f"[MEM0] Memory add error: {e}")
        logger.error(f"[MEM0] Failed messages: {messages}")
        return None