"""
Agent management API endpoints
Provides CRUD operations for RELATRIX agents
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from uuid import UUID
import logging
from datetime import datetime

from ..models.agent import (
    Agent, AgentCreate, AgentUpdate, AgentListResponse,
    AgentTestRequest, AgentTestResponse, OPENAI_MODELS
)
from ..services.agent_service import AgentService
from ..dependencies import get_agent_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/agents", tags=["agents"])

@router.get("/", response_model=AgentListResponse)
async def list_agents(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    List all agents with optional filtering
    """
    try:
        agents = await agent_service.list_agents(is_active=is_active)
        return AgentListResponse(
            agents=agents,
            total=len(agents)
        )
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list agents")

@router.get("/{slug}", response_model=Agent)
async def get_agent(
    slug: str,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Get a specific agent by slug
    """
    try:
        agent = await agent_service.get_agent_by_slug(slug)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{slug}' not found")
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {slug}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent")

@router.post("/", response_model=Agent)
async def create_agent(
    agent_data: AgentCreate,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Create a new agent
    """
    try:
        # Check if slug already exists
        existing = await agent_service.get_agent_by_slug(agent_data.slug)
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Agent with slug '{agent_data.slug}' already exists"
            )
        
        agent = await agent_service.create_agent(agent_data)
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to create agent")

@router.put("/{slug}", response_model=Agent)
async def update_agent(
    slug: str,
    agent_update: AgentUpdate,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Update an existing agent
    """
    try:
        # Check if agent exists
        existing = await agent_service.get_agent_by_slug(slug)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Agent '{slug}' not found")
        
        # Create version history before update
        await agent_service.create_agent_version(existing)
        
        # Update agent
        agent = await agent_service.update_agent(slug, agent_update)
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent {slug}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update agent")

@router.delete("/{slug}")
async def delete_agent(
    slug: str,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Delete an agent (soft delete - sets is_active to false)
    """
    try:
        existing = await agent_service.get_agent_by_slug(slug)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Agent '{slug}' not found")
        
        await agent_service.delete_agent(slug)
        return {"message": f"Agent '{slug}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent {slug}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete agent")

@router.post("/{slug}/test", response_model=AgentTestResponse)
async def test_agent(
    slug: str,
    test_request: AgentTestRequest,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Test an agent with a sample message
    """
    try:
        agent = await agent_service.get_agent_by_slug(slug)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{slug}' not found")
        
        # Test the agent
        result = await agent_service.test_agent(agent, test_request)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing agent {slug}: {e}")
        raise HTTPException(status_code=500, detail="Failed to test agent")

@router.get("/{slug}/versions")
async def get_agent_versions(
    slug: str,
    limit: int = Query(10, ge=1, le=100),
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Get version history for an agent
    """
    try:
        agent = await agent_service.get_agent_by_slug(slug)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{slug}' not found")
        
        versions = await agent_service.get_agent_versions(agent.id, limit=limit)
        return {"versions": versions, "total": len(versions)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent versions for {slug}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent versions")

@router.post("/{slug}/restore/{version_id}")
async def restore_agent_version(
    slug: str,
    version_id: UUID,
    agent_service: AgentService = Depends(get_agent_service)
):
    """
    Restore an agent to a previous version
    """
    try:
        agent = await agent_service.get_agent_by_slug(slug)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{slug}' not found")
        
        restored_agent = await agent_service.restore_agent_version(agent.id, version_id)
        return restored_agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring agent {slug} to version {version_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to restore agent version")

@router.get("/openai/models")
async def get_openai_models():
    """
    Get list of available OpenAI models with their specifications
    """
    return {
        "models": OPENAI_MODELS,
        "total": len(OPENAI_MODELS)
    }