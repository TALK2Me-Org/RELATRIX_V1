"""
Memory Mode Management API endpoints
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.orchestrator.memory_modes import MemoryMode, MemoryConfig, DEFAULT_CONFIGS
from app.orchestrator.orchestrator import orchestrator
from app.core.security import get_current_user

router = APIRouter()


class SetMemoryModeRequest(BaseModel):
    """Request to set memory mode"""
    mode: MemoryMode
    session_id: Optional[str] = None
    use_preset: Optional[str] = None  # "conservative", "balanced", "premium", "test"
    custom_config: Optional[MemoryConfig] = None


class GetMemoryMetricsResponse(BaseModel):
    """Response with memory metrics"""
    session_id: str
    mode: str
    retrieval_count: int
    cache_hits: int
    cache_misses: int
    cache_hit_rate: float
    total_tokens_retrieved: int
    total_cost: float
    avg_cost_per_retrieval: float
    avg_retrieval_time_ms: float
    triggers_fired: Dict[str, int]


@router.post("/mode")
async def set_memory_mode(
    request: SetMemoryModeRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Set memory mode globally or for a specific session"""
    
    # Get config - either preset or custom
    if request.use_preset:
        if request.use_preset not in DEFAULT_CONFIGS:
            raise HTTPException(400, f"Unknown preset: {request.use_preset}")
        config = DEFAULT_CONFIGS[request.use_preset]
    elif request.custom_config:
        config = request.custom_config
    else:
        # Just change mode, keep other settings
        if request.session_id:
            current_config = orchestrator.memory.get_session_config(request.session_id)
        else:
            current_config = orchestrator.memory.global_config
        
        config = current_config.copy(update={"mode": request.mode})
    
    # Apply to session or globally
    if request.session_id:
        orchestrator.memory.set_session_mode(request.session_id, config)
        return {"status": "success", "message": f"Session {request.session_id} mode set to {config.mode}"}
    else:
        orchestrator.memory.set_global_mode(config)
        return {"status": "success", "message": f"Global mode set to {config.mode}"}


