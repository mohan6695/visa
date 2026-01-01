from typing import Dict, Any, Optional, Tuple
import logging
import jwt
import time
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from ..core.config import settings

logger = logging.getLogger(__name__)

# Security scheme for JWT authentication
security = HTTPBearer()

class SupabaseAuthService:
    """Service for handling Supabase authentication and JWT validation"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.jwt_secret = settings.SUPABASE_JWT_SECRET
        
    async def validate_token(self, token: str) -> Tuple[Dict[str, Any], bool]:
        """
        Validate JWT token and extract claims
        
        Returns:
            Tuple[Dict, bool]: (JWT claims, is_premium flag)
        """
        try:
            # Decode JWT without verification first to get the header
            header = jwt.get_unverified_header(token)
            
            # Verify and decode the token
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[header.get("alg", "HS256")],
                options={"verify_signature": True}
            )
            
            # Check if token is expired
            if "exp" in payload and payload["exp"] < time.time():
                logger.warning(f"Expired token: {payload.get('sub')}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            # Get user profile to check premium status
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user ID in token"
                )
            
            # Get user profile from Supabase
            profile_response = self.supabase.table("profiles").select("*").eq("id", user_id).execute()
            
            if not profile_response.data:
                logger.warning(f"User profile not found: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User profile not found"
                )
            
            profile = profile_response.data[0]
            is_premium = profile.get("is_premium", False)
            
            # Add group_id to claims if not present
            if "group_id" not in payload and "group_id" in profile:
                payload["group_id"] = profile["group_id"]
            
            return payload, is_premium
            
        except jwt.PyJWTError as e:
            logger.error(f"JWT validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication token: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication error"
            )
    
    async def get_current_user(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        """
        FastAPI dependency for getting the current authenticated user
        
        Returns:
            Dict: User claims from JWT
        """
        token = credentials.credentials
        claims, _ = await self.validate_token(token)
        return claims
    
    async def get_premium_user(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        """
        FastAPI dependency for getting a premium user
        Raises 403 if user is not premium
        
        Returns:
            Dict: User claims from JWT
        """
        token = credentials.credentials
        claims, is_premium = await self.validate_token(token)
        
        if not is_premium:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Premium subscription required for this endpoint"
            )
        
        return claims
    
    async def verify_group_access(
        self, 
        group_id: str, 
        user_claims: Dict[str, Any]
    ) -> bool:
        """
        Verify if user has access to the specified group
        
        Args:
            group_id: Group ID to check access for
            user_claims: User JWT claims
            
        Returns:
            bool: True if user has access, False otherwise
        """
        # Premium users can access any group
        if await self.is_premium_user(user_claims.get("sub")):
            return True
        
        # Check if user belongs to the group
        user_group_id = user_claims.get("group_id")
        return user_group_id == group_id
    
    async def is_premium_user(self, user_id: str) -> bool:
        """
        Check if user has premium status
        
        Args:
            user_id: User ID to check
            
        Returns:
            bool: True if user is premium, False otherwise
        """
        try:
            profile_response = self.supabase.table("profiles").select("is_premium").eq("id", user_id).execute()
            
            if not profile_response.data:
                return False
            
            return profile_response.data[0].get("is_premium", False)
        except Exception as e:
            logger.error(f"Error checking premium status: {str(e)}")
            return False
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile data
        
        Args:
            user_id: User ID to get profile for
            
        Returns:
            Optional[Dict]: User profile data or None if not found
        """
        try:
            profile_response = self.supabase.table("profiles").select("*").eq("id", user_id).execute()
            
            if not profile_response.data:
                return None
            
            return profile_response.data[0]
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return None
    
    async def create_user_profile(self, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new user profile
        
        Args:
            user_id: User ID to create profile for
            data: Profile data
            
        Returns:
            Optional[Dict]: Created profile data or None if failed
        """
        try:
            # Ensure user_id is set correctly
            profile_data = {**data, "id": user_id}
            
            # Create profile
            profile_response = self.supabase.table("profiles").insert(profile_data).execute()
            
            if not profile_response.data:
                return None
            
            return profile_response.data[0]
        except Exception as e:
            logger.error(f"Error creating user profile: {str(e)}")
            return None
    
    async def update_user_profile(self, user_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update user profile data
        
        Args:
            user_id: User ID to update profile for
            data: Profile data to update
            
        Returns:
            Optional[Dict]: Updated profile data or None if failed
        """
        try:
            # Remove sensitive fields that should not be updated directly
            safe_data = {k: v for k, v in data.items() if k not in [
                "is_premium", 
                "stripe_customer_id", 
                "stripe_subscription_id",
                "subscription_tier",
                "subscription_ends_at"
            ]}
            
            # Update profile
            profile_response = self.supabase.table("profiles").update(safe_data).eq("id", user_id).execute()
            
            if not profile_response.data:
                return None
            
            return profile_response.data[0]
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return None
    
    async def update_premium_status(
        self, 
        user_id: str, 
        is_premium: bool, 
        stripe_data: Dict[str, Any]
    ) -> bool:
        """
        Update user premium status
        
        Args:
            user_id: User ID to update
            is_premium: New premium status
            stripe_data: Stripe subscription data
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            update_data = {
                "is_premium": is_premium,
                "stripe_customer_id": stripe_data.get("customer_id"),
                "stripe_subscription_id": stripe_data.get("subscription_id"),
                "subscription_tier": stripe_data.get("tier", "premium"),
                "subscription_ends_at": stripe_data.get("ends_at")
            }
            
            profile_response = self.supabase.table("profiles").update(update_data).eq("id", user_id).execute()
            
            return bool(profile_response.data)
        except Exception as e:
            logger.error(f"Error updating premium status: {str(e)}")
            return False
    
    async def increment_daily_posts(self, user_id: str) -> bool:
        """
        Increment user's daily post count
        
        Args:
            user_id: User ID to update
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Check if user is premium (they don't have post limits)
            if await self.is_premium_user(user_id):
                return True
            
            # Get current daily posts
            profile_response = self.supabase.table("profiles").select("daily_posts").eq("id", user_id).execute()
            
            if not profile_response.data:
                return False
            
            current_posts = profile_response.data[0].get("daily_posts", 0)
            
            # Check if user has reached daily limit
            if current_posts >= 10:
                return False
            
            # Increment daily posts
            update_response = self.supabase.table("profiles").update({
                "daily_posts": current_posts + 1
            }).eq("id", user_id).execute()
            
            return bool(update_response.data)
        except Exception as e:
            logger.error(f"Error incrementing daily posts: {str(e)}")
            return False

# Create dependency for getting auth service
async def get_auth_service(supabase_client: Client) -> SupabaseAuthService:
    """Dependency for getting auth service"""
    return SupabaseAuthService(supabase_client)