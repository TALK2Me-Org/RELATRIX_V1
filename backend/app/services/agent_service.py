"""
Agent Service Layer
Business logic for agent management
"""

from typing import List, Optional
from uuid import UUID
import logging
import time
import openai
from datetime import datetime
from supabase import create_client, Client

from ..models.agent import (
    Agent, AgentCreate, AgentUpdate, AgentVersion,
    AgentTestRequest, AgentTestResponse
)
from ..config import settings

logger = logging.getLogger(__name__)

class AgentService:
    """Service for managing agents and their interactions"""
    
    def __init__(self):
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key
        )
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
    
    async def list_agents(self, is_active: Optional[bool] = None) -> List[Agent]:
        """List all agents with optional filtering"""
        try:
            query = self.supabase.table('agents').select('*')
            
            if is_active is not None:
                query = query.eq('is_active', is_active)
            
            query = query.order('display_order', desc=False)
            response = query.execute()
            
            return [Agent(**agent) for agent in response.data]
        except Exception as e:
            logger.error(f"Error listing agents: {e}")
            raise
    
    async def get_agent_by_slug(self, slug: str) -> Optional[Agent]:
        """Get a specific agent by slug"""
        try:
            response = self.supabase.table('agents').select('*').eq('slug', slug).single().execute()
            if response.data:
                return Agent(**response.data)
            return None
        except Exception as e:
            if "No rows found" in str(e):
                return None
            logger.error(f"Error getting agent {slug}: {e}")
            raise
    
    async def create_agent(self, agent_data: AgentCreate) -> Agent:
        """Create a new agent"""
        try:
            data = agent_data.model_dump()
            response = self.supabase.table('agents').insert(data).execute()
            return Agent(**response.data[0])
        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            raise
    
    async def update_agent(self, slug: str, agent_update: AgentUpdate) -> Agent:
        """Update an existing agent"""
        try:
            # Only include non-None values
            update_data = {k: v for k, v in agent_update.model_dump().items() if v is not None}
            
            response = self.supabase.table('agents').update(update_data).eq('slug', slug).execute()
            return Agent(**response.data[0])
        except Exception as e:
            logger.error(f"Error updating agent {slug}: {e}")
            raise
    
    async def delete_agent(self, slug: str) -> bool:
        """Soft delete an agent by setting is_active to false"""
        try:
            self.supabase.table('agents').update({'is_active': False}).eq('slug', slug).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting agent {slug}: {e}")
            raise
    
    async def test_agent(self, agent: Agent, test_request: AgentTestRequest) -> AgentTestResponse:
        """Test an agent with a sample message"""
        try:
            start_time = time.time()
            
            # Use test parameters if provided, otherwise use agent defaults
            model = test_request.test_model or agent.openai_model
            temperature = test_request.test_temperature or agent.temperature
            
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": agent.system_prompt},
                    {"role": "user", "content": test_request.message}
                ],
                temperature=temperature,
                max_tokens=agent.max_tokens
            )
            
            processing_time = time.time() - start_time
            
            # Calculate cost estimate
            tokens_used = response.usage.total_tokens
            cost_estimate = self._calculate_cost(model, tokens_used)
            
            return AgentTestResponse(
                response=response.choices[0].message.content,
                model_used=model,
                tokens_used=tokens_used,
                cost_estimate=cost_estimate,
                processing_time=processing_time
            )
        except Exception as e:
            logger.error(f"Error testing agent: {e}")
            raise
    
    async def create_agent_version(self, agent: Agent) -> AgentVersion:
        """Create a version snapshot of an agent before updating"""
        try:
            # Get the latest version number
            versions = await self.get_agent_versions(agent.id, limit=1)
            next_version = 1 if not versions else versions[0].version + 1
            
            version_data = {
                'agent_id': str(agent.id),
                'version': next_version,
                'system_prompt': agent.system_prompt,
                'openai_model': agent.openai_model,
                'temperature': agent.temperature,
                'max_tokens': agent.max_tokens
            }
            
            response = self.supabase.table('agent_versions').insert(version_data).execute()
            return AgentVersion(**response.data[0])
        except Exception as e:
            logger.error(f"Error creating agent version: {e}")
            raise
    
    async def get_agent_versions(self, agent_id: UUID, limit: int = 10) -> List[AgentVersion]:
        """Get version history for an agent"""
        try:
            response = (self.supabase.table('agent_versions')
                       .select('*')
                       .eq('agent_id', str(agent_id))
                       .order('version', desc=True)
                       .limit(limit)
                       .execute())
            
            return [AgentVersion(**version) for version in response.data]
        except Exception as e:
            logger.error(f"Error getting agent versions: {e}")
            raise
    
    async def restore_agent_version(self, agent_id: UUID, version_id: UUID) -> Agent:
        """Restore an agent to a previous version"""
        try:
            # Get the version
            version_response = (self.supabase.table('agent_versions')
                              .select('*')
                              .eq('id', str(version_id))
                              .single()
                              .execute())
            
            if not version_response.data:
                raise ValueError("Version not found")
            
            version = version_response.data
            
            # Update the agent with version data
            update_data = {
                'system_prompt': version['system_prompt'],
                'openai_model': version['openai_model'],
                'temperature': version['temperature'],
                'max_tokens': version['max_tokens']
            }
            
            response = (self.supabase.table('agents')
                       .update(update_data)
                       .eq('id', str(agent_id))
                       .execute())
            
            return Agent(**response.data[0])
        except Exception as e:
            logger.error(f"Error restoring agent version: {e}")
            raise
    
    def _calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate estimated cost based on model and tokens"""
        # Simplified cost calculation - adjust based on actual OpenAI pricing
        cost_per_1k = {
            'gpt-4-turbo-preview': 0.02,  # $0.01 input + $0.03 output averaged
            'gpt-4': 0.045,  # $0.03 input + $0.06 output averaged
            'gpt-4-32k': 0.09,  # $0.06 input + $0.12 output averaged
            'gpt-3.5-turbo': 0.001,  # $0.0005 input + $0.0015 output averaged
            'gpt-3.5-turbo-16k': 0.0035  # $0.003 input + $0.004 output averaged
        }
        
        rate = cost_per_1k.get(model, 0.02)
        return (tokens / 1000) * rate