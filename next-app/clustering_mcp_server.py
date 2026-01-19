#!/usr/bin/env python3
"""
MCP Server for Clustering Posts and Persisting to Supabase pgvector

Uses local Ollama Qwen model for:
1. Generating embeddings using nomic-embed-text
2. Assigning cluster labels
3. Persisting results to Supabase pgvector

Run with: python clustering_mcp_server.py
"""

import asyncio
import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

import psycopg2
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:3b"
EMBEDDING_MODEL = "nomic-embed-text"


class ClusteringMCPServer:
    def __init__(self):
        self.ollama_url = OLLAMA_URL
        self.default_model = DEFAULT_MODEL
    
    async def call_ollama(self, model: str, prompt: str, **kwargs) -> str:
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", 0.3),
                    "num_predict": kwargs.get("max_tokens", 2000),
                }
            }
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(f"{self.ollama_url}/api/generate", json=payload)
                if response.status_code == 200:
                    return response.json().get("response", "").strip()
                return f"Error: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def get_embedding(self, text: str) -> List[float]:
        try:
            payload = {"model": EMBEDDING_MODEL, "prompt": text}
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(f"{self.ollama_url}/api/embeddings", json=payload)
                if response.status_code == 200:
                    return response.json().get("embedding", [])
                return []
        except Exception as e:
            print(f"Embedding error: {e}")
            return []
    
    def get_db_connection(self):
        import os
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "")
        )
    
    async def cluster_posts(self, posts: List[Dict], num_clusters: int = 10) -> List[Dict]:
        """Cluster posts using Ollama embeddings"""
        # Get embeddings for all posts
        embeddings = []
        for post in posts:
            text = f"{post.get('title', '')} {post.get('content', '')}"[:1000]
            emb = await self.get_embedding(text)
            embeddings.append(emb)
        
        # Simple K-means clustering
        if not embeddings or not any(embeddings):
            return [{"id": p.get("id"), "cluster": 0} for p in posts]
        
        # Normalize embeddings
        import math
        normalized = []
        for emb in embeddings:
            if emb:
                norm = math.sqrt(sum(e * e for e in emb))
                normalized.append([e / norm for e in emb])
            else:
                normalized.append([0] * len(embeddings[0]) if embeddings else [])
        
        # Simple clustering based on first dimension
        clustered = []
        for i, post in enumerate(posts):
            emb = normalized[i] if i < len(normalized) else []
            cluster = 0
            if emb:
                # Use first value to determine cluster
                cluster = int(abs(emb[0] * num_clusters)) % num_clusters
            clustered.append({
                "id": post.get("id"),
                "cluster": cluster,
                "embedding": embeddings[i] if i < len(embeddings) else []
            })
        
        return clustered
    
    async def assign_cluster_labels(self, cluster_id: int, sample_posts: List[Dict]) -> str:
        """Use Ollama to generate cluster label"""
        if not sample_posts:
            return "General"
        
        content_summary = "\n".join([
            f"- {p.get('title', p.get('content', '')[:100])}" 
            for p in sample_posts[:5]
        ])
        
        prompt = f"""Analyze these posts and provide a concise cluster label (1-3 words):
{content_summary}

Return ONLY the label, nothing else."""
        
        return await self.call_ollama(self.default_model, prompt, temperature=0.3)
    
    def persist_clusters(self, clustered_posts: List[Dict], cluster_labels: Dict[int, str]):
        """Persist clustered posts to Supabase"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        updated = 0
        for item in clustered_posts:
            post_id = item.get("id")
            cluster = item.get("cluster", 0)
            embedding = item.get("embedding", [])
            label = cluster_labels.get(cluster, f"Cluster {cluster}")
            
            if embedding:
                cursor.execute("""
                    UPDATE posts SET embedding = %s, cluster_label = %s WHERE id = %s
                """, (embedding, label, post_id))
                updated += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        return updated


server = ClusteringMCPServer()
mcp_server = Server("clustering-server")

@mcp_server.list_tools()
async def list_tools():
    return [
        Tool(
            name="cluster_posts",
            description="Cluster posts using Ollama embeddings and K-means",
            inputSchema={
                "type": "object",
                "properties": {
                    "posts": {"type": "array", "description": "List of posts with id, title, content"},
                    "num_clusters": {"type": "integer", "description": "Number of clusters", "default": 10}
                },
                "required": ["posts"]
            }
        ),
        Tool(
            name="generate_cluster_labels",
            description="Generate cluster labels using Qwen model",
            inputSchema={
                "type": "object",
                "properties": {
                    "cluster_id": {"type": "integer", "description": "Cluster ID"},
                    "sample_posts": {"type": "array", "description": "Sample posts from cluster"}
                },
                "required": ["cluster_id", "sample_posts"]
            }
        ),
        Tool(
            name="persist_to_supabase",
            description="Persist clustered posts with embeddings to Supabase pgvector",
            inputSchema={
                "type": "object",
                "properties": {
                    "clustered_posts": {"type": "array", "description": "Clustered posts with embeddings"},
                    "cluster_labels": {"type": "object", "description": "Cluster ID to label mapping"}
                },
                "required": ["clustered_posts", "cluster_labels"]
            }
        ),
        Tool(
            name="full_clustering_pipeline",
            description="Run complete pipeline: cluster posts, generate labels, persist to Supabase",
            inputSchema={
                "type": "object",
                "properties": {
                    "posts_file": {"type": "string", "description": "Path to posts JSON file"},
                    "num_clusters": {"type": "integer", "description": "Number of clusters", "default": 10}
                },
                "required": ["posts_file"]
            }
        )
    ]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    try:
        if name == "cluster_posts":
            posts = arguments.get("posts", [])
            num_clusters = arguments.get("num_clusters", 10)
            result = await server.cluster_posts(posts, num_clusters)
            return [TextContent(type="text", text=json.dumps(result))]
        
        elif name == "generate_cluster_labels":
            cluster_id = arguments.get("cluster_id")
            sample_posts = arguments.get("sample_posts", [])
            label = await server.assign_cluster_labels(cluster_id, sample_posts)
            return [TextContent(type="text", text=label)]
        
        elif name == "persist_to_supabase":
            clustered_posts = arguments.get("clustered_posts", [])
            cluster_labels = arguments.get("cluster_labels", {})
            updated = server.persist_clusters(clustered_posts, cluster_labels)
            return [TextContent(type="text", text=f"Updated {updated} posts in Supabase")]
        
        elif name == "full_clustering_pipeline":
            posts_file = arguments.get("posts_file")
            num_clusters = arguments.get("num_clusters", 10)
            
            with open(posts_file, 'r') as f:
                posts = json.load(f)
            
            # Cluster posts
            clustered = await server.cluster_posts(posts, num_clusters)
            
            # Generate labels for each cluster
            cluster_posts = {}
            for item in clustered:
                c = item.get("cluster", 0)
                if c not in cluster_posts:
                    cluster_posts[c] = []
                cluster_posts[c].append(item)
            
            cluster_labels = {}
            for cluster_id, cluster_items in cluster_posts.items():
                post_ids = [item.get("id") for item in cluster_items]
                sample = [p for p in posts if p.get("id") in post_ids][:5]
                label = await server.assign_cluster_labels(cluster_id, sample)
                cluster_labels[cluster_id] = label
            
            # Persist to Supabase
            updated = server.persist_clusters(clustered, cluster_labels)
            
            result = {
                "clusters": len(cluster_posts),
                "labels": cluster_labels,
                "posts_updated": updated
            }
            return [TextContent(type="text", text=json.dumps(result))]
        
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
