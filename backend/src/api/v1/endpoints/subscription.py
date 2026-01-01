from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header, Body
from pydantic import BaseModel, Field
import logging
from supabase import Client
from ....services.stripe_service import StripeService
from ....services.supabase_auth_service import SupabaseAuthService, get_auth_service
from ....core.config import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscription", tags=["Subscription"])

# Pydantic models for request validation
class CheckoutRequest(BaseModel):
    price_id: str
    success_url: str = Field(..., min_length=1)
    cancel_url: str = Field(..., min_length=1)
    currency: str = "usd"

class SubscriptionResponse(BaseModel):
    session_id: str
    url: str

class SubscriptionStatusResponse(BaseModel):
    is_premium: bool
    tier: str
    status: str
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: Optional[bool] = None

# Dependency to get Stripe service
async def get_stripe_service(
    supabase: Client = Depends(get_supabase_client)
) -> StripeService:
    return StripeService(supabase)

@router.post("/create-checkout", response_model=SubscriptionResponse)
async def create_checkout_session(
    checkout_data: CheckoutRequest,
    request: Request,
    stripe_service: StripeService = Depends(get_stripe_service),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """
    Create a Stripe checkout session for subscription
    """
    try:
        # Get user from request state
        user = request.state.user
        user_id = user.get("sub")
        
        # Get user email
        profile = await auth_service.get_user_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        email = user.get("email", "")
        
        # Create checkout session
        result = await stripe_service.create_checkout_session(
            user_id=user_id,
            price_id=checkout_data.price_id,
            email=email,
            success_url=checkout_data.success_url,
            cancel_url=checkout_data.cancel_url
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """
    Handle Stripe webhook events
    """
    try:
        # Read request body
        payload = await request.body()
        
        # Handle webhook event
        result = await stripe_service.handle_webhook_event(payload, stripe_signature)
        
        if "error" in result:
            logger.error(f"Webhook error: {result['error']}")
            return {"status": "error", "message": result["error"]}
        
        return {"status": "success", "event_handled": result}
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.get("/plans")
async def get_subscription_plans(
    currency: str = "usd",
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """
    Get available subscription plans
    """
    try:
        plans = await stripe_service.get_subscription_plans(currency)
        return {"plans": plans}
    except Exception as e:
        logger.error(f"Error getting subscription plans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subscription plans: {str(e)}"
        )

@router.get("/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    request: Request,
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """
    Get user subscription status
    """
    try:
        # Get user from request state
        user = request.state.user
        user_id = user.get("sub")
        
        # Get subscription status
        result = await stripe_service.get_subscription_status(user_id)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subscription status: {str(e)}"
        )

@router.post("/cancel")
async def cancel_subscription(
    request: Request,
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """
    Cancel user subscription
    """
    try:
        # Get user from request state
        user = request.state.user
        user_id = user.get("sub")
        
        # Cancel subscription
        result = await stripe_service.cancel_subscription(user_id)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel subscription: {str(e)}"
        )