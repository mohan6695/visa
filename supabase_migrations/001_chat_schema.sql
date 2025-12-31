-- Migration: Add chat schema for group messaging
-- This migration adds the necessary tables for Supabase Realtime chat functionality

-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Create group messages table
CREATE TABLE group_messages (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    content_html TEXT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    message_type VARCHAR(20) DEFAULT 'text' CHECK (message_type IN ('text', 'image', 'file')),
    status VARCHAR(20) DEFAULT 'published' CHECK (status IN ('published', 'edited', 'deleted')),
    like_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    search_vector TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    content_embedding VECTOR(1536)
);

-- Create message read receipts table
CREATE TABLE message_read_receipts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    message_id INTEGER NOT NULL REFERENCES group_messages(id) ON DELETE CASCADE,
    read_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, group_id, message_id)
);

-- Create user presence table
CREATE TABLE user_presence (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY(user_id, group_id)
);

-- Create group message likes table
CREATE TABLE group_message_likes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_id INTEGER NOT NULL REFERENCES group_messages(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, message_id)
);

-- Create indexes for performance
CREATE INDEX idx_group_messages_group_id ON group_messages(group_id);
CREATE INDEX idx_group_messages_user_id ON group_messages(user_id);
CREATE INDEX idx_group_messages_created_at ON group_messages(created_at);
CREATE INDEX idx_group_messages_status ON group_messages(status);
CREATE INDEX idx_group_messages_search_vector ON group_messages USING GIN(search_vector);
CREATE INDEX idx_group_messages_content_embedding ON group_messages USING ivfflat (content_embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_message_read_receipts_user_group ON message_read_receipts(user_id, group_id);
CREATE INDEX idx_message_read_receipts_message_id ON message_read_receipts(message_id);

CREATE INDEX idx_user_presence_group_id ON user_presence(group_id);
CREATE INDEX idx_user_presence_last_seen ON user_presence(last_seen);

CREATE INDEX idx_group_message_likes_message_id ON group_message_likes(message_id);
CREATE INDEX idx_group_message_likes_user_id ON group_message_likes(user_id);

-- Enable Row Level Security (RLS) for group messages
ALTER TABLE group_messages ENABLE ROW LEVEL SECURITY;

-- Create policies for group messages
CREATE POLICY "Users can view messages in groups they belong to" ON group_messages
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM community_members cm
            WHERE cm.user_id = auth.uid()
            AND cm.community_id = group_messages.group_id
            AND cm.is_active = true
        )
    );

CREATE POLICY "Users can insert messages in groups they belong to" ON group_messages
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM community_members cm
            WHERE cm.user_id = auth.uid()
            AND cm.community_id = group_messages.group_id
            AND cm.is_active = true
        )
    );

CREATE POLICY "Users can update their own messages" ON group_messages
    FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can delete their own messages" ON group_messages
    FOR DELETE
    USING (user_id = auth.uid());

-- Enable RLS for message read receipts
ALTER TABLE message_read_receipts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own read receipts" ON message_read_receipts
    FOR ALL
    USING (user_id = auth.uid());

-- Enable RLS for user presence
ALTER TABLE user_presence ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own presence" ON user_presence
    FOR ALL
    USING (user_id = auth.uid());

-- Enable RLS for group message likes
ALTER TABLE group_message_likes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view all likes" ON group_message_likes
    FOR SELECT
    USING (true);

CREATE POLICY "Users can insert likes for their own messages" ON group_message_likes
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM group_messages gm
            WHERE gm.id = message_id
            AND EXISTS (
                SELECT 1 FROM community_members cm
                WHERE cm.user_id = auth.uid()
                AND cm.community_id = gm.group_id
                AND cm.is_active = true
            )
        )
    );

CREATE POLICY "Users can delete their own likes" ON group_message_likes
    FOR DELETE
    USING (user_id = auth.uid());

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for group messages
CREATE TRIGGER update_group_messages_updated_at 
    BEFORE UPDATE ON group_messages 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to update search vector
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector = to_tsvector('english', NEW.content);
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for search vector
CREATE TRIGGER update_group_messages_search_vector 
    BEFORE INSERT OR UPDATE ON group_messages 
    FOR EACH ROW 
    EXECUTE FUNCTION update_search_vector();

-- Create function to update user presence
CREATE OR REPLACE FUNCTION update_user_presence()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_presence (user_id, group_id, last_seen)
    VALUES (NEW.user_id, NEW.group_id, NOW())
    ON CONFLICT (user_id, group_id)
    DO UPDATE SET last_seen = NOW();
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for user presence
CREATE TRIGGER update_user_presence_on_message
    AFTER INSERT ON group_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_user_presence();

-- Grant permissions to authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON group_messages TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON message_read_receipts TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_presence TO authenticated;
GRANT SELECT, INSERT, DELETE ON group_message_likes TO authenticated;

-- Grant sequence permissions
GRANT USAGE, SELECT ON SEQUENCE group_messages_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE message_read_receipts_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE group_message_likes_id_seq TO authenticated;