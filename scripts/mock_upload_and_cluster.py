#!/usr/bin/env python3
"""
Mock script to simulate uploading posts to Supabase and setting up clustering
This demonstrates the functionality without requiring actual Supabase credentials
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Mock database
class MockSupabase:
    def __init__(self):
        self.posts = []
        self.clusters = []
    
    def insert_post(self, post_data):
        """Mock insert post"""
        post_id = str(uuid.uuid4())
        post_with_id = {**post_data, "id": post_id}
        self.posts.append(post_with_id)
        return {"data": [post_with_id]}
    
    def create_function(self, function_name, function_sql):
        """Mock create function"""
        print(f"Created function: {function_name}")
        return {"success": True}
    
    def execute_rpc(self, function_name, params):
        """Mock execute RPC function"""
        if function_name == "cluster_similar_posts":
            post_id = params.get("post_id_param")
            threshold = params.get("similarity_threshold", 0.8)
            max_results = params.get("max_results", 10)
            
            # Find the source post
            source_post = next((p for p in self.posts if p["id"] == post_id), None)
            if not source_post:
                return {"data": []}
            
            # Find similar posts using cosine similarity on mock embeddings
            results = []
            for post in self.posts:
                if post["id"] == post_id:
                    continue
                
                # Mock similarity calculation
                similarity = self.calculate_mock_similarity(source_post, post)
                if similarity > threshold:
                    results.append({
                        "similar_post_id": post["id"],
                        "similarity_score": similarity,
                        "title": post["title"],
                        "content": post["content"],
                        "author_id": post["author_id"],
                        "created_at": post["created_at"]
                    })
            
            # Sort by similarity and limit results
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return {"data": results[:max_results]}
        
        return {"data": []}
    
    def calculate_mock_similarity(self, post1, post2):
        """Calculate mock similarity based on content overlap"""
        content1 = post1["content"].lower()
        content2 = post2["content"].lower()
        
        # Simple word overlap similarity
        words1 = set(content1.split())
        words2 = set(content2.split())
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if len(union) == 0:
            return 0.0
        
        jaccard_similarity = len(intersection) / len(union)
        
        # Add some randomness to simulate real embeddings
        random_factor = np.random.uniform(0.7, 1.0)
        
        return min(0.95, jaccard_similarity * random_factor)

def load_posts_from_json(file_path: str) -> List[Dict[str, Any]]:
    """Load posts from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def generate_mock_embedding(text: str) -> List[float]:
    """Generate mock embedding"""
    # Create a simple mock embedding based on text length and some content features
    words = text.lower().split()
    
    # Simple feature vector
    features = {
        'length': len(text),
        'word_count': len(words),
        'has_h1b': 1.0 if 'h1b' in text.lower() else 0.0,
        'has_visa': 1.0 if 'visa' in text.lower() else 0.0,
        'has_stamping': 1.0 if 'stamping' in text.lower() else 0.0,
        'has_interview': 1.0 if 'interview' in text.lower() else 0.0,
        'has_revocation': 1.0 if 'revocation' in text.lower() else 0.0,
        'has_221g': 1.0 if '221g' in text.lower() else 0.0,
        'has_social_media': 1.0 if 'social media' in text.lower() else 0.0,
        'has_travel': 1.0 if 'travel' in text.lower() else 0.0
    }
    
    # Create a 1536-dimensional vector (same as text-embedding-3-small)
    # Fill with some meaningful values and random noise
    embedding = []
    
    # Add the features
    for value in features.values():
        embedding.append(value)
    
    # Fill the rest with random values between 0 and 1
    while len(embedding) < 1536:
        embedding.append(np.random.uniform(0, 1))
    
    # Normalize to make it more realistic
    embedding = [x / sum(embedding) for x in embedding]
    
    return embedding

