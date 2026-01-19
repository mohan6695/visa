-- Hybrid Search with RRF and FlashRank Reranking
-- StackOverflow-style sidebar posts with sub-200ms latency

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create posts table with embedding support
CREATE TABLE IF NOT EXISTS posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL,
    author_id UUID,
    title TEXT,
    content TEXT NOT NULL,
    content_html TEXT,
    embedding VECTOR(1536),  -- OpenAI text-embedding-3-small dimension
    url TEXT,
    source_id TEXT UNIQUE,   -- External ID from source (Facebook/Reddit)
    source_type TEXT DEFAULT 'facebook',
    upvotes INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'published' CHECK (status IN ('published', 'draft', 'archived', 'deleted')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Posts are viewable by everyone" ON posts
    FOR SELECT USING (status = 'published');

CREATE POLICY "Authenticated users can insert posts" ON posts
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Create indexes for hybrid search
CREATE INDEX IF NOT EXISTS idx_posts_embedding ON posts 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_posts_search ON posts 
    USING gin (to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, '')));

CREATE INDEX IF NOT EXISTS idx_posts_group_id ON posts(group_id);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_source_id ON posts(source_id);

-- =============================================
-- HYBRID SEARCH FUNCTIONS
-- =============================================

-- 1. Semantic search using pgvector
CREATE OR REPLACE FUNCTION semantic_search(
    query_embedding VECTOR(1536),
    group_id_param UUID,
    limit_count INT DEFAULT 20
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.title,
        p.content,
        1 - (p.embedding <=> query_embedding) as similarity_score
    FROM posts p
    WHERE 
        p.group_id = group_id_param
        AND p.status = 'published'
        AND p.embedding IS NOT NULL
    ORDER BY p.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 2. Keyword search using BM25 (Full Text Search)
CREATE OR REPLACE FUNCTION keyword_search(
    query_text TEXT,
    group_id_param UUID,
    limit_count INT DEFAULT 20
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    keyword_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.title,
        p.content,
        ts_rank(
            to_tsvector('english', coalesce(p.title, '') || ' ' || coalesce(p.content, '')),
            plainto_tsquery('english', query_text)
        )::float as keyword_score
    FROM posts p
    WHERE 
        p.group_id = group_id_param
        AND p.status = 'published'
        AND to_tsvector('english', coalesce(p.title, '') || ' ' || coalesce(p.content, '')) 
            @@ plainto_tsquery('english', query_text)
    ORDER BY keyword_score DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 3. Reciprocal Rank Fusion (RRF) to merge results
CREATE OR REPLACE FUNCTION rrf_merge(
    semantic_results UUID[],
    keyword_results UUID[],
    limit_count INT DEFAULT 30
)
RETURNS TABLE (
    doc_id UUID,
    rrf_score FLOAT
) AS $$
DECLARE
    k CONSTANT := 60;  -- RRF constant
    doc_scores RECORD;
BEGIN
    -- Create temp table for scores
    CREATE TEMP TABLE IF NOT EXISTS rrf_scores (
        doc_id UUID PRIMARY KEY,
        score FLOAT DEFAULT 0
    );
    
    -- Clear previous scores
    DELETE FROM rrf_scores;
    
    -- Add semantic scores (weight 0.7)
    FOR i IN 1..array_length(semantic_results, 1) LOOP
        INSERT INTO rrf_scores (doc_id, score)
        VALUES (semantic_results[i], 0.7 * (1.0 / (i + k)))
        ON CONFLICT (doc_id) DO UPDATE SET 
            score = rrf_scores.score + 0.7 * (1.0 / (i + k));
    END LOOP;
    
    -- Add keyword scores (weight 0.3)
    FOR i IN 1..array_length(keyword_results, 1) LOOP
        INSERT INTO rrf_scores (doc_id, score)
        VALUES (keyword_results[i], 0.3 * (1.0 / (i + k)))
        ON CONFLICT (doc_id) DO UPDATE SET 
            score = rrf_scores.score + 0.3 * (1.0 / (i + k));
    END LOOP;
    
    -- Return merged results
    RETURN QUERY
    SELECT doc_id, score as rrf_score
    FROM rrf_scores
    ORDER BY score DESC
    LIMIT limit_count;
    
    -- Clean up
    DROP TABLE IF EXISTS rrf_scores;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. Main hybrid search function
CREATE OR REPLACE FUNCTION hybrid_search(
    query_embedding VECTOR(1536),
    query_text TEXT,
    group_id_param UUID,
    semantic_limit INT DEFAULT 40,
    keyword_limit INT DEFAULT 40,
    final_limit INT DEFAULT 30
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    score FLOAT,
    rank_method TEXT
) AS $$
DECLARE
    semantic_results UUID[];
    keyword_results UUID[];
    merged_results RECORD;
BEGIN
    -- Get semantic results
    SELECT array_agg(id ORDER BY similarity_score DESC) INTO semantic_results
    FROM semantic_search(query_embedding, group_id_param, semantic_limit);
    
    -- Get keyword results
    SELECT array_agg(id ORDER BY keyword_score DESC) INTO keyword_results
    FROM keyword_search(query_text, group_id_param, keyword_limit);
    
    -- Merge with RRF
    FOR merged_results IN 
        SELECT doc_id, rrf_score
        FROM rrf_merge(
            COALESCE(semantic_results, ARRAY[]::UUID[]),
            COALESCE(keyword_results, ARRAY[]::UUID[]),
            final_limit
        )
    LOOP
        RETURN QUERY
        SELECT 
            merged_results.doc_id,
            p.title,
            p.content,
            merged_results.rrf_score as score,
            'rrf' as rank_method
        FROM posts p
        WHERE p.id = merged_results.doc_id;
    END LOOP;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- CACHING FUNCTIONS (for Redis)
-- =============================================

-- Function to generate cache key for hybrid search
CREATE OR REPLACE FUNCTION generate_search_cache_key(
    group_id_param UUID,
    query_hash TEXT
)
RETURNS TEXT AS $$
BEGIN
    RETURN 'hybrid_search:' || group_id_param::TEXT || ':' || query_hash;
END;
$$ LANGUAGE plpgsql;

-- Function to cache search results (for manual cache population)
CREATE OR REPLACE FUNCTION cache_hybrid_results(
    group_id_param UUID,
    query_hash TEXT,
    result_data JSONB
)
RETURNS BOOLEAN AS $$
BEGIN
    -- This would be called from application layer with Redis
    RETURN true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- SIDEBAR POSTS FUNCTION
-- =============================================

-- Get sidebar posts for a group (top 12 posts)
CREATE OR REPLACE FUNCTION get_sidebar_posts(
    group_id_param UUID,
    exclude_post_id UUID DEFAULT NULL,
    limit_count INT DEFAULT 12
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    url TEXT,
    upvotes INTEGER,
    comment_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.title,
        p.content,
        p.url,
        p.upvotes,
        p.comment_count,
        p.created_at
    FROM posts p
    WHERE 
        p.group_id = group_id_param
        AND p.status = 'published'
        AND p.id != COALESCE(exclude_post_id, '00000000-0000-0000-0000-000000000000'::UUID)
    ORDER BY 
        p.upvotes DESC,
        p.comment_count DESC,
        p.created_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- GRANT PERMISSIONS
-- =============================================

GRANT EXECUTE ON FUNCTION semantic_search(VECTOR, UUID, INT) TO authenticated, anon;
GRANT EXECUTE ON FUNCTION keyword_search(TEXT, UUID, INT) TO authenticated, anon;
GRANT EXECUTE ON FUNCTION rrf_merge(UUID[], UUID[], INT) TO authenticated, anon;
GRANT EXECUTE ON FUNCTION hybrid_search(VECTOR, TEXT, UUID, INT, INT, INT) TO authenticated, anon;
GRANT EXECUTE ON FUNCTION get_sidebar_posts(UUID, UUID, INT) TO authenticated, anon;
GRANT SELECT ON posts TO authenticated, anon;
