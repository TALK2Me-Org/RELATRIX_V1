"""
Security utilities for authentication and authorization
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
import logging
from supabase import create_client, Client

from app.core.config import settings

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)

# Initialize Supabase client
supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_anon_key
)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.supabase_jwt_secret, 
        algorithm="HS256"
    )
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[Dict[str, Any]]:
    """
    Get current user from JWT token
    Returns None for anonymous users
    """
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials)
        
        # Extract user info from Supabase JWT
        user = {
            "id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "user"),
            "is_admin": payload.get("role") == "admin"
        }
        
        return user
        
    except HTTPException:
        # Allow anonymous access
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None


def require_auth(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Require authenticated user"""
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    return current_user


def require_admin(
    current_user: Dict[str, Any] = Depends(require_auth)
) -> Dict[str, Any]:
    """Require admin user"""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user


# Optional authentication dependency
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[Dict[str, Any]]:
    """
    Get current user from JWT token (optional - allows anonymous)
    Returns None for anonymous users
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


class AuthService:
    """Service for handling Supabase authentication operations"""
    
    def __init__(self):
        self.supabase = supabase
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
                    status_code=400,
                    detail="Failed to register user"
                )
                
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            raise HTTPException(
                status_code=400,
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
                    status_code=401,
                    detail="Invalid credentials"
                )
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise HTTPException(
                status_code=401,
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
                status_code=400,
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
                    status_code=401,
                    detail="Invalid refresh token"
                )
                
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Invalid refresh token"
            )
    
    async def get_current_user_supabase(self, access_token: str) -> Dict[str, Any]:
        """Get current user from Supabase using access token"""
        try:
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
                    status_code=401,
                    detail="User not found"
                )
                
        except Exception as e:
            logger.error(f"Get user error: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Authentication failed"
            )
    
    async def verify_admin(self, email: str) -> bool:
        """Check if user is an admin"""
        # For now, simple check against configured admin email
        # Later can be expanded to check user roles in database
        return email == settings.admin_email


# Create auth service instance
auth_service = AuthService()