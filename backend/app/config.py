"""
RELATRIX Configuration Module
Centralized configuration management for the application
"""

import os
from typing import Optional, List, Dict, Any
from pydantic import BaseSettings, Field, validator
from pydantic_settings import BaseSettings as Settings
import logging

logger = logging.getLogger(__name__)

class Settings(Settings):
    """Application settings with validation"""
    
    # Application Settings
    app_name: str = Field(default="RELATRIX", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment")
    
    # API Settings
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_prefix: str = Field(default="/api/v1", description="API prefix")
    
    # Database Settings
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/relatrix",
        description="Database connection URL"
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
    
    # Supabase Settings
    supabase_url: str = Field(
        default="https://placeholder-supabase-url.supabase.co",
        description="Supabase project URL"
    )
    supabase_anon_key: str = Field(
        default="placeholder-supabase-anon-key-here",
        description="Supabase anonymous key"
    )
    supabase_service_role_key: str = Field(
        default="placeholder-supabase-service-role-key-here",
        description="Supabase service role key"
    )
    
    # JWT Settings
    jwt_secret_key: str = Field(
        default="placeholder-jwt-secret-key-change-in-production",
        description="JWT secret key"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    jwt_expiration: int = Field(
        default=3600,
        description="JWT expiration time in seconds"
    )
    
    # Admin Settings
    admin_email: str = Field(
        default="admin@relatrix.com",
        description="Admin email address"
    )
    admin_password: str = Field(
        default="placeholder-admin-password-change-in-production",
        description="Admin password"
    )
    
    # Cost Monitoring Settings
    monthly_budget_limit: float = Field(
        default=100.0,
        description="Monthly budget limit in USD"
    )
    cost_alert_threshold: float = Field(
        default=0.8,
        description="Cost alert threshold (0.0-1.0)"
    )
    daily_cost_limit: float = Field(
        default=10.0,
        description="Daily cost limit in USD"
    )
    
    # MCP Server Settings
    mcp_server_host: str = Field(
        default="localhost",
        description="MCP server host"
    )
    mcp_server_port: int = Field(
        default=8001,
        description="MCP server port"
    )
    
    # Security Settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "https://relatrix.com"],
        description="CORS allowed origins"
    )
    allowed_hosts: List[str] = Field(
        default=["*"],
        description="Allowed hosts"
    )
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    rate_limit_requests: int = Field(
        default=100,
        description="Requests per minute per user"
    )
    
    # Logging Settings
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    
    # Session Settings
    session_timeout: int = Field(
        default=1800,
        description="Session timeout in seconds"
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
    
    # Memory Optimization
    memory_optimization_enabled: bool = Field(
        default=True,
        description="Enable memory optimization"
    )
    max_context_length: int = Field(
        default=8000,
        description="Maximum context length for conversations"
    )
    context_compression_threshold: int = Field(
        default=6000,
        description="Context compression threshold"
    )
    
    # File Upload Settings
    max_file_size: int = Field(
        default=10485760,  # 10MB
        description="Maximum file size in bytes"
    )
    allowed_file_types: List[str] = Field(
        default=[".txt", ".pdf", ".doc", ".docx"],
        description="Allowed file types for upload"
    )
    
    # Telemetry Settings
    telemetry_enabled: bool = Field(
        default=True,
        description="Enable telemetry collection"
    )
    telemetry_endpoint: Optional[str] = Field(
        default=None,
        description="Telemetry endpoint URL"
    )
    
    # Railway Settings
    railway_environment: str = Field(
        default="development",
        description="Railway environment"
    )
    port: int = Field(
        default=8000,
        description="Application port (Railway sets this automatically)"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    @validator("openai_api_key")
    def validate_openai_key(cls, v):
        if v.startswith("sk-placeholder"):
            logger.warning("Using placeholder OpenAI API key - update with real key")
        return v
    
    @validator("mem0_api_key")
    def validate_mem0_key(cls, v):
        if v.startswith("m0-placeholder"):
            logger.warning("Using placeholder Mem0 API key - update with real key")
        return v
    
    @validator("supabase_url")
    def validate_supabase_url(cls, v):
        if "placeholder" in v:
            logger.warning("Using placeholder Supabase URL - update with real URL")
        return v
    
    @validator("jwt_secret_key")
    def validate_jwt_secret(cls, v):
        if v.startswith("placeholder"):
            logger.warning("Using placeholder JWT secret - update with secure key")
        return v
    
    @validator("admin_password")
    def validate_admin_password(cls, v):
        if v.startswith("placeholder"):
            logger.warning("Using placeholder admin password - update with secure password")
        return v
    
    @validator("cors_origins")
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("allowed_hosts")
    def validate_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("cost_alert_threshold")
    def validate_cost_threshold(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Cost alert threshold must be between 0.0 and 1.0")
        return v
    
    def get_database_url(self) -> str:
        """Get formatted database URL"""
        return self.database_url
    
    def get_redis_url(self) -> str:
        """Get formatted Redis URL"""
        return self.redis_url
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration"""
        return {
            "api_key": self.openai_api_key,
            "model": self.openai_model,
            "temperature": self.openai_temperature,
            "max_tokens": self.openai_max_tokens
        }
    
    def get_mem0_config(self) -> Dict[str, Any]:
        """Get Mem0 configuration"""
        return {
            "api_key": self.mem0_api_key,
            "user_id": self.mem0_user_id,
            "agent_id": self.mem0_agent_id
        }
    
    def get_supabase_config(self) -> Dict[str, Any]:
        """Get Supabase configuration"""
        return {
            "url": self.supabase_url,
            "anon_key": self.supabase_anon_key,
            "service_role_key": self.supabase_service_role_key
        }
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment.lower() == "development"
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration"""
        return {
            "allow_origins": self.cors_origins,
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["*"]
        }
    
    def get_rate_limit_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration"""
        return {
            "enabled": self.rate_limit_enabled,
            "requests_per_minute": self.rate_limit_requests
        }
    
    def validate_required_keys(self) -> List[str]:
        """Validate required API keys and return missing ones"""
        missing_keys = []
        
        if self.openai_api_key.startswith("sk-placeholder"):
            missing_keys.append("OpenAI API Key")
        
        if self.mem0_api_key.startswith("m0-placeholder"):
            missing_keys.append("Mem0 API Key")
        
        if "placeholder" in self.supabase_url:
            missing_keys.append("Supabase URL")
        
        if self.supabase_anon_key.startswith("placeholder"):
            missing_keys.append("Supabase Anonymous Key")
        
        if self.supabase_service_role_key.startswith("placeholder"):
            missing_keys.append("Supabase Service Role Key")
        
        return missing_keys

# Create global settings instance
settings = Settings()

# Export commonly used configurations
DATABASE_URL = settings.get_database_url()
REDIS_URL = settings.get_redis_url()
OPENAI_CONFIG = settings.get_openai_config()
MEM0_CONFIG = settings.get_mem0_config()
SUPABASE_CONFIG = settings.get_supabase_config()

# Validate configuration on import
if __name__ == "__main__":
    print("RELATRIX Configuration Validation")
    print("=" * 40)
    
    missing_keys = settings.validate_required_keys()
    
    if missing_keys:
        print("⚠️  Missing required configuration:")
        for key in missing_keys:
            print(f"   - {key}")
        print("\nPlease update your environment variables or .env file")
    else:
        print("✅ All required configuration keys are present")
    
    print(f"\nEnvironment: {settings.environment}")
    print(f"Debug mode: {settings.debug}")
    print(f"API URL: http://{settings.api_host}:{settings.api_port}")
    print(f"MCP Server: http://{settings.mcp_server_host}:{settings.mcp_server_port}")
    
    if settings.telemetry_enabled:
        print("✅ Telemetry enabled")
    else:
        print("❌ Telemetry disabled")