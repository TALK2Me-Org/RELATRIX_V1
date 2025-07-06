"""
RELATRIX MCP Server Configuration
Simplified configuration for MCP server
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field

class MCPSettings(BaseSettings):
    """MCP Server settings"""
    
    # OpenAI API Settings
    openai_api_key: str = Field(
        default="sk-placeholder-openai-api-key-here",
        description="OpenAI API key"
    )
    openai_model: str = Field(
        default="gpt-4-turbo-preview",
        description="Default OpenAI model"
    )
    openai_temperature: float = Field(
        default=0.7,
        description="OpenAI temperature setting"
    )
    openai_max_tokens: int = Field(
        default=4000,
        description="OpenAI max tokens per response"
    )
    
    # Redis Settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    redis_password: Optional[str] = Field(
        default=None,
        description="Redis password"
    )
    
    # Mem0 API Settings
    mem0_api_key: str = Field(
        default="m0-placeholder-mem0-api-key-here",
        description="Mem0 API key"
    )
    mem0_user_id: str = Field(
        default="placeholder-mem0-user-id-here",
        description="Mem0 user ID"
    )
    mem0_agent_id: str = Field(
        default="relatrix-agent",
        description="Mem0 agent ID"
    )
    
    # Environment Settings
    environment: str = Field(
        default="development",
        description="Environment"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    
    # Agent Settings
    default_agent: str = Field(
        default="misunderstanding_protector",
        description="Default agent for new conversations"
    )
    agent_timeout: int = Field(
        default=30,
        description="Agent response timeout in seconds"
    )
    
    # Memory Settings
    max_context_length: int = Field(
        default=8000,
        description="Maximum context length for conversations"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance
settings = MCPSettings()