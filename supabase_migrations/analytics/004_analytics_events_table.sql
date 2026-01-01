-- =============================================
-- Analytics Events Storage for Hybrid PostHog Setup
-- This table stores all raw analytics events locally
-- Benefits: $0 storage, 100ms latency, full data control
-- =============================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Analytics events table
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Event identification
    event_id TEXT NOT NULL,
    event_name TEXT NOT NULL,
    
    -- User context
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    session_id TEXT,
    distinct_id TEXT,
    
    -- Event properties
    properties JSONB DEFAULT '{}',
    event_type TEXT DEFAULT 'custom',
    
    -- Page/context information
    page_url TEXT,
    page_title TEXT,
    referrer TEXT,
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    
    -- Device/browser information
    user_agent TEXT,
    ip_address INET,
    device_type TEXT,
    browser_name TEXT,
    browser_version TEXT,
    os_name TEXT,
    os_version TEXT,
    
    -- Geographic information
    country TEXT,
    region TEXT,
    city TEXT,
    timezone TEXT,
    
    -- Performance metrics
    load_time_ms INTEGER,
    time_on_page_ms INTEGER,
    
    -- Custom dimensions
    dimension_1 TEXT,
    dimension_2 TEXT,
    dimension_3 TEXT,
    dimension_4 TEXT,
    dimension_5 TEXT,
    
    -- Revenue tracking (for future e-commerce features)
    revenue DECIMAL(10,2),
    currency TEXT DEFAULT 'USD',
    
    -- Metadata
    source TEXT DEFAULT 'posthog', -- posthog, custom, etc.
    environment TEXT DEFAULT 'development',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id ON analytics_events(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_event_name ON analytics_events(event_name);
CREATE INDEX IF NOT EXISTS idx_analytics_events_created_at ON analytics_events(created_at);
CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON analytics_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_analytics_events_distinct_id ON analytics_events(distinct_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_properties_gin ON analytics_events USING GIN(properties);

-- Partitioning for large datasets (optional)
-- CREATE TABLE analytics_events_y2024m01 PARTITION OF analytics_events 
-- FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Row Level Security (RLS)
ALTER TABLE analytics_events ENABLE ROW LEVEL SECURITY;

-- Policy for authenticated users to insert their own events
CREATE POLICY "Users can insert their own events" ON analytics_events
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy for authenticated users to read their own events
CREATE POLICY "Users can read their own events" ON analytics_events
    FOR SELECT USING (auth.uid() = user_id);

-- Policy for service role to manage all events
CREATE POLICY "Service role can manage all events" ON analytics_events
    FOR ALL USING (auth.role() = 'service_role');

COMMENT ON TABLE analytics_events IS 'Local storage for analytics events - hybrid PostHog setup';
COMMENT ON COLUMN analytics_events.properties IS 'JSON object containing event properties';
COMMENT ON COLUMN analytics_events.source IS 'Event source: posthog, custom, etc.';

-- =============================================
-- PostgreSQL Function for Event Insertion
-- This function provides a simple interface for inserting analytics events
-- =============================================

CREATE OR REPLACE FUNCTION insert_analytics_event(
    p_event_id TEXT,
    p_event_name TEXT,
    p_user_id UUID DEFAULT NULL,
    p_session_id TEXT DEFAULT NULL,
    p_distinct_id TEXT DEFAULT NULL,
    p_properties JSONB DEFAULT '{}',
    p_event_type TEXT DEFAULT 'custom',
    p_page_url TEXT DEFAULT NULL,
    p_page_title TEXT DEFAULT NULL,
    p_referrer TEXT DEFAULT NULL,
    p_utm_source TEXT DEFAULT NULL,
    p_utm_medium TEXT DEFAULT NULL,
    p_utm_campaign TEXT DEFAULT NULL,
    p_user_agent TEXT DEFAULT NULL,
    p_ip_address INET DEFAULT NULL,
    p_device_type TEXT DEFAULT NULL,
    p_browser_name TEXT DEFAULT NULL,
    p_browser_version TEXT DEFAULT NULL,
    p_os_name TEXT DEFAULT NULL,
    p_os_version TEXT DEFAULT NULL,
    p_country TEXT DEFAULT NULL,
    p_region TEXT DEFAULT NULL,
    p_city TEXT DEFAULT NULL,
    p_timezone TEXT DEFAULT NULL,
    p_load_time_ms INTEGER DEFAULT NULL,
    p_time_on_page_ms INTEGER DEFAULT NULL,
    p_dimension_1 TEXT DEFAULT NULL,
    p_dimension_2 TEXT DEFAULT NULL,
    p_dimension_3 TEXT DEFAULT NULL,
    p_dimension_4 TEXT DEFAULT NULL,
    p_dimension_5 TEXT DEFAULT NULL,
    p_revenue DECIMAL(10,2) DEFAULT NULL,
    p_currency TEXT DEFAULT 'USD',
    p_source TEXT DEFAULT 'posthog',
    p_environment TEXT DEFAULT 'development',
    p_timestamp TIMESTAMPTZ DEFAULT NOW()
)
RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
AS $
DECLARE
    event_uuid UUID;
BEGIN
    INSERT INTO analytics_events (
        event_id,
        event_name,
        user_id,
        session_id,
        distinct_id,
        properties,
        event_type,
        page_url,
        page_title,
        referrer,
        utm_source,
        utm_medium,
        utm_campaign,
        user_agent,
        ip_address,
        device_type,
        browser_name,
        browser_version,
        os_name,
        os_version,
        country,
        region,
        city,
        timezone,
        load_time_ms,
        time_on_page_ms,
        dimension_1,
        dimension_2,
        dimension_3,
        dimension_4,
        dimension_5,
        revenue,
        currency,
        source,
        environment,
        timestamp
    ) VALUES (
        p_event_id,
        p_event_name,
        p_user_id,
        p_session_id,
        p_distinct_id,
        p_properties,
        p_event_type,
        p_page_url,
        p_page_title,
        p_referrer,
        p_utm_source,
        p_utm_medium,
        p_utm_campaign,
        p_user_agent,
        p_ip_address,
        p_device_type,
        p_browser_name,
        p_browser_version,
        p_os_name,
        p_os_version,
        p_country,
        p_region,
        p_city,
        p_timezone,
        p_load_time_ms,
        p_time_on_page_ms,
        p_dimension_1,
        p_dimension_2,
        p_dimension_3,
        p_dimension_4,
        p_dimension_5,
        p_revenue,
        p_currency,
        p_source,
        p_environment,
        p_timestamp
    ) RETURNING id INTO event_uuid;
    
    RETURN event_uuid;
END;
$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION insert_analytics_event TO authenticated;
GRANT EXECUTE ON FUNCTION insert_analytics_event TO service_role;

COMMENT ON FUNCTION insert_analytics_event IS 'Inserts an analytics event with all available fields';
