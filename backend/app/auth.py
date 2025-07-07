"""
User Authentication Module
Handles user registration, login, and session management using Supabase
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_anon_key
)

# Initialize HTTP Bearer for token extraction
security = HTTPBearer()


class AuthService:
    """Service for handling authentication operations"""
    
    def __init__(self):
        self.supabase = supabase
        # Use the JWT secret from Supabase service role key
        self.jwt_secret = settings.jwt_secret_key
        self.jwt_algorithm = settings.jwt_algorithm
    
    async def register_user(self, email: str, password: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Register a new user with Supabase"""
        try:
            # Sign up user with Supabase Auth
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": metadata or {}
                }
            })
            
            if response.user:
                logger.info(f"User registered successfully: {email}")
                return {
                    "user": response.user,
                    "session": response.session
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to register user"
                )
                
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user with Supabase"""
        try:
            # Sign in with email and password
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.session:
                logger.info(f"User logged in successfully: {email}")
                return {
                    "user": response.user,
                    "session": response.session,
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
    
    async def logout_user(self, access_token: str) -> Dict[str, str]:
        """Logout user from Supabase"""
        try:
            # Set the auth header for this request
            self.supabase.auth.set_session(access_token, "")
            
            # Sign out
            self.supabase.auth.sign_out()
            
            logger.info("User logged out successfully")
            return {"message": "Logged out successfully"}
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            response = self.supabase.auth.refresh_session(refresh_token)
            
            if response.session:
                return {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "user": response.user
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
                
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    
    async def get_current_user(self, access_token: str) -> Dict[str, Any]:
        """Get current user from Supabase using access token"""
        try:
            # Verify JWT token
            payload = jwt.decode(
                access_token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                options={"verify_aud": False}
            )
            
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
            
            # Get user data from Supabase
            response = self.supabase.auth.get_user(access_token)
            
            if response.user:
                return {
                    "id": response.user.id,
                    "email": response.user.email,
                    "metadata": response.user.user_metadata,
                    "created_at": response.user.created_at
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
                
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Get user error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
    
    async def verify_admin(self, email: str) -> bool:
        """Check if user is an admin"""
        # For now, simple check against configured admin email
        # Later can be expanded to check user roles in database
        return email == settings.admin_email


# Create auth service instance
auth_service = AuthService()


# Dependency for getting current user from JWT token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """FastAPI dependency for getting current authenticated user"""
    token = credentials.credentials
    return await auth_service.get_current_user(token)


# Dependency for requiring admin access
async def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """FastAPI dependency for requiring admin access"""
    if not await auth_service.verify_admin(current_user.get("email")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Optional dependency for getting current user (allows anonymous access)
async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """FastAPI dependency for optional authentication"""
    if credentials:
        try:
            token = credentials.credentials
            return await auth_service.get_current_user(token)
        except HTTPException:
            return None
    return None