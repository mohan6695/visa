from typing import Dict, Any, Optional, List, Tuple
import logging
import stripe
import json
from datetime import datetime, timedelta
from ..core.config import settings
from supabase import Client

logger = logging.getLogger(__name__)

class StripeService:
    """Service for handling Stripe payment processing and subscriptions"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.stripe_secret_key = settings.stripe_secret_key
        self.stripe_webhook_secret = settings.stripe_webhook_secret
        self.stripe_publishable_key = settings.stripe_publishable_key
        
        # Initialize Stripe
        stripe.api_key = self.stripe_secret_key
        
        # Subscription plans/products
        self.subscription_plans = {
            "premium": {
                "monthly": {
                    "inr": "price_1NxYzABCDEFGHIJKLMNOPQRS",  # Replace with actual price IDs
                    "usd": "price_1NxYzBBCDEFGHIJKLMNOPQRS"
                },
                "yearly": {
                    "inr": "price_1NxYzCBCDEFGHIJKLMNOPQRS",
                    "usd": "price_1NxYzDBCDEFGHIJKLMNOPQRS"
                }
            },
            "group_leader": {
                "monthly": {
                    "inr": "price_1NxYzEBCDEFGHIJKLMNOPQRS",
                    "usd": "price_1NxYzFBCDEFGHIJKLMNOPQRS"
                },
                "yearly": {
                    "inr": "price_1NxYzGBCDEFGHIJKLMNOPQRS",
                    "usd": "price_1NxYzHBCDEFGHIJKLMNOPQRS"
                }
            }
        }
    
    async def create_checkout_session(
        self, 
        user_id: str,
        price_id: str,
        email: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe checkout session for subscription
        
        Args:
            user_id: User ID
            price_id: Stripe Price ID
            email: User email
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment
            
        Returns:
            Dict: Checkout session data
        """
        try:
            # Get user profile
            profile_response = self.supabase.table("profiles").select("*").eq("id", user_id).execute()
            
            if not profile_response.data:
                logger.error(f"Profile not found for user {user_id}")
                return {"error": "User profile not found"}
            
            profile = profile_response.data[0]
            
            # Check if user already has a Stripe customer ID
            customer_id = profile.get("stripe_customer_id")
            
            # Create customer if not exists
            if not customer_id:
                customer = stripe.Customer.create(
                    email=email,
                    metadata={
                        "user_id": user_id
                    }
                )
                customer_id = customer.id
                
                # Update profile with customer ID
                self.supabase.table("profiles").update({
                    "stripe_customer_id": customer_id
                }).eq("id", user_id).execute()
            
            # Create checkout session
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": price_id,
                        "quantity": 1
                    }
                ],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": user_id
                }
            )
            
            return {
                "session_id": checkout_session.id,
                "url": checkout_session.url
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            return {"error": "Failed to create checkout session"}
    
    async def handle_webhook_event(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Handle Stripe webhook events
        
        Args:
            payload: Webhook payload
            signature: Stripe signature
            
        Returns:
            Dict: Result of webhook processing
        """
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, signature, self.stripe_webhook_secret
            )
            
            # Handle different event types
            event_type = event["type"]
            
            if event_type == "checkout.session.completed":
                return await self._handle_checkout_completed(event)
            elif event_type == "customer.subscription.created":
                return await self._handle_subscription_created(event)
            elif event_type == "customer.subscription.updated":
                return await self._handle_subscription_updated(event)
            elif event_type == "customer.subscription.deleted":
                return await self._handle_subscription_deleted(event)
            elif event_type == "invoice.payment_succeeded":
                return await self._handle_invoice_payment_succeeded(event)
            elif event_type == "invoice.payment_failed":
                return await self._handle_invoice_payment_failed(event)
            else:
                logger.info(f"Unhandled event type: {event_type}")
                return {"status": "ignored", "event_type": event_type}
                
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {str(e)}")
            return {"error": "Invalid signature"}
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            return {"error": f"Webhook error: {str(e)}"}
    
    async def _handle_checkout_completed(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle checkout.session.completed event"""
        try:
            session = event["data"]["object"]
            user_id = session["metadata"].get("user_id")
            
            if not user_id:
                logger.error("User ID not found in session metadata")
                return {"error": "User ID not found"}
            
            # Get subscription details
            subscription_id = session.get("subscription")
            if not subscription_id:
                logger.error("Subscription ID not found in session")
                return {"error": "Subscription ID not found"}
            
            # Update user profile with subscription info
            await self._update_user_subscription(user_id, subscription_id)
            
            return {
                "status": "success",
                "user_id": user_id,
                "subscription_id": subscription_id
            }
            
        except Exception as e:
            logger.error(f"Error handling checkout completed: {str(e)}")
            return {"error": str(e)}
    
    async def _handle_subscription_created(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.subscription.created event"""
        try:
            subscription = event["data"]["object"]
            customer_id = subscription["customer"]
            
            # Find user by customer ID
            profile_response = self.supabase.table("profiles").select("id").eq("stripe_customer_id", customer_id).execute()
            
            if not profile_response.data:
                logger.error(f"User not found for customer {customer_id}")
                return {"error": "User not found"}
            
            user_id = profile_response.data[0]["id"]
            
            # Update user subscription
            await self._update_user_subscription(user_id, subscription["id"])
            
            return {
                "status": "success",
                "user_id": user_id,
                "subscription_id": subscription["id"]
            }
            
        except Exception as e:
            logger.error(f"Error handling subscription created: {str(e)}")
            return {"error": str(e)}
    
    async def _handle_subscription_updated(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.subscription.updated event"""
        try:
            subscription = event["data"]["object"]
            customer_id = subscription["customer"]
            
            # Find user by customer ID
            profile_response = self.supabase.table("profiles").select("id").eq("stripe_customer_id", customer_id).execute()
            
            if not profile_response.data:
                logger.error(f"User not found for customer {customer_id}")
                return {"error": "User not found"}
            
            user_id = profile_response.data[0]["id"]
            
            # Update user subscription
            await self._update_user_subscription(user_id, subscription["id"])
            
            return {
                "status": "success",
                "user_id": user_id,
                "subscription_id": subscription["id"]
            }
            
        except Exception as e:
            logger.error(f"Error handling subscription updated: {str(e)}")
            return {"error": str(e)}
    
    async def _handle_subscription_deleted(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.subscription.deleted event"""
        try:
            subscription = event["data"]["object"]
            customer_id = subscription["customer"]
            
            # Find user by customer ID
            profile_response = self.supabase.table("profiles").select("id").eq("stripe_customer_id", customer_id).execute()
            
            if not profile_response.data:
                logger.error(f"User not found for customer {customer_id}")
                return {"error": "User not found"}
            
            user_id = profile_response.data[0]["id"]
            
            # Update user profile to remove premium status
            self.supabase.table("profiles").update({
                "is_premium": False,
                "subscription_tier": "free",
                "stripe_subscription_id": None,
                "subscription_ends_at": None
            }).eq("id", user_id).execute()
            
            return {
                "status": "success",
                "user_id": user_id,
                "subscription_id": subscription["id"]
            }
            
        except Exception as e:
            logger.error(f"Error handling subscription deleted: {str(e)}")
            return {"error": str(e)}
    
    async def _handle_invoice_payment_succeeded(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice.payment_succeeded event"""
        try:
            invoice = event["data"]["object"]
            customer_id = invoice["customer"]
            subscription_id = invoice.get("subscription")
            
            if not subscription_id:
                logger.info("No subscription associated with this invoice")
                return {"status": "ignored"}
            
            # Find user by customer ID
            profile_response = self.supabase.table("profiles").select("id").eq("stripe_customer_id", customer_id).execute()
            
            if not profile_response.data:
                logger.error(f"User not found for customer {customer_id}")
                return {"error": "User not found"}
            
            user_id = profile_response.data[0]["id"]
            
            # Update subscription end date
            await self._update_user_subscription(user_id, subscription_id)
            
            return {
                "status": "success",
                "user_id": user_id,
                "subscription_id": subscription_id
            }
            
        except Exception as e:
            logger.error(f"Error handling invoice payment succeeded: {str(e)}")
            return {"error": str(e)}
    
    async def _handle_invoice_payment_failed(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice.payment_failed event"""
        try:
            invoice = event["data"]["object"]
            customer_id = invoice["customer"]
            subscription_id = invoice.get("subscription")
            
            if not subscription_id:
                logger.info("No subscription associated with this invoice")
                return {"status": "ignored"}
            
            # Find user by customer ID
            profile_response = self.supabase.table("profiles").select("id").eq("stripe_customer_id", customer_id).execute()
            
            if not profile_response.data:
                logger.error(f"User not found for customer {customer_id}")
                return {"error": "User not found"}
            
            user_id = profile_response.data[0]["id"]
            
            # Get subscription status
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # If subscription is past_due or unpaid, update user status
            if subscription.status in ["past_due", "unpaid"]:
                self.supabase.table("profiles").update({
                    "is_premium": False,
                    "subscription_tier": "free"
                }).eq("id", user_id).execute()
            
            return {
                "status": "success",
                "user_id": user_id,
                "subscription_id": subscription_id,
                "subscription_status": subscription.status
            }
            
        except Exception as e:
            logger.error(f"Error handling invoice payment failed: {str(e)}")
            return {"error": str(e)}
    
    async def _update_user_subscription(self, user_id: str, subscription_id: str) -> bool:
        """
        Update user subscription status and details
        
        Args:
            user_id: User ID
            subscription_id: Stripe Subscription ID
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Get subscription details from Stripe
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Check subscription status
            is_active = subscription.status in ["active", "trialing"]
            
            # Get subscription tier from product
            product_id = subscription.items.data[0].price.product
            product = stripe.Product.retrieve(product_id)
            tier = product.metadata.get("tier", "premium")
            
            # Calculate subscription end date
            current_period_end = subscription.current_period_end
            ends_at = datetime.fromtimestamp(current_period_end).isoformat()
            
            # Update user profile
            self.supabase.table("profiles").update({
                "is_premium": is_active,
                "stripe_subscription_id": subscription_id,
                "subscription_tier": tier if is_active else "free",
                "subscription_ends_at": ends_at if is_active else None
            }).eq("id", user_id).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating user subscription: {str(e)}")
            return False
    
    async def get_subscription_plans(self, currency: str = "usd") -> List[Dict[str, Any]]:
        """
        Get available subscription plans
        
        Args:
            currency: Currency code (usd or inr)
            
        Returns:
            List[Dict]: List of subscription plans
        """
        try:
            currency = currency.lower()
            if currency not in ["usd", "inr"]:
                currency = "usd"  # Default to USD
            
            plans = []
            
            # Get premium plans
            premium_monthly = stripe.Price.retrieve(self.subscription_plans["premium"]["monthly"][currency])
            premium_yearly = stripe.Price.retrieve(self.subscription_plans["premium"]["yearly"][currency])
            
            plans.append({
                "id": premium_monthly.id,
                "name": "Premium Monthly",
                "description": "Unlimited posts, cross-group search, ad-free experience",
                "price": premium_monthly.unit_amount / 100,
                "currency": premium_monthly.currency.upper(),
                "interval": "month",
                "tier": "premium"
            })
            
            plans.append({
                "id": premium_yearly.id,
                "name": "Premium Yearly",
                "description": "Unlimited posts, cross-group search, ad-free experience",
                "price": premium_yearly.unit_amount / 100,
                "currency": premium_yearly.currency.upper(),
                "interval": "year",
                "tier": "premium"
            })
            
            # Get group leader plans
            group_leader_monthly = stripe.Price.retrieve(self.subscription_plans["group_leader"]["monthly"][currency])
            group_leader_yearly = stripe.Price.retrieve(self.subscription_plans["group_leader"]["yearly"][currency])
            
            plans.append({
                "id": group_leader_monthly.id,
                "name": "Group Leader Monthly",
                "description": "Premium features plus advanced analytics and featured placement",
                "price": group_leader_monthly.unit_amount / 100,
                "currency": group_leader_monthly.currency.upper(),
                "interval": "month",
                "tier": "group_leader"
            })
            
            plans.append({
                "id": group_leader_yearly.id,
                "name": "Group Leader Yearly",
                "description": "Premium features plus advanced analytics and featured placement",
                "price": group_leader_yearly.unit_amount / 100,
                "currency": group_leader_yearly.currency.upper(),
                "interval": "year",
                "tier": "group_leader"
            })
            
            return plans
            
        except Exception as e:
            logger.error(f"Error getting subscription plans: {str(e)}")
            return []
    
    async def cancel_subscription(self, user_id: str) -> Dict[str, Any]:
        """
        Cancel user subscription
        
        Args:
            user_id: User ID
            
        Returns:
            Dict: Result of cancellation
        """
        try:
            # Get user profile
            profile_response = self.supabase.table("profiles").select("*").eq("id", user_id).execute()
            
            if not profile_response.data:
                logger.error(f"Profile not found for user {user_id}")
                return {"error": "User profile not found"}
            
            profile = profile_response.data[0]
            
            # Check if user has an active subscription
            subscription_id = profile.get("stripe_subscription_id")
            if not subscription_id:
                return {"error": "No active subscription found"}
            
            # Cancel subscription
            subscription = stripe.Subscription.delete(subscription_id)
            
            # Update user profile
            self.supabase.table("profiles").update({
                "is_premium": False,
                "subscription_tier": "free",
                "stripe_subscription_id": None,
                "subscription_ends_at": None
            }).eq("id", user_id).execute()
            
            return {
                "status": "success",
                "message": "Subscription cancelled successfully"
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            return {"error": "Failed to cancel subscription"}
    
    async def get_subscription_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get user subscription status
        
        Args:
            user_id: User ID
            
        Returns:
            Dict: Subscription status
        """
        try:
            # Get user profile
            profile_response = self.supabase.table("profiles").select("*").eq("id", user_id).execute()
            
            if not profile_response.data:
                logger.error(f"Profile not found for user {user_id}")
                return {"error": "User profile not found"}
            
            profile = profile_response.data[0]
            
            # Check if user has an active subscription
            is_premium = profile.get("is_premium", False)
            subscription_id = profile.get("stripe_subscription_id")
            subscription_tier = profile.get("subscription_tier", "free")
            subscription_ends_at = profile.get("subscription_ends_at")
            
            if not is_premium or not subscription_id:
                return {
                    "is_premium": False,
                    "tier": "free",
                    "status": "inactive"
                }
            
            # Get subscription details from Stripe
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            return {
                "is_premium": is_premium,
                "tier": subscription_tier,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start).isoformat(),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end).isoformat(),
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error getting subscription status: {str(e)}")
            return {"error": "Failed to get subscription status"}