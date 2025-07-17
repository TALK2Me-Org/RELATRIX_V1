"""
Configuration for RELATRIX
Simple environment variable management
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    # Mem0
    mem0_api_key: str = os.getenv("MEM0_API_KEY", "")
    
    # Zep
    zep_api_key: Optional[str] = os.getenv("ZEP_API_KEY", None)
    
    # AWS Bedrock
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID", None)
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY", None)
    aws_default_region: str = os.getenv("AWS_DEFAULT_REGION", "eu-central-1")
    
    # Supabase
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://localhost/relatrix")
    
    # JWT
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days
    
    # App
    app_name: str = "RELATRIX"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings()