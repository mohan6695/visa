-- Migration: Visa Posts Schema for Stack Overflow Style Interface
-- This migration creates tables for handling Facebook visa community posts

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Create countries table for visa-related countries
CREATE TABLE IF NOT EXISTS countries (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    code TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert common visa countries
INSERT INTO countries (name, code) VALUES 
('United States', 'USA'),
('India', 'IND'),
('Canada', 'CAN'),
('United Kingdom', 'GBR'),
('Australia', 'AUS'),
('Germany', 'DEU'),
('France', 'FRA')
ON CONFLICT (name) DO NOTHING;

-- Create communities table for visa groups
CREATE TABLE IF NOT EXISTS communities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    country_id INTEGER REFERENCES countries(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert H1B Visa community
INSERT INTO communities (id, name, description, country_id) VALUES 
('550e8400-e29b-41d4-a716-446655440001', 'H1B Visa 2025, 2026 Community', 'Community for H1B visa discussions and experiences', 1)
ON CONFLICT (id) DO NOTHING;

-- Create users table for community members
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE,
    display_name TEXT NOT NULL,
    avatar_url TEXT,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create main posts table for visa community posts
CREATE TABLE IF NOT EXISTS posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id TEXT UNIQUE, -- Facebook post ID
    title TEXT,
    content TEXT NOT NULL,
    content_html TEXT,
    author_id UUID REFERENCES users(id) ON DELETE CASCADE,
    community_id UUID REFERENCES communities(id) ON DELETE CASCADE,
    country_id INTEGER REFERENCES countries(id),
    
    -- Post metadata
    url TEXT,
    post_type TEXT CHECK (post_type IN ('question', 'experience', 'update', 'discussion')) DEFAULT 'question',
    status TEXT CHECK (status IN ('published', 'draft', 'archived', 'deleted')) DEFAULT 'published',
    is_pinned BOOLEAN DEFAULT FALSE,
    is_locked BOOLEAN DEFAULT FALSE,
    
    -- Engagement metrics
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    score INTEGER GENERATED ALWAYS AS (upvotes - downvotes) STORED,
    view_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    
    -- Clustering and search
    embedding VECTOR(1536), -- For semantic search
    search_vector TSVECTOR,
    cluster_id INTEGER,
    similarity_score FLOAT DEFAULT 0.0,
    
    -- Source information
    source_platform TEXT DEFAULT 'facebook',
    source_data JSONB, -- Store original Facebook data
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    external_created_at TIMESTAMPTZ -- Original Facebook timestamp
);

-- Create comments table for post replies
CREATE TABLE IF NOT EXISTS comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    author_id UUID REFERENCES users(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    content_html TEXT,
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    score INTEGER GENERATED ALWAYS AS (upvotes - downvotes) STORED,
    is_accepted BOOLEAN DEFAULT FALSE, -- For marking accepted answers
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    external_data JSONB -- Store original Facebook comment data
);

-- Create tags table for post categorization
CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    post_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create post_tags junction table
CREATE TABLE IF NOT EXISTS post_tags (
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)
);

