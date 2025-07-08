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
        results = await client.search(
            query=query,
            user_id=user_id
        )
        logger.info(f"Found {len(results)} memories for user {user_id}")
        return results
    except Exception as e:
        logger.error(f"Memory search error: {e}")
        return []


async def add_memory(messages: list, user_id: str):
    """Add conversation to memory"""
    try:
        result = await client.add(
            messages=messages,
            user_id=user_id,
            version="v2"  # Important for automatic context management
        )
        logger.info(f"Memory saved for user {user_id}: {result}")
        return result
    except Exception as e:
        logger.error(f"Memory add error: {e}")
        return None