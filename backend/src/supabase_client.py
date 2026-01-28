import json

async def upsert_posts(env, posts: list, batch_size: int = 50):
    """Save posts to Supabase"""
    if not posts:
        return
    
    url = f"{env.SUPABASE_URL}/rest/v1/posts"
    headers = {
        "Content-Type": "application/json",
        "apikey": env.SUPABASE_KEY,
        "Authorization": f"Bearer {env.SUPABASE_KEY}",
        "Prefer": "resolution=merge-duplicates"
    }
    
    for i in range(0, len(posts), batch_size):
        batch = posts[i:i + batch_size]
        
        payload = [
            {
                "id": p["id"],
                "title": p["title"],
                "text_ref": p["text_ref"],
                "user_name": p["user_name"],
                "date": p["date"],
                "url": p.get("url", ""),
                "summary": p.get("summary", ""),
                "cluster_id": p.get("cluster_id", "general"),
                "ai_relevance_score": p.get("ai_relevance_score", 0.5),
                "comment_count": p.get("comment_count", 0)
            }
            for p in batch
        ]
        
        resp = await fetch(url, {
            "method": "POST",
            "headers": headers,
            "body": json.dumps(payload)
        })
        
        if resp.status >= 400:
            print(f"Posts error: {await resp.text()}")

async def upsert_comments(env, comments: list, batch_size: int = 100):
    """Save comments to Supabase"""
    if not comments:
        return
    
    url = f"{env.SUPABASE_URL}/rest/v1/comments"
    headers = {
        "Content-Type": "application/json",
        "apikey": env.SUPABASE_KEY,
        "Authorization": f"Bearer {env.SUPABASE_KEY}",
        "Prefer": "resolution=merge-duplicates"
    }
    
    for i in range(0, len(comments), batch_size):
        batch = comments[i:i + batch_size]
        
        payload = [
            {
                "id": c["id"],
                "post_id": c["post_id"],
                "text_ref": c["text_ref"],
                "user_name": c["user_name"],
                "date": c["date"],
                "url": c.get("url", "")
            }
            for c in batch
        ]
        
        resp = await fetch(url, {
            "method": "POST",
            "headers": headers,
            "body": json.dumps(payload)
        })
        
        if resp.status >= 400:
            print(f"Comments error: {await resp.text()}")

async def log_event(env, event: str, status: str = "info", error_msg: str = ""):
    """Log to Supabase"""
    try:
        url = f"{env.SUPABASE_URL}/rest/v1/pipeline_logs"
        headers = {
            "Content-Type": "application/json",
            "apikey": env.SUPABASE_KEY,
            "Authorization": f"Bearer {env.SUPABASE_KEY}"
        }
        
        await fetch(url, {
            "method": "POST",
            "headers": headers,
            "body": json.dumps({
                "event": event,
                "status": status,
                "error_msg": error_msg
            })
        })
    except:
        pass
