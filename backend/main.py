"""
RELATRIX - Clean Setup
Ultra simple FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RELATRIX API",
    description="Relationship AI Assistant with Agent Switching",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",  # LOCAL DEV
        "http://localhost:5173",  # Vite default port
        "http://localhost:8080",
        "https://relatrix-frontend.up.railway.app",
        "https://relatrix-backend.up.railway.app",
        "https://*.up.railway.app"  # Allow all Railway preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

# Detailed health check
@app.get("/health/detailed")
async def detailed_health_check():
    """Check health of all services"""
    from database import SessionLocal, Agent
    from memory_service import client as mem0_client
    from config import settings
    
    health = {
        "status": "checking",
        "version": "2.0.0",
        "services": {}
    }
    
    # Check database
    try:
        db = SessionLocal()
        agent_count = db.query(Agent).count()
        db.close()
        health["services"]["database"] = {
            "status": "healthy",
            "agents_count": agent_count
        }
        logger.info(f"[HEALTH] Database OK, agents: {agent_count}")
    except Exception as e:
        health["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        logger.error(f"[HEALTH] Database error: {e}")
    
    # Check Mem0
    try:
        if settings.mem0_api_key:
            health["services"]["mem0"] = {
                "status": "configured",
                "api_key_present": True,
                "api_key_preview": settings.mem0_api_key[:8] + "..."
            }
        else:
            health["services"]["mem0"] = {
                "status": "not_configured",
                "api_key_present": False
            }
    except Exception as e:
        health["services"]["mem0"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check OpenAI
    try:
        if settings.openai_api_key:
            health["services"]["openai"] = {
                "status": "configured",
                "model": settings.openai_model
            }
        else:
            health["services"]["openai"] = {
                "status": "not_configured"
            }
    except Exception as e:
        health["services"]["openai"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Overall status
    all_healthy = all(
        s.get("status") in ["healthy", "configured"] 
        for s in health["services"].values()
    )
    health["status"] = "healthy" if all_healthy else "degraded"
    
    return health

# Import routers
from auth import auth_router
from chat import chat_router
from agents import agents_router
from playground import playground_router
from database import seed_agents
from models import get_all_models

# System settings (in-memory for simplicity)
system_settings = {
    "enable_fallback": True,
    "default_agent": "misunderstanding_protector"
}

# Settings endpoints
@app.get("/api/settings")
async def get_settings():
    return system_settings

@app.post("/api/settings")
async def update_settings(settings: dict):
    global system_settings
    system_settings.update(settings)
    logger.info(f"System settings updated: {system_settings}")
    return system_settings

# Models endpoint
@app.get("/api/models")
async def get_models():
    """Get all available models organized by provider"""
    return get_all_models()

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(agents_router, prefix="/api/agents", tags=["agents"])
app.include_router(playground_router, prefix="/api/playground", tags=["playground"])

# Optional: Include Mem0 playground if configured
try:
    from config import settings
    if settings.mem0_api_key:
        from playground_mem0 import mem0_router
        app.include_router(mem0_router, prefix="/api/playground-mem0", tags=["playground-mem0"])
        logger.info("[MAIN] Mem0 playground enabled")
except Exception as e:
    logger.warning(f"[MAIN] Mem0 playground not loaded: {e}")

# Optional: Include Zep playground if configured
try:
    from config import settings
    if hasattr(settings, 'zep_api_key') and settings.zep_api_key:
        from playground_zep import zep_router
        app.include_router(zep_router, prefix="/api/playground-zep", tags=["playground-zep"])
        logger.info("[MAIN] Zep playground enabled")
except Exception as e:
    logger.warning(f"[MAIN] Zep playground not loaded: {e}")

# Optional: Include AWS Bedrock playground if configured
try:
    from config import settings
    if hasattr(settings, 'aws_access_key_id') and settings.aws_access_key_id:
        from playground_bedrock import bedrock_router
        app.include_router(bedrock_router, prefix="/api/playground-bedrock", tags=["playground-bedrock"])
        logger.info("[MAIN] AWS Bedrock playground enabled")
except Exception as e:
    logger.warning(f"[MAIN] AWS Bedrock playground not loaded: {e}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database with default agents"""
    logger.info("Starting RELATRIX...")
    seed_agents()
    logger.info("Default agents seeded")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)