-- User Sessions Table
-- Tracks user sessions separately for better session analytics
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Session identification
    session_id TEXT NOT NULL,
    distinct_id TEXT,
    user_id UUID REFERENCES auth.users(id),
    
    -- Session metadata
    session_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    session_end TIMESTAMPTZ,
    duration_seconds INTEGER,
    page_views INTEGER DEFAULT 0,
    events_count INTEGER DEFAULT 0,
    
    -- Session tracking
    is_active BOOLEAN DEFAULT TRUE,
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    
    -- Geographic and device information
    country_code TEXT,
    region TEXT,
    city TEXT,
    device_type TEXT, -- mobile, desktop, tablet
    device_browser TEXT,
    device_os TEXT,
    device_screen_resolution TEXT,
    
    -- Session flow tracking
    landing_page TEXT,
    exit_page TEXT,
    referrer TEXT,
    referrer_type TEXT, -- direct, search, social, email, etc.
    referrer_domain TEXT,
    
    -- Session quality metrics
    bounce_rate BOOLEAN DEFAULT FALSE, -- true if single page session
    engagement_score INTEGER DEFAULT 0, -- custom engagement metric
    
    -- Marketing and campaign tracking
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    utm_term TEXT,
    utm_content TEXT,
    
    -- Session timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Metadata
    session_metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_distinct_id ON user_sessions(distinct_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_start ON user_sessions(session_start);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_end ON user_sessions(session_end);
CREATE INDEX IF NOT EXISTS idx_user_sessions_is_active ON user_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_last_activity ON user_sessions(last_activity);
CREATE INDEX IF NOT EXISTS idx_user_sessions_country_code ON user_sessions(country_code);
CREATE INDEX IF NOT EXISTS idx_user_sessions_device_type ON user_sessions(device_type);
CREATE INDEX IF NOT EXISTS idx_user_sessions_referrer_type ON user_sessions(referrer_type);
CREATE INDEX IF NOT EXISTS idx_user_sessions_utm_campaign ON user_sessions(utm_campaign);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_active ON user_sessions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_date_range ON user_sessions(session_start, session_end);
CREATE INDEX IF NOT EXISTS idx_user_sessions_bounce_rate ON user_sessions(bounce_rate, session_start);

-- RLS (Row Level Security) - Allow users to see their own sessions
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

-- Create policy for users to see their own sessions
CREATE POLICY "Users can view own sessions" ON user_sessions
    FOR SELECT USING (
        auth.uid() = user_id OR 
        -- Allow viewing sessions for authenticated users (if user_id is null)
        (user_id IS NULL AND auth.uid() IS NOT NULL)
    );

-- Admin access policy
CREATE POLICY "Admins can view all sessions" ON user_sessions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM auth.users 
            WHERE auth.users.id = auth.uid() 
            AND auth.users.raw_user_meta_data->>'role' = 'admin'
        )
    );

-- Function to update session duration and activity
CREATE OR REPLACE FUNCTION update_session_activity(
    p_session_id TEXT,
    p_event_count INTEGER DEFAULT 1,
    p_page_view BOOLEAN DEFAULT FALSE
) RETURNS VOID AS $$
BEGIN
    UPDATE user_sessions 
    SET 
        events_count = events_count + p_event_count,
        page_views = page_views + CASE WHEN p_page_view THEN 1 ELSE 0 END,
        last_activity = NOW(),
        duration_seconds = EXTRACT(EPOCH FROM (NOW() - session_start))::INTEGER,
        updated_at = NOW()
    WHERE session_id = p_session_id;
END;
$$ LANGUAGE plpgsql;

-- Function to end session
CREATE OR REPLACE FUNCTION end_session(
    p_session_id TEXT
) RETURNS VOID AS $$
BEGIN
    UPDATE user_sessions 
    SET 
        session_end = NOW(),
        is_active = FALSE,
        duration_seconds = EXTRACT(EPOCH FROM (NOW() - session_start))::INTEGER,
        bounce_rate = (page_views <= 1 AND events_count <= 1),
        updated_at = NOW()
    WHERE session_id = p_session_id;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically end inactive sessions
CREATE OR REPLACE FUNCTION auto_end_inactive_sessions()
RETURNS TRIGGER AS $$
BEGIN
    -- Auto-end sessions that have been inactive for more than 30 minutes
    IF OLD.last_activity < NOW() - INTERVAL '30 minutes' AND OLD.is_active = TRUE THEN
        UPDATE user_sessions 
        SET 
            session_end = NOW(),
            is_active = FALSE,
            duration_seconds = EXTRACT(EPOCH FROM (NOW() - session_start))::INTEGER,
            updated_at = NOW()
        WHERE session_id = OLD.session_id;
    END IF;
    
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Trigger for auto-ending sessions
CREATE TRIGGER trigger_auto_end_inactive_sessions
    BEFORE UPDATE ON user_sessions
    FOR EACH ROW
    EXECUTE FUNCTION auto_end_inactive_sessions();