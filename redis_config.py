"""
Redis Configuration for RELATRIX
Provides Redis connection management and configuration
"""

import os
import redis
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class RedisConfig:
    """Redis configuration and connection management"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis_password = os.getenv("REDIS_PASSWORD", None)
        self.max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
        self.socket_timeout = int(os.getenv("REDIS_SOCKET_TIMEOUT", "5"))
        self.socket_connect_timeout = int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5"))
        self.retry_on_timeout = os.getenv("REDIS_RETRY_ON_TIMEOUT", "True").lower() == "true"
        
        # Parse Redis URL
        parsed_url = urlparse(self.redis_url)
        self.host = parsed_url.hostname or "localhost"
        self.port = parsed_url.port or 6379
        self.db = int(parsed_url.path.lstrip('/') or 0)
        
        # Connection pool
        self._pool: Optional[redis.ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
    
    def get_connection_pool(self) -> redis.ConnectionPool:
        """Get or create Redis connection pool"""
        if self._pool is None:
            self._pool = redis.ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.redis_password,
                max_connections=self.max_connections,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                retry_on_timeout=self.retry_on_timeout,
                decode_responses=True
            )
        return self._pool
    
    def get_client(self) -> redis.Redis:
        """Get Redis client instance"""
        if self._client is None:
            self._client = redis.Redis(connection_pool=self.get_connection_pool())
        return self._client
    
    def test_connection(self) -> bool:
        """Test Redis connection"""
        try:
            client = self.get_client()
            client.ping()
            logger.info("Redis connection successful")
            return True
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """Get Redis server info"""
        try:
            client = self.get_client()
            return client.info()
        except Exception as e:
            logger.error(f"Failed to get Redis info: {e}")
            return {}
    
    def flush_db(self) -> bool:
        """Flush current database (use with caution)"""
        try:
            client = self.get_client()
            client.flushdb()
            logger.warning("Redis database flushed")
            return True
        except Exception as e:
            logger.error(f"Failed to flush Redis database: {e}")
            return False
    
    def close(self):
        """Close Redis connections"""
        if self._pool:
            self._pool.disconnect()
            self._pool = None
        if self._client:
            self._client.close()
            self._client = None
        logger.info("Redis connections closed")

# Global Redis configuration instance
redis_config = RedisConfig()

# Convenience functions
def get_redis_client() -> redis.Redis:
    """Get Redis client instance"""
    return redis_config.get_client()

def test_redis_connection() -> bool:
    """Test Redis connection"""
    return redis_config.test_connection()

def get_redis_info() -> Dict[str, Any]:
    """Get Redis server information"""
    return redis_config.get_info()

# Cache key patterns
class CacheKeys:
    """Redis cache key patterns"""
    
    # User sessions
    USER_SESSION = "user_session:{user_id}"
    USER_CONVERSATIONS = "user_conversations:{user_id}"
    
    # Agent context
    AGENT_CONTEXT = "agent_context:{session_id}"
    AGENT_MEMORY = "agent_memory:{session_id}"
    
    # Memory optimization
    MEMORY_SUMMARY = "memory_summary:{user_id}"
    CONVERSATION_CONTEXT = "conversation_context:{session_id}"
    
    # Transfer protocols
    TRANSFER_STATE = "transfer_state:{session_id}"
    ACTIVE_AGENT = "active_agent:{session_id}"
    
    # Cost tracking
    DAILY_COSTS = "daily_costs:{date}"
    USER_COSTS = "user_costs:{user_id}:{date}"
    
    # Admin cache
    ADMIN_STATS = "admin_stats:{date}"
    SYSTEM_METRICS = "system_metrics"
    
    # Rate limiting
    RATE_LIMIT = "rate_limit:{user_id}:{endpoint}"
    
    @staticmethod
    def format_key(pattern: str, **kwargs) -> str:
        """Format cache key with parameters"""
        return pattern.format(**kwargs)

# Cache TTL settings (in seconds)
class CacheTTL:
    """Cache TTL constants"""
    
    # Short term (5 minutes)
    SHORT = 300
    
    # Medium term (1 hour)
    MEDIUM = 3600
    
    # Long term (24 hours)
    LONG = 86400
    
    # Extended (7 days)
    EXTENDED = 604800
    
    # Session data (30 minutes)
    SESSION = 1800
    
    # Agent context (2 hours)
    AGENT_CONTEXT = 7200
    
    # Memory summaries (24 hours)
    MEMORY = 86400
    
    # Cost data (24 hours)
    COSTS = 86400

if __name__ == "__main__":
    # Test Redis connection
    print("Testing Redis connection...")
    if test_redis_connection():
        print("✅ Redis connection successful")
        info = get_redis_info()
        print(f"Redis version: {info.get('redis_version', 'Unknown')}")
        print(f"Connected clients: {info.get('connected_clients', 'Unknown')}")
    else:
        print("❌ Redis connection failed")
        print("Please check your Redis server and configuration")