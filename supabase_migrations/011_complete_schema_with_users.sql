-- Complete Supabase Schema for H1B Visa Platform
-- This migration creates all required tables including user metadata

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Users table with metadata
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE,
    full_name VARCHAR(100),
    avatar_url TEXT,
    bio TEXT,
    country VARCHAR(50),
    visa_status VARCHAR(50),
    visa_category VARCHAR(50), -- H1B, F1, etc.
    current_location VARCHAR(100),
    years_in_usa INTEGER,
    profession VARCHAR(100),
    company VARCHAR(100),
    is_verified BOOLEAN DEFAULT false,
    is_premium BOOLEAN DEFAULT false,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Posts table with embeddings
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    country VARCHAR(50) NOT NULL,
    category VARCHAR(50), -- experience, question, discussion, etc.
    tags TEXT[],
    post_type VARCHAR(50), -- reddit, stackoverflow, etc.
    source_url TEXT,
    external_id VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    embedding vector(1536), -- text-embedding-3-small model dimension
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    views_count INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT false,
    is_pinned BOOLEAN DEFAULT false,
    status VARCHAR(20) DEFAULT 'active', -- active, hidden, deleted
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Comments table with embeddings
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536),
    likes_count INTEGER DEFAULT 0,
    is_solution BOOLEAN DEFAULT false, -- For Stack Overflow style answers
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Communities/Groups table
CREATE TABLE communities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    country VARCHAR(50),
    category VARCHAR(50),
    rules TEXT[],
    moderators UUID[],
    member_count INTEGER DEFAULT 0,
    is_private BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Community membership
CREATE TABLE community_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    community_id UUID REFERENCES communities(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member', -- member, moderator, admin
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(community_id, user_id)
);

-- Groups table for country-specific groups
CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    country VARCHAR(50) NOT NULL,
    city VARCHAR(100),
    category VARCHAR(50),
    member_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Group membership
CREATE TABLE group_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(group_id, user_id)
);

-- User interactions
CREATE TABLE user_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    target_id UUID, -- Can reference posts or comments
    target_type VARCHAR(20), -- 'post' or 'comment'
    interaction_type VARCHAR(20), -- 'like', 'bookmark', 'share', etc.
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, target_id, target_type, interaction_type)
);

-- Notifications
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    data JSONB DEFAULT '{}',
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Search queries for analytics
CREATE TABLE search_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    query TEXT NOT NULL,
    filters JSONB DEFAULT '{}',
    results_count INTEGER DEFAULT 0,
    clicked_result_id UUID,
    clicked_result_type VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_country ON users(country);
CREATE INDEX idx_users_visa_status ON users(visa_status);
CREATE INDEX idx_users_created_at ON users(created_at DESC);

CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_country ON posts(country);
CREATE INDEX idx_posts_category ON posts(category);
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_tags ON posts USING GIN(tags);
CREATE INDEX idx_posts_embedding ON posts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_posts_metadata ON posts USING GIN(metadata);

CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_comments_user_id ON comments(user_id);
CREATE INDEX idx_comments_parent_id ON comments(parent_id);
CREATE INDEX idx_comments_created_at ON comments(created_at DESC);
CREATE INDEX idx_comments_embedding ON comments USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_communities_country ON communities(country);
CREATE INDEX idx_communities_category ON communities(category);
CREATE INDEX idx_communities_active ON communities(is_active);

CREATE INDEX idx_groups_country ON groups(country);
CREATE INDEX idx_groups_active ON groups(is_active);

CREATE INDEX idx_community_members_community_id ON community_members(community_id);
CREATE INDEX idx_community_members_user_id ON community_members(user_id);

CREATE INDEX idx_group_members_group_id ON group_members(group_id);
CREATE INDEX idx_group_members_user_id ON group_members(user_id);

CREATE INDEX idx_user_interactions_user_id ON user_interactions(user_id);
CREATE INDEX idx_user_interactions_target ON user_interactions(target_id, target_type);
CREATE INDEX idx_user_interactions_type ON user_interactions(interaction_type);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);

CREATE INDEX idx_search_queries_user_id ON search_queries(user_id);
CREATE INDEX idx_search_queries_created_at ON search_queries(created_at DESC);

-- Triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_posts_updated_at BEFORE UPDATE ON posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_comments_updated_at BEFORE UPDATE ON comments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_communities_updated_at BEFORE UPDATE ON communities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_groups_updated_at BEFORE UPDATE ON groups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to generate embeddings using OpenAI
CREATE OR REPLACE FUNCTION generate_embedding(text_content TEXT)
RETURNS vector(1536) AS $$
DECLARE
    api_key TEXT := current_setting('app.openai_api_key', true);
    embedding_result JSONB;
