from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from ..dependencies import get_db, get_current_user
from ...services.chat_service import ChatService
from ...models.user import User
from ...core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/chat/history")
async def get_chat_history(
    community_id: int = Query(..., description="Community ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get chat history for a community"""
    try:
        chat_service = ChatService(db)
        messages = await chat_service.get_chat_history(community_id, limit, offset)
        
        return {
            "success": True,
            "data": {
                "messages": messages,
                "community_id": community_id,
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"Get chat history API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat history")

@router.post("/chat/send")
async def send_chat_message(
    community_id: int,
    content: str = Query(..., min_length=1, max_length=1000),
    message_type: str = Query("text", regex="^(text|image|file)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a chat message to a community"""
    try:
        chat_service = ChatService(db)
        result = await chat_service.send_chat_message(
            community_id, 
            current_user.id, 
            content, 
            message_type
        )
        
        if result:
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send message")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send chat message API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")

@router.get("/chat/members")
async def get_community_members(
    community_id: int = Query(..., description="Community ID"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get active members in a community"""
    try:
        chat_service = ChatService(db)
        members = await chat_service.get_community_members(community_id, limit)
        
        return {
            "success": True,
            "data": {
                "members": members,
                "community_id": community_id,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Get community members API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get community members")

@router.get("/chat/online-status")
async def get_online_status(
    user_ids: List[int] = Query(..., description="List of user IDs"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get online status for multiple users"""
    try:
        chat_service = ChatService(db)
        status = await chat_service.get_online_status(user_ids)
        
        return {
            "success": True,
            "data": {
                "online_status": status,
                "user_ids": user_ids
            }
        }
        
    except Exception as e:
        logger.error(f"Get online status API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get online status")

@router.post("/chat/mark-read")
async def mark_message_read(
    community_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a message as read by a user"""
    try:
        chat_service = ChatService(db)
        success = await chat_service.mark_message_read(
            current_user.id, 
            community_id, 
            message_id
        )
        
        return {
            "success": success,
            "data": {
                "user_id": current_user.id,
                "community_id": community_id,
                "message_id": message_id
            }
        }
        
    except Exception as e:
        logger.error(f"Mark message read API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark message as read")

@router.get("/chat/unread-count")
async def get_unread_count(
    community_id: int = Query(..., description="Community ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get unread message count for a user in a community"""
    try:
        chat_service = ChatService(db)
        count = await chat_service.get_unread_count(current_user.id, community_id)
        
        return {
            "success": True,
            "data": {
                "unread_count": count,
                "community_id": community_id,
                "user_id": current_user.id
            }
        }
        
    except Exception as e:
        logger.error(f"Get unread count API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get unread count")

@router.get("/chat/search")
async def search_chat_messages(
    community_id: int = Query(..., description="Community ID"),
    query: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search chat messages in a community"""
    try:
        chat_service = ChatService(db)
        result = await chat_service.search_chat_messages(community_id, query, limit, offset)
        
        return {
            "success": True,
            "data": result,
            "query": query,
            "community_id": community_id
        }
        
    except Exception as e:
        logger.error(f"Search chat messages API error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@router.get("/chat/activity")
async def get_recent_activity(
    community_id: int = Query(..., description="Community ID"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent activity in a community (posts, comments, new members)"""
    try:
        chat_service = ChatService(db)
        activity = await chat_service.get_recent_activity(community_id, limit)
        
        return {
            "success": True,
            "data": {
                "activity": activity,
                "community_id": community_id,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"Get recent activity API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent activity")

# WebSocket endpoint for real-time chat
@router.websocket("/chat/ws")
async def websocket_chat(
    websocket: WebSocket,
    community_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """WebSocket endpoint for real-time chat"""
    try:
        await websocket.accept()
        
        # Send recent chat history
        chat_service = ChatService(db)
        recent_messages = await chat_service.get_chat_history(community_id, 20, 0)
        
        await websocket.send_json({
            "type": "history",
            "data": recent_messages
        })
        
        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                
                if data.get("type") == "message":
                    content = data.get("content", "")
                    message_type = data.get("message_type", "text")
                    
                    if content:
                        # Send message to chat service
                        result = await chat_service.send_chat_message(
                            community_id,
                            current_user.id,
                            content,
                            message_type
                        )
                        
                        if result:
                            # Broadcast message to all connected clients
                            await websocket.send_json({
                                "type": "new_message",
                                "data": result
                            })
                            
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close(code=1011, reason="Internal server error")