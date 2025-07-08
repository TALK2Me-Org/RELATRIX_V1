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
import logging

logger = logging.getLogger(__name__)

# Database setup
logger.info(f"[DB] Connecting to database: {settings.database_url[:30]}...")
try:
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    logger.info("[DB] Database engine created successfully")
except Exception as e:
    logger.error(f"[DB] Failed to create database engine: {e}")
    raise


# Models
class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    system_prompt = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)


# Create tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("[DB] Tables created/verified successfully")
except Exception as e:
    logger.error(f"[DB] Failed to create tables: {e}")
    raise


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
    logger.info("[DB] Starting agent seeding...")
    db = SessionLocal()
    try:
        count = 0
        for agent_data in DEFAULT_AGENTS:
            # Check if agent exists
            existing = db.query(Agent).filter_by(slug=agent_data["slug"]).first()
            if not existing:
                agent = Agent(**agent_data)
                db.add(agent)
                count += 1
                logger.info(f"[DB] Added agent: {agent_data['slug']}")
            else:
                logger.debug(f"[DB] Agent already exists: {agent_data['slug']}")
        db.commit()
        logger.info(f"[DB] Seeding complete. Added {count} new agents")
        
        # Verify agents in database
        total_agents = db.query(Agent).count()
        logger.info(f"[DB] Total agents in database: {total_agents}")
    except Exception as e:
        logger.error(f"[DB] Failed to seed agents: {e}")
        db.rollback()
        raise
    finally:
        db.close()