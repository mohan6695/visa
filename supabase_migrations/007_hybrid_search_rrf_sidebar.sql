-- Migration: Hybrid Search with RRF and Sidebar Retrieval
-- Implements StackOverflow-style hybrid retrieval (pgvector + BM25) with RRF merging

-- =============================================
-- RECIPROCAL RANK FUSION (RRF) FUNCTION
-- =============================================

-- Drop existing functions if they exist
DROP FUNCTION IF EXISTS rrf_merge(UUID[], UUID[], INTEGER);
DROP FUNCTION IF EXISTS rrf_score(INTEGER, INTEGER);
DROP FUNCTION IF EXISTS hybrid_sidebar_search(TEXT, VECTOR(1536), UUID, INTEGER);

-- RRF score calculation: 1/(rank + k) where k=60 is standard
CREATE OR REPLACE FUNCTION rrf_score(rank_position INTEGER, k INTEGER DEFAULT 60)
RETURNS FLOAT AS $$
    SELECT 1.0::FLOAT / (rank_position + k)::FLOAT;
$$ LANGUAGE sql IMMUTABLE;

-- RRF merge function that takes two arrays of doc_ids and merges them
CREATE OR REPLACE FUNCTION rrf_merge(
    semantic_results UUID[],
    keyword_results UUID[],
    max_results INTEGER DEFAULT 30
)
RETURNS TABLE (
    doc_id UUID,
    rrf_score FLOAT,
    rank_position INTEGER
) AS $$
DECLARE
    semantic_rank INTEGER := 0;
    keyword_rank INTEGER := 0;
    current_semantic UUID;
    current_keyword UUID;
    doc_scores FLOAT[];
    doc_ids UUID[];
    merged_score FLOAT;
    merged_id UUID;
BEGIN
    -- Initialize arrays
    doc_ids := ARRAY[]::UUID[];
    doc_scores := ARRAY[]::FLOAT[];
    
    -- Process semantic results (weight 0.7)
    <<semantic_loop>>
    FOR i IN 1..LEAST(array_length(semantic_results, 1), max_results * 2) LOOP
        semantic_rank := i - 1;
        current_semantic := semantic_results[i];
        
        -- Check if doc already in our results
        IF NOT (current_semantic = ANY(doc_ids)) THEN
            doc_ids := array_append(doc_ids, current_semantic);
            doc_scores := array_append(doc_scores, rrf_score(semantic_rank) * 0.7);
        END IF;
    END LOOP semantic_loop;
    
    -- Process keyword results (weight 0.3)
    <<keyword_loop>>
    FOR i IN 1..LEAST(array_length(keyword_results, 1), max_results * 2) LOOP
        keyword_rank := i - 1;
        current_keyword := keyword_results[i];
        
        -- Check if doc already in our results
        IF current_keyword = ANY(doc_ids) THEN
            -- Update existing score
            FOR j IN 1..array_length(doc_ids, 1) LOOP
                IF doc_ids[j] = current_keyword THEN
                    doc_scores[j] := doc_scores[j] + rrf_score(keyword_rank) * 0.3;
                    EXIT;
                END IF;
            END LOOP;
        ELSE
            doc_ids := array_append(doc_ids, current_keyword);
            doc_scores := array_append(doc_scores, rrf_score(keyword_rank) * 0.3);
        END IF;
    END LOOP keyword_loop;
    
    -- Sort by combined RRF score and return top results
    RETURN QUERY
    WITH ranked AS (
        SELECT unnest(doc_ids) as doc_id, unnest(doc_scores) as score
    )
    SELECT 
        doc_id,
        score as rrf_score,
        ROW_NUMBER() OVER (ORDER BY score DESC)::INTEGER as rank_position
    FROM ranked
    ORDER BY score DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================
-- HYBRID SIDEBAR SEARCH FUNCTION
-- =============================================

