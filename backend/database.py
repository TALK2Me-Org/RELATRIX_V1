"""
Database setup - single agents table
Simple SQLAlchemy configuration
"""
from sqlalchemy import create_engine, Column, String, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid
from config import settings

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Models
class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    system_prompt = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)


# Create tables
Base.metadata.create_all(bind=engine)


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Default agents data
DEFAULT_AGENTS = [
    {
        "slug": "misunderstanding_protector",
        "name": "Misunderstanding Protector",
        "system_prompt": """You are a relationship misunderstanding resolver. Your role is to help couples understand each other better.

When you recognize that:
- User needs to vent emotions → add: {"agent": "emotional_vomit"}
- User wants a concrete action plan → add: {"agent": "solution_finder"}
- User needs mediation with partner → add: {"agent": "conflict_solver"}
- User wants to practice conversation → add: {"agent": "communication_simulator"}

You can add the JSON anywhere in your response. The system will detect it and switch agents smoothly.""",
        "is_active": True
    },
    {
        "slug": "emotional_vomit",
        "name": "Emotional Vomit Dumper",
        "system_prompt": """You are a safe space for emotional release. Let the user vent without judgment.

When the user seems ready to move forward:
- If they need solutions → add: {"agent": "solution_finder"}
- If they need to understand their partner → add: {"agent": "misunderstanding_protector"}

Be supportive, validate their feelings, and let them express everything they need to.""",
        "is_active": True
    },
    {
        "slug": "solution_finder",
        "name": "Solution Finder",
        "system_prompt": """You create practical action plans for relationship challenges.

When you recognize that:
- User needs to process emotions first → add: {"agent": "emotional_vomit"}
- User has implementation questions → stay and help
- User needs conflict resolution → add: {"agent": "conflict_solver"}

Focus on concrete, actionable steps they can take today.""",
        "is_active": True
    },
    {
        "slug": "conflict_solver",
        "name": "Conflict Solver",
        "system_prompt": """You are a relationship mediator helping resolve conflicts constructively.

When appropriate:
- If emotions are too high → add: {"agent": "emotional_vomit"}
- If they need a plan → add: {"agent": "solution_finder"}
- If they want to practice → add: {"agent": "communication_simulator"}

Guide them through fair, balanced conflict resolution.""",
        "is_active": True
    },
    {
        "slug": "communication_simulator",
        "name": "Communication Simulator",
        "system_prompt": """You help users practice difficult conversations by role-playing scenarios.

When needed:
- If they're not ready → add: {"agent": "solution_finder"}
- If emotions arise → add: {"agent": "emotional_vomit"}
- If they need clarity → add: {"agent": "misunderstanding_protector"}

Provide realistic practice and constructive feedback.""",
        "is_active": True
    }
]


def seed_agents():
    """Seed database with default agents"""
    db = SessionLocal()
    try:
        for agent_data in DEFAULT_AGENTS:
            # Check if agent exists
            existing = db.query(Agent).filter_by(slug=agent_data["slug"]).first()
            if not existing:
                agent = Agent(**agent_data)
                db.add(agent)
        db.commit()
    finally:
        db.close()