def upload_post_to_mock_supabase(post_data: Dict[str, Any], group_id: str, mock_db: MockSupabase) -> Dict[str, Any]:
    """Upload a single post to mock Supabase"""
    try:
        # Extract post information
        author_name = post_data.get("Post Author", "Anonymous")
        content = post_data.get("Post Content", "")
        title = content[:50] + "..." if len(content) > 50 else content
        
        # Generate mock embedding
        embedding = generate_mock_embedding(content)
        
        # Use a default user ID
        author_id = "00000000-0000-0000-0000-000000000001"  # Default user
        
        # Create post record
        post_record = {
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
        
        # Insert post
        result = mock_db.insert_post(post_record)
        
        if result and 'data' in result and result['data']:
            print(f"Uploaded post: {title}")
            return result['data'][0]
        else:
            print(f"Failed to upload post: {title}")
            return None
            
    except Exception as e:
        print(f"Error uploading post: {e}")
        return None

def create_mock_clustering_function(mock_db: MockSupabase):
    """Create a mock clustering function"""
    try:
        function_sql = """
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
        
        mock_db.create_function("cluster_similar_posts", function_sql)
        print("Created mock clustering function successfully")
        
    except Exception as e:
        print(f"Error creating mock clustering function: {e}")

def main():
    """Main function to simulate uploading posts and setting up clustering"""
    print("Starting mock post upload and clustering process...")
    
    # Initialize mock database
    mock_db = MockSupabase()
    
    # Load posts from JSON file
    posts = load_posts_from_json("/Users/mohanakrishnanarsupalli/Downloads/posts.json")
    print(f"Loaded {len(posts)} posts from JSON file")
    
    # Use H1B Visa Discussions group ID
    group_id = "550e8400-e29b-41d4-a716-446655440001"
    
    # Upload posts to mock Supabase
    uploaded_posts = []
    for i, post in enumerate(posts[:10]):  # Upload first 10 posts for testing
        print(f"Uploading post {i+1}/{min(10, len(posts))}")
        uploaded_post = upload_post_to_mock_supabase(post, group_id, mock_db)
        if uploaded_post:
            uploaded_posts.append(uploaded_post)
    
    print(f"Successfully uploaded {len(uploaded_posts)} posts to mock database")
    
    # Create clustering function
    print("Setting up mock clustering function...")
    create_mock_clustering_function(mock_db)
    
    # Test clustering with the first uploaded post
    clustering_result = None
    if uploaded_posts:
        test_post_id = uploaded_posts[0]["id"]
        print(f"Testing clustering with post ID: {test_post_id}")
        print(f"Test post title: {uploaded_posts[0]['title']}")
        
        # Test the clustering function
        try:
            clustering_result = mock_db.execute_rpc("cluster_similar_posts", {
                "post_id_param": test_post_id,
                "similarity_threshold": 0.7,
                "max_results": 5
            })
            
            if clustering_result and 'data' in clustering_result and clustering_result['data']:
                print(f"Found {len(clustering_result['data'])} similar posts:")
                for i, similar_post in enumerate(clustering_result['data'], 1):
                    print(f"  {i}. Similarity: {similar_post['similarity_score']:.3f}")
                    print(f"     Title: {similar_post['title'][:80]}...")
                    print(f"     Content preview: {similar_post['content'][:100]}...")
                    print()
            else:
                print("No similar posts found")
                
        except Exception as e:
            print(f"Error testing clustering: {e}")
    
    # Generate some statistics
    print("\n=== Upload Statistics ===")
    print(f"Total posts uploaded: {len(uploaded_posts)}")
    print(f"Total similar posts found: {len(clustering_result['data']) if clustering_result and 'data' in clustering_result and clustering_result['data'] else 0}")
    
    # Show some content analysis
    print("\n=== Content Analysis ===")
    h1b_count = sum(1 for post in uploaded_posts if 'h1b' in post['content'].lower())
    visa_count = sum(1 for post in uploaded_posts if 'visa' in post['content'].lower())
    stamping_count = sum(1 for post in uploaded_posts if 'stamping' in post['content'].lower())
    
    print(f"Posts mentioning H1B: {h1b_count}")
    print(f"Posts mentioning visa: {visa_count}")
    print(f"Posts mentioning stamping: {stamping_count}")
    
    print("\nMock post upload and clustering setup complete!")
    print("\nThis demonstrates how the real Supabase integration would work.")
    print("The actual implementation would:")
    print("1. Connect to real Supabase database")
    print("2. Use real OpenAI embeddings")
    print("3. Use pgvector for efficient similarity search")
    print("4. Store and retrieve real post data")

if __name__ == "__main__":
    main()