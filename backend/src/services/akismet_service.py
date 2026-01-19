"""Akismet spam filtering service for group posts chat"""

import logging
import httpx
from typing import Dict, Any, Optional
from ..core.config import settings

logger = logging.getLogger(__name__)


class AkismetService:
    """Service for checking messages against Akismet spam filter"""
    
    def __init__(self):
        self.api_key = settings.AKISMET_API_KEY
        self.blog_url = settings.AKISMET_BLOG_URL
        self.enabled = settings.AKISMET_ENABLED and self.api_key
        
    async def check_spam(
        self,
        content: str,
        user_ip: str = "127.0.0.1",
        user_agent: str = "Mozilla/5.0",
        username: str = "anonymous"
    ) -> Dict[str, Any]:
        """Check if content is spam using Akismet"""
        
        if not self.enabled:
            return {"is_spam": False, "skip_reason": "disabled"}
            
        if not self.api_key:
            return {"is_spam": False, "skip_reason": "no_api_key"}
        
        try:
            # Akismet API endpoint (legacy API for comment-check)
            api_url = f"https://{self.api_key}.rest.akismet.com/1.1/comment-check"
            
            data = {
                "blog": self.blog_url,
                "user_ip": user_ip,
                "user_agent": user_agent,
                "comment_author": username,
                "comment_content": content,
                "comment_type": "forum-post"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(api_url, data=data)
                
            if response.status_code == 200:
                is_spam = response.text.lower() == "true"
                return {"is_spam": is_spam}
            else:
                logger.warning(f"Akismet API returned status: {response.status_code}")
                return {"is_spam": False, "error": f"API error: {response.status_code}"}
                
        except httpx.RequestError as e:
            logger.error(f"Akismet request error: {e}")
            return {"is_spam": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Akismet check failed: {e}")
            return {"is_spam": False, "error": str(e)}
    
    async def report_spam(
        self,
        content: str,
        user_ip: str = "127.0.0.1",
        user_agent: str = "Mozilla/5.0",
        username: str = "anonymous"
    ) -> bool:
        """Report content as spam to Akismet"""
        
        if not self.enabled or not self.api_key:
            return False
            
        try:
            api_url = f"https://{self.api_key}.rest.akismet.com/1.1/submit-spam"
            
            data = {
                "blog": self.blog_url,
                "user_ip": user_ip,
                "user_agent": user_agent,
                "comment_author": username,
                "comment_content": content,
                "comment_type": "forum-post"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(api_url, data=data)
                
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to report spam to Akismet: {e}")
            return False
    
    async def report_ham(
        self,
        content: str,
        user_ip: str = "127.0.0.1",
        user_agent: str = "Mozilla/5.0",
        username: str = "anonymous"
    ) -> bool:
        """Report false positive (ham) to Akismet to improve detection"""
        
        if not self.enabled or not self.api_key:
            return False
            
        try:
            api_url = f"https://{self.api_key}.rest.akismet.com/1.1/submit-ham"
            
            data = {
                "blog": self.blog_url,
                "user_ip": user_ip,
                "user_agent": user_agent,
                "comment_author": username,
                "comment_content": content,
                "comment_type": "forum-post"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(api_url, data=data)
                
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Failed to report ham to Akismet: {e}")
            return False


# Singleton instance
_akismet_service: Optional[AkismetService] = None


def get_akismet_service() -> AkismetService:
    """Get or create the Akismet service singleton"""
    global _akismet_service
    if _akismet_service is None:
        _akismet_service = AkismetService()
    return _akismet_service
