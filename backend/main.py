"""
RELATRIX - Clean Setup
Ultra simple FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
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
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}

# Import routers
from auth import auth_router
from chat import chat_router
from agents import agents_router
from database import seed_agents

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(agents_router, prefix="/api/agents", tags=["agents"])

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