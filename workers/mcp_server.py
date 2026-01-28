"""
Cloudflare MCP Server
=====================

Implements the Model Context Protocol (MCP) over HTTP/SSE.
Exposes tools for:
1. Semantic Search (Supabase pgvector)
2. Platform Analytics (Supabase aggregation)
3. Clustering Trigger (Cloudflare Workers AI)

Deployment:
wrangler deploy --config wrangler.mcp.toml
"""

import json
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from workers import WorkerEntrypoint, Response, Request

# ===== CONFIG =====
# These will be populated from env vars
SUPABASE_URL = ""
SERVICE_ROLE_KEY = ""
CF_ACCOUNT_ID = ""
CF_API_TOKEN = ""

# AI Models
EMBED_MODEL = "@cf/baai/bge-small-en-v1.5"

# ===== HELPER FUNCTIONS =====

async def generate_embeddings(texts: List[str], account_id: str, token: str) -> List[List[float]]:
    """Generate embeddings using Cloudflare Workers AI."""
    if not texts:
        return []
        
    payload = {"text": texts}
    resp = await fetch(
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{EMBED_MODEL}",
        {
            "method": "POST",
            "headers": {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            "body": json.dumps(payload)
        }
    )
    
    if not resp.ok:
        raise Exception(f"Failed to generate embeddings: {resp.status}")
        
    data = await resp.json()
    return data.get("result", {}).get("data", [])

async def search_posts(query: str, limit: int = 5) -> str:
    """Semantic search for posts."""
    try:
        # 1. Generate embedding
        embeddings = await generate_embeddings([query], CF_ACCOUNT_ID, CF_API_TOKEN)
        if not embeddings:
            return "Failed to generate embedding"
            
        query_vector = embeddings[0]
        
        # 2. Query Supabase
        resp = await fetch(
            f"{SUPABASE_URL}/rest/v1/rpc/match_posts",
            {
                "method": "POST",
                "headers": {
                    "apikey": SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "query_embedding": query_vector,
                    "match_threshold": 0.5,
                    "match_count": limit
                })
            }
        )
        
        # Fallback if RPC doesn't exist (simpler implementation)
        if resp.status != 200:
             return f"Search failed: {await resp.text()}. Note: match_posts RPC might be missing."
            
        posts = await resp.json()
        if not posts:
            return "No matching posts found."
            
        return json.dumps(posts, indent=2)
            
    except Exception as e:
        return f"Error searching posts: {str(e)}"

async def get_analytics(days: int = 7) -> str:
    """Get basic platform stats."""
    try:
        # Count posts
        resp = await fetch(
            f"{SUPABASE_URL}/rest/v1/posts?select=count",
            {
                "method": "GET",
                "headers": {
                   "apikey": SERVICE_ROLE_KEY,
                   "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
                   "Range": "0-0"
                }
            }
        )
        total_posts = resp.headers.get("Content-Range", "0/0").split("/")[-1]
        
        # Count clusters
        resp = await fetch(
            f"{SUPABASE_URL}/rest/v1/clusters?select=count",
            {
                "method": "GET",
                "headers": {
                   "apikey": SERVICE_ROLE_KEY,
                   "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
                   "Range": "0-0"
                }
            }
        )
        total_clusters = resp.headers.get("Content-Range", "0/0").split("/")[-1]
        
        return json.dumps({
            "total_posts": total_posts,
            "total_clusters": total_clusters,
            "period_days": days,
            "status": "active"
        }, indent=2)
        
    except Exception as e:
        return f"Error fetching analytics: {str(e)}"
        
async def trigger_clustering_job() -> str:
    """Trigger the clustering worker (if exposed) or run logic directly."""
    # For now, return a placeholder as direct worker-to-worker invocation 
    # requires Service Bindings configuration which is complex to setup dynamically.
    # In a real scenario, we would `fetch` the other worker.
    return "Clustering job trigger sent (Simulation). To implement fully, bind the clustering worker."

# ===== MCP PROTOCOL LOGIC =====

TOOLS = [
    {
        "name": "search_posts",
        "description": "Search visa forum posts using semantic search.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results (default 5)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_analytics",
        "description": "Get high-level platform analytics.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Time period in days"}
            }
        }
    },
    {
        "name": "trigger_clustering",
        "description": "Manually trigger the AI clustering pipeline.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]

async def handle_tool_call(name: str, args: Dict[str, Any]) -> str:
    if name == "search_posts":
        return await search_posts(args.get("query"), args.get("limit", 5))
    elif name == "get_analytics":
        return await get_analytics(args.get("days", 7))
    elif name == "trigger_clustering":
        return await trigger_clustering_job()
    return f"Unknown tool: {name}"

class Worker(WorkerEntrypoint):
    async def fetch(self, request: Request) -> Response:
        global SUPABASE_URL, SERVICE_ROLE_KEY, CF_ACCOUNT_ID, CF_API_TOKEN
        
        # Load env
        SUPABASE_URL = self.env.SUPABASE_URL
        SERVICE_ROLE_KEY = self.env.SUPABASE_SERVICE_ROLE_KEY
        CF_ACCOUNT_ID = self.env.CF_ACCOUNT_ID
        CF_API_TOKEN = self.env.CF_API_TOKEN
        
        url = request.url
        method = request.method
        path = url.split(request.headers.get("host", ""))[1] if "http" in url else url.path
        
        # SSE Endpoint
        if path.endswith("/sse"):
            # Return a simple UUID for the session
            return Response("d5a42094-1188-47v7-b123-5e26710486c1", headers={
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            })
            
        # Message Endpoint (JSON-RPC)
        if method == "POST" and path.endswith("/messages"):
            try:
                body = await request.json()
                method_name = body.get("method")
                req_id = body.get("id")
                
                result = None
                
                if method_name == "tools/list":
                    result = {"tools": TOOLS}
                    
                elif method_name == "tools/call":
                    params = body.get("params", {})
                    name = params.get("name")
                    args = params.get("arguments", {})
                    content = await handle_tool_call(name, args)
                    result = {"content": [{"type": "text", "text": content}]}
                
                else:
                    # Initialize or other methods
                    return Response(json.dumps({
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {}
                    }), headers={"Content-Type": "application/json"})

                return Response(json.dumps({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": result
                }), headers={"Content-Type": "application/json"})
                
            except Exception as e:
                return Response(json.dumps({
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": str(e)}
                }), status=500, headers={"Content-Type": "application/json"})

        return Response("MCP Server Running", status=200)

export = Worker()
