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
RETURNS void AS $
DECLARE
    post_content TEXT;
    post_title TEXT;
    matching_tags TEXT[];
    tag_record RECORD;
BEGIN
    -- Get post content
    SELECT content, title INTO post_content, post_title
    FROM posts WHERE id = post_uuid;
    
    IF post_content IS NULL THEN
        RETURN;
    END IF;
    
    -- Find matching tags using similarity search
    SELECT array_agg(t.name) INTO matching_tags
    FROM tags t
    WHERE t.embedding IS NOT NULL
    AND (
        -- Text similarity in content
        to_tsvector('english', t.name || ' ' || COALESCE(post_title, '')) @@ plainto_tsquery('english', post_content)
        OR
        -- Category-based matching (simplified)
        (t.category = 'visa_type' AND post_content ILIKE '%h1b%' AND t.name ILIKE '%h1b%')
        OR (t.category = 'visa_type' AND post_content ILIKE '%f1%' AND t.name ILIKE '%f1%')
        OR (t.category = 'visa_type' AND post_content ILIKE '%b1%' AND t.name ILIKE '%b1%')
        OR (t.category = 'interview' AND post_content ILIKE '%interview%')
        OR (t.category = 'document' AND post_content ILIKE '%document%')
    )
    LIMIT 3;
    
    -- Insert matching tags
    IF matching_tags IS NOT NULL THEN
        FOR tag_record IN 
            SELECT id FROM tags WHERE name = ANY(matching_tags)
        LOOP
            INSERT INTO post_tags (post_id, tag_id) 
            VALUES (post_uuid, tag_record.id)
            ON CONFLICT (post_id, tag_id) DO NOTHING;
        END LOOP;
    END IF;
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user statistics
CREATE OR REPLACE FUNCTION get_user_stats(user_uuid UUID)
RETURNS JSON AS $
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_posts', (
            SELECT COUNT(*) FROM posts WHERE author_id = user_uuid
        ),
        'total_comments', (
            SELECT COUNT(*) FROM comments WHERE author_id = user_uuid
        ),
        'total_upvotes_received', (
            SELECT SUM(upvotes) FROM posts WHERE author_id = user_uuid
        ),
        'daily_posts_remaining', (
            CASE 
                WHEN (SELECT is_premium FROM profiles WHERE id = user_uuid) THEN -1
                ELSE GREATEST(10 - (SELECT daily_posts FROM profiles WHERE id = user_uuid), 0)
            END
        ),
        'is_premium', (
            SELECT is_premium FROM profiles WHERE id = user_uuid
        )
    ) INTO result;
    
    RETURN result;
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to increment user vote (with vote tracking)
CREATE OR REPLACE FUNCTION increment_post_vote(
    post_uuid UUID, 
    vote_type_param VARCHAR(10),
    user_uuid UUID DEFAULT auth.uid()
)
RETURNS void AS $
DECLARE
    current_vote VARCHAR(10);
BEGIN
    -- Check if user already voted
    SELECT vote_type INTO current_vote 
    FROM user_votes 
    WHERE post_id = post_uuid AND user_id = user_uuid;
    
    IF current_vote IS NULL THEN
        -- New vote
        INSERT INTO user_votes (user_id, post_id, vote_type) 
        VALUES (user_uuid, post_uuid, vote_type_param);
        
        -- Update post counts
        IF vote_type_param = 'upvote' THEN
            UPDATE posts SET upvotes = upvotes + 1 WHERE id = post_uuid;
        ELSE
            UPDATE posts SET downvotes = downvotes + 1 WHERE id = post_uuid;
        END IF;
    ELSIF current_vote != vote_type_param THEN
        -- Changing vote type
        UPDATE user_votes SET vote_type = vote_type_param WHERE post_id = post_uuid AND user_id = user_uuid;
        
        -- Update post counts
        IF vote_type_param = 'upvote' THEN
            UPDATE posts SET upvotes = upvotes + 1, downvotes = downvotes - 1 WHERE id = post_uuid;
        ELSE
            UPDATE posts SET upvotes = upvotes - 1, downvotes = downvotes + 1 WHERE id = post_uuid;
        END IF;
    END IF;
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to decrement post count for user
CREATE OR REPLACE FUNCTION decrement_user_daily_posts(user_uuid UUID)
RETURNS void AS $
BEGIN
    UPDATE profiles 
    SET daily_posts = daily_posts + 1, updated_at = NOW()
    WHERE id = user_uuid AND is_premium = false;
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- TRIGGERS FOR AUTOMATION
-- =============================================