-- Create post clusters table for similar posts grouping
CREATE TABLE IF NOT EXISTS post_clusters (
    cluster_id SERIAL PRIMARY KEY,
    cluster_name TEXT NOT NULL,
    centroid_embedding VECTOR(1536),
    post_count INTEGER DEFAULT 0,
    avg_similarity_score FLOAT DEFAULT 0.0,
    keywords TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert initial visa-related tags
INSERT INTO tags (name, description) VALUES 
('h1b', 'H1B visa related discussions'),
('h4', 'H4 dependent visa discussions'),
('ead', 'Employment Authorization Document'),
('stamping', 'Visa stamping experiences'),
('221g', 'Administrative processing cases'),
('rfe', 'Request for Evidence'),
('premium-processing', 'Premium processing cases'),
('interview', 'Visa interview experiences'),
('refusal', 'Visa refusal cases'),
('employment', 'Employment based immigration'),
('family', 'Family based immigration'),
('travel', 'Travel and re-entry issues'),
('documentation', 'Document related queries'),
('timeline', 'Processing timeline discussions'),
('attorney', 'Attorney and legal advice')
ON CONFLICT (name) DO NOTHING;

-- Create indexes for performance
CREATE INDEX idx_posts_community_id ON posts(community_id);
CREATE INDEX idx_posts_author_id ON posts(author_id);
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX idx_posts_score ON posts(score DESC);
CREATE INDEX idx_posts_cluster_id ON posts(cluster_id);
CREATE INDEX idx_posts_external_id ON posts(external_id);
CREATE INDEX idx_posts_embedding ON posts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_posts_search_vector ON posts USING GIN(search_vector);

CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_comments_author_id ON comments(author_id);
CREATE INDEX idx_comments_parent_id ON comments(parent_id);
CREATE INDEX idx_comments_created_at ON comments(created_at);

CREATE INDEX idx_post_tags_post_id ON post_tags(post_id);
CREATE INDEX idx_post_tags_tag_id ON post_tags(tag_id);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_communities_country_id ON communities(country_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_posts_updated_at 
    BEFORE UPDATE ON posts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_comments_updated_at 
    BEFORE UPDATE ON comments 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_post_clusters_updated_at 
    BEFORE UPDATE ON post_clusters 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create search vector update function
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector = to_tsvector('english', COALESCE(NEW.title, '') || ' ' || NEW.content);
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create search vector trigger
CREATE TRIGGER update_posts_search_vector 
    BEFORE INSERT OR UPDATE ON posts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_search_vector();

-- Function to find similar posts using vector similarity
CREATE OR REPLACE FUNCTION find_similar_posts(
    post_id_param UUID,
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INT DEFAULT 10
)
RETURNS TABLE (
    similar_post_id UUID,
    similarity_score FLOAT,
    title TEXT,
    content TEXT,
    author_id UUID,
    created_at TIMESTAMPTZ,
    cluster_id INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        1 - (p.embedding <=> source_post.embedding) as similarity_score,
        p.title,
        p.content,
        p.author_id,
        p.created_at,
        p.cluster_id
    FROM posts p
    CROSS JOIN (
        SELECT embedding FROM posts WHERE id = post_id_param
    ) as source_post
    WHERE 
        p.id != post_id_param
        AND p.embedding IS NOT NULL
        AND source_post.embedding IS NOT NULL
        AND p.status = 'published'
        AND (1 - (p.embedding <=> source_post.embedding)) > similarity_threshold
    ORDER BY similarity_score DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to search posts with full-text and vector search
CREATE OR REPLACE FUNCTION search_posts(
    search_query TEXT,
    search_embedding VECTOR(1536),
    community_uuid UUID DEFAULT NULL,
    limit_count INTEGER DEFAULT 20
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    content TEXT,
    author_id UUID,
    community_id UUID,
    score INTEGER,
    view_count INTEGER,
    comment_count INTEGER,
    created_at TIMESTAMPTZ,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH text_matches AS (
        SELECT 
            p.id,
            ts_rank(
                setweight(to_tsvector('english', COALESCE(p.title, '')), 'A') ||
                setweightsearch_vector, plainto_tsquery('english', search_query)
            ) AS text_similarity
        FROM posts p
        WHERE
            search_query IS NOT NULL
            AND (community_uuid IS NULL OR p.community_id = community_uuid)
            AND p.status = 'published'
            AND p.search_vector @@ plainto_tsquery('english', search_query)
    ),
    vector_matches AS (
        SELECT 
            p.id,
            1 - (p.embedding <=> search_embedding) AS vector_similarity
        FROM posts p
        WHERE 
            search_embedding IS NOT NULL
            AND p.embedding IS NOT NULL
            AND (community_uuid IS NULL OR p.community_id = community_uuid)
            AND p.status = 'published'
    )
    SELECT
        p.id,
        p.title,
        p.content,
        p.author_id,
        p.community_id,
        p.score,
        p.view_count,
        p.comment_count,
        p.created_at,
        COALESCE(vm.vector_similarity * 0.7, 0) + COALESCE(tm.text_similarity * 0.3, 0) AS similarity
    FROM posts p
    LEFT JOIN vector_matches vm ON p.id = vm.id
    LEFT JOIN text_matches tm ON p.id = tm.id
    WHERE
        (vm.id IS NOT NULL OR tm.id IS NOT NULL)
        AND (community_uuid IS NULL OR p.community_id = community_uuid)
        AND p.status = 'published'
    ORDER BY
        similarity DESC,
        p.score DESC,
        p.created_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Enable Row Level Security
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_tags ENABLE ROW LEVEL SECURITY;

-- RLS Policies for posts (allow public read access)
CREATE POLICY "Anyone can view published posts" ON posts
    FOR SELECT USING (status = 'published');

CREATE POLICY "Service role can manage all posts" ON posts
    FOR ALL USING (auth.role() = 'service_role');

-- RLS Policies for comments (allow public read access)
CREATE POLICY "Anyone can view comments on published posts" ON comments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM posts 
            WHERE posts.id = comments.post_id 
            AND posts.status = 'published'
        )
    );

CREATE POLICY "Service role can manage all comments" ON comments
    FOR ALL USING (auth.role() = 'service_role');

-- RLS Policies for users (allow public read, authenticated write)
CREATE POLICY "Anyone can view user profiles" ON users
    FOR SELECT USING (true);

CREATE POLICY "Users can update their own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Service role can manage all users" ON users
    FOR ALL USING (auth.role() = 'service_role');

-- RLS Policies for tags (public read, service role write)
CREATE POLICY "Anyone can view tags" ON tags
    FOR SELECT USING (true);

CREATE POLICY "Service role can manage tags" ON tags
    FOR ALL USING (auth.role() = 'service_role');

-- RLS Policies for post_tags (public read, service role write)
CREATE POLICY "Anyone can view post tags" ON post_tags
    FOR SELECT USING (true);

CREATE POLICY "Service role can manage post tags" ON post_tags
    FOR ALL USING (auth.role() = 'service_role');

-- Grant permissions
GRANT USAGE ON SCHEMA public TO authenticated, anon;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated, anon;
GRANT INSERT, UPDATE, DELETE ON posts TO authenticated;
GRANT INSERT, UPDATE, DELETE ON comments TO authenticated;
GRANT INSERT, UPDATE, DELETE ON users TO authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;