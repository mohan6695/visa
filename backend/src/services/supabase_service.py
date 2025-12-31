from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from ..core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

class SupabaseService:
    """Service for Supabase Realtime and database operations"""
    
    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError("Supabase URL and Key must be configured")
        
        self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    async def subscribe_to_group(self, group_id: int, callback):
        """Subscribe to group messages via Supabase Realtime"""
        try:
            channel = self.supabase.channel(f"group:{group_id}")
            
            channel.on(
                'postgres_changes',
                {
                    'event': 'INSERT',
                    'schema': 'public',
                    'table': 'group_messages',
                    'filter': f'group_id=eq.{group_id}'
                },
                callback
            )
            
            await channel.subscribe()
            return channel
            
        except Exception as e:
            logger.error(f"Failed to subscribe to group {group_id}: {e}")
            return None
    
    async def unsubscribe_from_group(self, channel):
        """Unsubscribe from group messages"""
        try:
            if channel:
                await self.supabase.removeChannel(channel)
        except Exception as e:
            logger.error(f"Failed to unsubscribe from channel: {e}")
    
    async def send_group_message(self, group_id: int, user_id: int, content: str, message_type: str = 'text') -> Optional[Dict[str, Any]]:
        """Send a message to a group using Supabase"""
        try:
            data = {
                'group_id': group_id,
                'user_id': user_id,
                'content': content,
                'message_type': message_type
            }
            
            result = self.supabase.table('group_messages').insert(data).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to send group message: {e}")
            return None
    
    async def get_group_history(self, group_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get message history for a group"""
        try:
            result = self.supabase.table('group_messages').select(
                '*'
            ).eq('group_id', group_id).order(
                'created_at', desc=True
            ).range(offset, offset + limit - 1).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Failed to get group history: {e}")
            return []
    
    async def mark_message_read(self, user_id: int, group_id: int, message_id: int) -> bool:
        """Mark a message as read"""
        try:
            data = {
                'user_id': user_id,
                'group_id': group_id,
                'message_id': message_id
            }
            
            self.supabase.table('message_read_receipts').upsert(data).execute()
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark message as read: {e}")
            return False
    
    async def get_unread_count(self, user_id: int, group_id: int) -> int:
        """Get unread message count for a user in a group"""
        try:
            # Get the latest read message for this user in this group
            latest_read = self.supabase.table('message_read_receipts').select(
                'message_id'
            ).eq('user_id', user_id).eq('group_id', group_id).order(
                'read_at', desc=True
            ).limit(1).execute()
            
            if not latest_read.data:
                return 0
            
            latest_message_id = latest_read.data[0]['message_id']
            
            # Count messages after the latest read message
            count_result = self.supabase.table('group_messages').select(
                'id', count='exact'
            ).eq('group_id', group_id).gt('id', latest_message_id).execute()
            
            return count_result.count or 0
            
        except Exception as e:
            logger.error(f"Failed to get unread count: {e}")
            return 0
    
    async def get_online_users(self, group_id: int) -> List[int]:
        """Get list of online users in a group"""
        try:
            result = self.supabase.table('user_presence').select(
                'user_id'
            ).eq('group_id', group_id).gt(
                'last_seen', 'NOW() - INTERVAL 5 minutes'
            ).execute()
            
            return [row['user_id'] for row in result.data] if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get online users: {e}")
            return []
    
    async def update_user_presence(self, user_id: int, group_id: int) -> bool:
        """Update user presence in a group"""
        try:
            data = {
                'user_id': user_id,
                'group_id': group_id,
                'last_seen': 'NOW()'
            }
            
            self.supabase.table('user_presence').upsert(data).execute()
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user presence: {e}")
            return False
    
    async def search_messages(self, group_id: int, query: str, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Search messages in a group using Supabase full-text search"""
        try:
            # Use Supabase's full-text search capabilities
            result = self.supabase.table('group_messages').select(
                '*'
            ).eq('group_id', group_id).text_search(
                'content', query, config='english', type='plain'
            ).order('created_at', desc=True).range(offset, offset + limit - 1).execute()
            
            # Get total count
            count_result = self.supabase.table('group_messages').select(
                'id', count='exact'
            ).eq('group_id', group_id).text_search(
                'content', query, config='english', type='plain'
            ).execute()
            
            return {
                'messages': result.data or [],
                'total': count_result.count or 0,
                'has_more': offset + limit < (count_result.count or 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to search messages: {e}")
            return {'messages': [], 'total': 0, 'has_more': False}