"""
Agent Loader for MCP Server
Loads agent configurations from backend API
"""

import logging
import httpx
from typing import Dict, Any, Optional
import asyncio
from config import settings

logger = logging.getLogger(__name__)

class AgentLoader:
    """Loads and caches agent configurations from backend API"""
    
    def __init__(self, backend_url: str = None):
        self.backend_url = backend_url or f"http://localhost:{getattr(settings, 'api_port', 8000)}"
        self.agents_cache: Dict[str, Dict[str, Any]] = {}
        self._last_fetch = None
    
    async def load_agents(self) -> Dict[str, Dict[str, Any]]:
        """Load all active agents from backend API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.backend_url}/api/admin/agents/",
                    params={"is_active": True}
                )
                response.raise_for_status()
                
                data = response.json()
                agents = {}
                
                for agent in data['agents']:
                    agents[agent['slug']] = {
                        'id': agent['id'],
                        'name': agent['name'],
                        'description': agent['description'],
                        'system_prompt': agent['system_prompt'],
                        'openai_model': agent['openai_model'],
                        'temperature': agent['temperature'],
                        'max_tokens': agent['max_tokens'],
                        'transfer_triggers': agent.get('transfer_triggers', [])
                    }
                
                self.agents_cache = agents
                logger.info(f"Loaded {len(agents)} agents from backend")
                return agents
                
        except httpx.ConnectError:
            logger.warning("Could not connect to backend API, using default agents")
            return self._get_default_agents()
        except Exception as e:
            logger.error(f"Error loading agents from API: {e}")
            return self._get_default_agents()
    
    def get_agent(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get a specific agent configuration"""
        return self.agents_cache.get(slug)
    
    def get_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get all loaded agents"""
        return self.agents_cache
    
    def _get_default_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get default hardcoded agents as fallback"""
        return {
            'misunderstanding_protector': {
                'name': 'Misunderstanding Protector',
                'description': 'Specialized in detecting and resolving misunderstandings',
                'system_prompt': '''You are the Misunderstanding Protector, focused on identifying and resolving misunderstandings between partners.
                
Your approach follows a 4-step card system:
1. Context Card: Understand the situation
2. Emotions Card: Identify feelings
3. Interpretations Card: Explore different viewpoints
4. Bridge Card: Build understanding

Transfer triggers: When emotions are too heated, suggest transfer to empathy_amplifier.''',
                'openai_model': 'gpt-4-turbo-preview',
                'temperature': 0.7,
                'max_tokens': 4000,
                'transfer_triggers': []
            },
            'empathy_amplifier': {
                'name': 'Empathy Amplifier',
                'description': 'Helps develop deeper emotional understanding',
                'system_prompt': '''You are the Empathy Amplifier, focused on helping partners understand emotions deeply.

Your role is to:
- Help recognize emotions
- Teach validation techniques
- Create safe space for vulnerability

Transfer triggers: When ready for solutions, transfer to solution_finder.''',
                'openai_model': 'gpt-4',
                'temperature': 0.7,
                'max_tokens': 4000,
                'transfer_triggers': []
            }
        }

# Global instance
agent_loader = AgentLoader()