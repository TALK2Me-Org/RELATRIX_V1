"""
Agent CRUD endpoints
Simple REST API for managing agent prompts
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from typing import List, Optional, Any
from database import get_db, Agent, seed_agents
from auth import require_user
import logging

logger = logging.getLogger(__name__)

# Router
agents_router = APIRouter()

# Models
class AgentBase(BaseModel):
    slug: str
    name: str
    system_prompt: str
    is_active: bool = True


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    is_active: Optional[bool] = None


class AgentResponse(AgentBase):
    id: str
    
    @field_validator('id', mode='before')
    def convert_uuid_to_str(cls, v):
        """Convert UUID to string"""
        if v is not None:
            return str(v)
        return v
    
    class Config:
        from_attributes = True


# Endpoints
@agents_router.get("/", response_model=List[AgentResponse])
async def get_agents(db: Session = Depends(get_db)):
    """Get all active agents"""
    logger.info("[AGENTS] GET /api/agents/ called")
    try:
        agents = db.query(Agent).filter(Agent.is_active == True).all()
        logger.info(f"[AGENTS] Found {len(agents)} active agents")
        for agent in agents:
            logger.debug(f"[AGENTS] Agent: {agent.slug} (ID: {agent.id})")
        return agents
    except Exception as e:
        logger.error(f"[AGENTS] Error fetching agents: {e}")
        raise


@agents_router.get("/{slug}", response_model=AgentResponse)
async def get_agent(slug: str, db: Session = Depends(get_db)):
    """Get agent by slug"""
    agent = db.query(Agent).filter(Agent.slug == slug).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@agents_router.post("/", response_model=AgentResponse)
async def create_agent(
    agent: AgentCreate,
    user: dict = Depends(require_user),
    db: Session = Depends(get_db)
):
    """Create new agent (requires auth)"""
    # Check if slug exists
    existing = db.query(Agent).filter(Agent.slug == agent.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Agent slug already exists")
    
    # Create agent
    db_agent = Agent(**agent.dict())
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    
    logger.info(f"Agent created: {agent.slug} by user {user['email']}")
    return db_agent


@agents_router.put("/{slug}", response_model=AgentResponse)
async def update_agent(
    slug: str,
    update: AgentUpdate,
    user: dict = Depends(require_user),
    db: Session = Depends(get_db)
):
    """Update agent (requires auth)"""
    agent = db.query(Agent).filter(Agent.slug == slug).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Update fields
    for field, value in update.dict(exclude_unset=True).items():
        setattr(agent, field, value)
    
    db.commit()
    db.refresh(agent)
    
    logger.info(f"Agent updated: {slug} by user {user['email']}")
    return agent


@agents_router.post("/seed")
async def seed_default_agents(db: Session = Depends(get_db)):
    """Seed database with default agents"""
    try:
        seed_agents()
        return {"message": "Default agents seeded successfully"}
    except Exception as e:
        logger.error(f"Seed error: {e}")
        raise HTTPException(status_code=500, detail=str(e))