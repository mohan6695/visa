-- Visa Q&A and Group Chat App Database Schema
-- Supabase Pro with Row-Level Security and Multi-tenancy

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =============================================
-- CORE SCHEMA: Auth, Profiles, Groups
-- =============================================

-- Profiles table (extends Supabase auth.users)
CREATE TABLE profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    group_id UUID DEFAULT gen_random_uuid() NOT NULL,
    is_premium BOOLEAN DEFAULT false,
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    daily_posts INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Groups table for multi-tenant structure
CREATE TABLE groups (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    user_count INTEGER DEFAULT 0,
    active_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Update profiles function to sync group_id
CREATE OR REPLACE FUNCTION update_user_group()
RETURNS TRIGGER AS $$
BEGIN
    -- Ensure user gets assigned to a group
    IF NEW.group_id IS NULL THEN
        NEW.group_id := gen_random_uuid();
    END IF;
    
    -- Update group user count
    UPDATE groups 
    SET user_count = (
        SELECT COUNT(*) FROM profiles 
        WHERE profiles.group_id = NEW.group_id
    ),
    updated_at = NOW()
    WHERE groups.id = NEW.group_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to update group user count
CREATE TRIGGER trigger_update_group_user_count
    AFTER INSERT OR UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_user_group();

-- =============================================
-- CONTENT: Posts, Comments, Voting
-- =============================================

-- Posts table (StackOverflow-style Q&A)
CREATE TABLE posts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE NOT NULL,
    author_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    embedding VECTOR(1536), -- For pgvector similarity search
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    score INTEGER GENERATED ALWAYS AS (upvotes - downvotes) STORED,
    watermark_hash TEXT GENERATED ALWAYS AS (md5(content || author_id::text || created_at::text)) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Comments table (nested, unlimited depth)
CREATE TABLE comments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE NOT NULL,
    parent_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    author_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    content TEXT NOT NULL,
    upvotes INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- User votes table for tracking individual votes
CREATE TABLE user_votes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE NOT NULL,
    vote_type VARCHAR(10) CHECK (vote_type IN ('upvote', 'downvote')) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, post_id)
);

-- =============================================
-- TAGGING SYSTEM
-- =============================================

-- Tags table with embeddings
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    embedding VECTOR(1536),
    category TEXT CHECK (category IN ('visa_type', 'document', 'process', 'country', 'interview', 'general')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Post-tags junction table
CREATE TABLE post_tags (
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (post_id, tag_id)
);

-- =============================================
-- PRESENCE TRACKING
-- =============================================

-- User presence for real-time active counts
CREATE TABLE user_presence (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE NOT NULL,
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- EXTERNAL CONTENT PIPELINE
-- =============================================

-- Staging area for external posts
CREATE TABLE external_posts_staging (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    source TEXT NOT NULL,
    cluster_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Live external content with clustering
CREATE TABLE external_posts_live (
    cluster_id UUID PRIMARY KEY,
    best_content TEXT NOT NULL,
    similarity_score FLOAT,
    sources TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- ANALYTICS (Optional)
-- =============================================

-- Analytics events table
CREATE TABLE analytics_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    event TEXT NOT NULL,
    properties JSONB,
    user_id UUID REFERENCES auth.users(id),
    group_id UUID REFERENCES groups(id),
    ip_address INET,
    geo JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- INDEXES FOR PERFORMANCE
-- =============================================

-- Posts indexes
CREATE INDEX idx_posts_group_id ON posts(group_id);
CREATE INDEX idx_posts_author_id ON posts(author_id);
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX idx_posts_score ON posts(score DESC);

-- Comments indexes
CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_comments_parent_id ON comments(parent_id);
CREATE INDEX idx_comments_author_id ON comments(author_id);

-- User votes index
CREATE INDEX idx_user_votes_post_id ON user_votes(post_id);
CREATE INDEX idx_user_votes_user_id ON user_votes(user_id);

-- Presence indexes
CREATE INDEX idx_user_presence_group_id ON user_presence(group_id);
CREATE INDEX idx_user_presence_last_seen ON user_presence(last_seen DESC);

-- Vector similarity indexes
CREATE INDEX idx_posts_embedding ON posts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_tags_embedding ON tags USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);

-- =============================================
-- ROW-LEVEL SECURITY (RLS) POLICIES
-- =============================================

-- Enable RLS on all sensitive tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_presence ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_votes ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view their own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

-- Posts policies
CREATE POLICY "Users can view posts in their group" ON posts
    FOR SELECT USING (
        group_id = (auth.jwt()->>'group_id')::uuid OR
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE profiles.id = auth.uid() 
            AND profiles.is_premium = true
        )
    );

CREATE POLICY "Users can create posts in their group" ON posts
    FOR INSERT WITH CHECK (
        group_id = (auth.jwt()->>'group_id')::uuid AND
        (
            EXISTS (
                SELECT 1 FROM profiles 
                WHERE profiles.id = auth.uid() 
                AND profiles.is_premium = true
            ) OR
            (
                SELECT daily_posts FROM profiles WHERE id = auth.uid()
            ) < 10
        )
    );

CREATE POLICY "Users can update their own posts" ON posts
    FOR UPDATE USING (auth.uid() = author_id);

-- Comments policies
CREATE POLICY "Users can view comments on accessible posts" ON comments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM posts 
            WHERE posts.id = comments.post_id 
            AND (
                posts.group_id = (auth.jwt()->>'group_id')::uuid OR
                EXISTS (
                    SELECT 1 FROM profiles 
                    WHERE profiles.id = auth.uid() 
                    AND profiles.is_premium = true
                )
            )
        )
    );

