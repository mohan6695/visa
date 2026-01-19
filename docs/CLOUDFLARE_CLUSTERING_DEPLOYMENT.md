# Cloudflare Workers AI Clustering - Deployment Guide

## Overview

This guide covers deploying the Cloudflare Workers AI clustering pipeline that automatically clusters posts using Cloudflare's AI models (no Ollama needed).

## Architecture

```
Cloudflare Workers AI
  ├── BGE Embeddings (@cf/baai/bge-small-en-v1.5)
  └── Llama 3.2 Clustering (@cf/meta/llama-3.2-1b-instruct)
       ↓
Supabase PostgreSQL + pgvector
  ├── posts table (with embeddings)
  └── clusters table
```

## Prerequisites

- Cloudflare account with Workers AI enabled
- Supabase project
- Python Cloudflare Workers support (`pywrangler`)

## Step 1: Supabase Setup

Run the SQL migration in your Supabase SQL Editor:

```bash
# File: supabase_migrations/007_cloudflare_workers_clustering.sql
```

This creates:
- `posts` table with pgvector support (768-dim embeddings)
- `clusters` table
- HNSW indexes for fast similarity search
- RLS policies
- Auto-update triggers

## Step 2: Configure Cloudflare Secrets

Set required secrets using Wrangler CLI:

```bash
# Supabase credentials
wrangler secret put SUPABASE_URL
# Enter: https://YOUR_PROJECT.supabase.co

wrangler secret put SUPABASE_SERVICE_ROLE_KEY
# Enter: your-service-role-key (from Supabase settings)

# Cloudflare credentials
wrangler secret put CF_ACCOUNT_ID
# Enter: your-cloudflare-account-id

wrangler secret put CF_API_TOKEN
# Enter: your-cloudflare-api-token
```

## Step 3: Deploy Worker

Deploy the clustering worker:

```bash
# Deploy using clustering-specific config
wrangler deploy --config wrangler.clustering.toml

# Or for production
wrangler deploy --config wrangler.clustering.toml --env production
```

## Step 4: Verify Deployment

Test the worker manually:

```bash
# Trigger clustering manually via HTTP
curl https://visa-clustering-worker.YOUR_SUBDOMAIN.workers.dev

# Expected response:
# {"status": "Clustering complete", "processed": 25, "clusters": 5}
```

## Cron Schedule

The worker runs automatically every 15 minutes to cluster new posts:

```toml
[triggers]
crons = ["*/15 * * * *"]  # Every 15 minutes
```

Adjust in `wrangler.clustering.toml` as needed.

## Monitoring

View worker logs in Cloudflare dashboard:

```
Workers & Pages → visa-clustering-worker → Logs
```

Common log messages:
- `"No posts to cluster"` - No unclustered posts found
- `"No clusters formed"` - LLM didn't create clusters
- `"Clustering complete"` - Success!

## Cost Estimation

### Cloudflare Workers AI

- **BGE Embeddings**: ~$0.004 per 1000 embeddings
- **Llama 3.2**: ~$0.01 per 1000 tokens
- **Expected cost**: ~$1-5/month for 10,000 posts

### Supabase

- Free tier includes pgvector
- Upgrade to Pro ($25/month) for production scale

## Troubleshooting

### "Invalid binding `SESSION`" error

Add SESSION KV binding to `wrangler.clustering.toml`:

```toml
[[kv_namespaces]]
binding = "SESSION"
id = "your-kv-namespace-id"
```

### "Unauthorized" errors

Check that service role key has correct permissions in Supabase.

### Clusters not forming

LLM may need more context. Increase batch size or adjust prompt in `workers/clustering.py`.

## Manual Testing

Insert test posts in Supabase:

```sql
INSERT INTO posts (content, embedding_status) VALUES
  ('Best visa for students in USA?', 'pending'),
  ('Canada PR requirements 2026', 'pending'),
  ('UK work visa timeline', 'pending');
```

Then trigger clustering and check `clusters` table.

## Next Steps

1. Set up monitoring/alerts for failed runs
2. Implement embedding generation for new posts
3. Add cluster analytics dashboard
4. Configure cluster merging for similar topics
