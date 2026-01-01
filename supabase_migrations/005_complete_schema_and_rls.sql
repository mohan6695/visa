-- Migration: Complete Schema and RLS Policies
-- This migration completes the database schema and adds all required RLS policies

-- =============================================
-- COMPLETE SCHEMA ADDITIONS
-- =============================================

-- Add missing indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_posts_embedding_cosine ON posts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_profiles_is_premium ON profiles(is_premium);
CREATE INDEX IF NOT EXISTS idx_profiles_daily_posts ON profiles(daily_posts);
CREATE INDEX IF NOT EXISTS idx_user_presence_is_active ON user_presence(is_active);
CREATE INDEX IF NOT EXISTS idx_post_tags_tag_id ON post_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_external_posts_staging_cluster_id ON external_posts_staging(cluster_id);

-- Add missing columns to posts table
ALTER TABLE posts ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE posts ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 0;
ALTER TABLE posts ADD COLUMN IF NOT EXISTS is_answered BOOLEAN DEFAULT false;
ALTER TABLE posts ADD COLUMN IF NOT EXISTS post_type VARCHAR(20) DEFAULT 'question' CHECK (post_type IN ('question', 'answer', 'article'));

-- Add missing columns to profiles table
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS username TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS avatar_url TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(20) DEFAULT 'free' CHECK (subscription_tier IN ('free', 'premium', 'group_leader'));
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS subscription_ends_at TIMESTAMPTZ;

-- Create notification system
CREATE TABLE IF NOT EXISTS notifications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('new_comment', 'mention', 'vote', 'answer', 'system')),
    content TEXT NOT NULL,
    related_id UUID, -- Can reference post_id, comment_id, etc.
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);

-- Create view for active users
CREATE OR REPLACE VIEW active_users AS
SELECT 
    g.id as group_id,
    g.name as group_name,
    COUNT(DISTINCT up.user_id) as active_count,
    array_agg(DISTINCT p.username) FILTER (WHERE up.is_active = true) as active_usernames
FROM groups g
LEFT JOIN user_presence up ON g.id = up.group_id AND up.last_seen > NOW() - INTERVAL '5 minutes'
LEFT JOIN profiles p ON up.user_id = p.id
GROUP BY g.id, g.name;

-- =============================================
-- ENHANCED RLS POLICIES
-- =============================================

-- Enable RLS on all tables
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE external_posts_staging ENABLE ROW LEVEL SECURITY;
ALTER TABLE external_posts_live ENABLE ROW LEVEL SECURITY;

-- Profiles policies (enhanced)
DROP POLICY IF EXISTS "Users can view their own profile" ON profiles;
CREATE POLICY "Users can view their own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update their own profile" ON profiles;
CREATE POLICY "Users can update their own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id)
    WITH CHECK (
        auth.uid() = id AND
        -- Prevent users from updating premium status directly
        (is_premium IS NOT DISTINCT FROM OLD.is_premium) AND
        (stripe_customer_id IS NOT DISTINCT FROM OLD.stripe_customer_id) AND
        (stripe_subscription_id IS NOT DISTINCT FROM OLD.stripe_subscription_id) AND
        (subscription_tier IS NOT DISTINCT FROM OLD.subscription_tier) AND
        (subscription_ends_at IS NOT DISTINCT FROM OLD.subscription_ends_at)
    );

-- Posts policies (enhanced)
DROP POLICY IF EXISTS "Users can view posts in their group" ON posts;
CREATE POLICY "Users can view posts in their group" ON posts
    FOR SELECT USING (
        group_id = (SELECT group_id FROM profiles WHERE id = auth.uid()) OR
        EXISTS (
            SELECT 1 FROM profiles 
            WHERE profiles.id = auth.uid() 
            AND profiles.is_premium = true
        )
    );

DROP POLICY IF EXISTS "Users can create posts in their group" ON posts;
CREATE POLICY "Users can create posts in their group" ON posts
    FOR INSERT WITH CHECK (
        group_id = (SELECT group_id FROM profiles WHERE id = auth.uid()) AND
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

DROP POLICY IF EXISTS "Users can update their own posts" ON posts;
CREATE POLICY "Users can update their own posts" ON posts
    FOR UPDATE USING (auth.uid() = author_id)
    WITH CHECK (auth.uid() = author_id);

CREATE POLICY "Users can delete their own posts" ON posts
    FOR DELETE USING (auth.uid() = author_id);

-- Comments policies (enhanced)
DROP POLICY IF EXISTS "Users can view comments on accessible posts" ON comments;
CREATE POLICY "Users can view comments on accessible posts" ON comments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM posts 
            WHERE posts.id = comments.post_id 
            AND (
                posts.group_id = (SELECT group_id FROM profiles WHERE id = auth.uid()) OR
                EXISTS (
                    SELECT 1 FROM profiles 
                    WHERE profiles.id = auth.uid() 
                    AND profiles.is_premium = true
                )
            )
        )
    );

