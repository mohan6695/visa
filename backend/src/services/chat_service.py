from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_, or_
from ..models.post import Post
from ..models.comment import Comment
from ..models.community import Community
from ..models.user import User
from ..models.notification import Notification
from ..core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, db: Session):
        self.db = db

    async def get_chat_history(
        self, 
        community_id: int, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get chat history for a community"""
        try:
            query = text("""
                SELECT c.*, u.username, u.avatar_url
                FROM comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.community_id = :community_id
                AND c.is_chat_message = true
                AND c.status = 'published'
                ORDER BY c.created_at DESC
                LIMIT :limit OFFSET :offset
            """)
            
            results = self.db.execute(query, {
                'community_id': community_id,
                'limit': limit,
                'offset': offset
            }).fetchall()

            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Get chat history error: {e}")
            return []

    async def send_chat_message(
        self, 
        community_id: int,
        user_id: int,
        content: str,
        message_type: str = 'text'
    ) -> Optional[Dict[str, Any]]:
        """Send a chat message to a community"""
        try:
            # Create chat message
            chat_message = Comment(
                community_id=community_id,
                user_id=user_id,
                content=content,
                is_chat_message=True,
                message_type=message_type,
                status='published'
            )
            
            self.db.add(chat_message)
            self.db.flush()  # Get the ID
            
            # Get user info for response
            user_query = text("SELECT username, avatar_url FROM users WHERE id = :user_id")
            user_result = self.db.execute(user_query, {'user_id': user_id}).first()
            
            response = {
                'id': chat_message.id,
                'community_id': community_id,
                'user_id': user_id,
                'username': user_result.username if user_result else 'Unknown',
                'avatar_url': user_result.avatar_url if user_result else None,
                'content': content,
                'message_type': message_type,
                'created_at': chat_message.created_at.isoformat(),
                'is_chat_message': True
            }
            
            self.db.commit()
            return response

        except Exception as e:
            self.db.rollback()
            logger.error(f"Send chat message error: {e}")
            return None

    async def get_community_members(
        self, 
        community_id: int,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get active members in a community"""
        try:
            query = text("""
                SELECT DISTINCT u.id, u.username, u.avatar_url, u.last_seen
                FROM users u
                JOIN community_members cm ON u.id = cm.user_id
                WHERE cm.community_id = :community_id
                AND u.last_seen >= NOW() - INTERVAL '24 hours'
                ORDER BY u.last_seen DESC
                LIMIT :limit
            """)
            
            results = self.db.execute(query, {
                'community_id': community_id,
                'limit': limit
            }).fetchall()

            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Get community members error: {e}")
            return []

    async def get_online_status(self, user_ids: List[int]) -> Dict[int, bool]:
        """Get online status for multiple users"""
        try:
            if not user_ids:
                return {}
            
            query = text("""
                SELECT id, last_seen >= NOW() - INTERVAL '5 minutes' as is_online
                FROM users
                WHERE id = ANY(:user_ids)
            """)
            
            results = self.db.execute(query, {'user_ids': user_ids}).fetchall()
            
            return {row.id: row.is_online for row in results}

        except Exception as e:
            logger.error(f"Get online status error: {e}")
            return {}

    async def mark_message_read(
        self, 
        user_id: int,
        community_id: int,
        message_id: int
    ) -> bool:
        """Mark a message as read by a user"""
        try:
            # This would typically update a read receipts table
            # For now, we'll just log it
            logger.info(f"User {user_id} read message {message_id} in community {community_id}")
            return True

        except Exception as e:
            logger.error(f"Mark message read error: {e}")
            return False

    async def get_unread_count(
        self, 
        user_id: int,
        community_id: int
    ) -> int:
        """Get unread message count for a user in a community"""
        try:
            # This would typically query a read receipts table
            # For now, we'll return a simple count of recent messages
            query = text("""
                SELECT COUNT(*) as unread_count
                FROM comments c
                WHERE c.community_id = :community_id
                AND c.is_chat_message = true
                AND c.status = 'published'
                AND c.created_at >= NOW() - INTERVAL '1 hour'
                AND c.user_id != :user_id
            """)
            
            result = self.db.execute(query, {
                'community_id': community_id,
                'user_id': user_id
            }).scalar()

            return result or 0

        except Exception as e:
            logger.error(f"Get unread count error: {e}")
            return 0

    async def search_chat_messages(
        self, 
        community_id: int,
        query: str,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search chat messages in a community"""
        try:
            search_query = text("""
                SELECT c.*, u.username, u.avatar_url
                FROM comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.community_id = :community_id
                AND c.is_chat_message = true
                AND c.status = 'published'
                AND (
                    to_tsvector('english', c.content) @@ plainto_tsquery('english', :query)
                    OR c.content ILIKE :like_query
                )
                ORDER BY c.created_at DESC
                LIMIT :limit OFFSET :offset
            """)
            
            results = self.db.execute(search_query, {
                'community_id': community_id,
                'query': query,
                'like_query': f'%{query}%',
                'limit': limit,
                'offset': offset
            }).fetchall()

            # Get total count
            count_query = text("""
                SELECT COUNT(*) as total
                FROM comments c
                WHERE c.community_id = :community_id
                AND c.is_chat_message = true
                AND c.status = 'published'
                AND (
                    to_tsvector('english', c.content) @@ plainto_tsquery('english', :query)
                    OR c.content ILIKE :like_query
                )
            """)
            
            total = self.db.execute(count_query, {
                'community_id': community_id,
                'query': query,
                'like_query': f'%{query}%'
            }).scalar()

            return {
                'messages': [dict(row) for row in results],
                'total': total,
                'has_more': offset + limit < total
            }

        except Exception as e:
            logger.error(f"Search chat messages error: {e}")
            return {'messages': [], 'total': 0, 'has_more': False}

    async def get_recent_activity(
        self, 
        community_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent activity in a community (posts, comments, new members)"""
        try:
            # Get recent posts
            posts_query = text("""
                SELECT 'post' as type, p.title as content, p.created_at, u.username
                FROM posts p
                JOIN users u ON p.user_id = u.id
                WHERE p.community_id = :community_id
                AND p.status = 'published'
                ORDER BY p.created_at DESC
                LIMIT :limit
            """)
            
            posts = self.db.execute(posts_query, {
                'community_id': community_id,
                'limit': limit // 3
            }).fetchall()

            # Get recent comments
            comments_query = text("""
                SELECT 'comment' as type, c.content, c.created_at, u.username
                FROM comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.community_id = :community_id
                AND c.status = 'published'
                ORDER BY c.created_at DESC
                LIMIT :limit
            """)
            
            comments = self.db.execute(comments_query, {
                'community_id': community_id,
                'limit': limit // 3
            }).fetchall()

            # Get new members
            members_query = text("""
                SELECT 'member' as type, 'joined community' as content, cm.created_at, u.username
                FROM community_members cm
                JOIN users u ON cm.user_id = u.id
                WHERE cm.community_id = :community_id
                ORDER BY cm.created_at DESC
                LIMIT :limit
            """)
            
            members = self.db.execute(members_query, {
                'community_id': community_id,
                'limit': limit // 3
            }).fetchall()

            # Combine and sort by date
            activity = []
            activity.extend([dict(row) for row in posts])
            activity.extend([dict(row) for row in comments])
            activity.extend([dict(row) for row in members])
            
            activity.sort(key=lambda x: x['created_at'], reverse=True)
            
            return activity[:limit]

        except Exception as e:
            logger.error(f"Get recent activity error: {e}")
            return []