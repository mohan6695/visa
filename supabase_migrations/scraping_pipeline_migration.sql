-- 1. Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net;
CREATE EXTENSION IF NOT EXISTS pgmq;

-- 2. Tables

-- Posts table with pgvector
CREATE TABLE IF NOT EXISTS posts (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  scraped_url text UNIQUE,
  title text,
  content text,
  embedding vector(384),
  embedding_status text DEFAULT 'pending',
  cluster_id integer,
  created_at timestamptz DEFAULT now(),
  processed_at timestamptz
);

-- Clusters table
CREATE TABLE IF NOT EXISTS clusters (
  id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  centroid vector(384),
  summary text,
  label text,
  post_count integer DEFAULT 0,
  updated_at timestamptz DEFAULT now()
);

-- 3. Indexes for pgvector
CREATE INDEX IF NOT EXISTS posts_embedding_idx
  ON posts USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS clusters_centroid_idx
  ON clusters USING hnsw (centroid vector_cosine_ops);

-- 4. PGMQ queue for raw posts from Apify (before embeddings)
SELECT pgmq.create('post_queue') WHERE NOT EXISTS (
  SELECT 1 FROM pgmq.queues WHERE name = 'post_queue'
);

-- 5. RLS: restrict direct access; only Edge Functions (service_role) should touch

ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE clusters ENABLE ROW LEVEL SECURITY;

-- Optional: allow nothing by default
DROP POLICY IF EXISTS "Allow all posts" ON posts;
DROP POLICY IF EXISTS "Allow all clusters" ON clusters;

CREATE POLICY "Service role only posts"
  ON posts
  FOR ALL
  USING (false);

CREATE POLICY "Service role only clusters"
  ON clusters
  FOR ALL
  USING (false);

-- 6. RPC: find nearest centroid
CREATE OR REPLACE FUNCTION assign_nearest_centroid(query_emb vector)
RETURNS TABLE (id integer, distance float) AS $$
BEGIN
  RETURN QUERY
  SELECT
    c.id,
    c.centroid <=> query_emb AS distance
  FROM clusters c
  ORDER BY c.centroid <=> query_emb
  LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- 7. RPC: update cluster count (increment post_count)
CREATE OR REPLACE FUNCTION update_cluster_count(cluster_id integer)
RETURNS void AS $$
BEGIN
  UPDATE clusters
  SET post_count = post_count + 1,
      updated_at = now()
  WHERE id = cluster_id;
END;
$$ LANGUAGE plpgsql;

-- 8. Cron jobs to call Edge Functions (you will set actual project URL)

-- Replace YOUR_PROJECT_ID with your project ref.
-- Also ensure app.settings.service_role_key is set (Supabase config).

-- CRON1: Apify scrape hourly
SELECT cron.schedule(
  'apify-scrape',
  '0 * * * *',
  $$
  SELECT net.http_post(
    url := 'https://YOUR_PROJECT_ID.functions.supabase.co/apify-scrape',
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key')
    )
  );
  $$
);

-- CRON2: generate embeddings every 1 min
SELECT cron.schedule(
  'generate-embeddings',
  '*/1 * * * *',
  $$
  SELECT net.http_post(
    url := 'https://YOUR_PROJECT_ID.functions.supabase.co/generate-embeddings',
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key')
    )
  );
  $$
);

-- CRON3: cluster posts every 5 min
SELECT cron.schedule(
  'cluster-posts',
  '*/5 * * * *',
  $$
  SELECT net.http_post(
    url := 'https://YOUR_PROJECT_ID.functions.supabase.co/cluster-posts',
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key')
    )
  );
  $$
);

-- CRON4: summarize clusters every 15 min
SELECT cron.schedule(
  'summarize-clusters',
  '*/15 * * * *',
  $$
  SELECT net.http_post(
    url := 'https://YOUR_PROJECT_ID.functions.supabase.co/summarize-clusters',
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key')
    )
  );
  $$
);