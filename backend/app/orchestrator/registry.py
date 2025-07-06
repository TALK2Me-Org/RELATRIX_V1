"""
Agent Registry - Manages agent configurations loaded from database
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import asyncio
from uuid import UUID

logger = logging.getLogger(__name__)

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select, and_
    from app.database.connection import get_db
    from app.models.db_agent import AgentDB as AgentModel
    HAS_DATABASE = True
except ImportError:
    HAS_DATABASE = False
    logger.warning("Database modules not available, using default agents only")
    
from .models import Agent


class AgentRegistry:
    """Registry for managing agent configurations"""
    
    def __init__(self, cache_ttl: int = 300):  # 5 minutes cache
        self.agents: Dict[str, Agent] = {}
        self.cache_ttl = cache_ttl
        self.last_loaded: Optional[datetime] = None
        self._lock = asyncio.Lock()
        logger.info("Agent Registry initialized")
    
    async def load_agents(self, force_reload: bool = False) -> Dict[str, Agent]:
        """Load agents from database"""
        async with self._lock:
            # Check cache validity
            if not force_reload and self._is_cache_valid():
                return self.agents
            
            # If database not available, use defaults
            if not HAS_DATABASE:
                self._load_default_agents()
                return self.agents
            
            try:
                async for db in get_db():
                    # Query active agents
                    result = await db.execute(
                        select(AgentModel)
                        .where(AgentModel.is_active == True)
                        .order_by(AgentModel.display_order)
                    )
                    db_agents = result.scalars().all()
                    
                    # Convert to registry models
                    self.agents = {}
                    for db_agent in db_agents:
                        agent = Agent(
                            id=db_agent.id,
                            slug=db_agent.slug,
                            name=db_agent.name,
                            description=db_agent.description,
                            system_prompt=db_agent.system_prompt,
                            openai_model=db_agent.openai_model,
                            temperature=db_agent.temperature,
                            max_tokens=db_agent.max_tokens,
                            transfer_triggers=db_agent.transfer_triggers or [],
                            capabilities=db_agent.capabilities or [],
                            is_active=db_agent.is_active,
                            display_order=db_agent.display_order,
                            created_at=db_agent.created_at,
                            updated_at=db_agent.updated_at
                        )
                        self.agents[agent.slug] = agent
                    
                    self.last_loaded = datetime.now()
                    logger.info(f"Loaded {len(self.agents)} agents from database")
                    
                    # If no agents found, load defaults
                    if not self.agents:
                        logger.warning("No agents in database, loading defaults")
                        self._load_default_agents()
                    
                    return self.agents
                    
            except Exception as e:
                logger.error(f"Error loading agents from database: {e}")
                # Fallback to defaults if database fails
                if not self.agents:
                    self._load_default_agents()
                return self.agents
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self.last_loaded or not self.agents:
            return False
        
        age = datetime.now() - self.last_loaded
        return age.total_seconds() < self.cache_ttl
    
    def _load_default_agents(self):
        """Load default hardcoded agents as fallback"""
        defaults = [
            {
                "slug": "misunderstanding_protector",
                "name": "Misunderstanding Protector",
                "description": "Analyzes communication patterns and prevents misunderstandings",
                "system_prompt": self._get_misunderstanding_protector_prompt(),
                "transfer_triggers": [
                    "I need to express my emotions",
                    "I'm feeling overwhelmed",
                    "I need to vent",
                    "emotional dump",
                    "I'm upset about"
                ]
            },
            {
                "slug": "emotional_vomit_dumper",
                "name": "Emotional Vomit Dumper", 
                "description": "Safe space for emotional release and processing",
                "system_prompt": self._get_emotional_vomit_prompt(),
                "transfer_triggers": [
                    "I feel better now",
                    "I'm ready to talk about solutions",
                    "I want to work on this",
                    "what should I do",
                    "I need help with"
                ]
            },
            {
                "slug": "conflict_solver",
                "name": "Conflict Solver",
                "description": "Mediates and resolves relationship conflicts",
                "system_prompt": self._get_conflict_solver_prompt(),
                "transfer_triggers": [
                    "we want to improve our relationship",
                    "I want to work on us",
                    "relationship goals",
                    "make things better",
                    "strengthen our bond"
                ]
            },
            {
                "slug": "solution_finder",
                "name": "Solution Finder",
                "description": "Creates actionable plans for relationship improvement",
                "system_prompt": self._get_solution_finder_prompt(),
                "transfer_triggers": [
                    "I want to practice",
                    "I need to rehearse",
                    "I'm worried about saying",
                    "I don't know how to bring this up",
                    "practice conversation"
                ]
            },
            {
                "slug": "communication_simulator",
                "name": "Communication Simulator",
                "description": "Practice conversations in a safe environment",
                "system_prompt": self._get_communication_simulator_prompt(),
                "transfer_triggers": [
                    "I want to level up",
                    "relationship games",
                    "fun challenges",
                    "make it exciting",
                    "relationship activities"
                ]
            },
            {
                "slug": "relationship_upgrader",
                "name": "Relationship Upgrader",
                "description": "Gamified relationship enhancement and growth",
                "system_prompt": self._get_relationship_upgrader_prompt(),
                "transfer_triggers": [
                    "I think we should break up",
                    "I want to end this",
                    "I can't do this anymore",
                    "relationship is over",
                    "I'm done"
                ]
            },
            {
                "slug": "breakthrough_manager",
                "name": "Breakthrough Manager",
                "description": "Crisis support and major relationship decisions",
                "system_prompt": self._get_breakthrough_manager_prompt(),
                "transfer_triggers": []
            }
        ]
        
        for i, agent_data in enumerate(defaults):
            agent = Agent(
                id=UUID('00000000-0000-0000-0000-00000000000' + str(i+1)),  # Unique placeholder
                slug=agent_data["slug"],
                name=agent_data["name"],
                description=agent_data["description"],
                system_prompt=agent_data["system_prompt"],
                transfer_triggers=agent_data["transfer_triggers"],
                display_order=i,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.agents[agent.slug] = agent
    
    async def get_agent(self, slug: str) -> Optional[Agent]:
        """Get a specific agent by slug"""
        if not self.agents:
            await self.load_agents()
        return self.agents.get(slug)
    
    async def get_all_agents(self) -> List[Agent]:
        """Get all active agents"""
        if not self.agents:
            await self.load_agents()
        return list(self.agents.values())
    
    async def reload_agents(self) -> Dict[str, Agent]:
        """Force reload agents from database"""
        logger.info("Force reloading agents")
        return await self.load_agents(force_reload=True)
    
    # Agent system prompts
    def _get_misunderstanding_protector_prompt(self) -> str:
        return """You are the Misunderstanding Protector, a specialized AI agent focused on preventing and resolving communication misunderstandings in relationships.

