-- =============================================
-- Complete Supabase RAG Chatbot Pipeline Schema
-- Run in Supabase SQL Editor
-- =============================================

-- =============================================
-- 1. Enable pgvector Extension
-- =============================================
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================
-- 2. Posts Table (metadata + embeddings + Storage reference)
-- =============================================
CREATE TABLE IF NOT EXISTS posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL,
    title TEXT NOT NULL,
    short_excerpt TEXT,
    storage_path TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(768),
    cluster_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for Posts
CREATE INDEX IF NOT EXISTS idx_posts_group ON posts(group_id);
CREATE INDEX IF NOT EXISTS idx_posts_cluster ON posts(cluster_id);
CREATE INDEX IF NOT EXISTS idx_posts_hnsw ON posts USING hnsw(embedding vector_cosine_ops);

-- =============================================
-- 3. Clusters Table (centroids for K-means)
-- =============================================
CREATE TABLE IF NOT EXISTS post_clusters (
    cluster_id INTEGER PRIMARY KEY,
    centroid_embedding VECTOR(768),
    summary TEXT,
    post_count INTEGER DEFAULT 0
);

-- =============================================
-- 4. Jobs Queue for Automatic Embeddings
-- =============================================
CREATE TABLE IF NOT EXISTS embedding_jobs (
    id SERIAL PRIMARY KEY,
    post_id UUID REFERENCES posts(id),
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- 5. Trigger for Auto-queueing Embedding Jobs
-- =============================================
CREATE OR REPLACE FUNCTION enqueue_embedding()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO embedding_jobs (post_id) VALUES (NEW.id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_posts_enqueue_embedding ON posts;
CREATE TRIGGER trg_posts_enqueue_embedding
AFTER INSERT ON posts
FOR EACH ROW EXECUTE FUNCTION enqueue_embedding();

-- =============================================
-- 6. Hybrid Search RPC Functions
-- =============================================

-- Semantic Search using Vector Similarity
CREATE OR REPLACE FUNCTION match_posts_semantic(
    query_embedding VECTOR(768),
    group_id UUID,
    limit_count INT DEFAULT 30
)
RETURNS TABLE (
    id UUID, 
    title TEXT, 
    short_excerpt TEXT, 
    storage_path TEXT, 
    score FLOAT
) AS $$
SELECT 
    p.id, 
    p.title, 
    p.short_excerpt, 
    p.storage_path,
    1 - (p.embedding <=> query_embedding) AS score
FROM posts p 
WHERE p.group_id = match_posts_semantic.group_id 
    AND p.embedding IS NOT NULL
ORDER BY p.embedding <=> query_embedding
LIMIT limit_count;
$$ LANGUAGE sql STABLE;

-- Full-text Keyword Search
CREATE OR REPLACE FUNCTION match_posts_keyword(
    query_text TEXT,
    group_id UUID,
    limit_count INT DEFAULT 30
)
RETURNS TABLE (
    id UUID, 
    title TEXT, 
    short_excerpt TEXT, 
    storage_path TEXT, 
    score FLOAT
) AS $$
SELECT 
    p.id, 
    p.title, 
    p.short_excerpt, 
    p.storage_path,
    ts_rank_cd(
        to_tsvector('english', p.title || ' ' || p.short_excerpt), 
        plainto_tsquery('english', query_text)
    ) AS score
FROM posts p 
WHERE p.group_id = match_posts_keyword.group_id
ORDER BY score DESC
LIMIT limit_count;
$$ LANGUAGE sql STABLE;

-- =============================================
-- 7. Cluster Assignment RPC
-- =============================================
CREATE OR REPLACE FUNCTION assign_cluster(post_embedding VECTOR(768))
RETURNS INTEGER AS $$
DECLARE
    nearest_cluster INTEGER;
BEGIN
    SELECT c.cluster_id INTO nearest_cluster
    FROM post_clusters c
    ORDER BY c.centroid_embedding <=> post_embedding
    LIMIT 1;
    
    RETURN nearest_cluster;
END;
$$ LANGUAGE plpgsql STABLE;

-- =============================================
-- 8. RLS Policies (Row Level Security)
-- =============================================
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE embedding_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_clusters ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to create posts
CREATE POLICY "Users can insert posts" ON posts
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Allow public read access to posts
CREATE POLICY "Public can view posts" ON posts
    FOR SELECT USING (true);

-- Service role can manage everything
CREATE POLICY "Service role can manage posts" ON posts
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage jobs" ON embedding_jobs
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage clusters" ON post_clusters
    FOR ALL USING (auth.role() = 'service_role');

-- =============================================
-- 9. Seed Sample Data (Optional)
-- =============================================
INSERT INTO post_clusters (cluster_id, centroid_embedding, summary, post_count)
VALUES 
    (1, gen_random_vector(768), 'H1B Visa Discussions', 0),
    (2, gen_random_vector(768), 'Green Card Applications', 0),
    (3, gen_random_vector(768), 'OPT/CPT Questions', 0),
    (4, gen_random_vector(768), 'Citizenship & Naturalization', 0),
    (5, gen_random_vector(768), 'General Visa Discussions', 0)
ON CONFLICT (cluster_id) DO NOTHING;

SELECT 'RAG Chatbot Schema created successfully!' as status;
