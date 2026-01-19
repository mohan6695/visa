"""
Hybrid Analytics Service - PostHog + Supabase Integration
Sends analytics events to both PostHog (for advanced analytics) and Supabase (for raw data storage)
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import httpx
import os
from posthog import Client
from supabase import create_client, Client as SupabaseClient


logger = logging.getLogger(__name__)


class AnalyticsService:
    """Hybrid analytics service that integrates PostHog and Supabase"""
    
    def __init__(self):
        # PostHog configuration
        self.posthog_api_key = os.getenv("POSTHOG_API_KEY")
        self.posthog_host = os.getenv("POSTHOG_HOST", "https://app.posthog.com")
        
        # Supabase configuration
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        # Initialize clients
        self.posthog_client = None
        self.supabase_client = None
        
        if self.posthog_api_key:
            self.posthog_client = Client(
                api_key=self.posthog_api_key,
                host=self.posthog_host
            )
            logger.info("PostHog client initialized")
        
        if self.supabase_url and self.supabase_key:
            self.supabase_client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Supabase client initialized")
        
        if not self.posthog_client and not self.supabase_client:
            logger.warning("No analytics clients initialized - check environment variables")
    
    def track_event(
        self,
        event: str,
        distinct_id: Optional[str] = None,
        user_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        device_info: Optional[Dict[str, Any]] = None,
        geo_info: Optional[Dict[str, Any]] = None,
        performance_metrics: Optional[Dict[str, Any]] = None,
        conversion_data: Optional[Dict[str, Any]] = None,
        custom_dimensions: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track an analytics event in both PostHog and Supabase
        
        Args:
            event: Event name (e.g., 'page_view', 'button_click', 'user_signup')
            distinct_id: Anonymous user identifier (for PostHog)
            user_id: Authenticated user ID
            properties: Event properties/dimensions
            session_id: Current session identifier
            timestamp: Event timestamp
            device_info: Device/browser information
            geo_info: Geographic information
            performance_metrics: Performance data (load times, etc.)
            conversion_data: Conversion funnel data
            custom_dimensions: Custom analytics dimensions
        
        Returns:
            bool: True if tracking was successful in at least one platform
        """
        
        if not timestamp:
            timestamp = datetime.now(timezone.utc)
        
        # Prepare common event data
        event_data = self._prepare_event_data(
            event=event,
            distinct_id=distinct_id,
            user_id=user_id,
            properties=properties or {},
            session_id=session_id,
            timestamp=timestamp,
            device_info=device_info,
            geo_info=geo_info,
            performance_metrics=performance_metrics,
            conversion_data=conversion_data,
            custom_dimensions=custom_dimensions
        )
        
        success = False
        
        # Track in PostHog (if configured)
        if self.posthog_client:
            success_posthog = self._track_posthog(event_data)
            success = success or success_posthog
        
        # Track in Supabase (if configured)
        if self.supabase_client:
            success_supabase = self._track_supabase(event_data)
            success = success or success_supabase
        
        return success
    
    def _prepare_event_data(
        self,
        event: str,
        distinct_id: Optional[str],
        user_id: Optional[str],
        properties: Dict[str, Any],
        session_id: Optional[str],
        timestamp: datetime,
        device_info: Optional[Dict[str, Any]],
        geo_info: Optional[Dict[str, Any]],
        performance_metrics: Optional[Dict[str, Any]],
        conversion_data: Optional[Dict[str, Any]],
        custom_dimensions: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare unified event data structure"""
        
        # Base event properties
        base_properties = {
            'timestamp': timestamp.isoformat(),
            'session_id': session_id,
            'user_id': user_id,
        }
        
        # Add device information
        if device_info:
            base_properties.update({
                'device_type': device_info.get('type'),
                'device_browser': device_info.get('browser'),
                'device_os': device_info.get('os'),
                'device_screen_resolution': device_info.get('screen_resolution'),
                'device_user_agent': device_info.get('user_agent'),
            })
        
        # Add geographic information
        if geo_info:
            base_properties.update({
                'country_code': geo_info.get('country_code'),
                'region': geo_info.get('region'),
                'city': geo_info.get('city'),
                'timezone': geo_info.get('timezone'),
            })
        
        # Add performance metrics
        if performance_metrics:
            base_properties.update({
                'page_load_time': performance_metrics.get('page_load_time'),
                'dom_content_loaded': performance_metrics.get('dom_content_loaded'),
                'first_contentful_paint': performance_metrics.get('first_contentful_paint'),
                'largest_contentful_paint': performance_metrics.get('largest_contentful_paint'),
                'cumulative_layout_shift': performance_metrics.get('cumulative_layout_shift'),
                'first_input_delay': performance_metrics.get('first_input_delay'),
            })
        
        # Add conversion data
        if conversion_data:
            base_properties.update({
                'conversion_funnel_step': conversion_data.get('funnel_step'),
                'conversion_value': conversion_data.get('value'),
                'conversion_currency': conversion_data.get('currency'),
                'conversion_category': conversion_data.get('category'),
            })
        
        # Add custom dimensions
        if custom_dimensions:
            base_properties.update(custom_dimensions)
        
        # Merge with provided properties (properties take precedence)
        base_properties.update(properties)
        
        # Add derived properties
        if 'url' in base_properties:
            parsed_url = urlparse(base_properties['url'])
            base_properties.update({
                'url_domain': parsed_url.netloc,
                'url_path': parsed_url.path,
                'url_query_params': dict(parse_qsl(parsed_url.query)) if parsed_url.query else {},
            })
        
        if 'referrer' in base_properties:
            parsed_referrer = urlparse(base_properties['referrer'])
            base_properties.update({
                'referrer_domain': parsed_referrer.netloc,
                'referrer_type': self._classify_referrer(parsed_referrer.netloc),
            })
        
        return {
            'event': event,
            'distinct_id': distinct_id,
            'user_id': user_id,
            'properties': base_properties,
            'timestamp': timestamp,
        }
    
    def _classify_referrer(self, domain: str) -> str:
        """Classify referrer domain type"""
        if not domain:
            return 'direct'
        
        domain = domain.lower()
        
        # Search engines
        search_engines = ['google', 'bing', 'yahoo', 'duckduckgo', 'baidu']
        if any(engine in domain for engine in search_engines):
            return 'search'
        
        # Social media
        social_platforms = ['facebook', 'twitter', 'linkedin', 'instagram', 'tiktok', 'youtube', 'reddit']
        if any(platform in domain for platform in social_platforms):
            return 'social'
        
        # Email
        email_domains = ['gmail', 'outlook', 'yahoo mail', 'hotmail']
        if any(email in domain for email in email_domains):
            return 'email'
        
        return 'referral'
    
    def _track_posthog(self, event_data: Dict[str, Any]) -> bool:
        """Track event in PostHog"""
        try:
            if not self.posthog_client:
                return False
            
            # Prepare PostHog event
            posthog_event = {
                'event': event_data['event'],
                'distinct_id': event_data['distinct_id'] or 'anonymous',
                'properties': event_data['properties']
            }
            
            # Add timestamp if provided
            if event_data.get('timestamp'):
                posthog_event['timestamp'] = event_data['timestamp']
            
            # Capture event
            self.posthog_client.capture(**posthog_event)
            logger.debug(f"Event '{event_data['event']}' tracked in PostHog")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track event in PostHog: {e}")
            return False
    
    def _track_supabase(self, event_data: Dict[str, Any]) -> bool:
        """Track event in Supabase"""
        try:
            if not self.supabase_client:
                return False
            
            # Prepare Supabase event record
            supabase_event = {
                'event_name': event_data['event'],
                'distinct_id': event_data['distinct_id'],
                'user_id': event_data['user_id'],
                'session_id': event_data['properties'].get('session_id'),
                'event_timestamp': event_data['timestamp'].isoformat(),
                'properties': event_data['properties'],
                'country_code': event_data['properties'].get('country_code'),
                'device_type': event_data['properties'].get('device_type'),
                'device_browser': event_data['properties'].get('device_browser'),
                'device_os': event_data['properties'].get('device_os'),
                'url_domain': event_data['properties'].get('url_domain'),
                'referrer_type': event_data['properties'].get('referrer_type'),
                'utm_source': event_data['properties'].get('utm_source'),
                'utm_medium': event_data['properties'].get('utm_medium'),
                'utm_campaign': event_data['properties'].get('utm_campaign'),
                'conversion_value': event_data['properties'].get('conversion_value'),
                'page_load_time': event_data['properties'].get('page_load_time'),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Insert into Supabase
            result = self.supabase_client.table('analytics_events').insert(supabase_event).execute()
            logger.debug(f"Event '{event_data['event']}' stored in Supabase")
            return True
            
        except Exception as e:
            logger.error(f"Failed to track event in Supabase: {e}")
            return False
    
    def identify_user(
        self,
        distinct_id: str,
        user_id: Optional[str] = None,
        user_properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Identify user in PostHog"""
        try:
            if not self.posthog_client:
                return False
            
            self.posthog_client.identify(
                distinct_id=distinct_id,
                properties=user_properties or {}
            )
            logger.info(f"User {distinct_id} identified in PostHog")
            return True
            
        except Exception as e:
            logger.error(f"Failed to identify user in PostHog: {e}")
            return False
    
    def track_session_start(
        self,
        distinct_id: str,
        session_id: str,
        user_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track session start in both platforms"""
        return self.track_event(
            event='session_start',
            distinct_id=distinct_id,
            user_id=user_id,
            session_id=session_id,
            properties=properties or {}
        )
    
    def track_session_end(
        self,
        distinct_id: str,
        session_id: str,
        user_id: Optional[str] = None,
        session_duration: Optional[int] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track session end in both platforms"""
        return self.track_event(
            event='session_end',
            distinct_id=distinct_id,
            user_id=user_id,
            session_id=session_id,
            properties={
                'session_duration': session_duration,
                **(properties or {})
            }
        )
    
    def track_page_view(
        self,
        distinct_id: str,
        url: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        referrer: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track page view event"""
        return self.track_event(
            event='page_view',
            distinct_id=distinct_id,
            user_id=user_id,
            session_id=session_id,
            properties={
                'url': url,
                'referrer': referrer,
                **(properties or {})
            }
        )
    
    def track_conversion(
        self,
        distinct_id: str,
        conversion_type: str,
        value: Optional[float] = None,
        currency: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track conversion event"""
        return self.track_event(
            event='conversion',
            distinct_id=distinct_id,
            user_id=user_id,
            session_id=session_id,
            conversion_data={
                'category': conversion_type,
                'value': value,
                'currency': currency
            },
            properties=properties or {}
        )
    
    def track_performance_metric(
        self,
        distinct_id: str,
        metric_name: str,
        value: float,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Track performance metric"""
        return self.track_event(
            event='performance_metric',
            distinct_id=distinct_id,
            user_id=user_id,
            session_id=session_id,
            performance_metrics={
                metric_name: value
            },
            properties=properties or {}
        )
    
    def batch_track_events(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Track multiple events in batch"""
        results = {'posthog': 0, 'supabase': 0, 'failed': 0}
        
        for event_data in events:
            if self.track_event(**event_data):
                if self.posthog_client:
                    results['posthog'] += 1
                if self.supabase_client:
                    results['supabase'] += 1
            else:
                results['failed'] += 1
        
        logger.info(f"Batch tracked {len(events)} events: {results}")
        return results
    
    def get_events_from_supabase(
        self,
        limit: int = 1000,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve events from Supabase for analysis"""
        try:
            if not self.supabase_client:
                return []
            
            query = self.supabase_client.table('analytics_events').select('*')
            
            # Apply filters
            if filters:
                for column, value in filters.items():
                    query = query.eq(column, value)
            
            # Apply pagination
            query = query.range(offset, offset + limit - 1)
            
            # Order by timestamp
            query = query.order('event_timestamp', desc=True)
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to retrieve events from Supabase: {e}")
            return []
    
    def get_session_analytics(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get session analytics from Supabase"""
        try:
            if not self.supabase_client:
                return None
            
            # Get session events
            events = self.supabase_client.table('analytics_events').select('*').eq('session_id', session_id).execute()
            
            if not events.data:
                return None
            
            # Calculate session metrics
            event_names = [event['event_name'] for event in events.data]
            page_views = event_names.count('page_view')
            conversions = event_names.count('conversion')
            
            # Get session start and end times
            timestamps = [datetime.fromisoformat(event['event_timestamp'].replace('Z', '+00:00')) for event in events.data]
            session_start = min(timestamps)
            session_end = max(timestamps)
            duration = (session_end - session_start).total_seconds()
            
            return {
                'session_id': session_id,
                'event_count': len(events.data),
                'page_views': page_views,
                'conversions': conversions,
                'duration_seconds': duration,
                'events': events.data,
                'start_time': session_start.isoformat(),
                'end_time': session_end.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get session analytics: {e}")
            return None


# Global instance
analytics_service = AnalyticsService()


# Convenience functions for common use cases
def track_page_view(distinct_id: str, url: str, **kwargs):
    """Track a page view event"""
    return analytics_service.track_page_view(distinct_id, url, **kwargs)


def track_user_action(distinct_id: str, action: str, **kwargs):
    """Track a user action event"""
    return analytics_service.track_event(
        event=action,
        distinct_id=distinct_id,
        **kwargs
    )


def track_conversion(distinct_id: str, conversion_type: str, **kwargs):
    """Track a conversion event"""
    return analytics_service.track_conversion(distinct_id, conversion_type, **kwargs)


def identify_user(distinct_id: str, **kwargs):
    """Identify a user"""
    return analytics_service.identify_user(distinct_id, **kwargs)