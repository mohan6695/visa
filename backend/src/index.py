import json
from worker import queue_handler, extract_posts_and_comments
from ai_cluster import cluster_posts_batched
from supabase_client import save_to_supabase

async def fetch(request, env, ctx):
    """HTTP API endpoints"""
    path = request.url.split("?")[0]
    
    if path.endswith("/health"):
        return Response(json.dumps({"status": "healthy", "timestamp": "2026-01-23"}),
                       headers={"Content-Type": "application/json"})
    
    elif path.endswith("/run"):
        # Manual trigger
        await env.PROCESS_QUEUE.send({"key": "posts.json"})
        return Response(json.dumps({"status": "triggered", "message": "Processing posts.json"}),
                       headers={"Content-Type": "application/json"})
    
    elif path.endswith("/api/posts"):
        # GET: List posts from Supabase
        posts = await get_posts_from_supabase(env)
        return Response(json.dumps(posts),
                       headers={"Content-Type": "application/json"})
    
    elif path.endswith("/api/upload") and request.method == "POST":
        # POST: Upload new posts to R2
        body = await request.json()
        key = await upload_to_r2(env, body)
        await env.PROCESS_QUEUE.send({"key": key})
        return Response(json.dumps({"status": "queued", "key": key}),
                       headers={"Content-Type": "application/json"})
    
    elif path.endswith("/api/modify") and request.method == "POST":
        # AI code modification
        return await ai_modify_worker(request, env)
    
    return Response("AI Stack Overflow API\nEndpoints: /health, /run, /api/posts, /api/upload, /api/modify")

async def get_posts_from_supabase(env):
    """Fetch posts from Supabase"""
    url = f"{env.SUPABASE_URL}/rest/v1/posts?select=*&order=inserted_at.desc&limit=20"
    headers = {
        "apikey": env.SUPABASE_KEY,
        "Authorization": f"Bearer {env.SUPABASE_KEY}"
    }
    resp = await fetch(url, {"headers": headers})
    return await resp.json()

async def upload_to_r2(env, posts_data):
    """Upload posts to R2"""
    key = f"posts-{int(datetime.now().timestamp())}.json"
    await env.MY_BUCKET.put(key, json.dumps(posts_data))
    return key

async def ai_modify_worker(request, env):
    """AI code modification"""
    body = await request.json()
    prompt = body.get("prompt", "")
    
    ai_response = await env.AI.run("@cf/meta/llama-3.1-8b-instruct", {
        "prompt": f"Modify Cloudflare Worker:\n{prompt}",
        "max_tokens": 4000
    })
    
    return Response(json.dumps({"modified": True, "response": ai_response.response}),
                   headers={"Content-Type": "application/json"})

__exports__ = {"fetch": fetch, "queue_handler": queue_handler}
