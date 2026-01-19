-- Enable pgvector extension for similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Create posts table with pgvector embedding support
CREATE TABLE IF NOT EXISTS posts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    author TEXT NOT NULL,
    post_url TEXT UNIQUE NOT NULL,
    post_date TIMESTAMP WITH TIME ZONE,
    number_of_likes INTEGER DEFAULT 0,
    number_of_comments INTEGER DEFAULT 0,
    source_type TEXT DEFAULT 'reddit',
    group_name TEXT,
    all_reactions TEXT,
    embedding vector(1536), -- OpenAI embedding dimension
    cluster_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create comments table
CREATE TABLE IF NOT EXISTS comments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    author TEXT,
    comment_date TIMESTAMP WITH TIME ZONE,
    number_of_likes INTEGER DEFAULT 0,
    comment_url TEXT,
    embedding vector(1536), -- OpenAI embedding dimension
    cluster_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_posts_post_url ON posts(post_url);
CREATE INDEX IF NOT EXISTS idx_posts_cluster_id ON posts(cluster_id);
CREATE INDEX IF NOT EXISTS idx_posts_embedding ON posts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_cluster_id ON comments(cluster_id);
CREATE INDEX IF NOT EXISTS idx_comments_embedding ON comments USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create function to find similar posts
CREATE OR REPLACE FUNCTION find_similar_posts(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.8,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    author TEXT,
    post_url TEXT,
    post_date TIMESTAMP WITH TIME ZONE,
    similarity float
)
LANGUAGE sql
AS $$
    SELECT
        posts.id,
        posts.title,
        posts.content,
        posts.author,
        posts.post_url,
        posts.post_date,
        1 - (posts.embedding <=> query_embedding) as similarity
    FROM posts
    WHERE posts.embedding IS NOT NULL
    AND 1 - (posts.embedding <=> query_embedding) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
$$;

-- Create function to cluster posts using similarity
CREATE OR REPLACE FUNCTION cluster_posts(
    similarity_threshold float DEFAULT 0.75
)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    post_record RECORD;
    cluster_record RECORD;
    current_cluster_id INTEGER := 0;
    threshold_embedding vector(1536);
BEGIN
    -- Reset cluster IDs
    UPDATE posts SET cluster_id = NULL WHERE cluster_id IS NOT NULL;
    
    -- Cluster posts based on embedding similarity
    FOR post_record IN 
        SELECT id, embedding FROM posts WHERE embedding IS NOT NULL ORDER BY id
    LOOP
        -- Check if this post belongs to an existing cluster
        SELECT c.cluster_id, c.centroid_embedding 
        INTO cluster_record
        FROM (
            SELECT 
                p.cluster_id,
                AVG(p.embedding) as centroid_embedding,
                COUNT(*) as cluster_size
            FROM posts p 
            WHERE p.cluster_id IS NOT NULL 
            AND p.embedding IS NOT NULL
            GROUP BY p.cluster_id
        ) c
        WHERE 1 - (c.centroid_embedding <=> post_record.embedding) > similarity_threshold
        AND c.cluster_size >= 2
        ORDER BY c.cluster_size DESC
        LIMIT 1;
        
        IF FOUND THEN
            -- Assign to existing cluster
            UPDATE posts SET cluster_id = cluster_record.cluster_id WHERE id = post_record.id;
        ELSE
            -- Create new cluster
            current_cluster_id := current_cluster_id + 1;
            UPDATE posts SET cluster_id = current_cluster_id WHERE id = post_record.id;
        END IF;
    END LOOP;
END;
$$;

-- Create function to get posts by cluster
CREATE OR REPLACE FUNCTION get_posts_by_cluster(
    cluster_id_param INTEGER,
    limit_count INTEGER DEFAULT 50
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    author TEXT,
    post_url TEXT,
    post_date TIMESTAMP WITH TIME ZONE,
    number_of_likes INTEGER,
    number_of_comments INTEGER,
    created_at TIMESTAMP WITH TIME ZONE
)
LANGUAGE sql
AS $$
    SELECT
        posts.id,
        posts.title,
        posts.content,
        posts.author,
        posts.post_url,
        posts.post_date,
        posts.number_of_likes,
        posts.number_of_comments,
        posts.created_at
    FROM posts
    WHERE posts.cluster_id = cluster_id_param
    ORDER BY posts.number_of_likes DESC, posts.created_at DESC
    LIMIT limit_count;
$$;

-- Create function to get cluster statistics
CREATE OR REPLACE FUNCTION get_cluster_stats()
RETURNS TABLE (
    cluster_id INTEGER,
    post_count BIGINT,
    avg_likes NUMERIC,
    avg_comments NUMERIC,
    sample_titles TEXT[]
)
LANGUAGE sql
AS $$
    SELECT
        p.cluster_id,
        COUNT(*) as post_count,
        AVG(p.number_of_likes)::NUMERIC as avg_likes,
        AVG(p.number_of_comments)::NUMERIC as avg_comments,
        ARRAY_AGG(p.title ORDER BY p.number_of_likes DESC)[:3] as sample_titles
    FROM posts p
    WHERE p.cluster_id IS NOT NULL
    GROUP BY p.cluster_id
    ORDER BY p.cluster_id;
$$;

-- Create function to search posts with clustering
CREATE OR REPLACE FUNCTION search_posts_with_clustering(
    search_query TEXT,
    similarity_threshold float DEFAULT 0.7,
    limit_count INTEGER DEFAULT 20
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    author TEXT,
    post_url TEXT,
    post_date TIMESTAMP WITH TIME ZONE,
    number_of_likes INTEGER,
    number_of_comments INTEGER,
    cluster_id INTEGER,
    similarity_score float
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- First, try similarity search if we have embeddings
    RETURN QUERY
    SELECT
        posts.id,
        posts.title,
        posts.content,
        posts.author,
        posts.post_url,
        posts.post_date,
        posts.number_of_likes,
        posts.number_of_comments,
        posts.cluster_id,
        0.0 as similarity_score
    FROM posts
    WHERE posts.title ILIKE '%' || search_query || '%'
    OR posts.content ILIKE '%' || search_query || '%'
    ORDER BY posts.number_of_likes DESC, posts.created_at DESC
    LIMIT limit_count;
END;
$$;

-- Create RLS policies
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;

-- Allow public read access
CREATE POLICY "Allow public read access on posts" ON posts FOR SELECT USING (true);
CREATE POLICY "Allow public read access on comments" ON comments FOR SELECT USING (true);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_posts_updated_at BEFORE UPDATE ON posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_comments_updated_at BEFORE UPDATE ON comments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();