@router.get("/mode")
async def get_memory_mode(
    session_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Get current memory mode configuration"""
    
    if session_id:
        config = orchestrator.memory.get_session_config(session_id)
        metrics = orchestrator.memory.get_session_metrics(session_id)
    else:
        config = orchestrator.memory.global_config
        metrics = None
    
    response = {
        "mode": config.mode,
        "config": config.dict(),
        "presets": list(DEFAULT_CONFIGS.keys())
    }
    
    if metrics:
        response["metrics"] = {
            "session_id": metrics.session_id,
            "mode": metrics.mode.value,
            "retrieval_count": metrics.retrieval_count,
            "cache_hits": metrics.cache_hits,
            "cache_misses": metrics.cache_misses,
            "cache_hit_rate": metrics.cache_hit_rate,
            "total_tokens_retrieved": metrics.total_tokens_retrieved,
            "total_cost": metrics.total_cost,
            "avg_cost_per_retrieval": metrics.avg_cost_per_retrieval,
            "avg_retrieval_time_ms": metrics.avg_retrieval_time_ms,
            "triggers_fired": metrics.triggers_fired
        }
    
    return response


@router.get("/metrics/{session_id}")
async def get_session_metrics(
    session_id: str,
    current_user: Dict = Depends(get_current_user)
) -> GetMemoryMetricsResponse:
    """Get memory metrics for a specific session"""
    
    metrics = orchestrator.memory.get_session_metrics(session_id)
    if not metrics:
        raise HTTPException(404, f"No metrics found for session {session_id}")
    
    return GetMemoryMetricsResponse(
        session_id=metrics.session_id,
        mode=metrics.mode.value,
        retrieval_count=metrics.retrieval_count,
        cache_hits=metrics.cache_hits,
        cache_misses=metrics.cache_misses,
        cache_hit_rate=metrics.cache_hit_rate,
        total_tokens_retrieved=metrics.total_tokens_retrieved,
        total_cost=metrics.total_cost,
        avg_cost_per_retrieval=metrics.avg_cost_per_retrieval,
        avg_retrieval_time_ms=metrics.avg_retrieval_time_ms,
        triggers_fired=metrics.triggers_fired
    )


@router.post("/cache/clear")
async def clear_cache(
    session_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Clear Redis cache for a session or all sessions"""
    
    if session_id:
        # Clear specific session cache
        cache_key = f"context:{session_id}"
        await orchestrator.memory.redis_client.delete(cache_key)
        return {"status": "success", "message": f"Cleared cache for session {session_id}"}
    else:
        # Clear all context caches
        cursor = 0
        cleared = 0
        while True:
            cursor, keys = await orchestrator.memory.redis_client.scan(
                cursor, 
                match="context:*",
                count=100
            )
            
            if keys:
                await orchestrator.memory.redis_client.delete(*keys)
                cleared += len(keys)
            
            if cursor == 0:
                break
        
        return {"status": "success", "message": f"Cleared {cleared} cache entries"}


@router.get("/debug/status")
async def debug_memory_status():
    """Debug endpoint to check Mem0 initialization status"""
    from app.orchestrator.memory import HAS_MEM0
    
    status = {
        "mem0_available": HAS_MEM0,
        "mem0_initialized": False,
        "mem0_client": None,
        "redis_initialized": orchestrator.memory._initialized,
        "error": None
    }
    
    # Check Mem0 initialization
    if orchestrator.memory._mem0_initialized:
        status["mem0_initialized"] = True
        status["mem0_client"] = "MemoryClient instance active"
    else:
        # Try to initialize to see what error we get
        try:
            orchestrator.memory._init_mem0()
            status["mem0_initialized"] = orchestrator.memory._mem0_initialized
            if orchestrator.memory.mem0_client:
                status["mem0_client"] = "MemoryClient instance created"
        except Exception as e:
            status["error"] = str(e)
    
    # Check API key
    from app.core.config import settings
    api_key = getattr(settings, 'mem0_api_key', 'NOT_SET')
    if api_key.startswith('m0-'):
        status["api_key_status"] = "Looks valid (starts with m0-)"
        status["api_key_length"] = len(api_key)
        status["api_key_preview"] = f"{api_key[:10]}...{api_key[-5:]}" if len(api_key) > 15 else "TOO_SHORT"
    elif api_key.startswith('m0-placeholder'):
        status["api_key_status"] = "PLACEHOLDER - needs real API key"
    else:
        status["api_key_status"] = "Invalid or not set"
    
    return status



@router.get("/modes")
async def list_memory_modes(current_user: Dict = Depends(get_current_user)):
    """List all available memory modes with descriptions"""
    
    return {
        "modes": [
            {
                "value": MemoryMode.CACHE_FIRST,
                "name": "Cache First",
                "description": "Minimal cost - 1 retrieval per session, uses cache extensively",
                "cost_profile": "~$0.02 per session",
                "use_case": "Most conversations, especially continuations"
            },
            {
                "value": MemoryMode.ALWAYS_FRESH,
                "name": "Always Fresh",
                "description": "Maximum accuracy - retrieval on every message",
                "cost_profile": "~$0.02 per message",
                "use_case": "Critical conversations, crisis therapy"
            },
            {
                "value": MemoryMode.SMART_TRIGGERS,
                "name": "Smart Triggers",
                "description": "Balanced - retrieval based on configurable triggers",
                "cost_profile": "~$0.06 per session",
                "use_case": "Longer, complex conversations"
            },
            {
                "value": MemoryMode.TEST_MODE,
                "name": "Test Mode",
                "description": "Testing - follows smart triggers with detailed logging",
                "cost_profile": "Variable",
                "use_case": "Optimization and testing"
            }
        ],
        "presets": {
            "conservative": {
                "description": "Minimal memory operations, maximum cost savings",
                "mode": "cache_first",
                "cache_ttl": 45,
                "triggers": "Only agent transfers and important info"
            },
            "balanced": {
                "description": "Smart balance between cost and accuracy",
                "mode": "smart_triggers",
                "cache_ttl": 30,
                "triggers": "All triggers enabled with moderate thresholds"
            },
            "premium": {
                "description": "Maximum accuracy, always fresh context",
                "mode": "always_fresh",
                "cache_ttl": 60,
                "triggers": "N/A - always retrieves"
            },
            "test": {
                "description": "Testing mode with full logging",
                "mode": "test_mode",
                "cache_ttl": 30,
                "triggers": "All triggers enabled for testing"
            }
        }
    }