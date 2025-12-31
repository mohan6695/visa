from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from ..models.post import Post
from ..models.comment import Comment
from ..models.group_message import GroupMessage
from ..core.config import settings
import logging
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for managing pgvector embeddings and semantic search"""
    
    def __init__(self, db: Session):
        self.db = db
        # Initialize embedding model (can be swapped for different models)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text content"""
        try:
            # Clean and preprocess text
            cleaned_text = self._clean_text(text)
            embedding = self.model.encode(cleaned_text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """Clean text for embedding generation"""
        # Remove excessive whitespace and normalize
        return ' '.join(text.split()[:500])  # Limit to 500 tokens
    
    async def update_post_embeddings(self, post_id: int) -> bool:
        """Update embeddings for a specific post"""
        try:
            # Get post content
            post_query = text("SELECT title, content FROM posts WHERE id = :post_id")
            post_result = self.db.execute(post_query, {'post_id': post_id}).first()
            
            if not post_result:
                return False
            
            # Generate combined embedding for title + content
            combined_text = f"{post_result.title} {post_result.content}"
            embedding = self.generate_embedding(combined_text)
            
            if embedding:
                # Update embedding in database
                update_query = text("""
                    UPDATE posts 
                    SET content_embedding = :embedding::vector
                    WHERE id = :post_id
                """)
                
                self.db.execute(update_query, {
                    'embedding': str(embedding),
                    'post_id': post_id
                })
                self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update post embeddings: {e}")
            self.db.rollback()
            return False
    
    async def update_comment_embeddings(self, comment_id: int) -> bool:
        """Update embeddings for a specific comment"""
        try:
            # Get comment content
            comment_query = text("SELECT content FROM comments WHERE id = :comment_id")
            comment_result = self.db.execute(comment_query, {'comment_id': comment_id}).first()
            
            if not comment_result:
                return False
            
            # Generate embedding for comment content
            embedding = self.generate_embedding(comment_result.content)
            
            if embedding:
                # Update embedding in database
                update_query = text("""
                    UPDATE comments 
                    SET content_embedding = :embedding::vector
                    WHERE id = :comment_id
                """)
                
                self.db.execute(update_query, {
                    'embedding': str(embedding),
                    'comment_id': comment_id
                })
                self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update comment embeddings: {e}")
            self.db.rollback()
            return False
    
    async def update_message_embeddings(self, message_id: int) -> bool:
        """Update embeddings for a specific group message"""
        try:
            # Get message content
            message_query = text("SELECT content FROM group_messages WHERE id = :message_id")
            message_result = self.db.execute(message_query, {'message_id': message_id}).first()
            
            if not message_result:
                return False
            
            # Generate embedding for message content
            embedding = self.generate_embedding(message_result.content)
            
            if embedding:
                # Update embedding in database
                update_query = text("""
                    UPDATE group_messages 
                    SET content_embedding = :embedding::vector
                    WHERE id = :message_id
                """)
                
                self.db.execute(update_query, {
                    'embedding': str(embedding),
                    'message_id': message_id
                })
                self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update message embeddings: {e}")
            self.db.rollback()
            return False
    
    async def semantic_search_posts(
        self, 
        query: str, 
        community_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Semantic search across posts"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            if not query_embedding:
                return []
            
            # Build search query
            base_query = text("""
                SELECT p.id, p.title, p.content, p.author_id, p.community_id, p.created_at,
                       (content_embedding <=> :query_embedding::vector) as distance
                FROM posts p
                WHERE p.status = 'published'
                AND content_embedding IS NOT NULL
            """)
            
            params = {'query_embedding': str(query_embedding)}
            
            # Add community filter if specified
            if community_id:
                base_query = text(str(base_query) + " AND p.community_id = :community_id")
                params['community_id'] = community_id
            
            # Order by similarity and limit results
            search_query = text(str(base_query) + " ORDER BY distance LIMIT :limit")
            params['limit'] = limit
            
            results = self.db.execute(search_query, params).fetchall()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed semantic search on posts: {e}")
            return []
    
    async def semantic_search_comments(
        self, 
        query: str, 
        community_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Semantic search across comments"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            if not query_embedding:
                return []
            
            # Build search query
            base_query = text("""
                SELECT c.id, c.content, c.author_id, c.community_id, c.post_id, c.created_at,
                       (content_embedding <=> :query_embedding::vector) as distance
                FROM comments c
                WHERE c.status = 'published'
                AND content_embedding IS NOT NULL
            """)
            
            params = {'query_embedding': str(query_embedding)}
            
            # Add community filter if specified
            if community_id:
                base_query = text(str(base_query) + " AND c.community_id = :community_id")
                params['community_id'] = community_id
            
            # Order by similarity and limit results
            search_query = text(str(base_query) + " ORDER BY distance LIMIT :limit")
            params['limit'] = limit
            
            results = self.db.execute(search_query, params).fetchall()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed semantic search on comments: {e}")
            return []
    
    async def semantic_search_messages(
        self, 
        query: str, 
        group_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Semantic search across group messages"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            if not query_embedding:
                return []
            
            # Build search query
            search_query = text("""
                SELECT gm.id, gm.content, gm.user_id, gm.group_id, gm.created_at,
                       (content_embedding <=> :query_embedding::vector) as distance
                FROM group_messages gm
                WHERE gm.group_id = :group_id
                AND content_embedding IS NOT NULL
                ORDER BY distance
                LIMIT :limit
            """)
            
            results = self.db.execute(search_query, {
                'query_embedding': str(query_embedding),
                'group_id': group_id,
                'limit': limit
            }).fetchall()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed semantic search on messages: {e}")
            return []
    
    async def hybrid_search(
        self, 
        query: str, 
        community_id: Optional[int] = None,
        group_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Hybrid search combining semantic and keyword search"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            if not query_embedding:
                return []
            
            # Build hybrid search query
            base_query = text("""
                WITH semantic_results AS (
                    SELECT 
                        'post' as type,
                        p.id,
                        p.title as content,
                        p.author_id,
                        p.community_id,
                        p.created_at,
                        (p.content_embedding <=> :query_embedding::vector) as semantic_score,
                        ts_rank(p.search_vector, plainto_tsquery('english', :query)) as keyword_score
                    FROM posts p
                    WHERE p.status = 'published'
                    AND p.content_embedding IS NOT NULL
                    AND (:community_id IS NULL OR p.community_id = :community_id)
                    
                    UNION ALL
                    
                    SELECT 
                        'comment' as type,
                        c.id,
                        c.content,
                        c.author_id,
                        c.community_id,
                        c.created_at,
                        (c.content_embedding <=> :query_embedding::vector) as semantic_score,
                        ts_rank(c.search_vector, plainto_tsquery('english', :query)) as keyword_score
                    FROM comments c
                    WHERE c.status = 'published'
                    AND c.content_embedding IS NOT NULL
                    AND (:community_id IS NULL OR c.community_id = :community_id)
            """)
            
            params = {
                'query_embedding': str(query_embedding),
                'query': query,
                'community_id': community_id
            }
            
            # Add group messages if group_id is provided
            if group_id:
                group_query = text("""
                    UNION ALL
                    
                    SELECT 
                        'message' as type,
                        gm.id,
                        gm.content,
                        gm.user_id as author_id,
                        gm.group_id as community_id,
                        gm.created_at,
                        (gm.content_embedding <=> :query_embedding::vector) as semantic_score,
                        ts_rank(gm.search_vector, plainto_tsquery('english', :query)) as keyword_score
                    FROM group_messages gm
                    WHERE gm.group_id = :group_id
                    AND gm.content_embedding IS NOT NULL
                """)
                base_query = text(str(base_query) + str(group_query))
                params['group_id'] = group_id
            
            # Complete the query with ordering and limiting
            final_query = text(str(base_query) + """
                )
                SELECT * FROM semantic_results
                ORDER BY (semantic_score * 0.7 + keyword_score * 0.3) ASC
                LIMIT :limit
            """)
            params['limit'] = limit
            
            results = self.db.execute(final_query, params).fetchall()
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Failed hybrid search: {e}")
            return []
    
    async def batch_update_embeddings(self, content_type: str, batch_size: int = 100) -> int:
        """Batch update embeddings for all content of a specific type"""
        try:
            updated_count = 0
            
            if content_type == 'posts':
                query = text("SELECT id, title, content FROM posts WHERE content_embedding IS NULL")
                for row in self.db.execute(query).fetchall():
                    combined_text = f"{row.title} {row.content}"
                    embedding = self.generate_embedding(combined_text)
                    
                    if embedding:
                        self.db.execute(text("""
                            UPDATE posts SET content_embedding = :embedding::vector WHERE id = :id
                        """), {'embedding': str(embedding), 'id': row.id})
                        updated_count += 1
                        
                        if updated_count % batch_size == 0:
                            self.db.commit()
            
            elif content_type == 'comments':
                query = text("SELECT id, content FROM comments WHERE content_embedding IS NULL")
                for row in self.db.execute(query).fetchall():
                    embedding = self.generate_embedding(row.content)
                    
                    if embedding:
                        self.db.execute(text("""
                            UPDATE comments SET content_embedding = :embedding::vector WHERE id = :id
                        """), {'embedding': str(embedding), 'id': row.id})
                        updated_count += 1
                        
                        if updated_count % batch_size == 0:
                            self.db.commit()
            
            elif content_type == 'messages':
                query = text("SELECT id, content FROM group_messages WHERE content_embedding IS NULL")
                for row in self.db.execute(query).fetchall():
                    embedding = self.generate_embedding(row.content)
                    
                    if embedding:
                        self.db.execute(text("""
                            UPDATE group_messages SET content_embedding = :embedding::vector WHERE id = :id
                        """), {'embedding': str(embedding), 'id': row.id})
                        updated_count += 1
                        
                        if updated_count % batch_size == 0:
                            self.db.commit()
            
            self.db.commit()
            return updated_count
            
        except Exception as e:
            logger.error(f"Failed batch update embeddings: {e}")
            self.db.rollback()
            return 0