-- Trigger to auto-tag new posts
CREATE OR REPLACE FUNCTION trigger_auto_tag_post()
RETURNS TRIGGER AS $
BEGIN
    -- Note: This will be called asynchronously by Edge Function
    -- The actual auto-tagging will be handled by Supabase Edge Function
    -- This trigger just ensures the function exists
    PERFORM auto_tag_post(NEW.id);
    RETURN NEW;
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to decrement daily posts
CREATE OR REPLACE FUNCTION trigger_decrement_daily_posts()
RETURNS TRIGGER AS $
BEGIN
    -- Only decrement for non-premium users
    IF NOT EXISTS (SELECT 1 FROM profiles WHERE id = NEW.author_id AND is_premium = true) THEN
        UPDATE profiles 
        SET daily_posts = daily_posts + 1, updated_at = NOW()
        WHERE id = NEW.author_id;
    END IF;
    RETURN NEW;
END;
$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create triggers
CREATE TRIGGER trigger_auto_tag_new_post
    AFTER INSERT ON posts
    FOR EACH ROW EXECUTE FUNCTION trigger_auto_tag_post();

CREATE TRIGGER trigger_decrement_daily_posts_on_post
    AFTER INSERT ON posts
    FOR EACH ROW EXECUTE FUNCTION trigger_decrement_daily_posts();

-- =============================================
-- VIEWS FOR COMMON QUERIES
-- =============================================

-- View for group statistics
CREATE VIEW group_stats AS
SELECT 
    g.id,
    g.name,
    g.user_count,
    g.active_count,
    COUNT(DISTINCT p.id) as total_posts,
    COUNT(DISTINCT c.id) as total_comments,
    AVG(p.score) as avg_post_score,
    MAX(p.created_at) as last_post_at
FROM groups g
LEFT JOIN posts p ON g.id = p.group_id
LEFT JOIN comments c ON p.id = c.post_id
GROUP BY g.id, g.name, g.user_count, g.active_count;

-- View for popular posts
CREATE VIEW popular_posts AS
SELECT 
    p.*,
    pr.name as author_name,
    pr.is_premium as author_is_premium,
    array_agg(t.name) as tags
FROM posts p
JOIN profiles pr ON p.author_id = pr.id
LEFT JOIN post_tags pt ON p.id = pt.post_id
LEFT JOIN tags t ON pt.tag_id = t.id
WHERE p.score > 0
GROUP BY p.id, pr.name, pr.is_premium
ORDER BY p.score DESC, p.created_at DESC;

-- =============================================
-- SAMPLE DATA (for development)
-- =============================================

-- Insert sample groups
INSERT INTO groups (id, name) VALUES 
    ('550e8400-e29b-41d4-a716-446655440001', 'H1B Visa Discussions'),
    ('550e8400-e29b-41d4-a716-446655440002', 'F1 Student Visa'),
    ('550e8400-e29b-41d4-a716-446655440003', 'Canada Immigration'),
    ('550e8400-e29b-41d4-a716-446655440004', 'UK Visa Applications'),
    ('550e8400-e29b-41d4-a716-446655440005', 'General Immigration');

-- Insert sample tags
INSERT INTO tags (name, category) VALUES 
    ('H1B', 'visa_type'),
    ('F1', 'visa_type'),
    ('B1', 'visa_type'),
    ('interview', 'interview'),
    ('document', 'document'),
    ('process', 'process'),
    ('DS160', 'document'),
    ('green card', 'process'),
    ('opt', 'process'),
    ('cpt', 'process');

-- Add embeddings for tags (this would normally be done by Edge Function)
-- UPDATE tags SET embedding = '[0.1, 0.2, ...]' WHERE name = 'H1B';

-- =============================================
-- COMMENTS
-- =============================================

/*
This schema provides:

1. Multi-tenant structure with groups and RLS policies
2. StackOverflow-style posts with voting and comments
3. Auto-tagging system with similarity search
4. Premium subscription support with daily post limits
5. Real-time presence tracking
6. External content pipeline support
7. Analytics events tracking
8. Performance-optimized indexes including vector similarity
9. Comprehensive security with RLS on all sensitive tables
10. Automated triggers for business logic

Key Features:
- Premium users can search across all groups
- Free users limited to 10 posts per day
- Auto-tagging based on content similarity
- Real-time active user counts
- Hybrid search (vector + text)
- Watermarking for anti-scraping
- Comprehensive voting system

Next Steps:
1. Apply this migration to Supabase
2. Create Edge Functions for auto-tagging
3. Set up Redis integration
4. Implement Groq LLM integration
5. Build FastAPI backend
6. Create Next.js frontend
*/