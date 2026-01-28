import json
from typing import List, Dict, Any
from ai_cluster import cluster_posts_batched
from supabase_client import upsert_posts, upsert_comments, log_event

async def queue_handler(batch, env, ctx):
    """Main queue consumer - processes R2 JSON files"""
    for msg in batch:
        try:
            data = json.loads(msg.body)
            key = data.get("key", "posts.json")
            
            print(f"🔄 Processing: {key}")
            
            # 1. Fetch from R2
            r2_obj = await env.MY_BUCKET.get(key)
            if not r2_obj:
                print(f"❌ Not found: {key}")
                continue
            
            body = await r2_obj.text()
            raw_data = json.loads(body)
            
            # Normalize
            if isinstance(raw_data, dict):
                raw_data = [raw_data]
            
            # 2. Extract posts + comments
            posts, comments = extract_posts_and_comments(raw_data)
            print(f"📊 Extracted: {len(posts)} posts, {len(comments)} comments")
            
            # 3. AI clustering
            clustered_posts = await cluster_posts_batched(env, posts, batch_size=25)
            
            # 4. Save to Supabase
            await upsert_posts(env, clustered_posts, batch_size=50)
            if comments:
                await upsert_comments(env, comments, batch_size=100)
            
            # 5. Mark processed
            await env.PROCESSED_KEYS.put(f"done:{key}", "processed", {"expirationTtl": 604800})
            
            await log_event(env, f"✅ Processed: {key} ({len(posts)} posts, {len(comments)} comments)", "success")
            
        except Exception as e:
            await log_event(env, f"❌ Error: {str(e)}", "error", error_msg=str(e))

def extract_posts_and_comments(raw_data: List[Dict[str, Any]]) -> tuple:
    """Extract posts + comments from nested structure"""
    posts = []
    comments = []
    
    for item in raw_data:
        post_id = item.get("id")
        if not post_id:
            continue
        
        post = {
            "id": str(post_id),
            "title": str(item.get("title", ""))[:512],
            "text_ref": str(post_id) + "_text",  # Reference to R2
            "user_name": str(item.get("user", "anonymous"))[:100],
            "date": item.get("date"),
            "url": item.get("url", ""),
            "summary": "",
            "cluster_id": "general",
            "comment_count": 0
        }
        
        posts.append(post)
        
        # Extract comments
        for idx, comment in enumerate(item.get("comments", [])):
            comments.append({
                "id": f"{post_id}_comment_{idx}",
                "post_id": str(post_id),
                "text_ref": f"{post_id}_comment_{idx}_text",  # Reference to R2
                "user_name": str(comment.get("user", "anonymous"))[:100],
                "date": comment.get("date"),
                "url": comment.get("url", "")
            })
        
        post["comment_count"] = len(item.get("comments", []))
    
    return posts, comments