Your primary role is to analyze communication patterns using the 4-card analysis method:

🔴 RED CARD - Problems/Issues
- Identify communication breakdowns
- Spot potential misunderstandings
- Highlight emotional triggers
- Point out defensive patterns

🟡 YELLOW CARD - Cautions/Risks
- Warning signs in communication
- Potential areas of concern
- Patterns that might escalate
- Things to be mindful of

🟢 GREEN CARD - Positive Aspects
- What's working well
- Strengths in communication
- Positive patterns to build on
- Good intentions to acknowledge

🔵 BLUE CARD - Recommendations/Actions
- Concrete next steps
- Communication techniques to try
- Ways to prevent future issues
- Specific tools and strategies

Always format your responses with these 4 cards and provide specific, actionable advice.

Transfer triggers: If the user needs emotional support, mentions being overwhelmed, or wants to "vent" - suggest transfer to emotional_vomit_dumper."""
    
    def _get_emotional_vomit_prompt(self) -> str:
        return """You are the Emotional Vomit Dumper, a safe space for emotional release and processing.

Your role is to provide unconditional support and allow users to express their emotions freely without judgment.

Key principles:
- Create a completely safe, non-judgmental space
- Allow emotional expression without trying to "fix" immediately
- Validate feelings and experiences
- Use empathetic language and active listening
- Don't offer solutions until the person is ready
- Maintain privacy - don't store sensitive emotional content

Remember: Sometimes people just need to be heard before they're ready for solutions.

Transfer triggers: When the user feels calmer, mentions being "ready to work on this," or asks for solutions - suggest transfer to solution_finder or conflict_solver."""
    
    def _get_conflict_solver_prompt(self) -> str:
        return """You are the Conflict Solver, a specialized mediator for relationship conflicts.

Your role is to:
- Mediate between partners fairly
- Help understand different perspectives
- Guide towards mutually beneficial solutions
- Assess if both partners are ready for resolution
- Facilitate productive conversations

Key techniques:
- Active listening and reflection
- Perspective-taking exercises
- Finding common ground
- De-escalation strategies
- Structured problem-solving

Always check: Are both partners ready and willing to work on this together?

Transfer triggers: If they want to "improve the relationship" or "work on us" - suggest transfer to relationship_upgrader."""
    
    def _get_solution_finder_prompt(self) -> str:
        return """You are the Solution Finder, focused on creating actionable plans for relationship improvement.

Your role is to:
- Create concrete, specific action plans
- Break down big problems into manageable steps
- Provide practical tools and techniques
- Track progress and adjust plans
- Ensure accountability

Always provide:
- Clear, specific next steps
- Realistic timelines
- Ways to measure progress
- Backup plans if things don't work

Transfer triggers: If they want to "practice" conversations or are worried about "how to say" something - suggest transfer to communication_simulator."""
    
    def _get_communication_simulator_prompt(self) -> str:
        return """You are the Communication Simulator, a practice environment for difficult conversations.

Your role is to:
- Role-play as the user's partner
- Provide realistic conversation practice
- Give constructive feedback
- Help build communication confidence
- Create various scenarios to practice

Key features:
- Adapt to the partner's communication style
- Provide both supportive and challenging scenarios
- Offer feedback on communication effectiveness
- Help refine message delivery
- Build confidence through practice

Transfer triggers: If they want "relationship games" or to "level up" their relationship - suggest transfer to relationship_upgrader."""
    
    def _get_relationship_upgrader_prompt(self) -> str:
        return """You are the Relationship Upgrader, focused on gamified relationship enhancement.

Your role is to:
- Create fun challenges and activities
- Gamify relationship improvement
- Design relationship "quests" and achievements
- Make growth exciting and engaging
- Celebrate progress and milestones

Key elements:
- Weekly relationship challenges
- Point systems and achievements
- Fun activities to do together
- Progress tracking and rewards
- Making improvement feel like a game

Transfer triggers: If they mention wanting to "break up" or "end the relationship" - suggest transfer to breakthrough_manager."""
    
    def _get_breakthrough_manager_prompt(self) -> str:
        return """You are the Breakthrough Manager, specialized in crisis support and major relationship decisions.

Your role is to:
- Provide crisis support and stability
- Help with major relationship decisions
- Support through breakups if necessary
- Facilitate healing and recovery
- Guide through major life transitions

Key principles:
- Non-judgmental support
- Safety and wellbeing first
- Respect for all decisions
- Comprehensive support through transitions
- Focus on healing and growth

This is a specialized role for critical moments in relationships."""