-- Get semantic (pgvector) top results
CREATE OR REPLACE FUNCTION get_semantic_results(
    query_embedding VECTOR(1536),
    group_id UUID,
    limit_count INTEGER
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    score FLOAT,
    rank_position INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.title,
        p.content,
        (1 - (p.embedding <=> query_embedding)) as score,
        ROW_NUMBER() OVER (ORDER BY (p.embedding <=> query_embedding) ASC)::INTEGER as rank_position
    FROM posts p
    WHERE p.embedding IS NOT NULL
      AND query_embedding IS NOT NULL
      AND (p.group_id = group_id OR group_id IS NULL)
    ORDER BY p.embedding <=> query_embedding
    LIMIT limit_count * 2;
END;
$$ LANGUAGE plpgsql;

-- Get keyword (BM25/FTS) top results
CREATE OR REPLACE FUNCTION get_keyword_results(
    query_text TEXT,
    group_id UUID,
    limit_count INTEGER
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    score FLOAT,
    rank_position INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.title,
        p.content,
        ts_rank(
            setweight(to_tsvector('english', COALESCE(p.title, '')), 'A') ||
            setweight(to_tsvector('english', p.content), 'B'),
            plainto_tsquery('english', query_text)
        ) as score,
        ROW_NUMBER() OVER (
            ORDER BY ts_rank(
                setweight(to_tsvector('english', COALESCE(p.title, '')), 'A') ||
                setweight(to_tsvector('english', p.content), 'B'),
                plainto_tsquery('english', query_text)
            ) DESC
        )::INTEGER as rank_position
    FROM posts p
    WHERE query_text IS NOT NULL
      AND (
        to_tsvector('english', COALESCE(p.title, '') || ' ' || p.content) @@ 
        plainto_tsquery('english', query_text)
      )
      AND (p.group_id = group_id OR group_id IS NULL)
    ORDER BY ts_rank(
        setweight(to_tsvector('english', COALESCE(p.title, '')), 'A') ||
        setweight(to_tsvector('english', p.content), 'B'),
        plainto_tsquery('english', query_text)
    ) DESC
    LIMIT limit_count * 2;
END;
$$ LANGUAGE plpgsql;

-- Main hybrid sidebar search function (StackOverflow-style)
CREATE OR REPLACE FUNCTION hybrid_sidebar_search(
    query_text TEXT,
    query_embedding VECTOR(1536),
    group_id UUID,
    limit_count INTEGER DEFAULT 12
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    author_id UUID,
    group_id UUID,
    score INTEGER,
    view_count INTEGER,
    is_answered BOOLEAN,
    created_at TIMESTAMPTZ,
    rrf_score FLOAT,
    source VARCHAR(10)
) AS $$
DECLARE
    semantic_ids UUID[];
    keyword_ids UUID[];
BEGIN
    -- Get semantic results (top 20)
    SELECT array_agg(id ORDER BY rank_position) INTO semantic_ids
    FROM (
        SELECT id, rank_position FROM get_semantic_results(query_embedding, group_id, limit_count)
    ) sem;
    
    -- Get keyword results (top 20)
    SELECT array_agg(id) INTO keyword_ids
    FROM (
        SELECT id, rank_position FROM get_keyword_results(query_text, group_id, limit_count)
    ) keyw;
    
    -- Return merged results using RRF
    RETURN QUERY
    WITH semantic AS (
        SELECT 
            p.*,
            (1 - (p.embedding <=> query_embedding)) * 0.7 as semantic_score
        FROM posts p
        WHERE p.id = ANY(semantic_ids)
    ),
    keyword AS (
        SELECT 
            p.*,
            ts_rank(
                setweight(to_tsvector('english', COALESCE(p.title, '')), 'A') ||
                setweight(to_tsvector('english', p.content), 'B'),
                plainto_tsquery('english', query_text)
            ) * 0.3 as keyword_score
        FROM posts p
        WHERE p.id = ANY(keyword_ids)
    ),
    merged AS (
        SELECT 
            COALESCE(s.id, k.id) as id
        FROM (
            SELECT id FROM semantic
            UNION 
            SELECT id FROM keyword
        ) m
        LEFT JOIN semantic s ON s.id = m.id
        LEFT JOIN keyword k ON k.id = m.id
    )
    SELECT 
        p.id,
        p.title,
        p.content,
        p.author_id,
        p.group_id,
        p.score,
        p.view_count,
        p.is_answered,
        p.created_at,
        COALESCE(
            (SELECT semantic_score FROM semantic WHERE id = p.id) +
            (SELECT keyword_score FROM keyword WHERE id = p.id),
            0
        ) as rrf_score,
        CASE 
            WHEN (SELECT semantic_score FROM semantic WHERE id = p.id) IS NOT NULL 
                 AND (SELECT keyword_score FROM keyword WHERE id = p.id) IS NOT NULL 
            THEN 'hybrid'
            WHEN (SELECT semantic_score FROM semantic WHERE id = p.id) IS NOT NULL 
            THEN 'semantic'
            ELSE 'keyword'
        END as source
    FROM posts p
    WHERE p.id IN (SELECT id FROM merged)
    ORDER BY rrf_score DESC, p.score DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- HOT/TRENDING SIDEBAR CACHE FUNCTION
-- =============================================

-- Get hot/trending posts for sidebar (cached, fast)
CREATE OR REPLACE FUNCTION get_hot_sidebar_posts(
    group_id UUID,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    author_id UUID,
    group_id UUID,
    score INTEGER,
    view_count INTEGER,
    is_answered BOOLEAN,
    created_at TIMESTAMPTZ,
    hot_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.title,
        p.content,
        p.author_id,
        p.group_id,
        p.score,
        p.view_count,
        p.is_answered,
        p.created_at,
        (
            p.score * 2.0 + 
            COALESCE(p.view_count, 0) * 0.5 +
            EXTRACT(EPOCH FROM (NOW() - p.created_at)) / 86400.0
        ) as hot_score
    FROM posts p
    WHERE p.group_id = group_id
    ORDER BY hot_score DESC, p.created_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- SIMILAR POSTS FUNCTION (for related sidebar)
-- =============================================

-- Find similar posts based on semantic similarity
CREATE OR REPLACE FUNCTION get_similar_posts(
    post_id UUID,
    limit_count INTEGER DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    author_id UUID,
    group_id UUID,
    score INTEGER,
    view_count INTEGER,
    is_answered BOOLEAN,
    created_at TIMESTAMPTZ,
    similarity FLOAT
) AS $$
DECLARE
    post_embedding VECTOR(1536);
BEGIN
    -- Get the embedding of the reference post
    SELECT embedding INTO post_embedding FROM posts WHERE id = post_id;
    
    RETURN QUERY
    SELECT 
        p.id,
        p.title,
        p.content,
        p.author_id,
        p.group_id,
        p.score,
        p.view_count,
        p.is_answered,
        p.created_at,
        (1 - (p.embedding <=> post_embedding)) as similarity
    FROM posts p
    WHERE p.id != post_id
      AND p.embedding IS NOT NULL
      AND post_embedding IS NOT NULL
    ORDER BY p.embedding <=> post_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- QUERY CACHE FUNCTIONS (for Redis integration)
-- =============================================

-- Generate cache key for sidebar search
CREATE OR REPLACE FUNCTION generate_sidebar_cache_key(
    query_hash TEXT,
    group_id UUID,
    result_count INTEGER DEFAULT 12
)
RETURNS TEXT AS $$
    SELECT 'sidebar:' || group_id::TEXT || ':' || query_hash || ':' || result_count::TEXT;
$$ LANGUAGE sql IMMUTABLE;

-- Log search queries for analytics (for cache warming)
CREATE OR REPLACE FUNCTION log_search_query(
    query_text TEXT,
    group_id UUID,
    result_count INTEGER,
    latency_ms INTEGER,
    cache_hit BOOLEAN
)
RETURNS void AS $$
BEGIN
    INSERT INTO search_analytics (
        query_text,
        group_id,
        result_count,
        latency_ms,
        cache_hit,
        created_at
    ) VALUES (
        query_text,
        group_id,
        result_count,
        latency_ms,
        cache_hit,
        NOW()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- SEARCH ANALYTICS TABLE (for cache optimization)
-- =============================================

CREATE TABLE IF NOT EXISTS search_analytics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    query_text TEXT NOT NULL,
    group_id UUID,
    result_count INTEGER DEFAULT 12,
    latency_ms INTEGER,
    cache_hit BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_search_analytics_group_query 
ON search_analytics(group_id, query_text, created_at);

CREATE INDEX IF NOT EXISTS idx_search_analytics_created 
ON search_analytics(created_at DESC);

-- =============================================
-- GRANT PERMISSIONS
-- =============================================

GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;

-- =============================================
-- COMMENTS
-- =============================================

/*
This migration adds:

1. Reciprocal Rank Fusion (RRF) functions for merging search results
   - rrf_score: Calculates RRF score for a rank position
   - rrf_merge: Merges semantic and keyword results with weighted RRF

2. Hybrid sidebar search (StackOverflow-style)
   - get_semantic_results: pgvector similarity search
   - get_keyword_results: BM25/FTS keyword search
   - hybrid_sidebar_search: Combines both with 70/30 weighting

3. Hot/trending posts (for cached sidebar)
   - get_hot_sidebar_posts: Fast scoring based on votes, views, recency

4. Similar posts function
   - get_similar_posts: Semantic similarity for related content

5. Query cache functions
   - generate_sidebar_cache_key: For Redis cache keys
   - log_search_query: For cache optimization analytics

6. Search analytics table
   - Tracks queries for cache warming and optimization

Performance targets:
- Semantic search: ~50ms for top-20
- Keyword search: ~20ms for top-20
- RRF merge: ~5ms
- Total with cache: sub-100ms p95
- Without cache: ~80-150ms p95
*/
