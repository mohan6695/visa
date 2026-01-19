"""
===============================================================================
CLOUDFLARE WORKERS AI + SUPABASE CLUSTERING PIPELINE
===============================================================================

Complete production pipeline:
1. Cloudflare Workers AI: embeddings (EmbeddingGemma) + LLM clustering (Llama 3.2)
2. Supabase: tables (posts, clusters) + pgvector
3. Cloudflare Workers: Python + cron triggers
4. No Ollama needed – everything via Cloudflare Workers AI API

SETUP:
------
1. Save as: worker.py
2. Create wrangler.toml (see below)
3. Deploy: pywrangler deploy

ENVIRONMENT SETUP:
------------------
wrangler.toml:
--------------
name = "supabase-clustering"
main = "worker.py"
compatibility_date = "2026-01-19"

[triggers]
crons = ["*/5 * * * *"]  # every 5 minutes

[env.production]
vars = { SUPABASE_URL = "https://YOUR_PROJECT.supabase.co" }

Secrets (via: wrangler secret put):
- SUPABASE_SERVICE_ROLE_KEY
- CF_ACCOUNT_ID
- CF_API_TOKEN

SQL (Supabase - run once):
--------------------------
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS posts (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  content text,
  embedding vector(768),
  embedding_status text DEFAULT 'pending',
  cluster_id integer,
  clustered_at timestamptz,
  created_at timestamptz DEFAULT now()
);
CREATE TABLE IF NOT EXISTS clusters (
  id serial PRIMARY KEY,
  label text,
  post_count integer DEFAULT 0,
  updated_at timestamptz DEFAULT now()
);
CREATE INDEX ON posts USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON clusters(id);

===============================================================================
"""

import json
import asyncio
from typing import Any, Dict, List
import httpx
from datetime import datetime
from workers import WorkerEntrypoint, Response, Request


# ===== CONFIG =====
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"  # from env
SERVICE_ROLE_KEY = "YOUR_SERVICE_ROLE_KEY"  # from secret
CF_ACCOUNT_ID = "YOUR_ACCOUNT_ID"  # from secret
CF_API_TOKEN = "YOUR_API_TOKEN"  # from secret

# Workers AI models
EMBED_MODEL = "@cf/baai-bge-small-en-v1.5"  # 768-dim embeddings
CLUSTER_MODEL = "@cf/meta/llama-3.2-1b-instruct"  # fast clustering


# ===== WORKERS AI API CALLS =====

async def generate_embeddings(texts: List[str], env) -> List[List[float]]:
    """
    Generate embeddings using Cloudflare Workers AI (EmbeddingGemma / BGE).
    Returns list of embedding vectors.
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
                f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{EMBED_MODEL}",
                headers={"Authorization": f"Bearer {CF_API_TOKEN}"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        # BGE model returns {"result": {"data": [ [embeddings], ... ]}}
        batch_embeddings = data.get("result", {}).get("data", [])
        embeddings.extend(batch_embeddings)

    return embeddings


async def cluster_posts_with_llm(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Use Cloudflare Workers AI LLM to cluster posts semantically.
    Sends prompt + post contents → LLM → JSON clusters.
    """
    if not posts:
        return {"clusters": []}

    # Build prompt
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
            f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{CLUSTER_MODEL}",
            headers={"Authorization": f"Bearer {CF_API_TOKEN}"},
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


# ===== SUPABASE API CALLS =====

async def fetch_unclustered_posts(limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch posts that need clustering from Supabase."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(
            f"{SUPABASE_URL}/rest/v1/posts",
            params={
                "select": "id,content",
                "clustered_at": "is.null",
                "embedding": "not.is.null",
                "limit": str(limit),
                "order": "created_at.asc",
            },
            headers={
                "apikey": SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def create_cluster_and_assign(
    label: str, post_ids: List[str]
) -> int:
    """Create a cluster in Supabase and return its ID."""
    async with httpx.AsyncClient(timeout=20.0) as client:
        # Insert cluster
        c_resp = await client.post(
            f"{SUPABASE_URL}/rest/v1/clusters",
            headers={
                "apikey": SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
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
                f"{SUPABASE_URL}/rest/v1/posts",
                headers={
                    "apikey": SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
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


# ===== MAIN PIPELINE =====

async def run_clustering_pipeline():
    """
    Main pipeline:
    1. Fetch unclustered posts
    2. Use LLM to cluster them
    3. Create clusters + assign posts
    """
    # 1. Fetch posts needing clustering
    posts = await fetch_unclustered_posts(limit=100)
    if not posts:
        return {"status": "No posts to cluster", "processed": 0}

    # 2. Ask LLM to cluster them
    clusters_json = await cluster_posts_with_llm(posts)
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
            await create_cluster_and_assign(label, post_ids)
            processed += len(post_ids)

    return {"status": "Clustering complete", "processed": processed, "clusters": len(clusters)}


# ===== CLOUDFLARE WORKER ENTRYPOINT =====

class Worker(WorkerEntrypoint):
    """Cloudflare Workers AI + Supabase clustering."""

    async def fetch(self, request: Request) -> Response:
        """HTTP endpoint (optional manual trigger)."""
        result = await run_clustering_pipeline()
        return Response(json.dumps(result), headers={"Content-Type": "application/json"})

    async def scheduled(self, event, env, ctx):
        """Cron trigger handler (runs on schedule)."""
        result = await run_clustering_pipeline()
        print(f"Clustering cron: {result}")
        return result


# ===== EXPORT FOR CLOUDFLARE =====

export = Worker()



-- Run in Supabase SQL Editor

CREATE EXTENSION IF NOT EXISTS vector;

-- Posts table (pgvector)
CREATE TABLE IF NOT EXISTS posts (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  content text NOT NULL,
  embedding vector(768),
  embedding_status text DEFAULT 'pending',
  cluster_id integer,
  clustered_at timestamptz,
  created_at timestamptz DEFAULT now()
);

-- Clusters table
CREATE TABLE IF NOT EXISTS clusters (
  id serial PRIMARY KEY,
  label text NOT NULL,
  post_count integer DEFAULT 0,
  updated_at timestamptz DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS posts_embedding_idx 
  ON posts USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS posts_clustered_idx 
  ON posts(clustered_at);

-- RLS (optional security)
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_posts" ON posts FOR ALL USING (false);
ALTER TABLE clusters ENABLE ROW LEVEL SECURITY;
CREATE POLICY "service_role_clusters" ON clusters FOR ALL USING (false);
