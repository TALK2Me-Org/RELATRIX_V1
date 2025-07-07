"""Test endpoint for Memory Modes with mock user"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.orchestrator.orchestrator import orchestrator
from app.orchestrator.memory_modes import MemoryMode

router = APIRouter()


class TestChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = "test-user-123"  # Mock user for testing


@router.post("/test-chat-with-user")
async def test_chat_with_user(request: TestChatRequest):
    """Test chat endpoint that includes user_id for memory operations"""
    
    # Create or get session
    session = await orchestrator.create_session(
        session_id=request.session_id,
        user_id=request.user_id  # This enables memory operations
    )
    
    # Force memory refresh for testing
    if request.user_id:
        # This will trigger memory operations
        should_refresh = await orchestrator.memory.should_refresh_memory(
            session, 
            request.message
        )
        
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "memory_mode": orchestrator.memory.get_session_config(session.session_id).mode,
            "should_refresh_memory": should_refresh,
            "message": "Use the regular /api/chat/stream endpoint with this session_id to chat"
        }
    
    return {"error": "No user_id provided"}


@router.get("/test-memory-operations/{session_id}")
async def test_memory_operations(session_id: str):
    """Test memory operations for a session"""
    
    # Get session
    session = orchestrator.active_sessions.get(session_id)
    if not session:
        session = await orchestrator.memory.load_session_state(session_id)
        if not session:
            raise HTTPException(404, "Session not found")
    
    config = orchestrator.memory.get_session_config(session_id)
    metrics = orchestrator.memory.get_session_metrics(session_id)
    
    # Test operations
    results = {
        "session_id": session_id,
        "user_id": session.user_id,
        "has_user": session.user_id is not None,
        "memory_mode": config.mode.value,
        "config": {
            "cache_ttl": config.cache_ttl,
            "save_on_session_end": config.save_on_session_end,
            "log_all_operations": config.log_all_operations
        }
    }
    
    if metrics:
        results["metrics"] = {
            "retrieval_count": metrics.retrieval_count,
            "cache_hits": metrics.cache_hits,
            "cache_misses": metrics.cache_misses,
            "cache_hit_rate": metrics.cache_hit_rate
        }
    
    # Check cache
    cache_key = f"context:{session_id}"
    cached = await orchestrator.memory.redis_client.get(cache_key)
    results["has_cached_context"] = cached is not None
    
    return results


@router.post("/test-memory-refresh/{session_id}")
async def test_memory_refresh(session_id: str):
    """Force memory refresh for testing"""
    
    session = orchestrator.active_sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found in active sessions")
    
    if not session.user_id:
        return {"error": "Session has no user_id - memory operations disabled"}
    
    # Force refresh
    context = await orchestrator.memory.retrieve_user_context(session, force_refresh=True)
    
    # Get metrics
    metrics = orchestrator.memory.get_session_metrics(session_id)
    
    return {
        "session_id": session_id,
        "user_id": session.user_id,
        "context_retrieved": context is not None,
        "context_size": len(str(context)) if context else 0,
        "metrics": {
            "retrieval_count": metrics.retrieval_count if metrics else 0,
            "cache_hits": metrics.cache_hits if metrics else 0,
            "cache_misses": metrics.cache_misses if metrics else 0
        }
    }


@router.post("/simulate-memory-modes")
async def simulate_memory_modes():
    """Simulate different memory modes to see how they work"""
    
    results = {}
    test_user = "test-user-sim"
    
    # Test each mode
    for mode_name in ["cache_first", "always_fresh", "smart_triggers", "test_mode"]:
        session_id = f"sim-{mode_name}"
        
        # Create session with user
        session = await orchestrator.create_session(
            session_id=session_id,
            user_id=test_user
        )
        
        # Set memory mode
        from app.orchestrator.memory_modes import DEFAULT_CONFIGS
        config = DEFAULT_CONFIGS.get(mode_name.replace("_", ""), DEFAULT_CONFIGS["balanced"])
        orchestrator.memory.set_session_mode(session_id, config)
        
        # Simulate some checks
        checks = []
        
        # Check 1: First message
        should_refresh = await orchestrator.memory.should_refresh_memory(session, "Hello")
        checks.append({"message": 1, "should_refresh": should_refresh})
        
        # Add some messages to history
        from app.orchestrator.models import Message
        for i in range(5):
            session.conversation_history.append(
                Message(role="user", content=f"Test message {i}")
            )
        
        # Check 2: After 5 messages
        should_refresh = await orchestrator.memory.should_refresh_memory(session, "Message 6")
        checks.append({"message": 6, "should_refresh": should_refresh})
        
        # Check 3: Emotion trigger
        should_refresh = await orchestrator.memory.should_refresh_memory(session, "Jestem wściekła!")
        checks.append({"emotion_trigger": True, "should_refresh": should_refresh})
        
        results[mode_name] = {
            "session_id": session_id,
            "checks": checks,
            "config": {
                "mode": config.mode.value,
                "cache_ttl": config.cache_ttl,
                "triggers_enabled": {
                    "message_count": config.triggers.message_count.enabled,
                    "emotion_spike": config.triggers.emotion_spike.enabled
                }
            }
        }
    
    return results