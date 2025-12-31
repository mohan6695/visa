from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from supabase import create_client, Client
from ..dependencies import get_db, get_current_user
from ...models.user import User
from ...core.config import settings
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

@router.post("/supabase/posts")
async def get_supabase_posts(
    category: Optional[str] = Query(None, description="Post category filter"),
    sort: str = Query("newest", regex="^(newest|oldest|popular)$", description="Sort order"),
    search: Optional[str] = Query(None, min_length=2, max_length=100, description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Number of posts to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    country: Optional[str] = Query(None, description="Country filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get posts from Supabase bucket 'recent_h1b_posts'"""
    try:
        supabase = get_supabase_client()
        
        # Build query
        query = supabase.table('recent_h1b_posts').select('*')
        
        # Apply filters
        if category:
            query = query.eq('category', category)
        
        if country:
            query = query.eq('country', country)
        
        if search:
            # Use full-text search if available, otherwise use ilike
            try:
                query = query.text_search('content', search, config='english', type='plain')
            except:
                # Fallback to ilike search
                query = query.ilike('content', f'%{search}%')
        
        # Apply sorting
        if sort == "newest":
            query = query.order('created_at', desc=True)
        elif sort == "oldest":
            query = query.order('created_at', desc=False)
        elif sort == "popular":
            query = query.order('like_count', desc=True)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Execute query
        result = query.execute()
        
        if result.data:
            posts = []
            for post_data in result.data:
                post = {
                    'id': post_data.get('id'),
                    'title': post_data.get('title', ''),
                    'content': post_data.get('content', ''),
                    'author': {
                        'id': post_data.get('author_id'),
                        'name': post_data.get('author_name', 'Unknown'),
                        'avatar_url': post_data.get('author_avatar_url')
                    },
                    'community': {
                        'id': post_data.get('community_id'),
                        'name': post_data.get('community_name', 'General'),
                        'slug': post_data.get('community_slug')
                    },
                    'category': post_data.get('category', ''),
                    'status': post_data.get('status', 'published'),
                    'like_count': post_data.get('like_count', 0),
                    'comment_count': post_data.get('comment_count', 0),
                    'view_count': post_data.get('view_count', 0),
                    'created_at': post_data.get('created_at'),
                    'updated_at': post_data.get('updated_at'),
                    'tags': post_data.get('tags', []),
                    'is_pinned': post_data.get('is_pinned', False),
                    'is_locked': post_data.get('is_locked', False)
                }
                posts.append(post)
            
            return {
                "success": True,
                "posts": posts,
                "total": len(posts),
                "has_more": len(posts) == limit
            }
        else:
            return {
                "success": True,
                "posts": [],
                "total": 0,
                "has_more": False
            }
            
    except Exception as e:
        logger.error(f"Failed to get Supabase posts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch posts from Supabase")

@router.get("/supabase/posts/{post_id}")
async def get_supabase_post_by_id(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific post from Supabase by ID"""
    try:
        supabase = get_supabase_client()
        
        result = supabase.table('recent_h1b_posts').select('*').eq('id', post_id).single().execute()
        
        if result.data:
            post_data = result.data
            post = {
                'id': post_data.get('id'),
                'title': post_data.get('title', ''),
                'content': post_data.get('content', ''),
                'content_html': post_data.get('content_html', ''),
                'author': {
                    'id': post_data.get('author_id'),
                    'name': post_data.get('author_name', 'Unknown'),
                    'avatar_url': post_data.get('author_avatar_url'),
                    'bio': post_data.get('author_bio')
                },
                'community': {
                    'id': post_data.get('community_id'),
                    'name': post_data.get('community_name', 'General'),
                    'slug': post_data.get('community_slug'),
                    'description': post_data.get('community_description')
                },
                'category': post_data.get('category', ''),
                'status': post_data.get('status', 'published'),
                'like_count': post_data.get('like_count', 0),
                'comment_count': post_data.get('comment_count', 0),
                'view_count': post_data.get('view_count', 0),
                'created_at': post_data.get('created_at'),
                'updated_at': post_data.get('updated_at'),
                'tags': post_data.get('tags', []),
                'is_pinned': post_data.get('is_pinned', False),
                'is_locked': post_data.get('is_locked', False),
                'search_vector': post_data.get('search_vector'),
                'content_embedding': post_data.get('content_embedding')
            }
            
            # Get comments for this post
            comments_result = supabase.table('comments').select('*').eq('post_id', post_id).order('created_at', desc=True).limit(10).execute()
            
            comments = []
            if comments_result.data:
                for comment_data in comments_result.data:
                    comment = {
                        'id': comment_data.get('id'),
                        'content': comment_data.get('content', ''),
                        'author': {
                            'id': comment_data.get('author_id'),
                            'name': comment_data.get('author_name', 'Unknown'),
                            'avatar_url': comment_data.get('author_avatar_url')
                        },
                        'created_at': comment_data.get('created_at'),
                        'like_count': comment_data.get('like_count', 0),
                        'is_reply': comment_data.get('parent_id') is not None
                    }
                    comments.append(comment)
            
            return {
                "success": True,
                "post": post,
                "comments": comments,
                "comment_count": len(comments)
            }
        else:
            raise HTTPException(status_code=404, detail="Post not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get Supabase post: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch post from Supabase")

@router.post("/supabase/posts/similar")
async def get_similar_supabase_posts(
    post_id: int = Query(..., description="Post ID to find similar posts for"),
    limit: int = Query(5, ge=1, le=20, description="Number of similar posts to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get similar posts using semantic search"""
    try:
        supabase = get_supabase_client()
        
        # First get the target post to get its embedding
        target_post_result = supabase.table('recent_h1b_posts').select('content_embedding').eq('id', post_id).single().execute()
        
        if not target_post_result.data or not target_post_result.data.get('content_embedding'):
            raise HTTPException(status_code=404, detail="Post or embedding not found")
        
        target_embedding = target_post_result.data['content_embedding']
        
        # Find similar posts using vector similarity
        # Note: This assumes pgvector is enabled in Supabase
        query = f"""
            SELECT *, 
                   content_embedding <=> '{json.dumps(target_embedding)}' as distance
            FROM recent_h1b_posts 
            WHERE id != {post_id} 
            AND content_embedding IS NOT NULL
            ORDER BY distance 
            LIMIT {limit}
        """
        
        result = supabase.rpc('sql', {'query': query}).execute()
        
        similar_posts = []
        if result.data:
            for post_data in result.data:
                post = {
                    'id': post_data.get('id'),
                    'title': post_data.get('title', ''),
                    'content': post_data.get('content', ''),
                    'author': {
                        'id': post_data.get('author_id'),
                        'name': post_data.get('author_name', 'Unknown')
                    },
                    'community': {
                        'id': post_data.get('community_id'),
                        'name': post_data.get('community_name', 'General')
                    },
                    'like_count': post_data.get('like_count', 0),
                    'comment_count': post_data.get('comment_count', 0),
                    'created_at': post_data.get('created_at'),
                    'similarity_score': post_data.get('distance')
                }
                similar_posts.append(post)
        
        return {
            "success": True,
            "similar_posts": similar_posts,
            "post_id": post_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get similar Supabase posts: {e}")
        raise HTTPException(status_code=500, detail="Failed to find similar posts")

@router.post("/supabase/posts/vote")
async def vote_supabase_post(
    post_id: int = Query(..., description="Post ID"),
    vote_type: str = Query(..., regex="^(up|down)$", description="Vote type: up or down"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Vote on a post in Supabase"""
    try:
        supabase = get_supabase_client()
        
        # Check if user already voted
        existing_vote = supabase.table('post_votes').select('*').eq('post_id', post_id).eq('user_id', current_user.id).single().execute()
        
        vote_value = 1 if vote_type == "up" else -1
        
        if existing_vote.data:
            # Update existing vote
            if existing_vote.data.get('vote_type') == vote_type:
                # Remove vote
                supabase.table('post_votes').delete().eq('id', existing_vote.data['id']).execute()
                vote_value = 0
            else:
                # Change vote
                supabase.table('post_votes').update({
                    'vote_type': vote_type,
                    'updated_at': 'now()'
                }).eq('id', existing_vote.data['id']).execute()
        else:
            # Create new vote
            supabase.table('post_votes').insert({
                'post_id': post_id,
                'user_id': current_user.id,
                'vote_type': vote_type
            }).execute()
        
        # Update post like count
        # This would ideally be handled by a database trigger, but we'll do it manually here
        post_result = supabase.table('recent_h1b_posts').select('like_count').eq('id', post_id).single().execute()
        
        if post_result.data:
            new_like_count = post_result.data['like_count'] + vote_value
            
            supabase.table('recent_h1b_posts').update({
                'like_count': new_like_count
            }).eq('id', post_id).execute()
        
        return {
            "success": True,
            "post_id": post_id,
            "vote_type": vote_type,
            "new_like_count": new_like_count if 'new_like_count' in locals() else post_result.data['like_count']
        }
        
    except Exception as e:
        logger.error(f"Failed to vote on Supabase post: {e}")
        raise HTTPException(status_code=500, detail="Failed to process vote")

@router.get("/supabase/posts/stats")
async def get_supabase_posts_stats(
    country: Optional[str] = Query(None, description="Country filter"),
    category: Optional[str] = Query(None, description="Category filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics about posts in Supabase"""
    try:
        supabase = get_supabase_client()
        
        # Build base query
        query = supabase.table('recent_h1b_posts').select('id, created_at, like_count, comment_count, view_count')
        
        if country:
            query = query.eq('country', country)
        
        if category:
            query = query.eq('category', category)
        
        result = query.execute()
        
        if result.data:
            posts = result.data
            total_posts = len(posts)
            
            # Calculate statistics
            total_likes = sum(post.get('like_count', 0) for post in posts)
            total_comments = sum(post.get('comment_count', 0) for post in posts)
            total_views = sum(post.get('view_count', 0) for post in posts)
            
            avg_likes = total_likes / total_posts if total_posts > 0 else 0
            avg_comments = total_comments / total_posts if total_posts > 0 else 0
            avg_views = total_views / total_posts if total_posts > 0 else 0
            
            # Get recent activity
            recent_posts = sorted(posts, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
            
            return {
                "success": True,
                "stats": {
                    "total_posts": total_posts,
                    "total_likes": total_likes,
                    "total_comments": total_comments,
                    "total_views": total_views,
                    "average_likes_per_post": round(avg_likes, 2),
                    "average_comments_per_post": round(avg_comments, 2),
                    "average_views_per_post": round(avg_views, 2)
                },
                "recent_posts": [
                    {
                        'id': post['id'],
                        'title': post.get('title', ''),
                        'created_at': post.get('created_at'),
                        'like_count': post.get('like_count', 0),
                        'comment_count': post.get('comment_count', 0)
                    }
                    for post in recent_posts
                ]
            }
        else:
            return {
                "success": True,
                "stats": {
                    "total_posts": 0,
                    "total_likes": 0,
                    "total_comments": 0,
                    "total_views": 0,
                    "average_likes_per_post": 0,
                    "average_comments_per_post": 0,
                    "average_views_per_post": 0
                },
                "recent_posts": []
            }
            
    except Exception as e:
        logger.error(f"Failed to get Supabase posts stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")

@router.get("/supabase/posts/categories")
async def get_supabase_post_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all available post categories from Supabase"""
    try:
        supabase = get_supabase_client()
        
        # Get distinct categories
        result = supabase.table('recent_h1b_posts').select('category').distinct().execute()
        
        categories = []
        if result.data:
            categories = [item['category'] for item in result.data if item['category']]
        
        # Get category counts
        category_counts = {}
        for category in categories:
            count_result = supabase.table('recent_h1b_posts').select('id', count='exact').eq('category', category).execute()
            category_counts[category] = count_result.count or 0
        
        return {
            "success": True,
            "categories": categories,
            "category_counts": category_counts
        }
        
    except Exception as e:
        logger.error(f"Failed to get Supabase post categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch categories")