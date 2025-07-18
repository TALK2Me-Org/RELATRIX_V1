"""
Authentication endpoints using Supabase
Simple and clean
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
from supabase import create_client, Client
from config import settings
import jwt
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Supabase client - using service role key for full permissions
supabase: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)

# Router
auth_router = APIRouter()

# Security
security = HTTPBearer(auto_error=False)


# Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


# Helper functions
def create_access_token(user_id: str, email: str) -> str:
    """Create JWT token"""
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[dict]:
    """Get current user from JWT token"""
    if not credentials:
        return None
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return {"id": payload["sub"], "email": payload["email"]}
    except jwt.PyJWTError:
        return None


async def require_user(user: Optional[dict] = Depends(get_current_user)) -> dict:
    """Require authenticated user"""
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# Endpoints
@auth_router.post("/register", response_model=Token)
async def register(data: UserRegister):
    """Register new user"""
    try:
        logger.info(f"Registration attempt for: {data.email}")
        
        # Register with Supabase
        response = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password
        })
        
        # Log response for debugging
        logger.info(f"Registration response type: {type(response)}")
        logger.info(f"Has user: {hasattr(response, 'user')}")
        
        if not response.user:
            logger.error("No user in registration response")
            raise HTTPException(status_code=400, detail="Registration failed")
        
        # Create token
        token = create_access_token(response.user.id, response.user.email)
        
        logger.info(f"Registration successful for: {response.user.email}")
        
        return Token(
            access_token=token,
            user_id=response.user.id,
            email=response.user.email
        )
        
    except Exception as e:
        logger.error(f"Registration error details: {str(e)}")
        if "User already registered" in str(e):
            raise HTTPException(status_code=409, detail="Email already registered")
        raise HTTPException(status_code=400, detail=str(e))


@auth_router.post("/login", response_model=Token)
async def login(data: UserLogin):
    """Login user"""
    try:
        logger.info(f"Login attempt for: {data.email}")
        
        # Login with Supabase
        response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })
        
        # Log response for debugging
        logger.info(f"Supabase response type: {type(response)}")
        logger.info(f"Has user: {hasattr(response, 'user')}")
        
        if not response.user:
            logger.error("No user in response")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create token
        token = create_access_token(response.user.id, response.user.email)
        
        logger.info(f"Login successful for: {response.user.email}")
        
        return Token(
            access_token=token,
            user_id=response.user.id,
            email=response.user.email
        )
        
    except Exception as e:
        logger.error(f"Login error details: {str(e)}")
        if "Email not confirmed" in str(e):
            raise HTTPException(status_code=403, detail="Please verify your email first")
        raise HTTPException(status_code=401, detail="Invalid credentials")


@auth_router.post("/logout")
async def logout(user: dict = Depends(require_user)):
    """Logout user"""
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return {"message": "Logged out"}


@auth_router.get("/me")
async def get_me(user: dict = Depends(require_user)):
    """Get current user info"""
    return user