"""
Agent models for RELATRIX
Pydantic models for agent configuration and management
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID

class AgentBase(BaseModel):
    """Base agent model with common fields"""
    slug: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    system_prompt: str = Field(..., min_length=1)
    openai_model: str = Field(default="gpt-4-turbo-preview", max_length=50)
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4000, gt=0, le=8000)
    transfer_triggers: List[Dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True
    display_order: int = Field(default=0)

    @validator('openai_model')
    def validate_model(cls, v):
        """Validate OpenAI model name"""
        valid_models = [
            'gpt-4-turbo-preview',
            'gpt-4-turbo',
            'gpt-4',
            'gpt-4-32k',
            'gpt-3.5-turbo',
            'gpt-3.5-turbo-16k'
        ]
        if v not in valid_models:
            raise ValueError(f"Model must be one of: {', '.join(valid_models)}")
        return v

class AgentCreate(AgentBase):
    """Model for creating a new agent"""
    pass

class AgentUpdate(BaseModel):
    """Model for updating an agent - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    system_prompt: Optional[str] = Field(None, min_length=1)
    openai_model: Optional[str] = Field(None, max_length=50)
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, gt=0, le=8000)
    transfer_triggers: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None

class Agent(AgentBase):
    """Complete agent model with database fields"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AgentVersion(BaseModel):
    """Model for agent version history"""
    id: UUID
    agent_id: UUID
    version: int
    system_prompt: str
    openai_model: Optional[str]
    temperature: Optional[float]
    max_tokens: Optional[int]
    changed_by: Optional[UUID]
    change_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class AgentTestRequest(BaseModel):
    """Request model for testing an agent"""
    message: str = Field(..., min_length=1)
    session_context: Optional[Dict[str, Any]] = None
    test_model: Optional[str] = None
    test_temperature: Optional[float] = None

class AgentTestResponse(BaseModel):
    """Response model for agent testing"""
    response: str
    model_used: str
    tokens_used: int
    cost_estimate: float
    processing_time: float

class AgentListResponse(BaseModel):
    """Response model for agent list"""
    agents: List[Agent]
    total: int

class TransferTrigger(BaseModel):
    """Model for agent transfer trigger"""
    target_agent: str
    keywords: List[str]
    conditions: Optional[Dict[str, Any]] = None
    priority: int = Field(default=0)

class OpenAIModel(BaseModel):
    """OpenAI model information"""
    id: str
    name: str
    context_window: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    supports_functions: bool = True
    supports_vision: bool = False

# Available OpenAI models with pricing (as of 2024)
OPENAI_MODELS = [
    OpenAIModel(
        id="gpt-4-turbo-preview",
        name="GPT-4 Turbo Preview",
        context_window=128000,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03
    ),
    OpenAIModel(
        id="gpt-4",
        name="GPT-4",
        context_window=8192,
        cost_per_1k_input=0.03,
        cost_per_1k_output=0.06
    ),
    OpenAIModel(
        id="gpt-4-32k",
        name="GPT-4 32K",
        context_window=32768,
        cost_per_1k_input=0.06,
        cost_per_1k_output=0.12
    ),
    OpenAIModel(
        id="gpt-3.5-turbo",
        name="GPT-3.5 Turbo",
        context_window=4096,
        cost_per_1k_input=0.0005,
        cost_per_1k_output=0.0015
    ),
    OpenAIModel(
        id="gpt-3.5-turbo-16k",
        name="GPT-3.5 Turbo 16K",
        context_window=16384,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.004
    ),
]