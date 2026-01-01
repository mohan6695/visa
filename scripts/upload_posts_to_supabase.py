#!/usr/bin/env python3
"""
Script to upload posts.json to Supabase and set up clustering
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
from supabase import create_client, Client
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY

def load_posts_from_json(file_path: str) -> List[Dict[str, Any]]:
    """Load posts from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def generate_embedding(text: str) -> List[float]:
    """Generate embedding using OpenAI API"""
    try:
        response = openai.Embedding.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response['data'][0]['embedding']
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def upload_post_to_supabase(post_data: Dict[str, Any], group_id: str) -> Dict[str, Any]:
    """Upload a single post to Supabase"""
    try:
        # Extract post information
        author_name = post_data.get("Post Author", "Anonymous")
        content = post_data.get("Post Content", "")
        title = content[:50] + "..." if len(content) > 50 else content
        
        # Generate embedding
        embedding = generate_embedding(content)
        
        # Create a user for the author if they don't exist
        # For now, we'll use a default user ID
        author_id = "00000000-0000-0000-0000-000000000001"  # Default user
        
        # Insert post
        post_record = {
            "id": str(uuid.uuid4()),
            "group_id": group_id,
            "author_id": author_id,
            "title": title,
            "content": content,
            "embedding": embedding,
            "upvotes": int(post_data.get("Number of Likes", 0)),
            "downvotes": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Remove embedding if it's None to avoid errors
        if embedding is None:
            post_record.pop("embedding")
        
        result = supabase.table("posts").insert(post_record).execute()
        
        if result.data:
            print(f"Uploaded post: {title}")
            return result.data[0]
        else:
            print(f"Failed to upload post: {title}")
            return None
            
    except Exception as e:
        print(f"Error uploading post: {e}")
        return None

def create_clustering_function():
    """Create a function for clustering similar posts using pgvector"""
    try:
        clustering_function = """
        CREATE OR REPLACE FUNCTION cluster_similar_posts(
            post_id_param UUID,
            similarity_threshold FLOAT DEFAULT 0.8,
            max_results INT DEFAULT 10
        )
        RETURNS TABLE (
            similar_post_id UUID,
            similarity_score FLOAT,
            title TEXT,
            content TEXT,
            author_id UUID,
            created_at TIMESTAMPTZ
        )
        AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                p.id,
                1 - (p.embedding <=> source_post.embedding) as similarity_score,
                p.title,
                p.content,
                p.author_id,
                p.created_at
            FROM posts p
            CROSS JOIN (
                SELECT embedding FROM posts WHERE id = post_id_param
            ) as source_post
            WHERE 
                p.id != post_id_param
                AND p.embedding IS NOT NULL
                AND source_post.embedding IS NOT NULL
                AND (1 - (p.embedding <=> source_post.embedding)) > similarity_threshold
            ORDER BY similarity_score DESC
            LIMIT max_results;
        END;
        $$
        LANGUAGE plpgsql SECURITY DEFINER;
        """
        
        # Execute the function creation
        supabase.rpc("cluster_similar_posts", {}).execute()
        print("Created clustering function successfully")
        
    except Exception as e:
        print(f"Error creating clustering function: {e}")

def main():
    """Main function to upload posts and set up clustering"""
    print("Starting post upload process...")
    
    # Load posts from JSON file
    posts = load_posts_from_json("/Users/mohanakrishnanarsupalli/Downloads/posts.json")
    print(f"Loaded {len(posts)} posts from JSON file")
    
    # Use H1B Visa Discussions group ID
    group_id = "550e8400-e29b-41d4-a716-446655440001"
    
    # Upload posts to Supabase
    uploaded_posts = []
    for i, post in enumerate(posts[:10]):  # Upload first 10 posts for testing
        print(f"Uploading post {i+1}/{min(10, len(posts))}")
        uploaded_post = upload_post_to_supabase(post, group_id)
        if uploaded_post:
            uploaded_posts.append(uploaded_post)
    
    print(f"Successfully uploaded {len(uploaded_posts)} posts")
    
    # Create clustering function
    print("Setting up clustering function...")
    create_clustering_function()
    
    # Test clustering with the first uploaded post
    if uploaded_posts:
        test_post_id = uploaded_posts[0]["id"]
        print(f"Testing clustering with post ID: {test_post_id}")
        
        # Test the clustering function
        try:
            result = supabase.rpc("cluster_similar_posts", {
                "post_id_param": test_post_id,
                "similarity_threshold": 0.7,
                "max_results": 5
            }).execute()
            
            if result.data:
                print(f"Found {len(result.data)} similar posts:")
                for similar_post in result.data:
                    print(f"  - Similarity: {similar_post['similarity_score']:.3f} - {similar_post['title']}")
            else:
                print("No similar posts found")
                
        except Exception as e:
            print(f"Error testing clustering: {e}")
    
    print("Post upload and clustering setup complete!")

if __name__ == "__main__":
    main()