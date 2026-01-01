from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from pydantic import BaseModel, Field
import logging
from datetime import datetime, timedelta
from supabase import Client
from ....services.analytics_service import AnalyticsService
from ....services.supabase_auth_service import SupabaseAuthService, get_auth_service
from ....core.config import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Pydantic models for request validation
class EventTrackRequest(BaseModel):
    event_type: str
    properties: Optional[Dict[str, Any]] = None

class DateRangeRequest(BaseModel):
    start_date: str
    end_date: str
    group_by: Optional[str] = "event"

class AnalyticsResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None

# Dependency to get AnalyticsService
async def get_analytics_service(
    supabase: Client = Depends(get_supabase_client)
) -> AnalyticsService:
    return AnalyticsService(supabase)

@router.post("/track", response_model=AnalyticsResponse)
async def track_event(
    event_data: EventTrackRequest,
    request: Request,
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """
    Track an analytics event
    """
    try:
        # Get user from request state
        user = request.state.user
        user_id = user.get("sub") if user else None
        
        # Get client IP
        client_ip = request.client.host if request.client else None
        
        # Track event
        success = await analytics_service.track_event(
            event_type=event_data.event_type,
            user_id=user_id,
            properties=event_data.properties,
            ip_address=client_ip,
            store_locally=True
        )
        
        if not success:
            return {
                "success": False,
                "data": {},
                "error": "Failed to track event"
            }
        
        return {
            "success": True,
            "data": {
                "event_type": event_data.event_type,
                "tracked_at": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error tracking event: {str(e)}")
        return {
            "success": False,
            "data": {},
            "error": str(e)
        }

@router.get("/dashboard", response_model=AnalyticsResponse)
async def get_dashboard_data(
    request: Request,
    period: str = Query("week", description="Time period (day, week, month)"),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """
    Get analytics dashboard data
    """
    try:
        # Check if user is admin
        user = request.state.user
        if user.get("role") not in ["admin", "service_role"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Calculate date range based on period
        now = datetime.utcnow()
        
        if period == "day":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == "week":
            # Start of current week (Monday)
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == "month":
            # Start of current month
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid period. Must be one of: day, week, month"
            )
        
        # Format dates
        start_date_str = start_date.isoformat()
        end_date_str = end_date.isoformat()
        
        # Get event counts
        event_counts = await analytics_service.get_event_counts(
            start_date=start_date_str,
            end_date=end_date_str,
            group_by="event"
        )
        
        # Get active users
        active_users = await analytics_service.get_active_users(period=period)
        
        # Get premium conversion rate
        premium_conversion = await analytics_service.get_premium_conversion_rate(
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        # Get search analytics
        search_analytics = await analytics_service.get_search_analytics(
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        # Get AI analytics
        ai_analytics = await analytics_service.get_ai_analytics(
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        # Combine all data
        dashboard_data = {
            "period": period,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "event_counts": event_counts,
            "active_users": active_users,
            "premium_conversion": premium_conversion,
            "search_analytics": search_analytics,
            "ai_analytics": ai_analytics
        }
        
        return {
            "success": True,
            "data": dashboard_data
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        return {
            "success": False,
            "data": {},
            "error": str(e)
        }

@router.get("/user/{user_id}", response_model=AnalyticsResponse)
async def get_user_analytics(
    user_id: str,
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """
    Get analytics for a specific user
    """
    try:
        # Check if user is admin or the user themselves
        request_user = request.state.user
        if request_user.get("role") not in ["admin", "service_role"] and request_user.get("sub") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get user activity
        user_activity = await analytics_service.get_user_activity(
            user_id=user_id,
            limit=limit
        )
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "activity": user_activity
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting user analytics: {str(e)}")
        return {
            "success": False,
            "data": {},
            "error": str(e)
        }

@router.get("/group/{group_id}", response_model=AnalyticsResponse)
async def get_group_analytics(
    group_id: str,
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """
    Get analytics for a specific group
    """
    try:
        # Check if user is admin or group leader
        user = request.state.user
        
        # Check if user is admin
        is_admin = user.get("role") in ["admin", "service_role"]
        
        # Check if user is group leader
        is_group_leader = False
        if not is_admin:
            profile = await auth_service.get_user_profile(user.get("sub"))
            is_group_leader = (
                profile and 
                profile.get("group_id") == group_id and 
                profile.get("subscription_tier") == "group_leader"
            )
        
        if not (is_admin or is_group_leader):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get group activity
        group_activity = await analytics_service.get_group_activity(
            group_id=group_id,
            limit=limit
        )
        
        return {
            "success": True,
            "data": {
                "group_id": group_id,
                "activity": group_activity
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error getting group analytics: {str(e)}")
        return {
            "success": False,
            "data": {},
            "error": str(e)
        }