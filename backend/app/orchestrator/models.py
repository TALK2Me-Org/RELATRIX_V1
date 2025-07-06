"""
Data models for the Multi-Agent Orchestrator
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


class TransferReason(str, Enum):
    """Reasons for agent transfers"""
    TRIGGER_MATCH = "trigger_match"
    USER_REQUEST = "user_request"
    AGENT_SUGGESTION = "agent_suggestion"
    ERROR_FALLBACK = "error_fallback"
    SESSION_START = "session_start"


class Agent(BaseModel):
    """Agent configuration model"""
    id: UUID
    slug: str
    name: str
    description: str
    system_prompt: str
    openai_model: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    max_tokens: int = 4000
    transfer_triggers: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    is_active: bool = True
    display_order: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }


class Message(BaseModel):
    """Chat message model"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TransferEvent(BaseModel):
    """Agent transfer event"""
    timestamp: datetime = Field(default_factory=datetime.now)
    from_agent: str
    to_agent: str
    reason: TransferReason
    trigger: Optional[str] = None
    user_message: str
    context: Dict[str, Any] = Field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


class SessionState(BaseModel):
    """Orchestrator session state"""
    session_id: str
    user_id: Optional[str] = None
    current_agent: str
    conversation_history: List[Message] = Field(default_factory=list)
    transfer_history: List[TransferEvent] = Field(default_factory=list)
    memory_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def add_message(self, message: Message):
        """Add a message to conversation history"""
        self.conversation_history.append(message)
        self.updated_at = datetime.now()

    def add_transfer(self, transfer: TransferEvent):
        """Add a transfer event"""
        self.transfer_history.append(transfer)
        self.current_agent = transfer.to_agent
        self.updated_at = datetime.now()


class StreamChunk(BaseModel):
    """Streaming response chunk"""
    type: str  # 'content', 'transfer', 'metadata', 'error'
    content: Optional[str] = None
    agent_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class OrchestratorStatus(BaseModel):
    """Orchestrator health and status"""
    healthy: bool
    version: str = "1.0.0"
    agents_loaded: int
    active_sessions: int
    total_transfers: int
    uptime_seconds: float
    last_reload: Optional[datetime] = None
    errors: List[str] = Field(default_factory=list)