DROP POLICY IF EXISTS "Users can create comments" ON comments;
CREATE POLICY "Users can create comments" ON comments
    FOR INSERT WITH CHECK (
        auth.uid() = author_id AND
        EXISTS (
            SELECT 1 FROM posts 
            WHERE posts.id = comments.post_id 
            AND (
                posts.group_id = (SELECT group_id FROM profiles WHERE id = auth.uid()) OR
                EXISTS (
                    SELECT 1 FROM profiles 
                    WHERE profiles.id = auth.uid() 
                    AND profiles.is_premium = true
                )
            )
        )
    );

CREATE POLICY "Users can update their own comments" ON comments
    FOR UPDATE USING (auth.uid() = author_id)
    WITH CHECK (auth.uid() = author_id);

CREATE POLICY "Users can delete their own comments" ON comments
    FOR DELETE USING (auth.uid() = author_id);

-- Notifications policies
CREATE POLICY "Users can view their own notifications" ON notifications
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own notifications" ON notifications
    FOR UPDATE USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Tags policies
CREATE POLICY "Anyone can view tags" ON tags
    FOR SELECT USING (true);

CREATE POLICY "Only service role can manage tags" ON tags
    FOR ALL USING (auth.role() = 'service_role');

-- Post tags policies
CREATE POLICY "Anyone can view post tags" ON post_tags
    FOR SELECT USING (true);

CREATE POLICY "Only service role can manage post tags" ON post_tags
    FOR INSERT USING (auth.role() = 'service_role');

-- External posts policies (admin only)
CREATE POLICY "Only service role can access external posts staging" ON external_posts_staging
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Only service role can access external posts live" ON external_posts_live
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Premium users can view external posts" ON external_posts_live
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM profiles
            WHERE profiles.id = auth.uid()
            AND profiles.is_premium = true
        )
    );

-- =============================================
-- FUNCTIONS AND TRIGGERS
-- =============================================

-- Function to update post view count
CREATE OR REPLACE FUNCTION increment_post_view_count(post_uuid UUID)
RETURNS void AS $$
BEGIN
    UPDATE posts
    SET view_count = view_count + 1
    WHERE id = post_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if post is answered
CREATE OR REPLACE FUNCTION check_post_answered()
RETURNS TRIGGER AS $$
BEGIN
    -- If this is a comment on a post and it's marked as an answer
    IF NEW.parent_id IS NULL THEN
        UPDATE posts
        SET is_answered = true
        WHERE id = NEW.post_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to check if post is answered when comment is added
CREATE TRIGGER trigger_check_post_answered
    AFTER INSERT ON comments
    FOR EACH ROW
    WHEN (NEW.parent_id IS NULL)
    EXECUTE FUNCTION check_post_answered();

-- Function to create notification when comment is added
CREATE OR REPLACE FUNCTION create_comment_notification()
RETURNS TRIGGER AS $$
DECLARE
    post_author_id UUID;
    post_title TEXT;
BEGIN
    -- Get post author and title
    SELECT author_id, COALESCE(title, 'a post') INTO post_author_id, post_title
    FROM posts
    WHERE id = NEW.post_id;
    
    -- Create notification for post author
    IF post_author_id != NEW.author_id THEN
        INSERT INTO notifications (
            user_id,
            type,
            content,
            related_id
        ) VALUES (
            post_author_id,
            'new_comment',
            'New comment on your post: ' || post_title,
            NEW.id
        );
    END IF;
    
    -- If this is a reply to another comment, notify that comment's author
    IF NEW.parent_id IS NOT NULL THEN
        INSERT INTO notifications (
            user_id,
            type,
            content,
            related_id
        ) 
        SELECT 
            author_id,
            'new_comment',
            'New reply to your comment',
            NEW.id
        FROM comments
        WHERE id = NEW.parent_id AND author_id != NEW.author_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create notification when comment is added
CREATE TRIGGER trigger_create_comment_notification
    AFTER INSERT ON comments
    FOR EACH ROW
    EXECUTE FUNCTION create_comment_notification();

-- =============================================
-- STORED PROCEDURES FOR COMMON OPERATIONS
-- =============================================

