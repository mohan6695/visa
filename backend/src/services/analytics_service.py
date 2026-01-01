from typing import Dict, Any, Optional, List
import logging
import json
import httpx
import os
from datetime import datetime
from supabase import Client

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for analytics tracking and reporting"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        
        # PostHog configuration
        self.posthog_api_key = os.getenv("POSTHOG_API_KEY", "")
        self.posthog_host = os.getenv("POSTHOG_HOST", "https://app.posthog.com")
        
        # Hybrid analytics configuration
        self.enable_hybrid_analytics = os.getenv("ENABLE_HYBRID_ANALYTICS", "false").lower() == "true"
        self.store_events_locally = os.getenv("STORE_EVENTS_LOCALLY", "true").lower() == "true"
        
        # Check if PostHog is configured
        self.posthog_enabled = bool(self.posthog_api_key and self.posthog_host)
        
        # Log configuration status
        if self.posthog_enabled:
            logger.info(f"PostHog enabled: {self.posthog_host}")
        if self.enable_hybrid_analytics:
            logger.info("Hybrid analytics enabled")
        if self.store_events_locally:
            logger.info("Local event storage enabled")
        
        # Event types
        self.event_types = {
            "page_view": "Page View",
            "user_signup": "User Signup",
            "user_login": "User Login",
            "post_created": "Post Created",
            "post_viewed": "Post Viewed",
            "post_voted": "Post Voted",
            "comment_created": "Comment Created",
            "chat_message_sent": "Chat Message Sent",
            "search_performed": "Search Performed",
            "ai_question_asked": "AI Question Asked",
            "premium_checkout_started": "Premium Checkout Started",
            "premium_subscription_completed": "Premium Subscription Completed"
        }
    
    async def track_event(
        self, 
        event_type: str, 
        user_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        store_locally: bool = True
    ) -> bool:
        """
        Track an analytics event
        
        Args:
            event_type: Type of event
            user_id: User ID
            properties: Event properties
            ip_address: User IP address
            store_locally: Whether to store event in local database
            
        Returns:
            bool: Success status
        """
        try:
            # Prepare event data
            event_data = {
                "event": event_type,
                "properties": properties or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if user_id:
                event_data["distinct_id"] = user_id
                event_data["properties"]["user_id"] = user_id
            
            if ip_address:
                event_data["properties"]["ip"] = ip_address
            
            # Track in PostHog if enabled and hybrid analytics is not forcing local-only
            if self.posthog_enabled and not self.enable_hybrid_analytics:
                await self._send_to_posthog(event_data)
            
            # Store in local database if enabled (always for hybrid setup)
            if store_locally and self.store_events_locally:
                await self._store_event_locally(event_data)
            
            # For hybrid setup, always send to PostHog and store locally
            if self.enable_hybrid_analytics:
                if self.posthog_enabled:
                    await self._send_to_posthog(event_data)
                if self.store_events_locally:
                    await self._store_event_locally(event_data)
            
            return True
        except Exception as e:
            logger.error(f"Error tracking event {event_type}: {e}")
            return False
    
    async def _send_to_posthog(self, event_data: Dict[str, Any]) -> bool:
        """
        Send event to PostHog
        
        Args:
            event_data: Event data
            
        Returns:
            bool: Success status
        """
        try:
            # Prepare PostHog API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.posthog_api_key}"
            }
            
            # Send to PostHog
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.posthog_host}/capture/",
                    headers=headers,
                    json=event_data
                )
                
                if response.status_code != 200:
                    logger.error(f"PostHog API error: {response.status_code} - {response.text}")
                    return False
                
                return True
        except Exception as e:
            logger.error(f"Error sending to PostHog: {e}")
            return False
    
    async def _store_event_locally(self, event_data: Dict[str, Any]) -> bool:
        """
        Store event in local database using the new hybrid analytics table
        
        Args:
            event_data: Event data
            
        Returns:
            bool: Success status
        """
        try:
            # Extract event details
            event_id = f"{event_data['event']}_{datetime.utcnow().timestamp()}"
            event_name = event_data["event"]
            user_id = event_data["properties"].get("user_id")
            session_id = event_data["properties"].get("session_id")
            distinct_id = event_data.get("distinct_id")
            properties = event_data["properties"]
            
            # Extract page context
            page_url = properties.get("page_url")
            page_title = properties.get("page_title")
            referrer = properties.get("referrer")
            utm_source = properties.get("utm_source")
            utm_medium = properties.get("utm_medium")
            utm_campaign = properties.get("utm_campaign")
            
            # Extract device info
            user_agent = properties.get("user_agent")
            ip_address = properties.get("ip")
            device_type = properties.get("device_type")
            browser_name = properties.get("browser_name")
            browser_version = properties.get("browser_version")
            os_name = properties.get("os_name")
            os_version = properties.get("os_version")
            
            # Extract geographic info
            country = properties.get("country")
            region = properties.get("region")
            city = properties.get("city")
            timezone = properties.get("timezone")
            
            # Extract performance metrics
            load_time_ms = properties.get("load_time_ms")
            time_on_page_ms = properties.get("time_on_page_ms")
            
            # Extract custom dimensions
            dimension_1 = properties.get("dimension_1")
            dimension_2 = properties.get("dimension_2")
            dimension_3 = properties.get("dimension_3")
            dimension_4 = properties.get("dimension_4")
            dimension_5 = properties.get("dimension_5")
            
            # Extract revenue info
            revenue = properties.get("revenue")
            currency = properties.get("currency", "USD")
            
            # Convert UUID string to UUID object if needed
            if user_id:
                try:
                    import uuid
                    user_id = uuid.UUID(user_id)
                except (ValueError, TypeError):
                    user_id = None
            
            # Use the PostgreSQL function for insertion
            result = self.supabase.rpc('insert_analytics_event', {
                'p_event_id': event_id,
                'p_event_name': event_name,
                'p_user_id': user_id,
                'p_session_id': session_id,
                'p_distinct_id': distinct_id,
                'p_properties': properties,
                'p_event_type': 'custom',
                'p_page_url': page_url,
                'p_page_title': page_title,
                'p_referrer': referrer,
                'p_utm_source': utm_source,
                'p_utm_medium': utm_medium,
                'p_utm_campaign': utm_campaign,
                'p_user_agent': user_agent,
                'p_ip_address': ip_address,
                'p_device_type': device_type,
                'p_browser_name': browser_name,
                'p_browser_version': browser_version,
                'p_os_name': os_name,
                'p_os_version': os_version,
                'p_country': country,
                'p_region': region,
                'p_city': city,
                'p_timezone': timezone,
                'p_load_time_ms': load_time_ms,
                'p_time_on_page_ms': time_on_page_ms,
                'p_dimension_1': dimension_1,
                'p_dimension_2': dimension_2,
                'p_dimension_3': dimension_3,
                'p_dimension_4': dimension_4,
                'p_dimension_5': dimension_5,
                'p_revenue': revenue,
                'p_currency': currency,
                'p_source': 'posthog',
                'p_environment': os.getenv('ENVIRONMENT', 'development'),
                'p_timestamp': event_data["timestamp"]
            }).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error storing event locally: {e}")
            return False
    
    async def get_event_counts(
        self, 
        start_date: str, 
        end_date: str, 
        group_by: str = "event"
    ) -> List[Dict[str, Any]]:
        """
        Get event counts for reporting
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            group_by: Field to group by (event, user_id, group_id)
            
        Returns:
            List[Dict]: Event counts
        """
        try:
            # Query database for event counts
            query = self.supabase.table("analytics_events").select(
                f"{group_by}, count(*)"
            ).gte("created_at", start_date).lte("created_at", end_date).group_by(group_by)
            
            result = query.execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Error getting event counts: {e}")
            return []
    
    async def get_user_activity(
        self, 
        user_id: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get activity for a specific user
        
        Args:
            user_id: User ID
            limit: Maximum number of events to return
            
        Returns:
            List[Dict]: User activity events
        """
        try:
            # Query database for user events
            query = self.supabase.table("analytics_events").select(
                "*"
            ).eq("user_id", user_id).order("created_at", desc=True).limit(limit)
            
            result = query.execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Error getting user activity: {e}")
            return []
    
    async def get_group_activity(
        self, 
        group_id: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get activity for a specific group
        
        Args:
            group_id: Group ID
            limit: Maximum number of events to return
            
        Returns:
            List[Dict]: Group activity events
        """
        try:
            # Query database for group events
            query = self.supabase.table("analytics_events").select(
                "*"
            ).eq("group_id", group_id).order("created_at", desc=True).limit(limit)
            
            result = query.execute()
            
            return result.data
        except Exception as e:
            logger.error(f"Error getting group activity: {e}")
            return []
    
    async def get_active_users(
        self, 
        period: str = "day"
    ) -> Dict[str, int]:
        """
        Get active user counts
        
        Args:
            period: Time period (day, week, month)
            
        Returns:
            Dict: Active user counts
        """
        try:
            # Determine time period
            now = datetime.utcnow()
            
            if period == "day":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            elif period == "week":
                # Start of current week (Monday)
                start_date = (now.replace(hour=0, minute=0, second=0, microsecond=0) - 
                             datetime.timedelta(days=now.weekday())).isoformat()
            elif period == "month":
                # Start of current month
                start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
            else:
                raise ValueError(f"Invalid period: {period}")
            
            # Query database for distinct users
            query = self.supabase.table("analytics_events").select(
                "user_id"
            ).gte("created_at", start_date).execute()
            
            # Count distinct users
            distinct_users = set()
            for event in query.data:
                if event.get("user_id"):
                    distinct_users.add(event["user_id"])
            
            return {
                "period": period,
                "active_users": len(distinct_users)
            }
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return {
                "period": period,
                "active_users": 0
            }
    
    async def get_premium_conversion_rate(
        self, 
        start_date: str, 
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get premium conversion rate
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            
        Returns:
            Dict: Conversion rate data
        """
        try:
            # Query checkout started events
            checkout_query = self.supabase.table("analytics_events").select(
                "count(*)"
            ).eq("event", "premium_checkout_started").gte("created_at", start_date).lte("created_at", end_date).execute()
            
            # Query subscription completed events
            subscription_query = self.supabase.table("analytics_events").select(
                "count(*)"
            ).eq("event", "premium_subscription_completed").gte("created_at", start_date).lte("created_at", end_date).execute()
            
            # Calculate conversion rate
            checkout_count = checkout_query.data[0]["count"] if checkout_query.data else 0
            subscription_count = subscription_query.data[0]["count"] if subscription_query.data else 0
            
            conversion_rate = (subscription_count / checkout_count) * 100 if checkout_count > 0 else 0
            
            return {
                "checkout_count": checkout_count,
                "subscription_count": subscription_count,
                "conversion_rate": conversion_rate
            }
        except Exception as e:
            logger.error(f"Error getting premium conversion rate: {e}")
            return {
                "checkout_count": 0,
                "subscription_count": 0,
                "conversion_rate": 0
            }
    
    async def get_search_analytics(
        self, 
        start_date: str, 
        end_date: str, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get search analytics
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            limit: Maximum number of top queries to return
            
        Returns:
            Dict: Search analytics data
        """
        try:
            # Query search events
            search_query = self.supabase.table("analytics_events").select(
                "*"
            ).eq("event", "search_performed").gte("created_at", start_date).lte("created_at", end_date).execute()
            
            # Count total searches
            total_searches = len(search_query.data)
            
            # Count searches by query
            query_counts = {}
            for event in search_query.data:
                query = event.get("properties", {}).get("query", "")
                if query:
                    query_counts[query] = query_counts.get(query, 0) + 1
            
            # Get top queries
            top_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
            
            return {
                "total_searches": total_searches,
                "top_queries": [{"query": q, "count": c} for q, c in top_queries]
            }
        except Exception as e:
            logger.error(f"Error getting search analytics: {e}")
            return {
                "total_searches": 0,
                "top_queries": []
            }
    
    async def get_ai_analytics(
        self, 
        start_date: str, 
        end_date: str
    ) -> Dict[str, Any]:
        """
        Get AI analytics
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            
        Returns:
            Dict: AI analytics data
        """
        try:
            # Query AI question events
            question_query = self.supabase.table("analytics_events").select(
                "*"
            ).eq("event", "ai_question_asked").gte("created_at", start_date).lte("created_at", end_date).execute()
            
            # Query AI rating events
            rating_query = self.supabase.table("analytics_events").select(
                "*"
            ).eq("event", "ai_answer_rated").gte("created_at", start_date).lte("created_at", end_date).execute()
            
            # Count total questions
            total_questions = len(question_query.data)
            
            # Count cache hits
            cache_hits = sum(1 for event in question_query.data if event.get("properties", {}).get("use_cache", False))
            
            # Calculate average rating
            ratings = [event.get("properties", {}).get("rating", 0) for event in rating_query.data]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            
            return {
                "total_questions": total_questions,
                "cache_hits": cache_hits,
                "cache_hit_rate": (cache_hits / total_questions) * 100 if total_questions > 0 else 0,
                "rating_count": len(ratings),
                "average_rating": avg_rating
            }
        except Exception as e:
            logger.error(f"Error getting AI analytics: {e}")
            return {
                "total_questions": 0,
                "cache_hits": 0,
                "cache_hit_rate": 0,
                "rating_count": 0,
                "average_rating": 0
            }