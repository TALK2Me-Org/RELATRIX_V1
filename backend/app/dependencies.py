"""
FastAPI Dependencies
Dependency injection for services
"""

from functools import lru_cache
from .services.agent_service import AgentService

@lru_cache()
def get_agent_service() -> AgentService:
    """Get agent service instance"""
    return AgentService()