BEGIN
    IF api_key IS NULL OR api_key = '' THEN
        RAISE EXCEPTION 'OpenAI API key not configured';
    END IF;
    
    -- Call OpenAI API to generate embedding
    SELECT net.http_post(
        url := 'https://api.openai.com/v1/embeddings',
        headers := jsonb_build_object(
            'Authorization', 'Bearer ' || api_key,
            'Content-Type', 'application/json'
        ),
        body := jsonb_build_object(
            'model', 'text-embedding-3-small',
            'input', text_content
        )
    ) INTO embedding_result;
    
    -- Extract embedding vector from response
    RETURN (embedding_result->'data'->0->'embedding')::vector;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically generate embeddings for posts
CREATE OR REPLACE FUNCTION update_post_embedding()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.embedding IS NULL OR NEW.embedding = '[]'::vector THEN
        NEW.embedding := generate_embedding(NEW.title || ' ' || NEW.content);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER generate_post_embedding_trigger
    BEFORE INSERT OR UPDATE ON posts
    FOR EACH ROW EXECUTE FUNCTION update_post_embedding();

-- Trigger to automatically generate embeddings for comments
CREATE OR REPLACE FUNCTION update_comment_embedding()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.embedding IS NULL OR NEW.embedding = '[]'::vector THEN
        NEW.embedding := generate_embedding(NEW.content);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER generate_comment_embedding_trigger
    BEFORE INSERT OR UPDATE ON comments
    FOR EACH ROW EXECUTE FUNCTION update_comment_embedding();

-- Similarity search function for posts
CREATE OR REPLACE FUNCTION search_similar_posts(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.78,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    title VARCHAR(500),
    content TEXT,
    country VARCHAR(50),
    category VARCHAR(50),
    tags TEXT[],
    similarity float
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.title,
        p.content,
        p.country,
        p.category,
        p.tags,
        1 - (p.embedding <=> query_embedding) AS similarity
    FROM posts p
    WHERE 1 - (p.embedding <=> query_embedding) > match_threshold
    AND p.status = 'active'
    ORDER BY p.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Similarity search function for comments
CREATE OR REPLACE FUNCTION search_similar_comments(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.78,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    post_id UUID,
    content TEXT,
    similarity float
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.post_id,
        c.content,
        1 - (c.embedding <=> query_embedding) AS similarity
    FROM comments c
    WHERE 1 - (c.embedding <=> query_embedding) > match_threshold
    AND c.status = 'active'
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- K-means clustering function for posts
CREATE OR REPLACE FUNCTION cluster_posts(k_clusters int DEFAULT 5)
RETURNS TABLE (
    cluster_id int,
    post_count bigint,
    sample_posts UUID[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (ARRAY(
            SELECT (result).cluster_id
            FROM (
                SELECT kmeans(embedding, k_clusters) AS result
                FROM posts 
                WHERE embedding IS NOT NULL 
                AND status = 'active'
            ) kmeans_result
        ))[row_number() OVER ()]::int as cluster_id,
        COUNT(*) as post_count,
        ARRAY_AGG(id ORDER BY RANDOM())[1:3] as sample_posts
    FROM (
        SELECT id, embedding, 
               (kmeans(embedding, k_clusters) OVER ()) as cluster_result
        FROM posts 
        WHERE embedding IS NOT NULL 
        AND status = 'active'
    ) clustered_posts
    GROUP BY cluster_id;
END;
$$ LANGUAGE plpgsql;

-- Row Level Security (RLS) Policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE communities ENABLE ROW LEVEL SECURITY;
ALTER TABLE community_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE group_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_queries ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (allow public read access for posts, restrict writes to authenticated users)
CREATE POLICY "Public posts are viewable by everyone" ON posts
    FOR SELECT USING (status = 'active');

CREATE POLICY "Users can insert their own posts" ON posts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own posts" ON posts
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Public comments are viewable by everyone" ON comments
    FOR SELECT USING (status = 'active');

CREATE POLICY "Users can insert their own comments" ON comments
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own comments" ON comments
    FOR UPDATE USING (auth.uid() = user_id);

-- Comments for documentation
COMMENT ON TABLE users IS 'User profiles with visa and location metadata';
COMMENT ON TABLE posts IS 'User-generated content with AI embeddings for similarity search';
COMMENT ON TABLE comments IS 'Comments on posts with conversation threading';
COMMENT ON TABLE communities IS 'Discussion communities organized by country/topic';
COMMENT ON TABLE groups IS 'Location-based groups for networking';
COMMENT ON TABLE user_interactions IS 'User engagement tracking (likes, bookmarks, shares)';
COMMENT ON TABLE notifications IS 'User notification system';
COMMENT ON TABLE search_queries IS 'Search analytics for improving recommendations';