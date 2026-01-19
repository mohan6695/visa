#!/usr/bin/env python3
"""
Upload new_posts.json to Supabase with embeddings

This script:
1. Loads posts from Downloads/new_posts.json
2. Generates embeddings for each post
3. Uploads to Supabase posts table with pgvector embeddings
"""

import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
import hashlib

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

load_dotenv()

# Configuration
POSTS_FILE = os.path.expanduser("~/Downloads/new_posts.json")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384 dimensions
BATCH_SIZE = 50


def get_db_connection():
    """Get Supabase database connection"""
    import os
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "")
    )
    return conn


def load_posts(filepath: str) -> List[Dict]:
    """Load posts from JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        posts = json.load(f)
    print(f"Loaded {len(posts)} posts from {filepath}")
    return posts


def generate_embeddings(posts: List[Dict], model) -> List[Dict]:
    """Generate embeddings for all posts"""
    print(f"Generating embeddings using {EMBEDDING_MODEL}...")
    
    # Prepare texts for embedding
    texts = []
    for post in posts:
        # Combine title and content for embedding
        title = post.get('text', '')[:200]  # First 200 chars as pseudo-title
        content = post.get('text', '')
        combined = f"{title}\n\n{content}"
        texts.append(combined)
    
    # Generate embeddings in batches
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=BATCH_SIZE)
    
    # Attach embeddings to posts
    for i, post in enumerate(posts):
        post['embedding'] = embeddings[i].tolist()
    
    print(f"Generated {len(embeddings)} embeddings")
    return posts


def create_group_id(group_title: str) -> str:
    """Create a consistent group_id from group title"""
    # Use hash of group title
    hash_obj = hashlib.md5(group_title.encode())
    return f"550e8400-e29b-41d4-a716-{hash_obj.hexdigest()[:12]}"


def insert_posts_to_supabase(posts: List[Dict], conn):
    """Insert posts with embeddings to Supabase"""
    print("Inserting posts to Supabase...")
    
    cursor = conn.cursor()
    
    inserted = 0
    errors = 0
    
    for post in posts:
        try:
            # Extract post data
            text = post.get('text', '')
            group_title = post.get('groupTitle', 'Unknown Group')
            url = post.get('url', '')
            user_id = post.get('user', {}).get('id', 'anonymous')
            created_at = post.get('time', datetime.utcnow().isoformat())
            
            # Create group_id
            group_id = create_group_id(group_title)
            
            # Create excerpt (first 200 chars)
            excerpt = text[:200] + '...' if len(text) > 200 else text
            
            # Insert post
            cursor.execute("""
                INSERT INTO posts (
                    title,
                    content,
                    excerpt,
                    url,
                    author_id,
                    group_id,
                    embedding,
                    score,
                    view_count,
                    is_answered,
                    status,
                    created_at,
                    updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    updated_at = EXCLUDED.updated_at
                RETURNING id
            """, (
                f"Post from {group_title}",
                text,
                excerpt,
                url,
                user_id,
                group_id,
                post.get('embedding'),
                0,  # Initial score
                0,  # Initial view count
                False,
                'published',
                created_at,
                datetime.utcnow().isoformat()
            ))
            
            result = cursor.fetchone()
            if result:
                inserted += 1
                if inserted % 100 == 0:
                    print(f"  Inserted {inserted} posts...")
            
            conn.commit()
            
        except Exception as e:
            errors += 1
            conn.rollback()
            if errors <= 5:  # Only print first 5 errors
                print(f"  Error inserting post: {e}")
    
    cursor.close()
    print(f"Inserted {inserted} posts, {errors} errors")
    return inserted


def ensure_group_exists(conn, group_title: str, group_id: str):
    """Ensure group exists in groups table"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO groups (id, name, created_at, updated_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (group_id, group_title, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error creating group: {e}")
    finally:
        cursor.close()


def main():
    """Main function to upload posts with embeddings"""
    print("=" * 60)
    print("Upload new_posts.json to Supabase with embeddings")
    print("=" * 60)
    
    # Check if file exists
    if not os.path.exists(POSTS_FILE):
        print(f"ERROR: Posts file not found: {POSTS_FILE}")
        return 1
    
    # Load posts
    posts = load_posts(POSTS_FILE)
    if not posts:
        print("No posts to upload")
        return 0
    
    # Load embedding model
    print(f"Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    
    # Generate embeddings
    posts = generate_embeddings(posts, model)
    
    # Connect to database
    print("Connecting to Supabase...")
    conn = get_db_connection()
    
    # Create groups for each unique group_title
    unique_groups = set(p.get('groupTitle', 'Unknown') for p in posts)
    for group_title in unique_groups:
        group_id = create_group_id(group_title)
        ensure_group_exists(conn, group_title, group_id)
    
    # Insert posts
    inserted = insert_posts_to_supabase(posts, conn)
    
    # Close connection
    conn.close()
    
    print("=" * 60)
    print(f"Complete! Uploaded {inserted} posts with embeddings.")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