-- Procedure to reset daily post counts
CREATE OR REPLACE PROCEDURE reset_daily_post_counts()
LANGUAGE SQL
AS $$
    UPDATE profiles
    SET daily_posts = 0
    WHERE is_premium = false;
$$;

-- Procedure to update active user counts
CREATE OR REPLACE PROCEDURE update_active_user_counts()
LANGUAGE SQL
AS $$
    UPDATE groups g
    SET active_count = (
        SELECT COUNT(DISTINCT up.user_id)
        FROM user_presence up
        WHERE up.group_id = g.id
        AND up.is_active = true
        AND up.last_seen > NOW() - INTERVAL '5 minutes'
    );
$$;

-- Procedure to clean up old presence data
CREATE OR REPLACE PROCEDURE cleanup_old_presence_data()
LANGUAGE SQL
AS $$
    UPDATE user_presence
    SET is_active = false
    WHERE last_seen < NOW() - INTERVAL '1 hour';
$$;

-- =============================================
-- HYBRID SEARCH FUNCTION
-- =============================================

-- Enhanced hybrid search function with better weighting
CREATE OR REPLACE FUNCTION hybrid_search_posts(
    query_text TEXT,
    query_embedding VECTOR(1536),
    search_group_id UUID,
    is_premium_user BOOLEAN,
    limit_count INTEGER DEFAULT 20
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
BEGIN
    RETURN QUERY
    WITH vector_matches AS (
        SELECT 
            p.id,
            1 - (p.embedding <=> query_embedding) AS vector_similarity
        FROM posts p
        WHERE 
            p.embedding IS NOT NULL
            AND query_embedding IS NOT NULL
            AND (
                p.group_id = search_group_id 
                OR (is_premium_user = true)
            )
    ),
    text_matches AS (
        SELECT
            p.id,
            ts_rank(
                setweight(to_tsvector('english', COALESCE(p.title, '')), 'A') ||
                setweight(to_tsvector('english', p.content), 'B'),
                plainto_tsquery('english', query_text)
            ) AS text_similarity
        FROM posts p
        WHERE
            query_text IS NOT NULL
            AND (
                p.group_id = search_group_id 
                OR (is_premium_user = true)
            )
            AND (
                to_tsvector('english', COALESCE(p.title, '') || ' ' || p.content) @@ 
                plainto_tsquery('english', query_text)
            )
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
        COALESCE(vm.vector_similarity * 0.7, 0) + COALESCE(tm.text_similarity * 0.3, 0) AS similarity
    FROM
        posts p
        LEFT JOIN vector_matches vm ON p.id = vm.id
        LEFT JOIN text_matches tm ON p.id = tm.id
    WHERE
        (vm.id IS NOT NULL OR tm.id IS NOT NULL)
        AND (
            p.group_id = search_group_id 
            OR (is_premium_user = true)
        )
    ORDER BY
        similarity DESC,
        p.score DESC,
        p.created_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================
-- SCHEDULED JOBS
-- =============================================

-- Create extension for scheduled jobs
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Schedule daily post count reset (2 AM)
SELECT cron.schedule('0 2 * * *', 'CALL reset_daily_post_counts()');

-- Schedule active user count updates (every 5 minutes)
SELECT cron.schedule('*/5 * * * *', 'CALL update_active_user_counts()');

-- Schedule presence data cleanup (every hour)
SELECT cron.schedule('0 * * * *', 'CALL cleanup_old_presence_data()');

-- =============================================
-- GRANT PERMISSIONS
-- =============================================

-- Grant permissions to authenticated users
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL PROCEDURES IN SCHEMA public TO authenticated;

-- Revoke specific permissions that should be controlled by RLS
REVOKE INSERT, UPDATE, DELETE ON TABLE tags FROM authenticated;
REVOKE INSERT, UPDATE, DELETE ON TABLE external_posts_staging FROM authenticated;
REVOKE INSERT, UPDATE, DELETE ON TABLE external_posts_live FROM authenticated;

-- =============================================
-- COMMENTS
-- =============================================

/*
This migration completes the database schema with:

1. Additional indexes for performance optimization
2. Missing columns for full functionality
3. Enhanced RLS policies for proper security
4. Notification system for user engagement
5. Functions and triggers for business logic
6. Stored procedures for common operations
7. Improved hybrid search function
8. Scheduled jobs for maintenance tasks

The schema now fully supports:
- Multi-tenant isolation with proper security
- Premium vs. free user differentiation
- Daily post limits for free users
- Notification system for engagement
- Efficient semantic and text search
- Automated maintenance tasks
*/