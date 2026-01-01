from typing import Callable, Dict, Any, Optional
import logging
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from ....services.supabase_auth_service import SupabaseAuthService

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication and authorization"""
    
    def __init__(
        self, 
        app, 
        auth_service: SupabaseAuthService,
        exclude_paths: list = None
    ):
        super().__init__(app)
        self.auth_service = auth_service
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
        ]
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process each request through the middleware"""
        
        # Skip authentication for excluded paths
        if self._should_skip_auth(request.url.path):
            return await call_next(request)
        
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authorization header missing"}
            )
        
        # Extract token
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication scheme"}
                )
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid authorization header format"}
            )
        
        # Validate token
        try:
            claims, is_premium = await self.auth_service.validate_token(token)
            
            # Add user claims to request state
            request.state.user = claims
            request.state.is_premium = is_premium
            
            # Check group access for group-specific endpoints
            path_parts = request.url.path.split("/")
            if "groups" in path_parts and len(path_parts) > path_parts.index("groups") + 1:
                group_index = path_parts.index("groups")
                if len(path_parts) > group_index + 1:
                    group_id = path_parts[group_index + 1]
                    
                    # Skip group validation for list endpoints
                    if group_id not in ["", "list"]:
                        has_access = await self.auth_service.verify_group_access(group_id, claims)
                        if not has_access:
                            return JSONResponse(
                                status_code=status.HTTP_403_FORBIDDEN,
                                content={"detail": "Access to this group is not allowed"}
                            )
            
            # Continue with the request
            return await call_next(request)
            
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication failed"}
            )
    
    def _should_skip_auth(self, path: str) -> bool:
        """Check if authentication should be skipped for this path"""
        return any(path.startswith(excluded) for excluded in self.exclude_paths)


class PremiumMiddleware(BaseHTTPMiddleware):
    """Middleware for premium-only endpoints"""
    
    def __init__(
        self, 
        app, 
        premium_paths: list = None
    ):
        super().__init__(app)
        self.premium_paths = premium_paths or [
            "/api/v1/premium/",
            "/api/v1/search/all",
        ]
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process each request through the middleware"""
        
        # Check if endpoint requires premium
        if self._is_premium_endpoint(request.url.path):
            # Check if user is premium
            is_premium = getattr(request.state, "is_premium", False)
            if not is_premium:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Premium subscription required for this endpoint"}
                )
        
        # Continue with the request
        return await call_next(request)
    
    def _is_premium_endpoint(self, path: str) -> bool:
        """Check if endpoint requires premium subscription"""
        return any(path.startswith(premium_path) for premium_path in self.premium_paths)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests"""
    
    def __init__(
        self, 
        app, 
        redis_client,
        rate_limits: Dict[str, int] = None
    ):
        super().__init__(app)
        self.redis = redis_client
        self.rate_limits = rate_limits or {
            "default": 100,  # 100 requests per minute
            "search": 20,    # 20 search requests per minute
            "ai": 10,        # 10 AI requests per minute
        }
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process each request through the middleware"""
        
        # Skip rate limiting for excluded paths
        if request.url.path.startswith(("/health", "/docs", "/redoc", "/openapi.json")):
            return await call_next(request)
        
        # Get user ID from request state
        user_id = getattr(request.state, "user", {}).get("sub", "anonymous")
        
        # Determine rate limit category
        category = self._get_rate_limit_category(request.url.path)
        limit = self.rate_limits.get(category, self.rate_limits["default"])
        
        # Check rate limit
        rate_limit_key = f"rate_limit:{user_id}:{category}"
        current_count = await self.redis.get(rate_limit_key)
        
        if current_count is None:
            # First request in window
            await self.redis.setex(rate_limit_key, 60, 1)  # 1-minute window
        else:
            current_count = int(current_count)
            if current_count >= limit:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded. Please try again later."}
                )
            
            # Increment counter
            await self.redis.incr(rate_limit_key)
        
        # Continue with the request
        return await call_next(request)
    
    def _get_rate_limit_category(self, path: str) -> str:
        """Determine rate limit category based on path"""
        if "/search" in path:
            return "search"
        elif "/ai" in path:
            return "ai"
        else:
            return "default"