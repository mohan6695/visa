from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field
import logging
from supabase import Client
from ....services.supabase_auth_service import SupabaseAuthService, get_auth_service
from ....core.config import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Pydantic models for request validation
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenRefresh(BaseModel):
    refresh_token: str

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordChange(BaseModel):
    password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)

# Response models
class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: Dict[str, Any]
    expires_at: int

@router.post("/register", response_model=AuthResponse)
async def register(
    user_data: UserRegister,
    request: Request,
    supabase: Client = Depends(get_supabase_client),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """Register a new user"""
    try:
        # Register user with Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to register user"
            )
        
        user_id = auth_response.user.id
        
        # Create user profile
        profile_data = {
            "username": user_data.username,
            "full_name": user_data.full_name,
            "avatar_url": user_data.avatar_url,
            "is_premium": False,
            "daily_posts": 0
        }
        
        profile = await auth_service.create_user_profile(user_id, profile_data)
        
        if not profile:
            # If profile creation fails, we should ideally delete the auth user
            # but Supabase doesn't expose a direct API for this
            logger.error(f"Failed to create profile for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user profile"
            )
        
        # Return auth response
        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "user": {
                "id": user_id,
                "email": user_data.email,
                "username": user_data.username,
                "is_premium": False,
                **profile
            },
            "expires_at": auth_response.session.expires_at
        }
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=AuthResponse)
async def login(
    credentials: UserLogin,
    supabase: Client = Depends(get_supabase_client),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """Login with email and password"""
    try:
        # Login with Supabase Auth
        auth_response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        user_id = auth_response.user.id
        
        # Get user profile
        profile = await auth_service.get_user_profile(user_id)
        
        if not profile:
            logger.warning(f"Profile not found for user {user_id}")
            # Create a basic profile if it doesn't exist
            profile = await auth_service.create_user_profile(user_id, {
                "username": credentials.email.split('@')[0],
                "is_premium": False,
                "daily_posts": 0
            })
        
        # Return auth response
        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "user": {
                "id": user_id,
                "email": credentials.email,
                **profile
            },
            "expires_at": auth_response.session.expires_at
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login failed"
        )

@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    token_data: TokenRefresh,
    supabase: Client = Depends(get_supabase_client),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """Refresh access token"""
    try:
        # Refresh token with Supabase Auth
        auth_response = supabase.auth.refresh_session(token_data.refresh_token)
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = auth_response.user.id
        
        # Get user profile
        profile = await auth_service.get_user_profile(user_id)
        
        # Return auth response
        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "user": {
                "id": user_id,
                "email": auth_response.user.email,
                **(profile or {})
            },
            "expires_at": auth_response.session.expires_at
        }
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout(
    request: Request,
    supabase: Client = Depends(get_supabase_client)
):
    """Logout user"""
    try:
        # Get token from request
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing"
            )
        
        # Extract token
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )
        
        # Sign out with Supabase Auth
        supabase.auth.sign_out(token)
        
        return {"message": "Logged out successfully"}
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        # Return success even if there's an error to ensure client clears tokens
        return {"message": "Logged out successfully"}

@router.post("/reset-password")
async def reset_password(
    password_data: PasswordReset,
    supabase: Client = Depends(get_supabase_client)
):
    """Request password reset"""
    try:
        # Request password reset with Supabase Auth
        supabase.auth.reset_password_email(password_data.email)
        
        return {"message": "Password reset email sent"}
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        # Return success even if there's an error to prevent email enumeration
        return {"message": "If your email is registered, you will receive a password reset link"}

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    request: Request,
    supabase: Client = Depends(get_supabase_client),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """Change user password"""
    try:
        # Get token from request
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing"
            )
        
        # Extract token
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format"
            )
        
        # Validate token
        claims, _ = await auth_service.validate_token(token)
        
        # Change password with Supabase Auth
        supabase.auth.update_user({
            "password": password_data.new_password
        })
        
        return {"message": "Password changed successfully"}
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )