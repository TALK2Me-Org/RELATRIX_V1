"""
RELATRIX Backend Main Application
FastAPI application entry point for relationship counseling platform
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import logging
import os

from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RELATRIX Backend",
    description="Backend API for RELATRIX relationship counseling platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

class ChatRequest(BaseModel):
    message: str
    session_id: str = None

class ChatResponse(BaseModel):
    response: str
    agent: str
    session_id: str

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Railway deployment"""
    return HealthResponse(
        status="healthy",
        message="RELATRIX Backend is running",
        version="1.0.0"
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "RELATRIX Backend",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "chat": "/chat"
        }
    }

# Chat endpoint (placeholder for MCP integration)
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint - will integrate with MCP server"""
    # Placeholder response
    return ChatResponse(
        response="Hello! RELATRIX backend is running. MCP integration coming soon.",
        agent="system",
        session_id=request.session_id or "default"
    )

# Environment info endpoint (development only)
@app.get("/env")
async def env_info():
    """Development endpoint to check environment"""
    if settings.environment == "production":
        raise HTTPException(status_code=404, detail="Not found")
    
    return {
        "environment": settings.environment,
        "port": os.environ.get("PORT", "8000"),
        "python_path": os.environ.get("PYTHONPATH", "not set")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))