CREATE POLICY "Users can create comments" ON comments
    FOR INSERT WITH CHECK (
        auth.uid() = author_id AND
        EXISTS (
            SELECT 1 FROM posts 
            WHERE posts.id = comments.post_id 
            AND (
                posts.group_id = (auth.jwt()->>'group_id')::uuid OR
                EXISTS (
                    SELECT 1 FROM profiles 
                    WHERE profiles.id = auth.uid() 
                    AND profiles.is_premium = true
                )
            )
        )
    );

-- User presence policies
CREATE POLICY "Users can view presence in their group" ON user_presence
    FOR SELECT USING (group_id = (auth.jwt()->>'group_id')::uuid);

CREATE POLICY "Users can update their own presence" ON user_presence
    FOR ALL USING (auth.uid() = user_id);

-- User votes policies
CREATE POLICY "Users can view votes on accessible posts" ON user_votes
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM posts 
            WHERE posts.id = user_votes.post_id 
            AND (
                posts.group_id = (auth.jwt()->>'group_id')::uuid OR
                EXISTS (
                    SELECT 1 FROM profiles 
                    WHERE profiles.id = auth.uid() 
                    AND profiles.is_premium = true
                )
            )
        )
    );

CREATE POLICY "Users can manage their own votes" ON user_votes
    FOR ALL USING (auth.uid() = user_id);

-- Analytics policies (admin only)
CREATE POLICY "Only service role can access analytics" ON analytics_events
    FOR ALL USING (auth.role() = 'service_role');

-- =============================================
-- FUNCTIONS FOR BUSINESS LOGIC
-- =============================================

-- Function to reset daily posts for non-premium users
CREATE OR REPLACE FUNCTION reset_daily_posts()
RETURNS void AS $$
BEGIN
    UPDATE profiles 
    SET daily_posts = 0 
    WHERE is_premium = false 
    AND updated_at < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to update active user counts
CREATE OR REPLACE FUNCTION update_active_counts()
RETURNS void AS $$
BEGIN
    UPDATE groups 
    SET active_count = (
        SELECT COUNT(*) FROM user_presence 
        WHERE user_presence.group_id = groups.id 
        AND user_presence.last_seen > NOW() - INTERVAL '5 minutes'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function for hybrid search (vector + text)
CREATE OR REPLACE FUNCTION hybrid_search_posts(
    query_embedding VECTOR(1536),
    query_text TEXT,
    search_group_id UUID,
    is_premium_user BOOLEAN,
    limit_count INTEGER DEFAULT 20
)
RETURNS TABLE (
    post_id UUID,
    title TEXT,
    content TEXT,
    author_id UUID,
    upvotes INTEGER,
    downvotes INTEGER,
    score INTEGER,
    similarity_score FLOAT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.title,
        p.content,
        p.author_id,
        p.upvotes,
        p.downvotes,
        p.score,
        (
            0.7 * (1 - (p.embedding <=> query_embedding)) +
            0.3 * ts_rank(to_tsvector('english', p.content), plainto_tsquery('english', query_text))
        ) as similarity_score,
        p.created_at
    FROM posts p
    WHERE 
        (p.group_id = search_group_id OR (is_premium_user AND p.group_id != search_group_id))
        AND (
            query_embedding IS NULL OR
            p.embedding IS NOT NULL
        )
        AND (
            query_text IS NULL OR
            to_tsvector('english', p.content) @@ plainto_tsquery('english', query_text)
        )
    ORDER BY similarity_score DESC, p.score DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- EDGE FUNCTION HOOKS
-- =============================================

-- Function to auto-tag posts using LLM
CREATE OR REPLACE FUNCTION auto_tag_post(post_uuid UUID)
RETURNS void AS $$
DECLARE
    post_content TEXT;
    matching_tags TEXT[];
BEGIN
    -- Get post content
    SELECT content INTO post_content 
    FROM posts WHERE id = post_uuid