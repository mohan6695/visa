"""
Cloudflare Workers AI + Supabase Post Clustering Pipeline

Uses Cloudflare Workers AI for embeddings and clustering (no Ollama needed).
Designed to run as a Cloudflare Worker with cron triggers.
"""

import json
import asyncio
from typing import Any, Dict, List
import httpx
from datetime import datetime
from workers import WorkerEntrypoint, Response, Request


# Workers AI models
EMBED_MODEL = "@cf/baai/bge-small-en-v1.5"  # 768-dim embeddings
CLUSTER_MODEL = "@cf/meta/llama-3.2-1b-instruct"  # fast clustering


async def generate_embeddings(texts: List[str], cf_account_id: str, cf_api_token: str) -> List[List[float]]:
    """
    Generate embeddings using Cloudflare Workers AI.
    Returns list of embedding vectors (768-dim).
    """
    if not texts:
        return []

    batch_size = 20  # Workers AI limit
    embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        payload = {"text": batch}

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/ai/run/{EMBED_MODEL}",
                headers={"Authorization": f"Bearer {cf_api_token}"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        # BGE model returns {"result": {"data": [ [embeddings], ... ]}}
        batch_embeddings = data.get("result", {}).get("data", [])
        embeddings.extend(batch_embeddings)

    return embeddings


async def cluster_posts_with_llm(posts: List[Dict[str, Any]], cf_account_id: str, cf_api_token: str) -> Dict[str, Any]:
    """
    Use Cloudflare Workers AI LLM to cluster posts semantically.
    Returns JSON with cluster labels and post assignments.
    """
    if not posts:
        return {"clusters": []}

    # Build prompt with post contents
    posts_text = "\n".join(
        f"#{i} ({p['id']}): {p['content'][:300]}" for i, p in enumerate(posts)
    )

    prompt = f"""You are clustering forum/community posts into coherent topic groups.

Posts to cluster:
{posts_text}

Analyze posts and return a JSON object with this structure:

{{
  "clusters": [
    {{
      "label": "Topic Name",
      "description": "Short description",
      "post_indexes": [0, 2, 5]
    }},
    ...
  ]
}}

Return ONLY valid JSON, no markdown or extra text."""

    payload = {
        "prompt": prompt,
        "max_tokens": 2000,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"https://api.cloudflare.com/client/v4/accounts/{cf_account_id}/ai/run/{CLUSTER_MODEL}",
            headers={"Authorization": f"Bearer {cf_api_token}"},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    # Parse response
    text = data.get("result", {}).get("response", "")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from text
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start : end + 1])
        return {"clusters": []}


async def fetch_unclustered_posts(supabase_url: str, service_role_key: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch posts that need clustering from Supabase."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(
            f"{supabase_url}/rest/v1/posts",
            params={
                "select": "id,content",
                "clustered_at": "is.null",
                "embedding": "not.is.null",
                "limit": str(limit),
                "order": "created_at.asc",
            },
            headers={
                "apikey": service_role_key,
                "Authorization": f"Bearer {service_role_key}",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def create_cluster_and_assign(
    supabase_url: str, service_role_key: str, label: str, post_ids: List[str]
) -> int:
    """Create a cluster in Supabase and assign posts to it."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        # Insert cluster
        c_resp = await client.post(
            f"{supabase_url}/rest/v1/clusters",
            headers={
                "apikey": service_role_key,
                "Authorization": f"Bearer {service_role_key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
            json={"label": label, "post_count": len(post_ids)},
        )
        c_resp.raise_for_status()
        cluster = c_resp.json()[0]
        cluster_id = cluster["id"]

        # Update posts: set cluster_id & clustered_at
        if post_ids:
            ids_str = ",".join(f'"{pid}"' for pid in post_ids)
            upd_resp = await client.patch(
                f"{supabase_url}/rest/v1/posts",
                headers={
                    "apikey": service_role_key,
                    "Authorization": f"Bearer {service_role_key}",
                    "Content-Type": "application/json",
                },
                params={"id": f"in.({ids_str})"},
                json={
                    "cluster_id": cluster_id,
                    "clustered_at": datetime.utcnow().isoformat(),
                },
            )
            upd_resp.raise_for_status()

        return cluster_id


async def run_clustering_pipeline(env):
    """
    Main clustering pipeline:
    1. Fetch unclustered posts
    2. Use LLM to cluster them
    3. Create clusters + assign posts
    """
    # Get environment variables
    supabase_url = env.SUPABASE_URL
    service_role_key = env.SUPABASE_SERVICE_ROLE_KEY
    cf_account_id = env.CF_ACCOUNT_ID
    cf_api_token = env.CF_API_TOKEN

    # 1. Fetch posts needing clustering
    posts = await fetch_unclustered_posts(supabase_url, service_role_key, limit=100)
    if not posts:
        return {"status": "No posts to cluster", "processed": 0}

    # 2. Ask LLM to cluster them
    clusters_json = await cluster_posts_with_llm(posts, cf_account_id, cf_api_token)
    clusters = clusters_json.get("clusters", [])
    if not clusters:
        return {"status": "No clusters formed", "processed": 0}

    # 3. Create clusters + assign posts
    processed = 0
    for cluster in clusters:
        label = cluster.get("label", "Uncategorized")
        post_indexes = cluster.get("post_indexes", [])
        post_ids = [posts[i]["id"] for i in post_indexes if 0 <= i < len(posts)]

        if post_ids:
            await create_cluster_and_assign(supabase_url, service_role_key, label, post_ids)
            processed += len(post_ids)

    return {"status": "Clustering complete", "processed": processed, "clusters": len(clusters)}


class Worker(WorkerEntrypoint):
    """Cloudflare Workers AI + Supabase clustering worker."""

    async def fetch(self, request: Request) -> Response:
        """HTTP endpoint (manual trigger)."""
        result = await run_clustering_pipeline(self.env)
        return Response(json.dumps(result), headers={"Content-Type": "application/json"})

    async def scheduled(self, event, env, ctx):
        """Cron trigger handler (runs on schedule)."""
        result = await run_clustering_pipeline(env)
        print(f"Clustering cron: {result}")
        return result


# Export for Cloudflare Workers
export = Worker()
