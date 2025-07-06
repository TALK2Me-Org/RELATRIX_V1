"""
Redis Configuration and Client Setup
Provides Redis client for MCP server
"""

import redis
from typing import Optional
import logging
from config import settings

logger = logging.getLogger(__name__)

def get_redis_client() -> redis.Redis:
    """
    Create and return Redis client instance
    
    Returns:
        redis.Redis: Configured Redis client
    """
    try:
        # Parse Redis URL or use default localhost
        redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/0')
        redis_password = getattr(settings, 'redis_password', None)
        
        # Create Redis client
        if redis_password:
            client = redis.from_url(
                redis_url,
                password=redis_password,
                decode_responses=True
            )
        else:
            client = redis.from_url(
                redis_url,
                decode_responses=True
            )
        
        # Test connection
        client.ping()
        logger.info("Redis connection established")
        
        return client
        
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        logger.warning("Creating mock Redis client for development")
        # Return a mock client for development/testing
        return MockRedisClient()
    except Exception as e:
        logger.error(f"Unexpected error creating Redis client: {e}")
        raise

class MockRedisClient:
    """Mock Redis client for development when Redis is not available"""
    
    def __init__(self):
        self.data = {}
        logger.warning("Using mock Redis client - data will not persist")
    
    def get(self, key):
        return self.data.get(key)
    
    def set(self, key, value, ex=None):
        self.data[key] = value
        return True
    
    def delete(self, key):
        if key in self.data:
            del self.data[key]
            return 1
        return 0
    
    def exists(self, key):
        return key in self.data
    
    def expire(self, key, seconds):
        # Mock implementation - doesn't actually expire
        return True
    
    def ttl(self, key):
        # Mock implementation - returns -1 (no expiry)
        return -1 if key in self.data else -2
    
    def ping(self):
        return True
    
    def flushdb(self):
        self.data.clear()
        return True