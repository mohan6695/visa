/**
 * Cloudflare MCP Server
 * =====================
 * 
 * Implements the Model Context Protocol (MCP) over HTTP/SSE.
 * Exposes tools for:
 * 1. Semantic Search (Supabase pgvector)
 * 2. Platform Analytics (Supabase aggregation)
 * 3. Clustering Trigger (Cloudflare Workers AI)
 * 
 * Deployment:
 * wrangler deploy --config wrangler.mcp.toml
 */

import type { KVNamespace, R2Bucket } from '@cloudflare/workers-types';

export interface Env {
  SUPABASE_URL: string;
  SUPABASE_SERVICE_ROLE_KEY: string;
  CF_ACCOUNT_ID: string;
  CF_API_TOKEN: string;
  MY_BUCKET: R2Bucket;
  SESSION: KVNamespace;
  AI: any;
}

// ===== CONFIG =====
const EMBED_MODEL = "@cf/baai/bge-small-en-v1.5";

// ===== HELPER FUNCTIONS =====

async function generateEmbeddings(texts: string[], accountId: string, token: string): Promise<number[][]> {
  if (!texts.length) return [];
  
  const payload = { text: texts };
  const resp = await fetch(
    `https://api.cloudflare.com/client/v4/accounts/${accountId}/ai/run/${EMBED_MODEL}`,
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    }
  );
  
  if (!resp.ok) {
    throw new Error(`Failed to generate embeddings: ${resp.status}`);
  }
  
  const data = await resp.json();
  return data.result?.data || [];
}

async function searchPosts(query: string, limit: number, env: Env): Promise<string> {
  try {
    // 1. Generate embedding
    const embeddings = await generateEmbeddings([query], env.CF_ACCOUNT_ID, env.CF_API_TOKEN);
    if (!embeddings.length) {
      return "Failed to generate embedding";
    }
    
    const queryVector = embeddings[0];
    
    // 2. Query Supabase
    const resp = await fetch(
      `${env.SUPABASE_URL}/rest/v1/rpc/match_posts`,
      {
        method: "POST",
        headers: {
          "apikey": env.SUPABASE_SERVICE_ROLE_KEY,
          "Authorization": `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          "query_embedding": queryVector,
          "match_threshold": 0.5,
          "match_count": limit
        })
      }
    );
    
    // Fallback if RPC doesn't exist (simpler implementation)
    if (resp.status !== 200) {
         return `Search failed: ${await resp.text()}. Note: match_posts RPC might be missing.`;
    }
    
    const posts = await resp.json();
    if (!posts.length) {
      return "No matching posts found.";
    }
    
    return JSON.stringify(posts, null, 2);
    
  } catch (error) {
    return `Error searching posts: ${(error as Error).message}`;
  }
}

async function getAnalytics(days: number, env: Env): Promise<string> {
  try {
    // Count posts
    const postsResp = await fetch(
      `${env.SUPABASE_URL}/rest/v1/posts?select=count`,
      {
        method: "GET",
        headers: {
          "apikey": env.SUPABASE_SERVICE_ROLE_KEY,
          "Authorization": `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
          "Range": "0-0"
        }
      }
    );
    const totalPosts = postsResp.headers.get("Content-Range")?.split("/")?.[1] || "0";
    
    // Count clusters
    const clustersResp = await fetch(
      `${env.SUPABASE_URL}/rest/v1/clusters?select=count`,
      {
        method: "GET",
        headers: {
          "apikey": env.SUPABASE_SERVICE_ROLE_KEY,
          "Authorization": `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
          "Range": "0-0"
        }
      }
    );
    const totalClusters = clustersResp.headers.get("Content-Range")?.split("/")?.[1] || "0";
    
    return JSON.stringify({
      total_posts: totalPosts,
      total_clusters: totalClusters,
      period_days: days,
      status: "active"
    }, null, 2);
    
  } catch (error) {
    return `Error fetching analytics: ${(error as Error).message}`;
  }
}

async function triggerClusteringJob(env: Env): Promise<string> {
  return "Clustering job trigger sent (Simulation). To implement fully, bind the clustering worker.";
}

// ===== MCP PROTOCOL LOGIC =====

const TOOLS = [
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
];

async function handleToolCall(name: string, args: any, env: Env): Promise<string> {
  if (name === "search_posts") {
    return await searchPosts(args.query, args.limit || 5, env);
  } else if (name === "get_analytics") {
    return await getAnalytics(args.days || 7, env);
  } else if (name === "trigger_clustering") {
    return await triggerClusteringJob(env);
  }
  return `Unknown tool: ${name}`;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const method = request.method;
    const path = url.pathname;
    
    // SSE Endpoint
    if (path.endsWith("/sse")) {
      return new Response("d5a42094-1188-47v7-b123-5e26710486c1", {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          "Connection": "keep-alive"
        }
      });
    }
    
    // Message Endpoint (JSON-RPC)
    if (method === "POST" && path.endsWith("/messages")) {
      try {
        const body = await request.json();
        const methodName = body.method;
        const reqId = body.id;
        
        let result: any = null;
        
        if (methodName === "tools/list") {
          result = {"tools": TOOLS};
        } else if (methodName === "tools/call") {
          const params = body.params || {};
          const name = params.name;
          const args = params.arguments || {};
          const content = await handleToolCall(name, args, env);
          result = {"content": [{"type": "text", "text": content}]};
        } else {
          // Initialize or other methods
          return new Response(JSON.stringify({
            "jsonrpc": "2.0",
            "id": reqId,
            "result": {}
          }), {
            headers: {"Content-Type": "application/json"}
          });
        }
        
        return new Response(JSON.stringify({
          "jsonrpc": "2.0",
          "id": reqId,
          "result": result
        }), {
          headers: {"Content-Type": "application/json"}
        });
        
      } catch (error) {
        return new Response(JSON.stringify({
          "jsonrpc": "2.0",
          "error": {"code": -32603, "message": (error as Error).message}
        }), {
          status: 500,
          headers: {"Content-Type": "application/json"}
        });
      }
    }
    
    return new Response("MCP Server Running", {status: 200});
  }
};
