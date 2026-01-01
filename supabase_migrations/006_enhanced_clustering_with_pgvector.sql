-- Enhanced Clustering with pgvector for Stack Overflow Style Posts
-- This migration enables vector similarity search and clustering for similar posts

-- Enable pgvector extension
_messages_received + 1 ELSE total_messages_received END,
            total_answers = CASE WHEN counter_type = 'answer' THEN total_answers + 1 ELSE total_answers END,
            total_commentsCREATE EXTENSION IF NOT EXISTS vector;

-- Create clusters table for storing cluster information
CREATE TABLE IF NOT EXISTS post_clusters (
    cluster_id SERIAL PRIMARY KEY,
    cluster_name TEXT NOT NULL,
 = CASE WHEN counter_type = 'comment' THEN total_comments + 1 ELSE total_comments END,
            updated_at = NOW()
        WHERE user_id = user_uuid;
    ELSE
        UPDATE user    centroid_embedding VECTOR(1536), -- OpenAI text-embedding-3-small dimension
    post_count INTEGER DEFAULT 0,
    avg_similarity_score FLOAT DEFAULT 0.0,
_spaces 
        SET 
            total_interviews = CASE WHEN counter_type = 'interview' THEN GREATEST(total_interviews - 1, 0) ELSE total_interviews END    keywords TEXT[], -- Array of common keywords for this cluster
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create,
            total_posts = CASE WHEN counter_type = 'post' THEN GREATEST(total_posts - 1, 0) ELSE total_posts END,
            total_messages_sent = CASE WHEN counter_type = posts table with enhanced clustering support
CREATE TABLE IF NOT EXISTS posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID NOT NULL REFERENCES groups(id),
    country_id INTEGER REFERENCES countries 'message_sent' THEN GREATEST(total_messages_sent - 1, 0) ELSE total_messages_sent END,
            total_messages_received = CASE WHEN counter_type = 'message_received' THEN GREATEST(id),
    author_id INTEGER NOT NULL REFERENCES users(id),
    title TEXT,
    content TEXT NOT NULL,
    content_html TEXT,
    embedding VECTOR(1536), -- OpenAI text-(total_messages_received - 1, 0) ELSE total_messages_received END,
            total_answers = CASE WHEN counter_type = 'answer' THEN GREATEST(total_answers - 1, embedding-3-small
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    score INTEGER GENERATED ALWAYS AS (upvotes - downvotes) STORED,
    status TEXT0) ELSE total_answers END,
            total_comments = CASE WHEN counter_type = 'comment' THEN GREATEST(total_comments - 1, 0) ELSE total_comments END,
            updated_at DEFAULT 'published' CHECK (status IN ('published', 'draft', 'archived', 'deleted')),
    is_pinned BOOLEAN DEFAULT FALSE,
    is_locked BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    cluster_id INTEGER REFERENCES post_clusters(cluster_id),
    similarity_score FLOAT DEFAULT 0.0, -- Similarity to cluster centroid = NOW()
        WHERE user_id = user_uuid;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user's personal feed
CREATE OR RE
    search_vector TSVECTOR,
    watermark_hash TEXT,
    display_watermark TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for posts table
CREATE TRIGGER update_posts_updated_at 
    BEFORE UPDATE ON posts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for post_clusters table
CREATE TRIGGER update_post_clusters_updated_at 
    BEFORE UPDATE ON post_clusters 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_posts_embedding ON posts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_posts_cluster_id ON posts(cluster_id);
CREATE INDEX IF NOT EXISTS idx_posts_group_id ON posts(group_id);
CREATE INDEX IF NOT EXISTS idx_posts_country_id ON posts(country_id);
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_score ON posts(score DESC);
CREATE INDEX IF NOT EXISTS idx_post_clusters_centroid ON post_clusters USING ivfflat (centroid_embedding vector_cosine_ops) WITH (lists = 50);

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
    author_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE,
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

-- Function to find posts similar to a query text
CREATE OR REPLACE FUNCTION find_similar_posts_by_text(
    query_text TEXT,
    queryPLACE FUNCTION get_user_personal_feed(
    target_user_id UUID,
    viewer_id UUID,
    limit_count INTEGER DEFAULT 20
)
RETURNS TABLE (
_embedding VECTOR(1536),
    similarity_threshold FLOAT DEFAULT 0.6,
    max_results INT DEFAULT 20
)
RETURNS TABLE (
    post_id UUID,
    similarity_score FLOAT    id UUID,
    type TEXT,
    title TEXT,
    content TEXT,
    created_at TIMESTAMPTZ,
    author_id UUID,
    author,
    title TEXT,
    content TEXT,
    author_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE,
    cluster_id INTEGER
) AS $$
BEGIN
    RETURN QUERY
   _name TEXT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH combined_content AS (
        -- User SELECT 
        p.id,
        1 - (p.embedding <=> query_embedding) as similarity_score,
        p.title,
        p.content,
        p.author_id,
        p.created_at posts
        SELECT 
            up.id,
            'user_post' as type,
            up.title,
            up.content,
            up.created_at,
            up.author_id,
            us,
        p.cluster_id
    FROM posts p
    WHERE 
        p.embedding IS NOT NULL
        AND p.status = 'published'
        AND (1 - (p.embedding <=.display_name as author_name,
            json_build_object('post_type', up.post_type, 'tags', up.tags, 'view_count', up.view_count, 'like_count',> query_embedding)) > similarity_threshold
    ORDER BY similarity_score DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to assign posts to clusters
CREATE OR REPLACE FUNCTION assign_posts_to_clusters(
    cluster_count INT DEFAULT 20
)
RETURNS INTEGER AS $$
DECLARE
    cluster_record RECORD;
    post_record RECORD;
    min_distance FLOAT up.like_count) as metadata
        FROM user_posts up
        JOIN user_spaces us ON up.author_id = us.user_id
        WHERE up.author_id = target_user_id
;
    best_cluster_id INT;
    updated_count INT := 0;
BEGIN
    -- Update cluster centroids first
    FOR cluster_record IN 
        SELECT cluster_id, AVG(embedding)        AND (
            up.visibility = 'public' OR
            up.author_id = viewer_id OR
            (up.visibility = 'followers_only' AND viewer as centroid 
        FROM posts 
        WHERE embedding IS NOT NULL AND cluster_id IS NOT NULL
        GROUP BY cluster_id
    LOOP
        UPDATE post_clusters 
        SET centroid_embedding =_id IN (SELECT follower_id FROM user_follows WHERE followed_id = target_user_id))
        )
        
        UNION ALL
        
        -- Interview experiences
        SELECT 
            ie.id,
            ' cluster_record.centroid,
            updated_at = NOW()
        WHERE cluster_id = cluster_record.cluster_id;
    END LOOP;
    
    -- Assign unassigned posts to nearest cluster
    FORinterview_experience' as type,
            ie.title,
            ie.content,
            ie.created_at,
            ie.user_id as author_id,
            us.display_name as author_name,
            post_record IN 
        SELECT id, embedding 
        FROM posts 
        WHERE embedding IS NOT NULL AND cluster_id IS NULL
    LOOP
        SELECT 
            cluster_id,
            (embedding json_build_object('company', ie.company_name, 'position', ie.position_title, 'difficulty', ie.difficulty_rating, 'outcome', ie.outcome) as metadata
        <=> post_record.embedding) as distance
        INTO best_cluster_id, min_distance
        FROM post_clusters 
        WHERE centroid_embedding IS NOT NULL
        ORDER BY embedding <=> post_record FROM interview_experiences ie
        JOIN user_spaces us ON ie.user_id = us.user_id
        WHERE ie.user_id = target_user_id
        AND (ie.is_public = true.embedding
        LIMIT 1;
        
        IF best_cluster_id IS NOT NULL THEN
            UPDATE posts 
            SET cluster_id = best_cluster_id,
                similarity_score = 1 - min OR ie.user_id = viewer_id)
        
        UNION ALL
        
        -- User activities (public only)
        SELECT 
            ua.id,
            'user_activity' as type,
_distance,
                updated_at = NOW()
            WHERE id = post_record.id;
            
            updated_count := updated_count + 1;
        END IF;
    END LOOP;
    
    -- Update            ua.description as title,
            '' as content,
            ua.created_at,
            ua.user_id as author_id,
            us.display_name as author_name,
            ua.metadata
 cluster post counts
    UPDATE post_clusters 
    SET post_count = (
        SELECT COUNT(*) 
        FROM posts 
        WHERE posts.cluster_id = post_clusters.cluster_id
    );
    
    RETURN        FROM user_activities ua
        JOIN user_spaces us ON ua.user_id = us.user_id
        WHERE ua.user_id = target_user_id
        AND ua.is_public = true
 updated_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get clustered posts for a country
CREATE OR REPLACE FUNCTION get_clustered_posts_by_country(
    country_param TEXT,
    )
    SELECT * FROM combined_content
    ORDER BY created_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to search user's personal content
CREATE OR REPLACE FUNCTION search_user_content(
    target_user_id UUID,
    search_query TEXT,
    search_embedding VECTOR(1536),
    viewer_id UUID,
    limit_per_cluster INT DEFAULT 5
)
RETURNS TABLE (
    post_id UUID,
    title TEXT,
    content TEXT,
    author_id INTEGER,
    created_at TIMESTAMP WITH TIME    limit_count INTEGER DEFAULT 20
)
RETURNS TABLE (
    id UUID,
    type TEXT,
    title TEXT,
    content TEXT,
    created_at TIMESTAMPTZ,
    ZONE,
    cluster_id INTEGER,
    cluster_name TEXT,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.title,
        p.content,
        p.author_id,
        p.created_at,
        p.cluster_id,
        pc.cluster_name,
        p.similarity_score
    FROM posts p
    JOIN post_clusters pc ON p.cluster_id = pc.cluster_id
    JOIN countries c ON p.country_id = c.id
    WHERE 
        c.name = country_param
        AND p.status = 'published'
        AND similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH content_matches AS (
        -- User posts
        SELECT 
            up.id,
            'user_post' as p.embedding IS NOT NULL
    ORDER BY 
        pc.cluster_id,
        p.similarity_score DESC,
        p.created_at DESC
    LIMIT (cluster_count * limit_per_cluster);
END type,
            up.title,
            up.content,
            up.created_at,
            COALESCE(
                0.7 * (1 - (up.embedding <=> search_embedding)) +
                0.3 * ts_rank(up.search_vector, plainto_tsquery('english', search_query)),
                0
            ) as similarity_score
       ;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Insert initial clusters for USA visa posts
INSERT INTO post_clusters (cluster_name, keywords) VALUES
('H1B Processing Issues', ARRAY['h FROM user_posts up
        WHERE up.author_id = target_user_id
        AND (
            up.visibility = 'public' OR
            up.author_id = viewer_id OR
            (up.visibility = 'followers_only' AND viewer_id IN (SELECT follower_id FROM user_follows WHERE followed_id = target_user_id))
        )
        AND (
            search_embedding IS NULL OR up1b', 'processing', 'pending', 'rfe', 'approval']),
('Visa Stamping Problems', ARRAY['stamping', 'interview', '221g', 'administrative', '.embedding IS NOT NULL
        )
        AND (
            search_query IS NULL OR up.search_vector @@ plainto_tsquery('english', search_query)
        )
        
        UNION ALL
        
        --processing']),
('Visa Revocation Cases', ARRAY['revocation', '221i', 'notice', 'revoked', 'cancelled']),
('Social Media Screening', ARRAY['social', 'media', Interview experiences
        SELECT 
            ie.id,
            'interview_experience' as type,
            ie.title,
            ie.content,
            ie.created_at,
            COALESCE(
                 'facebook', 'twitter', 'instagram']),
('H4 EAD and Spousal Issues', ARRAY['h4', 'ead', 'spouse', 'dependent', 'work', 'authorization']),
0.7 * (1 - (ie.embedding <=> search_embedding)) +
                0.3 * ts_rank(ie.search_vector, plainto_tsquery('english', search_query)),
('F1 Student Visa Issues', ARRAY['f1', 'student', 'cpt', 'opt', 'stem', 'academic']),
('Travel and Re-entry', ARRAY['travel', 'reentry', 'port', 'entry', 'border', 'airport']),
('Green Card and Employment', ARRAY['green', 'card', 'employment', 'eb1', 'eb2', '                0
            ) as similarity_score
        FROM interview_experiences ie
        WHERE ie.user_id = target_user_id
        AND (ie.is_public = true OR ie.user_idimmigration']),
('Family-based Immigration', ARRAY['family', 'spouse', 'parent', 'child', 'marriage']),
('Immigration Court and Legal', ARRAY['court', 'deportation', = viewer_id)
        AND (
            search_embedding IS NULL OR ie.embedding IS NOT NULL
        )
        AND (
            search_query IS NULL OR ie.search_vector @@ plainto_tsquery(' 'removal', 'attorney', 'legal']),
('Work Authorization', ARRAY['work', 'authorization', 'ead', 'employment', 'permit']),
('Change of Status', ARRAY['change',english', search_query)
        )
    )
    SELECT * FROM content_matches
    ORDER BY similarity_score DESC, created_at DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFIN 'status', 'cos', 'adjustment', 'aos']),
('Naturalization and Citizenship', ARRAY['citizenship', 'naturalization', 'n400', 'test', 'ceremonyER;

-- =============================================
-- TRIGGERS FOR AUTOMATION
-- =============================================

-- Trigger to create user space on registration
CREATE TRIGGER trigger_create_user_space
    AFTER INSERT']),
('Consulate and Embassy', ARRAY['consulate', 'embassy', 'interview', 'appointment', 'visa']),
('Immigration Updates and News', ARRAY['policy', 'update', 'news', 'rule', 'change'])
ON CONFLICT (cluster_name) DO NOTHING;

-- Create view for easy access to clustered posts
CREATE OR REPLACE VIEW clustered_posts_view AS
SELECT 
    p.id,
    p.title,
    p.content,
    p.author_id,
    u.username as author_name,
    p.upvotes,
    p.downvotes,
    p.score,
    ON auth.users
    FOR EACH ROW EXECUTE FUNCTION create_user_space();

-- Trigger to update space counters on content creation
CREATE OR REPLACE FUNCTION trigger_update_counters()
RETURNS TRIGGER AS $$
BEGIN
    -- Update counters based on content type
    IF TG_TABLE_NAME = ' p.view_count,
    p.comment_count,
    p.cluster_id,
    pc.cluster_name,
    pc.keywords as cluster_keywords,
    p.similarity_score,
    c.name as country_name,
interview_experiences' THEN
        PERFORM update_space_counters(NEW.user_id, 'interview', true);
        -- Create activity
    p.created_at,
    p.updated_at
FROM posts p
LEFT JOIN users u ON p.author_id = u.id
LEFT JOIN post_clusters pc ON p.cluster_id = pc.cluster_id
        INSERT INTO user_activities (user_id, activity_type, target_type, target_id, description, metadata)
        VALUES (NEW.user_id, 'posted', 'interview_exLEFT JOIN countries c ON p.country_id = c.id
WHERE p.status = 'published';

-- Grant necessary permissions
GRANT EXECUTE ON FUNCTION find_similar_posts(UUID, FLOAT, INT) TO authenticated;
GRANT EXECUTE ON FUNCTION find_similar_posts_by_text(TEXT, VECTOR(1536), FLOAT, INT) TO authenticated;
GRANT EXECUTE ON FUNCTION assign_posts_to_clusters(INT) TO authenticated;
GRANT EXECUTE ON FUNCTION get_clustered_posts_by_country(TEXT, INT) TO authenticated;
GRANT SELECT ON clustered_posts_view TO authenticated;