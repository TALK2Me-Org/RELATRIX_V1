"""
Authentication API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, Union

from app.core.security import auth_service, get_current_user, get_current_user_optional

router = APIRouter(prefix="/auth", tags=["authentication"])


class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(min_length=6)
    metadata: Optional[Dict[str, Any]] = None


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class AuthResponse(BaseModel):
    """Authentication response"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    user: Dict[str, Any]


class RegistrationPendingResponse(BaseModel):
    """Registration response when email verification is required"""
    message: str
    requires_verification: bool = True
    user_email: str


@router.post("/register", response_model=Union[AuthResponse, RegistrationPendingResponse])
async def register(request: RegisterRequest):
    """
    Register a new user
    
    - **email**: User's email address
    - **password**: Password (min 6 characters)
    - **metadata**: Optional user metadata
    """
    result = await auth_service.register_user(
        email=request.email,
        password=request.password,
        metadata=request.metadata
    )
    
    # Check if session was created (no email verification required)
    if result.get("session"):
        return AuthResponse(
            access_token=result["session"].access_token,
            refresh_token=result["session"].refresh_token,
            user={
                "id": result["user"].id,
                "email": result["user"].email,
                "metadata": result["user"].user_metadata
            }
        )
    
    # Registration successful but email verification required
    if result.get("user"):
        return RegistrationPendingResponse(
            message="Registration successful! Please check your email to verify your account.",
            requires_verification=True,
            user_email=result["user"].email
        )
    
    # This shouldn't happen, but just in case
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Registration failed. Please try again."
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Login with email and password
    
    - **email**: User's email address
    - **password**: User's password
    """
    result = await auth_service.login_user(
        email=request.email,
        password=request.password
    )
    
    return AuthResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        user={
            "id": result["user"].id,
            "email": result["user"].email,
            "metadata": result["user"].user_metadata
        }
    )


@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Logout current user
    
    Requires authentication
    """
    # In a real app, you might want to invalidate the token
    # For now, we just return success
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current user information
    
    Requires authentication
    """
    return {
        "user": current_user
    }


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token
    """
    result = await auth_service.refresh_token(request.refresh_token)
    
    return AuthResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        user={
            "id": result["user"].id,
            "email": result["user"].email,
            "metadata": result["user"].user_metadata
        }
    )


@router.get("/check")
async def check_auth(current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """
    Check if user is authenticated (optional auth)
    
    Returns user info if authenticated, null otherwise
    """
    return {
        "authenticated": current_user is not None,
        "user": current_user
    }