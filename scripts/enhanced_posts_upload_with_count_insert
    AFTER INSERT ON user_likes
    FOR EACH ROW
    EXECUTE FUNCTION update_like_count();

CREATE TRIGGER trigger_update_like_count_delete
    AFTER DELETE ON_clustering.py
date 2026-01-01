#!/usr/bin/env python3
"""
Enhanced Posts Upload with pgvector Clustering
Uploads posts.json from Downloads to Supabase with semantic clustering user_likes
    FOR EACH ROW
    EXECUTE FUNCTION update_like_count();

-- Trigger to update conversation last message
CREATE TRIGGER trigger_update_conversation_last_message
    AFTER INSERT ON
"""

import json
import os
import uuid
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from supabase import create_client, Client direct_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_conversation_last_message();

-- =============================================
-- VIEWS FOR COMMON QUERIES
-- =============================================

-- View for user space
import openai
from dotenv import load_dotenv
import hashlib
import re

# Load environment variables
load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("SUP overview
CREATE OR REPLACE VIEW user_space_overview AS
SELECT 
    us.id,
    us.user_id,
    us.display_name,
    us.bio,
    us.profile_image_url,
    us.total_interviews,
    us.total_posts,
    us.total_messages_sent,
    us.total_messages_received,
    us.created_at,
    COUNT(DISTINCT ieABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize clients
supabase: Client = create_client.id) FILTER (WHERE ie.is_public = true) as public_interviews,
    COUNT(DISTINCT up.id) FILTER (WHERE up.visibility = 'public') as public(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY

def load_posts_from_json(file_path: str) -> List[Dict[str, Any]]:
    """Load_posts,
    COUNT(DISTINCT uf.follower_id) as follower_count,
    COUNT(DISTINCT uf2.following_id) as following_count
 posts from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Loaded {FROM user_spaces us
LEFT JOIN interview_experiences ie ON us.user_id = ie.user_id
LEFT JOIN user_posts up ON us.user_id = up.author_id
LEFT JOIN userlen(data)} posts from {file_path}")
        return data
    except Exception as e:
        print(f"❌ Error loading posts from {file_path}: {e}")
        return_follows uf ON us.user_id = uf.following_id
LEFT JOIN user_follows uf2 ON us.user_id = uf2.follower_id
GROUP BY us.id, us.user_id []

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text, us.display_name, us.bio, us.profile_image_url, us.total_interviews, us.total_posts, us.total_messages_sent, us.total_messages_received, us.created_at;

-- View for = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters that might interfere
    text = re.sub(r'[^\w\s., direct message conversations with preview
CREATE OR REPLACE VIEW conversation_preview AS
SELECT 
    dc.id,
    dc.user1_id,
    dc.user2_id,
    dc.created_at,
    dc.last_message_at,
    dc.last_message_preview,
    dc.is_blocked,
    us1.display_name as user1_name,
    us1.profile_image!?;:\-\'"]', '', text)
    
    return text

def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding using Open_url as user1_image,
    us2.display_name as user2_name,
    us2.profile_image_url as user2_image,
    COUNT(dm.id) FILTERAI API"""
    try:
        # Clean the text first
        clean_text_content = clean_text(text)
        
        if not clean_text_content or len(clean (WHERE dm.is_read = false AND dm.sender_id != auth.uid()) as unread_count
FROM direct_conversations dc
JOIN user_spaces us1 ON dc.user1_id =_text_content.strip()) < 10:
            print("⚠️  Text too short for embedding generation")
            return None
            
        response = openai.Embedding.create(
            input= us1.user_id
JOIN user_spaces us2 ON dc.user2_id = us2.user_id
LEFT JOIN direct_messages dm ON dc.id = dm.conversation_id
GROUP BY dc.id, dc.user1_id, dc.user2_id, dc.created_at, dc.last_message_at, dc.last_message_preview, dc.is_blocked, us1.display_name, us1.profileclean_text_content,
            model="text-embedding-3-small"  # 1536 dimensions
        )
        embedding = response['data'][0]['embedding']
        print_image_url, us2.display_name, us2.profile_image_url;

-- =============================================
-- SAMPLE DATA (for development)
-- =============================================

-- Insert sample user spaces
--(f"✅ Generated embedding for text of length {len(clean_text_content)}")
        return embedding
        
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        return None

def determine_country_from_content(content: str, title: str) -> str:
    """Determine country from post Note: This would normally be done via the application

-- =============================================
-- COMMENTS
-- =============================================

/*
This migration creates a comprehensive user-centric data model with:

1. User Spaces: Personal profiles with analytics counters
2. Interview Experiences: Personal interview documentation content"""
    text = f"{title} {content}".lower()
    
    if any(keyword in text for keyword in ['usa', 'united states', 'america', 'h
3. User Posts: Personal content with visibility controls
4. User Comments: Nested comments on user content
5. Private Messaging: Secure direct1b', 'us ', 'uscis']):
        return "USA"
    elif any(keyword in text for keyword in ['canada', '