from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..dependencies import get_db, get_current_user
from ...models.user import User
from ...models.post import Post
from ...models.comment import Comment
from ...models.community import CommunityMember
from ...schemas.user import UserResponse, UserUpdate, UserProfile
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/profile/{username}", response_model=UserProfile)
async def get_user_profile(
    username: str,
    db: Session = Depends(get_db)
):
    """Get user profile by username"""
    try:
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        # Get user statistics
        post_count = db.query(Post).filter(Post.author_id == user.id).count()
        comment_count = db.query(Comment).filter(Comment.author_id == user.id).count()
        community_count = db.query(CommunityMember).filter(CommunityMember.user_id == user.id).count()
        
        return UserProfile(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            bio=user.bio,
            post_count=post_count,
            comment_count=comment_count,
            community_count=community_count,
            last_seen=user.last_seen,
            is_active=user.is_active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user profile error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get user profile"
        )

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    try:
        # Update user fields
        if user_data.full_name is not None:
            current_user.full_name = user_data.full_name
        if user_data.bio is not None:
            current_user.bio = user_data.bio
        if user_data.avatar_url is not None:
            current_user.avatar_url = user_data.avatar_url
        
        db.commit()
        db.refresh(current_user)
        
        return UserResponse(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            full_name=current_user.full_name,
            avatar_url=current_user.avatar_url
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Update user profile error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update profile"
        )

@router.get("/search", response_model=List[UserResponse])
async def search_users(
    query: str = Query(..., min_length=2, max_length=50),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search users by username or full name"""
    try:
        users = db.query(User).filter(
            User.is_active == True,
            (
                User.username.ilike(f"%{query}%") |
                User.full_name.ilike(f"%{query}%")
            )
        ).limit(limit).all()
        
        return [
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                avatar_url=user.avatar_url
            ) for user in users
        ]
        
    except Exception as e:
        logger.error(f"Search users error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Search failed"
        )

@router.get("/recent-activity")
async def get_user_recent_activity(
    username: Optional[str] = Query(None, description="Username to get activity for (defaults to current user)"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent activity for a user"""
    try:
        target_user = current_user
        
        # If username is provided, get that user's activity (if they're active)
        if username and username != current_user.username:
            target_user = db.query(User).filter(
                User.username == username,
                User.is_active == True
            ).first()
            
            if not target_user:
                raise HTTPException(
                    status_code=404,
                    detail="User not found or inactive"
                )
        
        # Get recent posts
        posts = db.query(Post).filter(
            Post.author_id == target_user.id,
            Post.status == "published"
        ).order_by(Post.created_at.desc()).limit(limit // 3).all()
        
        # Get recent comments
        comments = db.query(Comment).filter(
            Comment.author_id == target_user.id,
            Comment.status == "published"
        ).order_by(Comment.created_at.desc()).limit(limit // 3).all()
        
        # Get community activities
        community_activities = []
        community_memberships = db.query(CommunityMember).filter(
            CommunityMember.user_id == target_user.id
        ).all()
        
        for membership in community_memberships[:limit // 3]:
            community_activities.append({
                "type": "community_joined",
                "community_id": membership.community_id,
                "joined_at": membership.joined_at,
                "role": membership.role
            })
        
        # Combine and sort by date
        activity = []
        
        for post in posts:
            activity.append({
                "type": "post",
                "content": post.title,
                "created_at": post.created_at,
                "post_id": post.id
            })
        
        for comment in comments:
            activity.append({
                "type": "comment",
                "content": comment.content[:100] + "..." if len(comment.content) > 100 else comment.content,
                "created_at": comment.created_at,
                "comment_id": comment.id
            })
        
        activity.extend(community_activities)
        
        activity.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "user_id": target_user.id,
            "username": target_user.username,
            "activity": activity[:limit]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user recent activity error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get recent activity"
        )

@router.get("/stats")
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user statistics and metrics"""
    try:
        # Get user's content counts
        post_count = db.query(Post).filter(
            Post.author_id == current_user.id,
            Post.status == "published"
        ).count()
        
        comment_count = db.query(Comment).filter(
            Comment.author_id == current_user.id,
            Comment.status == "published"
        ).count()
        
        community_count = db.query(CommunityMember).filter(
            CommunityMember.user_id == current_user.id,
            CommunityMember.is_active == True
        ).count()
        
        # Get user's engagement metrics (likes received)
        post_likes = db.query(Post).filter(
            Post.author_id == current_user.id
        ).with_entities(func.sum(Post.like_count)).scalar() or 0
        
        comment_likes = db.query(Comment).filter(
            Comment.author_id == current_user.id
        ).with_entities(func.sum(Comment.like_count)).scalar() or 0
        
        total_engagement = post_likes + comment_likes
        
        return {
            "user_id": current_user.id,
            "username": current_user.username,
            "stats": {
                "posts": post_count,
                "comments": comment_count,
                "communities": community_count,
                "total_engagement": total_engagement,
                "post_likes_received": post_likes,
                "comment_likes_received": comment_likes
            },
            "last_activity": current_user.last_seen
        }
        
    except Exception as e:
        logger.error(f"Get user stats error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get user stats"
        )