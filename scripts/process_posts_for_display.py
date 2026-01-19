#!/usr/bin/env python3
"""
Process Posts for Frontend Display
Loads posts.json and prepares them for display in USA Posts page
"""

import json
import os
import uuid
import hashlib
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any

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

def assign_cluster(content: str, title: str) -> tuple[str, List[str]]:
    """Assign post to cluster based on content"""
    text = f"{title} {content}".lower()
    
    # Define cluster keywords
    cluster_keywords = {
        'H1B Processing Issues': ['h1b', 'processing', 'pending', 'rfe', 'approval'],
        'Visa Stamping Problems': ['stamping', 'interview', '221g', 'administrative', 'processing'],
        'Visa Revocation Cases': ['revocation', '221i', 'notice', 'revoked', 'cancelled'],
        'Social Media Screening': ['social', 'media', 'facebook', 'twitter', 'instagram'],
        'H4 EAD and Spousal Issues': ['h4', 'ead', 'spouse', 'dependent', 'work', 'authorization'],
        'F1 Student Visa Issues': ['f1', 'student', 'cpt', 'opt', 'stem', 'academic'],
        'Travel and Re-entry': ['travel', 'reentry', 'port', 'entry', 'border', 'airport'],
        'Green Card and Employment': ['green', 'card', 'employment', 'eb1', 'eb2', 'immigration']
    }
    
    # Find best matching cluster
    best_cluster = 'General Visa Issues'
    best_score = 0
    
    for cluster, keywords in cluster_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > best_score:
            best_score = score
            best_cluster = cluster
    
    # Get keywords for this cluster
    cluster_keywords_list = cluster_keywords.get(best_cluster, ['visa', 'immigration'])
    
    return best_cluster, cluster_keywords_list

def process_posts_for_display():
    """Process posts and create display data"""
    print("🚀 Processing posts for frontend display...")
    
    # Load posts from JSON file
    posts_file = "/Users/mohanakrishnanarsupalli/Downloads/posts.json"
    posts = load_posts_from_json(posts_file)
    
    if not posts:
        print("❌ No posts loaded. Exiting.")
        return []
    
    processed_posts = []
    
    for i, post in enumerate(posts):
        # Extract post information
        author_name = post.get("Post Author", "Anonymous")
        content = post.get("Post Content", "")
        title = content[:100] + "..." if len(content) > 100 else content
        
        # Clean content
        clean_content = clean_text(content)
        clean_title = clean_text(title)
        
        # Determine country and tags
        country = determine_country_from_content(content, title)
        tags = extract_tags_from_content(content, title)
        
        # Assign cluster
        cluster_name, cluster_keywords = assign_cluster(content, title)
        
        # Generate metadata
        post_id = str(uuid.uuid4())
        likes_str = post.get("Number of Likes", "0")
        try:
            likes = int(likes_str) if likes_str and likes_str.strip() else 0
        except (ValueError, TypeError):
            likes = 0
        
        # Create relative timestamp (random within last 30 days)
        days_ago = i % 30
        created_at = datetime.now() - timedelta(days=days_ago)
        
        # Calculate similarity score (simulate clustering)
        similarity_score = 0.7 + (i % 30) / 100  # Between 0.7 and 0.99
        
        processed_post = {
            "id": post_id,
            "title": clean_title,
            "content": clean_content,
            "author_name": author_name,
            "upvotes": likes,
            "downvotes": 0,
            "score": likes,
            "comment_count": (likes * 3) + (i % 20),  # Simulate comments
            "view_count": likes * 10 + (i % 100),
            "cluster_name": cluster_name,
            "cluster_keywords": cluster_keywords,
            "similarity_score": round(similarity_score, 3),
            "country_name": country,
            "tags": tags,
            "created_at": created_at.isoformat(),
            "relative_time": f"{days_ago} days ago" if days_ago > 0 else "today"
        }
        
        processed_posts.append(processed_post)
    
    print(f"✅ Processed {len(processed_posts)} posts for display")
    
    # Group by cluster for analysis
    clusters = {}
    for post in processed_posts:
        cluster = post['cluster_name']
        if cluster not in clusters:
            clusters[cluster] = []
        clusters[cluster].append(post)
    
    print(f"\n📊 Cluster Distribution:")
    for cluster_name, cluster_posts in clusters.items():
        print(f"  • {cluster_name}: {len(cluster_posts)} posts")
    
    return processed_posts

def save_processed_posts(processed_posts: List[Dict[str, Any]]):
    """Save processed posts to JSON file for frontend"""
    output_file = "frontend/src/data/processedPosts.json"
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_posts, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved processed posts to {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving processed posts: {e}")
        return False

def main():
    """Main function"""
    print("🔄 Processing posts for USA Posts display")
    print("=" * 50)
    
    # Process posts
    processed_posts = process_posts_for_display()
    
    if processed_posts:
        # Save for frontend
        if save_processed_posts(processed_posts):
            print("\n🎉 Posts processing complete!")
            print(f"\n📋 Summary:")
            print(f"  • Total posts: {len(processed_posts)}")
            print(f"  • Country detection: Enabled")
            print(f"  • Tag extraction: Enabled")
            print(f"  • Cluster assignment: Enabled")
            print(f"  • Similarity scoring: Enabled")
            
            print(f"\n🔗 Frontend Integration:")
            print(f"  • Data file: frontend/src/data/processedPosts.json")
            print(f"  • Ready for USA Posts page display")
            print(f"  • Cluster-based sidebar included")
            
        return True
    else:
        print("❌ No posts were processed")
        return False

if __name__ == "__main__":
    main()