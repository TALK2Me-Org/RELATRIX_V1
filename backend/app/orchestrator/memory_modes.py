"""
Memory Modes for RELATRIX - defines how memory retrieval and caching works
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class MemoryMode(str, Enum):
    """
    Available memory operation modes
    """
    CACHE_FIRST = "cache_first"        # Minimal cost - 1 retrieval per session
    ALWAYS_FRESH = "always_fresh"      # Maximum accuracy - retrieval per message
    SMART_TRIGGERS = "smart_triggers"  # Balanced - retrieval on triggers
    TEST_MODE = "test_mode"           # Testing - logs everything


class TriggerType(str, Enum):
    """Types of smart triggers"""
    MESSAGE_COUNT = "message_count"
    TIME_ELAPSED = "time_elapsed"
    AGENT_TRANSFER = "agent_transfer"
    EMOTION_SPIKE = "emotion_spike"
    TOPIC_CHANGE = "topic_change"
    IMPORTANT_INFO = "important_info"


class TriggerConfig(BaseModel):
    """Configuration for a single trigger"""
    enabled: bool = True
    # Type-specific settings
    threshold: Optional[int] = None        # For message_count
    minutes: Optional[int] = None          # For time_elapsed
    keywords: Optional[List[str]] = None   # For emotion/topic triggers
    description: str = ""


class SmartTriggers(BaseModel):
    """Configuration for all smart triggers"""
    message_count: TriggerConfig = Field(
        default=TriggerConfig(
            enabled=True,
            threshold=5,
            description="Refresh context every N messages"
        )
    )
    time_elapsed: TriggerConfig = Field(
        default=TriggerConfig(
            enabled=True,
            minutes=15,
            description="Refresh if session is long"
        )
    )
    agent_transfer: TriggerConfig = Field(
        default=TriggerConfig(
            enabled=True,
            description="Always refresh on agent change"
        )
    )
    emotion_spike: TriggerConfig = Field(
        default=TriggerConfig(
            enabled=True,
            keywords=["wściekła", "płaczę", "kryzys", "nie mogę", "panika"],
            description="Refresh on emotional intensity"
        )
    )
    topic_change: TriggerConfig = Field(
        default=TriggerConfig(
            enabled=False,
            keywords=["inna sprawa", "zmieniam temat", "a propos", "przy okazji"],
            description="Refresh when topic shifts"
        )
    )
    important_info: TriggerConfig = Field(
        default=TriggerConfig(
            enabled=True,
            keywords=["zdecydowałam", "postanowiłam", "powiem mu", "muszę powiedzieć"],
            description="Save immediately on decisions"
        )
    )


class MemoryConfig(BaseModel):
    """
    Complete memory configuration for a session or globally
    """
    mode: MemoryMode = MemoryMode.CACHE_FIRST
    cache_ttl: int = Field(default=1800, ge=300, le=7200)  # 5 min to 2 hours
    triggers: SmartTriggers = Field(default_factory=SmartTriggers)
    
    # Cost optimization settings
    max_context_tokens: int = Field(default=2000, ge=500, le=4000)
    compress_after_tokens: int = Field(default=1000, ge=500, le=3000)
    max_memories_per_retrieval: int = Field(default=10, ge=5, le=50)
    
    # Behavior flags
    save_on_session_end: bool = True
    save_on_important_info: bool = True
    log_all_operations: bool = False  # For test mode
    
    class Config:
        json_encoders = {
            MemoryMode: lambda v: v.value
        }


class MemoryMetrics(BaseModel):
    """Metrics for monitoring memory operations"""
    session_id: str
    mode: MemoryMode
    retrieval_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_tokens_retrieved: int = 0
    total_cost: float = 0.0
    avg_retrieval_time_ms: float = 0.0
    triggers_fired: Dict[str, int] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=datetime.now)
    
    def add_retrieval(self, tokens: int, time_ms: float, cost: float = 0.01):
        """Record a retrieval operation"""
        self.retrieval_count += 1
        self.total_tokens_retrieved += tokens
        self.total_cost += cost
        # Update average time
        if self.retrieval_count == 1:
            self.avg_retrieval_time_ms = time_ms
        else:
            self.avg_retrieval_time_ms = (
                (self.avg_retrieval_time_ms * (self.retrieval_count - 1) + time_ms) 
                / self.retrieval_count
            )
    
    def add_cache_hit(self):
        """Record a cache hit"""
        self.cache_hits += 1
    
    def add_cache_miss(self):
        """Record a cache miss"""
        self.cache_misses += 1
    
    def add_trigger(self, trigger_type: str):
        """Record a trigger firing"""
        if trigger_type not in self.triggers_fired:
            self.triggers_fired[trigger_type] = 0
        self.triggers_fired[trigger_type] += 1
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0
    
    @property
    def avg_cost_per_retrieval(self) -> float:
        """Calculate average cost per retrieval"""
        return self.total_cost / self.retrieval_count if self.retrieval_count > 0 else 0.0


# Default configurations for different use cases
DEFAULT_CONFIGS = {
    "conservative": MemoryConfig(
        mode=MemoryMode.CACHE_FIRST,
        cache_ttl=2700,  # 45 minutes
        triggers=SmartTriggers(
            message_count=TriggerConfig(enabled=False),
            time_elapsed=TriggerConfig(enabled=True, minutes=30),
            agent_transfer=TriggerConfig(enabled=True),
            emotion_spike=TriggerConfig(enabled=False),
            topic_change=TriggerConfig(enabled=False),
            important_info=TriggerConfig(enabled=True)
        )
    ),
    "balanced": MemoryConfig(
        mode=MemoryMode.SMART_TRIGGERS,
        cache_ttl=1800,  # 30 minutes
        triggers=SmartTriggers()  # All defaults
    ),
    "premium": MemoryConfig(
        mode=MemoryMode.ALWAYS_FRESH,
        cache_ttl=3600,  # 60 minutes (for fallback)
        save_on_session_end=False,  # Save continuously
        save_on_important_info=False  # Save everything
    ),
    "test": MemoryConfig(
        mode=MemoryMode.TEST_MODE,
        cache_ttl=1800,
        log_all_operations=True,
        triggers=SmartTriggers()  # Test all triggers
    )
}