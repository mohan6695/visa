from typing import Callable, Dict, Any, Optional, List
import logging
import time
import re
import hashlib
import ipaddress
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security and anti-abuse measures"""
    
    def __init__(
        self, 
        app, 
        redis_client: Redis,
        trusted_proxies: List[str] = None,
        blocked_ips: List[str] = None,
        blocked_user_agents: List[str] = None,
        blocked_referers: List[str] = None,
        blocked_paths: List[str] = None,
        rate_limits: Dict[str, Dict[str, int]] = None
    ):
        super().__init__(app)
        self.redis = redis_client
        self.trusted_proxies = trusted_proxies or ["127.0.0.1", "::1"]
        self.blocked_ips = blocked_ips or []
        self.blocked_user_agents = blocked_user_agents or [
            "scrapy", "crawler", "spider", "bot", "semrush"
        ]
        self.blocked_referers = blocked_referers or []
        self.blocked_paths = blocked_paths or []
        self.rate_limits = rate_limits or {
            "default": {"limit": 100, "window": 60},  # 100 requests per minute
            "auth": {"limit": 10, "window": 60},      # 10 auth requests per minute
            "api": {"limit": 60, "window": 60},       # 60 API requests per minute
            "search": {"limit": 20, "window": 60},    # 20 search requests per minute
            "post": {"limit": 10, "window": 60}       # 10 post requests per minute
        }
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process each request through the middleware"""
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check if IP is blocked
        if self._is_ip_blocked(client_ip):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Access denied"}
            )
        
        # Check if user agent is blocked
        if self._is_user_agent_blocked(request):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Access denied"}
            )
        
        # Check if referer is blocked
        if self._is_referer_blocked(request):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Access denied"}
            )
        
        # Check if path is blocked
        if self._is_path_blocked(request):
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Access denied"}
            )
        
        # Check rate limits
        rate_limit_key = self._get_rate_limit_key(request, client_ip)
        rate_limit_category = self._get_rate_limit_category(request)
        rate_limit_config = self.rate_limits.get(rate_limit_category, self.rate_limits["default"])
        
        is_rate_limited = await self._check_rate_limit(
            rate_limit_key,
            rate_limit_config["limit"],
            rate_limit_config["window"]
        )
        
        if is_rate_limited:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests"}
            )
        
        # Add security headers to response
        response = await call_next(request)
        return self._add_security_headers(response)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address, handling proxies"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        
        if forwarded_for:
            # Get the first IP in the chain that's not a trusted proxy
            ips = [ip.strip() for ip in forwarded_for.split(",")]
            
            for ip in ips:
                if ip not in self.trusted_proxies:
                    return ip
        
        # Fallback to direct client
        return request.client.host if request.client else "127.0.0.1"
    
    def _is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is in blocked list"""
        # Direct match
        if ip in self.blocked_ips:
            return True
        
        # CIDR match
        try:
            client_ip = ipaddress.ip_address(ip)
            for blocked in self.blocked_ips:
                if "/" in blocked:  # CIDR notation
                    network = ipaddress.ip_network(blocked, strict=False)
                    if client_ip in network:
                        return True
        except ValueError:
            pass
        
        return False
    
    def _is_user_agent_blocked(self, request: Request) -> bool:
        """Check if user agent is blocked"""
        user_agent = request.headers.get("User-Agent", "").lower()
        
        if not user_agent:
            return True  # Block requests with no user agent
        
        for blocked in self.blocked_user_agents:
            if blocked.lower() in user_agent:
                return True
        
        return False
    
    def _is_referer_blocked(self, request: Request) -> bool:
        """Check if referer is blocked"""
        referer = request.headers.get("Referer", "").lower()
        
        if not referer:
            return False  # Don't block requests with no referer
        
        for blocked in self.blocked_referers:
            if blocked.lower() in referer:
                return True
        
        return False
    
    def _is_path_blocked(self, request: Request) -> bool:
        """Check if path is blocked"""
        path = request.url.path
        
        for blocked in self.blocked_paths:
            if re.match(blocked, path):
                return True
        
        return False
    
    def _get_rate_limit_key(self, request: Request, client_ip: str) -> str:
        """Get rate limit key based on user ID or IP"""
        # Try to get user ID from request state
        user_id = getattr(request.state, "user", {}).get("sub", None)
        
        if user_id:
            return f"rate_limit:{user_id}:{self._get_rate_limit_category(request)}"
        else:
            return f"rate_limit:{client_ip}:{self._get_rate_limit_category(request)}"
    
    def _get_rate_limit_category(self, request: Request) -> str:
        """Determine rate limit category based on path and method"""
        path = request.url.path
        method = request.method
        
        if path.startswith("/api/v1/auth"):
            return "auth"
        elif path.startswith("/api/v1/search"):
            return "search"
        elif method == "POST" and (
            path.startswith("/api/v1/posts") or 
            path.startswith("/api/v1/comments")
        ):
            return "post"
        elif path.startswith("/api/v1"):
            return "api"
        else:
            return "default"
    
    async def _check_rate_limit(
        self, 
        key: str, 
        limit: int, 
        window: int
    ) -> bool:
        """Check if request is rate limited"""
        try:
            # Get current count
            current = await self.redis.get(key)
            
            if current is None:
                # First request in window
                await self.redis.setex(key, window, 1)
                return False
            
            current_count = int(current)
            
            if current_count >= limit:
                return True
            
            # Increment counter
            await self.redis.incr(key)
            return False
            
        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            return False  # Don't block on errors
    
    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response"""
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' https://api.groq.com https://*.supabase.co; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "base-uri 'self';"
        )
        
        # Other security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )
        
        return response


class ContentSecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for content security and anti-abuse"""
    
    def __init__(
        self, 
        app,
        redis_client: Redis,
        blocked_words: List[str] = None,
        spam_threshold: float = 0.7,
        max_content_length: int = 10000
    ):
        super().__init__(app)
        self.redis = redis_client
        self.blocked_words = blocked_words or []
        self.spam_threshold = spam_threshold
        self.max_content_length = max_content_length
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process each request through the middleware"""
        
        # Only check POST/PUT requests
        if request.method in ["POST", "PUT"] and self._is_content_endpoint(request):
            try:
                # Get request body
                body = await request.json()
                
                # Check content length
                content = self._extract_content(body)
                if content and len(content) > self.max_content_length:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={"detail": "Content too large"}
                    )
                
                # Check for blocked words
                if content and self._contains_blocked_words(content):
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": "Content contains prohibited words"}
                    )
                
                # Check for spam
                if content and await self._is_spam(content, request):
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": "Content detected as spam"}
                    )
            except Exception as e:
                logger.error(f"Error in content security check: {e}")
                # Continue with request if there's an error in the middleware
        
        # Continue with the request
        return await call_next(request)
    
    def _is_content_endpoint(self, request: Request) -> bool:
        """Check if endpoint is for content creation/update"""
        path = request.url.path
        return (
            path.startswith("/api/v1/posts") or
            path.startswith("/api/v1/comments") or
            path.startswith("/api/v1/chat")
        )
    
    def _extract_content(self, body: Dict[str, Any]) -> Optional[str]:
        """Extract content from request body"""
        if "content" in body:
            return body["content"]
        elif "message" in body:
            return body["message"]
        elif "text" in body:
            return body["text"]
        return None
    
    def _contains_blocked_words(self, content: str) -> bool:
        """Check if content contains blocked words"""
        content_lower = content.lower()
        
        for word in self.blocked_words:
            if word.lower() in content_lower:
                return True
        
        return False
    
    async def _is_spam(self, content: str, request: Request) -> bool:
        """Check if content is spam"""
        # Simple spam detection based on repetition and characteristics
        
        # Check for excessive repetition
        words = content.split()
        if len(words) > 10:
            unique_words = set(words)
            repetition_ratio = len(unique_words) / len(words)
            
            if repetition_ratio < 0.3:  # High repetition
                return True
        
        # Check for excessive uppercase
        if len(content) > 20:
            uppercase_ratio = sum(1 for c in content if c.isupper()) / len(content)
            
            if uppercase_ratio > 0.5:  # More than 50% uppercase
                return True
        
        # Check for excessive special characters
        if len(content) > 20:
            special_chars = sum(1 for c in content if not c.isalnum() and not c.isspace())
            special_ratio = special_chars / len(content)
            
            if special_ratio > 0.3:  # More than 30% special characters
                return True
        
        # Check for URL spam
        url_count = len(re.findall(r'https?://\S+', content))
        if url_count > 5 or (len(words) > 0 and url_count / len(words) > 0.2):
            return True
        
        # Check user spam history
        user_id = getattr(request.state, "user", {}).get("sub", None)
        client_ip = request.client.host if request.client else "127.0.0.1"
        
        if user_id:
            spam_key = f"spam_score:{user_id}"
        else:
            spam_key = f"spam_score:{client_ip}"
        
        spam_score = await self.redis.get(spam_key)
        
        if spam_score and float(spam_score) > self.spam_threshold:
            return True
        
        return False


class WatermarkMiddleware(BaseHTTPMiddleware):
    """Middleware for content watermarking"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Process each request through the middleware"""
        
        # Only process POST requests to content endpoints
        if request.method == "POST" and self._is_content_endpoint(request):
            try:
                # Get request body
                body_bytes = await request.body()
                
                # Parse JSON
                import json
                body = json.loads(body_bytes)
                
                # Add watermark if needed
                if "content" in body and isinstance(body["content"], str):
                    # Generate watermark
                    watermark = self._generate_watermark(
                        content=body["content"],
                        user_id=getattr(request.state, "user", {}).get("sub", "anonymous")
                    )
                    
                    # Add watermark to request state for later use
                    request.state.watermark = watermark
            except Exception as e:
                logger.error(f"Error in watermark middleware: {e}")
                # Continue with request if there's an error in the middleware
        
        # Continue with the request
        return await call_next(request)
    
    def _is_content_endpoint(self, request: Request) -> bool:
        """Check if endpoint is for content creation"""
        path = request.url.path
        return (
            path.startswith("/api/v1/posts") or
            path.startswith("/api/v1/comments")
        )
    
    def _generate_watermark(self, content: str, user_id: str) -> str:
        """Generate watermark for content"""
        timestamp = int(time.time())
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        user_hash = hashlib.md5(user_id.encode()).hexdigest()[:8]
        
        return f"POST-{content_hash}-{user_hash}-{timestamp}"