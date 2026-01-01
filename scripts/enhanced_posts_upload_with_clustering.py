#!/usr/bin/env python3
"""
Enhanced Posts Upload with pgvector Clustering
Uploads posts.json from Downloads to Supabase with semantic clustering
"""

import json
import os
import uuid
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
import openai
from dotenv import load_dotenv
import hashlib
import re

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
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Loaded {len(data)} posts from {file_path}")
        return data
    except Exception as e:
        print(f"❌ Error loading posts from {file_path}: {e}")
        return []

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters that might interfere
    text = re.sub(r'[^\w\s.,!?;:\-\'"]', '', text)
    
    return text

def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding using OpenAI API"""
    try:
        # Clean the text first
        clean_text_content = clean_text(text)
        
        if not clean_text_content or len(clean_text_content.strip()) < 10:
            print("⚠️  Text too short for embedding generation")
            return None
            
        response = openai.Embedding.create(
            input=clean_text_content,
            model="text-embedding-3-small"  # 1536 dimensions
        )
        embedding = response['data'][0]['embedding']
        print(f"✅ Generated embedding for text of length {len(clean_text_content)}")
        return embedding
        
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        return None

def determine_country_from_content(content: str, title: str) -> str:
    """Determine country from post content"""
    text = f"{title} {content}".lower()
    
    if any(keyword in text for keyword in ['usa', 'united states', 'america', 'h1b', 'us ', 'uscis']):
        return "USA"
    elif any(keyword in text for keyword in ['canada', 'ca ', 'cic']):
        return "Canada"
    elif any(keyword in text for keyword in ['australia', 'au ', 'immi']):
        return "Australia"
    elif any(keyword in text for keyword in ['uk', 'united kingdom', 'britain', 'gb ']):
        return "United Kingdom"
    else:
        return "USA"  # Default to USA

def extract_tags_from_content(content: str, title: str) -> List[str]:
    """Extract relevant tags from post content"""
    text = f"{title} {content}".lower()
    tags = []
    
    # Common visa-related tags
    tag_keywords = {
        'H1B': ['h1b', 'h-1b'],
        'H4': ['h4', 'h-4', 'spouse'],
        'F1': ['f1', 'f-1', 'student'],
        'OPT': ['opt', 'stem opt'],
        'CPT': ['cpt'],
        'Green Card': ['green card', 'gc', 'permanent resident'],
        'Stamping': ['stamping', 'visa interview'],
        '221(g)': ['221g', '221(g)', 'administrative processing'],
        '221(i)': ['221i', '221(i)', 'revocation'],
        'RFE': ['rfe', 'request for evidence'],
        'L1': ['l1', 'l-1'],
        'L2': ['l2', 'l-2'],
        'EAD': ['ead', 'work authorization'],
        'Travel': ['travel', 're-entry', 'port of entry'],
        'Social Media': ['social media', 'facebook', 'twitter', 'instagram'],
        'Interview': ['interview', 'visa interview'],
        'Processing': ['processing', 'pending'],
        'Revocation': ['revocation', 'revoked', 'cancelled']
    }
    
    for tag, keywords in tag_keywords.items():
        if any(keyword in text for keyword in keywords):
            tags.append(tag)
    
    return tags

def get_or_create_country_id(country_name: str) -> Optional[int]:
    """Get or create country ID"""
    try:
        # Try to get existing country
        result = supabase.table("countries").select("id").eq("name", country_name).execute()
        
        if result.data:
            return result.data[0]["id"]
        
        # Create new country if it doesn't exist
        country_data = {
            "name": country_name,
            "code": country_name[:3].upper(),
            "created_at": datetime.now().isoformat()
        }
        
        result = supabase.table("countries").insert(country_data).execute()
        if result.data:
            print(f"✅ Created new country: {country_name}")
            return result.data[0]["id"]
        
        return None
        
    except Exception as e:
        print(f"❌ Error creating country {country_name}: {e}")
        return None

def upload_post_to_supabase(post_data: Dict[str, Any], group_id: str) -> Optional[Dict[str, Any]]:
    """Upload a single post to Supabase with enhanced metadata"""
    try:
        # Extract post information
        author_name = post_data.get("Post Author", "Anonymous")
        content = post_data.get("Post Content", "")
        title = content[:100] + "..." if len(content) > 100 else content
        
        # Clean and prepare content for embedding
        full_text = f"{title}\n\n{content}"
        embedding = generate_embedding(full_text)
        
        # Determine country and get country ID
        country_name = determine_country_from_content(content, title)
        country_id = get_or_create_country_id(country_name)
        
        # Extract tags
        tags = extract_tags_from_content(content, title)
        
        # Generate watermarks for DMCA tracking
        watermark_hash = hashlib.md5(f"{content}{author_name}{datetime.now().isoformat()}".encode()).hexdigest()
        display_watermark = f"POST-{str(uuid.uuid4())[:8]}-{int(time.time())}"
        
        # Create post record with enhanced metadata
        post_record = {
            "id": str(uuid.uuid4()),
            "group_id": group_id,
            "country_id": country_id,
            "author_id": 1,  # Default user ID
            "title": title,
            "content": content,
            "content_html": content.replace('\n', '<br>'),
            "embedding": embedding,
            "upvotes": int(post_data.get("Number of Likes", 0)),
            "downvotes": 0,
            "view_count": 0,
            "comment_count": 0,
            "watermark_hash": watermark_hash,
            "display_watermark": display_watermark,
            "status": "published",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Remove embedding if it's None to avoid errors
        if embedding is None:
            post_record.pop("embedding")
        
        # Insert post
        result = supabase.table("posts").insert(post_record).execute()
        
        if result.data:
            uploaded_post = result.data[0]
            print(f"✅ Uploaded post: {title[:50]}...")
            
            # Add tags if any were extracted
            if tags:
                post_id = uploaded_post["id"]
                for tag in tags:
                    tag_data = {
                        "post_id": post_id,
                        "tag": tag,
                        "created_at": datetime.now().isoformat()
                    }
                    try:
                        supabase.table("post_tags").insert(tag_data).execute()
                    except Exception as e:
                        print(f"⚠️  Could not add tag {tag}: {e}")
            
            return uploaded_post
        else:
            print(f"❌ Failed to upload post: {title}")
            return None
            
    except Exception as e:
        print(f"❌ Error uploading post: {e}")
        return None

def assign_posts_to_clusters():
    """Assign posts to clusters using the database function"""
    try:
        print("🔄 Assigning posts to clusters...")
        result = supabase.rpc("assign_posts_to_clusters", {"cluster_count": 15}).execute()
        
        if result.data:
            updated_count = result.data[0]["assign_posts_to_clusters"]
            print(f"✅ Assigned {updated_count} posts to clusters")
        else:
            print("⚠️  No posts were assigned to clusters")
            
    except Exception as e:
        print(f"❌ Error assigning posts to clusters: {e}")

def test_clustering_functionality():
    """Test the clustering functionality"""
    try:
        print("🧪 Testing clustering functionality...")
        
        # Get a random post with embedding
        result = supabase.table("posts").select("id, title").not_.in_("embedding", "null").limit(1).execute()
        
        if result.data:
            test_post_id = result.data[0]["id"]
            test_title = result.data[0]["title"]
            print(f"🎯 Testing with post: {test_title[:50]}...")
            
            # Test similarity search
            similar_result = supabase.rpc("find_similar_posts", {
                "post_id_param": test_post_id,
                "similarity_threshold": 0.6,
                "max_results": 5
            }).execute()
            
            if similar_result.data:
                print(f"✅ Found {len(similar_result.data)} similar posts:")
                for i, post in enumerate(similar_result.data, 1):
                    print(f"  {i}. {post['similarity_score']:.3f} - {post['title'][:50]}...")
            else:
                print("⚠️  No similar posts found")
        else:
            print("⚠️  No posts with embeddings found for testing")
            
    except Exception as e:
        print(f"❌ Error testing clustering: {e}")

def get_clustered_posts_summary():
    """Get a summary of clustered posts"""
    try:
        print("📊 Getting clustered posts summary...")
        
        # Get cluster information
        clusters_result = supabase.table("post_clusters").select("*").execute()
        
        if clusters_result.data:
            print(f"\n📈 Found {len(clusters_result.data)} clusters:")
            for cluster in clusters_result.data:
                print(f"  • {cluster['cluster_name']}: {cluster['post_count']} posts")
        
        # Get posts by country
        country_result = supabase.table("posts").select("country_id, countries(name)").join("countries", "country_id", "countries.id").execute()
        
        if country_result.data:
            countries = {}
            for post in country_result.data:
                country = post["countries"]["name"]
                countries[country] = countries.get(country, 0) + 1
            
            print(f"\n🌍 Posts by country:")
            for country, count in countries.items():
                print(f"  • {country}: {count} posts")
        
    except Exception as e:
        print(f"❌ Error getting summary: {e}")

def main():
    """Main function to upload posts with clustering"""
    print("🚀 Starting enhanced post upload with clustering...")
    print("=" * 60)
    
    # Load posts from JSON file
    posts_file = "/Users/mohanakrishnanarsupalli/Downloads/posts.json"
    posts = load_posts_from_json(posts_file)
    
    if not posts:
        print("❌ No posts loaded. Exiting.")
        return
    
    # Use H1B Visa Discussions group ID
    group_id = "550e8400-e29b-41d4-a716-446655440001"
    
    # Upload posts to Supabase with enhanced metadata
    uploaded_posts = []
    batch_size = 5  # Process in smaller batches to avoid rate limits
    
    for i in range(0, len(posts), batch_size):
        batch = posts[i:i + batch_size]
        print(f"\n📤 Processing batch {i//batch_size + 1}/{(len(posts) + batch_size - 1)//batch_size} ({len(batch)} posts)")
        
        for j, post in enumerate(batch):
            print(f"  Uploading post {i + j + 1}/{len(posts)}")
            uploaded_post = upload_post_to_supabase(post, group_id)
            if uploaded_post:
                uploaded_posts.append(uploaded_post)
        
        # Small delay between batches to respect rate limits
        if i + batch_size < len(posts):
            time.sleep(1)
    
    print(f"\n✅ Successfully uploaded {len(uploaded_posts)} posts out of {len(posts)} total")
    
    if uploaded_posts:
        # Assign posts to clusters
        assign_posts_to_clusters()
        
        # Test clustering functionality
        test_clustering_functionality()
        
        # Get summary
        get_clustered_posts_summary()
        
        print("\n🎉 Enhanced post upload and clustering complete!")
        print("\n📋 Summary:")
        print(f"  • Posts uploaded: {len(uploaded_posts)}")
        print(f"  • Country detection: Enabled")
        print(f"  • Tag extraction: Enabled")
        print(f"  • Semantic clustering: Enabled")
        print(f"  • Watermark tracking: Enabled")
        
        print("\n🔍 Next steps:")
        print("  1. Check the USA Posts page for clustered posts")
        print("  2. Test similarity search functionality")
        print("  3. Monitor cluster performance")
        
    else:
        print("\n⚠️  No posts were uploaded successfully")

if __name__ == "__main__":
    main()
    
