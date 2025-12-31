from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from ..models.post import Post
from ..models.comment import Comment
from ..models.community import Community
from ..models.user import User
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, db: Session):
        self.db = db

    async def search_posts(
        self, 
        query: str, 
        country: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search posts with full-text search and filtering"""
        try:
            # Build search query with full-text search
            search_query = text("""
                SELECT p.*, 
                       ts_rank_cd(to_tsvector('english', p.title || ' ' || p.content), query) as rank
                FROM posts p
                JOIN communities c ON p.community_id = c.id
                WHERE c.country = :country
                AND (
                    to_tsvector('english', p.title || ' ' || p.content) @@ plainto_tsquery('english', :query)
                    OR p.title ILIKE :like_query
                    OR p.content ILIKE :like_query
                )
                AND p.status = 'published'
                ORDER BY rank DESC, p.created_at DESC
                LIMIT :limit OFFSET :offset
            """)
            
            results = self.db.execute(search_query, {
                'country': country,
                'query': query,
                'like_query': f'%{query}%',
                'limit': limit,
                'offset': offset
            }).fetchall()

            # Get total count for pagination
            count_query = text("""
                SELECT COUNT(*) as total
                FROM posts p
                JOIN communities c ON p.community_id = c.id
                WHERE c.country = :country
                AND (
                    to_tsvector('english', p.title || ' ' || p.content) @@ plainto_tsquery('english', :query)
                    OR p.title ILIKE :like_query
                    OR p.content ILIKE :like_query
                )
                AND p.status = 'published'
            """)
            
            total = self.db.execute(count_query, {
                'country': country,
                'query': query,
                'like_query': f'%{query}%'
            }).scalar()

            return {
                'posts': [dict(row) for row in results],
                'total': total,
                'has_more': offset + limit < total
            }

        except Exception as e:
            logger.error(f"Search posts error: {e}")
            return {'posts': [], 'total': 0, 'has_more': False}

    async def search_comments(
        self, 
        query: str, 
        post_id: Optional[int] = None,
        limit: int = 20, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search comments with full-text search"""
        try:
            base_query = text("""
                SELECT c.*, p.title as post_title
                FROM comments c
                JOIN posts p ON c.post_id = p.id
                WHERE c.status = 'published'
                AND to_tsvector('english', c.content) @@ plainto_tsquery('english', :query)
                AND c.content ILIKE :like_query
            """)
            
            params = {
                'query': query,
                'like_query': f'%{query}%'
            }
            
            if post_id:
                base_query = text(str(base_query) + " AND c.post_id = :post_id")
                params['post_id'] = post_id

            base_query = text(str(base_query) + " ORDER BY c.created_at DESC LIMIT :limit OFFSET :offset")
            params.update({'limit': limit, 'offset': offset})

            results = self.db.execute(base_query, params).fetchall()

            # Get total count
            count_query = text("""
                SELECT COUNT(*) as total
                FROM comments c
                JOIN posts p ON c.post_id = p.id
                WHERE c.status = 'published'
                AND to_tsvector('english', c.content) @@ plainto_tsquery('english', :query)
                AND c.content ILIKE :like_query
            """)
            
            if post_id:
                count_query = text(str(count_query) + " AND c.post_id = :post_id")
            
            total = self.db.execute(count_query, params).scalar()

            return {
                'comments': [dict(row) for row in results],
                'total': total,
                'has_more': offset + limit < total
            }

        except Exception as e:
            logger.error(f"Search comments error: {e}")
            return {'comments': [], 'total': 0, 'has_more': False}

    async def search_communities(
        self, 
        query: str, 
        country: str,
        limit: int = 20, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search communities with full-text search"""
        try:
            search_query = text("""
                SELECT c.*, 
                       COUNT(p.id) as post_count,
                       COUNT(DISTINCT cm.user_id) as member_count
                FROM communities c
                LEFT JOIN posts p ON c.id = p.community_id AND p.status = 'published'
                LEFT JOIN community_members cm ON c.id = cm.community_id
                WHERE c.country = :country
                AND (
                    to_tsvector('english', c.name || ' ' || c.description) @@ plainto_tsquery('english', :query)
                    OR c.name ILIKE :like_query
                    OR c.description ILIKE :like_query
                )
                AND c.is_public = true
                GROUP BY c.id
                ORDER BY post_count DESC, c.created_at DESC
                LIMIT :limit OFFSET :offset
            """)
            
            results = self.db.execute(search_query, {
                'country': country,
                'query': query,
                'like_query': f'%{query}%',
                'limit': limit,
                'offset': offset
            }).fetchall()

            # Get total count
            count_query = text("""
                SELECT COUNT(*) as total
                FROM communities c
                WHERE c.country = :country
                AND (
                    to_tsvector('english', c.name || ' ' || c.description) @@ plainto_tsquery('english', :query)
                    OR c.name ILIKE :like_query
                    OR c.description ILIKE :like_query
                )
                AND c.is_public = true
            """)
            
            total = self.db.execute(count_query, {
                'country': country,
                'query': query,
                'like_query': f'%{query}%'
            }).scalar()

            return {
                'communities': [dict(row) for row in results],
                'total': total,
                'has_more': offset + limit < total
            }

        except Exception as e:
            logger.error(f"Search communities error: {e}")
            return {'communities': [], 'total': 0, 'has_more': False}

    async def get_trending_topics(
        self, 
        country: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get trending topics based on recent activity"""
        try:
            query = text("""
                WITH recent_activity AS (
                    SELECT 
                        p.title,
                        p.content,
                        p.created_at,
                        COUNT(c.id) as comment_count,
                        COUNT(DISTINCT p.user_id) as author_count
                    FROM posts p
                    LEFT JOIN comments c ON p.id = c.post_id
                    JOIN communities com ON p.community_id = com.id
                    WHERE com.country = :country
                    AND p.created_at >= NOW() - INTERVAL '7 days'
                    AND p.status = 'published'
                    GROUP BY p.id, p.title, p.content, p.created_at
                ),
                topic_scores AS (
                    SELECT 
                        title,
                        content,
                        comment_count,
                        author_count,
                        (comment_count * 2 + author_count * 3 + 
                         EXTRACT(EPOCH FROM (NOW() - created_at))/3600) as score
                    FROM recent_activity
                )
                SELECT title, content, comment_count, author_count, score
                FROM topic_scores
                ORDER BY score DESC
                LIMIT :limit
            """)
            
            results = self.db.execute(query, {
                'country': country,
                'limit': limit
            }).fetchall()

            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Get trending topics error: {e}")
            return []

    async def get_search_suggestions(
        self, 
        query: str, 
        country: str,
        limit: int = 5
    ) -> List[str]:
        """Get search suggestions based on popular queries and content"""
        try:
            # Get suggestions from post titles and content
            query = text("""
                SELECT DISTINCT title as suggestion
                FROM posts p
                JOIN communities c ON p.community_id = c.id
                WHERE c.country = :country
                AND p.title ILIKE :like_query
                AND p.status = 'published'
                ORDER BY p.created_at DESC
                LIMIT :limit
                
                UNION
                
                SELECT DISTINCT split_part(lower(regexp_replace(p.content, '[^a-zA-Z0-9 ]', '', 'g')), ' ', 1) as suggestion
                FROM posts p
                JOIN communities c ON p.community_id = c.id
                WHERE c.country = :country
                AND p.content ILIKE :like_query
                AND p.status = 'published'
                AND length(split_part(lower(regexp_replace(p.content, '[^a-zA-Z0-9 ]', '', 'g')), ' ', 1)) > 3
                ORDER BY p.created_at DESC
                LIMIT :limit
            """)
            
            results = self.db.execute(query, {
                'country': country,
                'like_query': f'%{query}%',
                'limit': limit
            }).fetchall()

            suggestions = [row[0] for row in results if row[0] and len(row[0]) > 2]
            return list(dict.fromkeys(suggestions))[:limit]  # Remove duplicates while preserving order

        except Exception as e:
            logger.error(f"Get search suggestions error: {e}")
            return []