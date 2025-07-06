"""
SQLAlchemy Agent model for database
"""

try:
    from sqlalchemy import Column, String, Text, Float, Integer, Boolean, JSON, DateTime
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.sql import func
    import uuid
    from app.database.connection import Base
    
    if Base is None:
        raise ImportError("Database not configured")
    
    class AgentDB(Base):
        """Agent database model"""
        __tablename__ = "agents"
        
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        slug = Column(String(50), unique=True, nullable=False, index=True)
        name = Column(String(100), nullable=False)
        description = Column(Text)
        system_prompt = Column(Text, nullable=False)
        openai_model = Column(String(50), default="gpt-4-turbo-preview")
        temperature = Column(Float, default=0.7)
        max_tokens = Column(Integer, default=4000)
        transfer_triggers = Column(JSON, default=list)
        capabilities = Column(JSON, default=list)
        is_active = Column(Boolean, default=True)
        display_order = Column(Integer, default=0)
        created_at = Column(DateTime(timezone=True), server_default=func.now())
        updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
        
except ImportError:
    # Dummy class when database is not available
    class AgentDB:
        pass