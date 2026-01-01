-- Essential functions for visa chat app
-- This creates the core functions needed for the application

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Function to reset daily posts for non-premium users
CREATE OR REPLACE FUNCTION reset_daily_posts()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  UPDATE user_profiles 
  SET daily_posts = 0 
  WHERE is_premium = false;
END;
$$;

-- Function to update user presence
CREATE OR REPLACE FUNCTION update_user_presence(
  p_user_id uuid,
  p_group_id uuid,
  p_is_active boolean DEFAULT true
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  INSERT INTO user_presence (user_id, group_id, last_seen, is_active)
  VALUES (p_user_id, p_group_id, now(), p_is_active)
  ON CONFLICT (user_id, group_id)
  DO UPDATE SET
    last_seen = now(),
    is_active = p_is_active;
END;
$$;

-- Function to get active users count for a group
CREATE OR REPLACE FUNCTION get_active_users_count(p_group_id uuid)
RETURNS integer
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT COUNT(*)::integer
  FROM user_presence
  WHERE group_id = p_group_id 
    AND last_seen > now() - interval '5 minutes';
$$;

-- Hybrid search function (combines vector similarity and text search)
CREATE OR REPLACE FUNCTION search_posts_hybrid(
  p_query_embedding vector(1536),
  p_match_query text,
  p_group_id uuid,
  p_limit integer DEFAULT 20,
  p_min_similarity float DEFAULT 0.7
)
RETURNS TABLE (
  id uuid,
  content text,
  author_id uuid,
  upvotes integer,
  downvotes integer,
  score integer,
  created_at timestamptz,
  similarity_score float,
  tag_names text[]
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  WITH search_results AS (
    SELECT 
      p.id,
      p.content,
      p.author_id,
      p.upvotes,
      p.downvotes,
      p.score,
      p.created_at,
      1 - (p.embedding <=> p_query_embedding) as similarity_score,
      array_agg(DISTINCT t.name) as tag_names
    FROM posts p
    LEFT JOIN post_tags pt ON p.id = pt.post_id
    LEFT JOIN tags t ON pt.tag_id = t.id
    WHERE p.group_id = p_group_id
      AND (
        1 - (p.embedding <=> p_query_embedding) > p_min_similarity
        OR to_tsvector('english', p.content) @@ plainto_tsquery('english', p_match_query)
      )
      AND p.status = 'active'
    GROUP BY p.id, p.content, p.author_id, p.upvotes, p.downvotes, p.score, p.created_at, p.embedding
    ORDER BY similarity_score DESC
    LIMIT p_limit
  )
  SELECT * FROM search_results;
END;
$$;

-- Function to inherit tags from similar posts
CREATE OR REPLACE FUNCTION inherit_tags_from_similar_posts(
  p_post_id uuid,
  p_min_similarity float DEFAULT 0.85,
  p_max_tags integer DEFAULT 3
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  similar_post RECORD;
  tag_record RECORD;
  inherited_count integer := 0;
BEGIN
  -- Get similar posts and their tags
  FOR similar_post IN
    SELECT p.id, p.embedding, array_agg(DISTINCT t.id ORDER BY t.name) as tag_ids
    FROM posts p
    LEFT JOIN post_tags pt ON p.id = pt.post_id
    LEFT JOIN tags t ON pt.tag_id = t.id
    WHERE p.id != p_post_id
      AND 1 - (p.embedding <=> (SELECT embedding FROM posts WHERE id = p_post_id)) > p_min_similarity
      AND p.status = 'active'
    GROUP BY p.id, p.embedding
    ORDER BY 1 - (p.embedding <=> (SELECT embedding FROM posts WHERE id = p_post_id)) DESC
    LIMIT 5
  LOOP
    -- Inherit tags from this similar post
    FOR tag_record IN
      SELECT id FROM unnest(similar_post.tag_ids) AS tag_id
      WHERE tag_id IS NOT NULL
    LOOP
      IF inherited_count < p_max_tags THEN
        INSERT INTO post_tags (post_id, tag_id)
        VALUES (p_post_id, tag_record.id)
        ON CONFLICT (post_id, tag_id) DO NOTHING;
        inherited_count := inherited_count + 1;
      END IF;
    END LOOP;
  END LOOP;
END;
$$;

-- Function to generate watermark hash
CREATE OR REPLACE FUNCTION generate_watermark_hash(
  p_content text,
  p_author_id uuid,
  p_created_at timestamptz
)
RETURNS text
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT encode(
    digest(
      p_content || p_author_id::text || extract(epoch from p_created_at)::text,
      'md5'
    ),
    'hex'
  );
$$;

-- Function to check if user can create post (quota check)
CREATE OR REPLACE FUNCTION can_create_post(p_user_id uuid)
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT 
    COALESCE(up.is_premium, false) 
    OR COALESCE(up.daily_posts, 0) < 10
  FROM user_profiles up
  WHERE up.user_id = p_user_id;
$$;

-- Function to increment daily posts
CREATE OR REPLACE FUNCTION increment_daily_posts(p_user_id uuid)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  UPDATE user_profiles 
  SET daily_posts = COALESCE(daily_posts, 0) + 1
  WHERE user_id = p_user_id;
END;
$$;

-- Function to calculate user engagement score
CREATE OR REPLACE FUNCTION calculate_user_engagement_score(p_user_id uuid)
RETURNS float
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT 
    COALESCE(
      (
        COUNT(DISTINCT p.id) * 2.0 +  -- Posts weight
        COUNT(DISTINCT c.id) * 1.0 +  -- Comments weight  
        SUM(p.upvotes) * 0.1 +        -- Upvotes received
        SUM(c.upvotes) * 0.1
      ) / GREATEST(
        EXTRACT(days FROM now() - COALESCE(MIN(p.created_at), now())) + 1,
        1
      ), 0
    ) as engagement_score
  FROM auth.users u
  LEFT JOIN posts p ON p.author_id = u.id
  LEFT JOIN comments c ON c.author_id = u.id
  WHERE u.id = p_user_id
    AND (p.created_at > now() - interval '30 days' OR p.created_at IS NULL)
    AND (c.created_at > now() - interval '30 days' OR c.created_at IS NULL);
$$;

-- Function to get trending tags in a time period
CREATE OR REPLACE FUNCTION get_trending_tags(
  p_group_id uuid,
  p_hours_back integer DEFAULT 24,
  p_limit integer DEFAULT 20
)
RETURNS TABLE (
  tag_id integer,
  tag_name text,
  post_count bigint,
  engagement_score float
)
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT 
    t.id as tag_id,
    t.name as tag_name,
    COUNT(DISTINCT pt.post_id) as post_count,
    COALESCE(
      AVG(
        p.upvotes::float + p.comments_count::float * 0.5
      ), 0
    ) as engagement_score
  FROM tags t
  JOIN post_tags pt ON t.id = pt.tag_id
  JOIN posts p ON pt.post_id = p.id
  WHERE p.group_id = p_group_id
    AND p.created_at > now() - (p_hours_back || ' hours')::interval
    AND p.status = 'active'
  GROUP BY t.id, t.name
  HAVING COUNT(DISTINCT pt.post_id) > 0
  ORDER BY engagement_score DESC, post_count DESC
  LIMIT p_limit;
$$;

-- Function to clean up old presence records
CREATE OR REPLACE FUNCTION cleanup_old_presence()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  DELETE FROM user_presence 
  WHERE last_seen < now() - interval '1 day';
END;
$$;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_posts_group_embedding ON posts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_posts_content_fts ON posts USING gin (to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_post_tags_post_id ON post_tags(post_id);
CREATE INDEX IF NOT EXISTS idx_post_tags_tag_id ON post_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_user_presence_group_active ON user_presence(group_id, last_seen);
CREATE INDEX IF NOT EXISTS idx_user_presence_user_active ON user_presence(user_id, last_seen);
CREATE INDEX IF NOT EXISTS idx_posts_score ON posts(score DESC);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_profiles_daily_posts ON user_profiles(user_id);

-- Comment on functions for documentation
COMMENT ON FUNCTION reset_daily_posts() IS 'Resets daily post count for non-premium users';
COMMENT ON FUNCTION update_user_presence(uuid, uuid, boolean) IS 'Updates user presence in a group';
COMMENT ON FUNCTION get_active_users_count(uuid) IS 'Returns count of active users in group (active in last 5 minutes)';
COMMENT ON FUNCTION search_posts_hybrid(vector, text, uuid, integer, float) IS 'Performs hybrid search combining vector similarity and text search';
COMMENT ON FUNCTION inherit_tags_from_similar_posts(uuid, float, integer) IS 'Inherits tags from similar posts to improve tagging';
COMMENT ON FUNCTION generate_watermark_hash(text, uuid, timestamptz) IS 'Generates unique watermark hash for content';
COMMENT ON FUNCTION can_create_post(uuid) IS 'Checks if user can create post based on premium status and quota';
COMMENT ON FUNCTION increment_daily_posts(uuid) IS 'Increments daily post count for user';
COMMENT ON FUNCTION calculate_user_engagement_score(uuid) IS 'Calculates user engagement score based on activity';
COMMENT ON FUNCTION get_trending_tags(uuid, integer, integer) IS 'Returns trending tags for a group within time period';
COMMENT ON FUNCTION cleanup_old_presence() IS 'Removes old presence records older than 1 day';