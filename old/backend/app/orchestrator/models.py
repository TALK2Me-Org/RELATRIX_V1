"""
Simple models for the orchestrator
Just the essentials!
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class Agent(BaseModel):
    """Agent definition - only what we need"""
    id: UUID
    slug: str
    name: str
    description: str
    system_prompt: str
    openai_model: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    max_tokens: int = 2000
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class Message(BaseModel):
    """Simple message structure"""
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = datetime.now()
    agent_id: Optional[str] = None