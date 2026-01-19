-- Cloudflare Workers AI + Supabase Clustering Schema
-- Run this in your Supabase SQL Editor

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Posts table with pgvector embeddings
CREATE TABLE IF NOT EXISTS posts (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  content text NOT NULL,
  embedding vector(768),  -- Cloudflare BGE embeddings are 768-dim
  embedding_status text DEFAULT 'pending',
  cluster_id integer,
  clustered_at timestamptz,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Clusters table
CREATE TABLE IF NOT EXISTS clusters (
  id serial PRIMARY KEY,
  label text NOT NULL,
  description text,
  post_count integer DEFAULT 0,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS posts_embedding_idx 
  ON posts USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS posts_clustered_idx 
  ON posts(clustered_at) WHERE clustered_at IS NULL;

CREATE INDEX IF NOT EXISTS posts_cluster_id_idx 
  ON posts(cluster_id);

CREATE INDEX IF NOT EXISTS clusters_label_idx 
  ON clusters(label);

-- Row Level Security (RLS)
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE clusters ENABLE ROW LEVEL SECURITY;

-- Service role can do everything (for Workers)
CREATE POLICY "service_role_posts_all" 
  ON posts FOR ALL 
  USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "service_role_clusters_all" 
  ON clusters FOR ALL 
  USING (auth.jwt() ->> 'role' = 'service_role');

-- Public can read posts and clusters
CREATE POLICY "public_read_posts" 
  ON posts FOR SELECT 
  USING (true);

CREATE POLICY "public_read_clusters" 
  ON clusters FOR SELECT 
  USING (true);

-- Function to update cluster post counts
CREATE OR REPLACE FUNCTION update_cluster_post_count()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
    UPDATE clusters 
    SET post_count = (SELECT COUNT(*) FROM posts WHERE cluster_id = NEW.cluster_id),
        updated_at = now()
    WHERE id = NEW.cluster_id;
  END IF;
  
  IF TG_OP = 'DELETE' THEN
    UPDATE clusters 
    SET post_count = (SELECT COUNT(*) FROM posts WHERE cluster_id = OLD.cluster_id),
        updated_at = now()
    WHERE id = OLD.cluster_id;
  END IF;
  
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to keep cluster counts updated
DROP TRIGGER IF EXISTS update_cluster_count ON posts;
CREATE TRIGGER update_cluster_count
  AFTER INSERT OR UPDATE OF cluster_id OR DELETE ON posts
  FOR EACH ROW
  EXECUTE FUNCTION update_cluster_post_count();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_posts_updated_at 
  BEFORE UPDATE ON posts
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clusters_updated_at 
  BEFORE UPDATE ON clusters
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
