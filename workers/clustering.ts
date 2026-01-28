/**
 * Cloudflare Workers AI + Supabase Post Clustering Pipeline
 * 
 * Uses Cloudflare Workers AI for embeddings and clustering (no Ollama needed).
 * Designed to run as a Cloudflare Worker with cron triggers.
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

// Workers AI models
const EMBED_MODEL = "@cf/baai/bge-small-en-v1.5";  // 768-dim embeddings
const CLUSTER_MODEL = "@cf/meta/llama-3.2-1b-instruct";  // fast clustering

async function generateEmbeddings(texts: string[], cfAccountId: string, cfApiToken: string): Promise<number[][]> {
  if (!texts.length) return [];

  const batchSize = 20;  // Workers AI limit
  const embeddings: number[][] = [];

  for (let i = 0; i < texts.length; i += batchSize) {
    const batch = texts.slice(i, i + batchSize);
    const payload = { text: batch };

    const resp = await fetch(
      `https://api.cloudflare.com/client/v4/accounts/${cfAccountId}/ai/run/${EMBED_MODEL}`,
      {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${cfApiToken}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      }
    );

    if (!resp.ok) {
      throw new Error(`Failed to generate embeddings: ${resp.status}`);
    }

    const data = await resp.json();
    const batchEmbeddings = data.result?.data || [];
    embeddings.push(...batchEmbeddings);
  }

  return embeddings;
}

async function clusterPostsWithLLM(posts: any[], cfAccountId: string, cfApiToken: string): Promise<any> {
  if (!posts.length) return { clusters: [] };

  // Build prompt with post contents
  const postsText = posts.map((p, i) => `#${i} (${p.id}): ${p.content.slice(0, 300)}`).join("\n");

  const prompt = `You are clustering forum/community posts into coherent topic groups.

Posts to cluster:
${postsText}

Analyze posts and return a JSON object with this structure:

{
  "clusters": [
    {
      "label": "Topic Name",
      "description": "Short description",
      "post_indexes": [0, 2, 5]
    },
    ...
  ]
}

Return ONLY valid JSON, no markdown or extra text.`;

  const payload = {
    prompt: prompt,
    max_tokens: 2000,
  };

  const resp = await fetch(
    `https://api.cloudflare.com/client/v4/accounts/${cfAccountId}/ai/run/${CLUSTER_MODEL}`,
    {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${cfApiToken}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    }
  );

  if (!resp.ok) {
    throw new Error(`Failed to cluster posts: ${resp.status}`);
  }

  const data = await resp.json();
  const text = data.result?.response || "";

  try {
    return JSON.parse(text);
  } catch (jsonError) {
    // Try to extract JSON from text
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}");
    if (start !== -1 && end !== -1) {
      return JSON.parse(text.slice(start, end + 1));
    }
    return { clusters: [] };
  }
}

async function fetchUnclusteredPosts(supabaseUrl: string, serviceRoleKey: string, limit: number = 100): Promise<any[]> {
  const resp = await fetch(
    `${supabaseUrl}/rest/v1/posts?select=id,content&clustered_at=is.null&embedding=not.is.null&limit=${limit}&order=created_at.asc`,
    {
      method: "GET",
      headers: {
        "apikey": serviceRoleKey,
        "Authorization": `Bearer ${serviceRoleKey}`,
      },
    }
  );

  if (!resp.ok) {
    throw new Error(`Failed to fetch posts: ${resp.status}`);
  }

  return await resp.json();
}

async function createClusterAndAssign(
  supabaseUrl: string,
  serviceRoleKey: string,
  label: string,
  postIds: string[]
): Promise<string> {
  // Insert cluster
  const clusterResp = await fetch(
    `${supabaseUrl}/rest/v1/clusters`,
    {
      method: "POST",
      headers: {
        "apikey": serviceRoleKey,
        "Authorization": `Bearer ${serviceRoleKey}`,
        "Content-Type": "application/json",
        "Prefer": "return=representation",
      },
      body: JSON.stringify({ label, post_count: postIds.length }),
    }
  );

  if (!clusterResp.ok) {
    throw new Error(`Failed to create cluster: ${clusterResp.status}`);
  }

  const cluster = await clusterResp.json();
  const clusterId = cluster[0].id;

  // Update posts: set cluster_id & clustered_at
  if (postIds.length > 0) {
    const idsStr = postIds.map(id => `"${id}"`).join(",");
    const updateResp = await fetch(
      `${supabaseUrl}/rest/v1/posts?id=in.(${idsStr})`,
      {
        method: "PATCH",
        headers: {
          "apikey": serviceRoleKey,
          "Authorization": `Bearer ${serviceRoleKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          cluster_id: clusterId,
          clustered_at: new Date().toISOString(),
        }),
      }
    );

    if (!updateResp.ok) {
      throw new Error(`Failed to update posts: ${updateResp.status}`);
    }
  }

  return clusterId;
}

async function runClusteringPipeline(env: Env): Promise<any> {
  // Get environment variables
  const supabaseUrl = env.SUPABASE_URL;
  const serviceRoleKey = env.SUPABASE_SERVICE_ROLE_KEY;
  const cfAccountId = env.CF_ACCOUNT_ID;
  const cfApiToken = env.CF_API_TOKEN;

  // 1. Fetch posts needing clustering
  const posts = await fetchUnclusteredPosts(supabaseUrl, serviceRoleKey, 100);
  if (!posts.length) {
    return { status: "No posts to cluster", processed: 0 };
  }

  // 2. Ask LLM to cluster them
  const clustersJson = await clusterPostsWithLLM(posts, cfAccountId, cfApiToken);
  const clusters = clustersJson.clusters || [];
  if (!clusters.length) {
    return { status: "No clusters formed", processed: 0 };
  }

  // 3. Create clusters + assign posts
  let processed = 0;
  for (const cluster of clusters) {
    const label = cluster.label || "Uncategorized";
    const postIndexes = cluster.post_indexes || [];
    const postIds = postIndexes
      .filter((i: number) => i >= 0 && i < posts.length)
      .map((i: number) => posts[i].id);

    if (postIds.length > 0) {
      await createClusterAndAssign(supabaseUrl, serviceRoleKey, label, postIds);
      processed += postIds.length;
    }
  }

  return { status: "Clustering complete", processed, clusters: clusters.length };
}
