-- Migration: Add Telegram chat schema for bulk upload
-- This migration adds tables specifically for Telegram chat data import

-- Create telegram_chats table to store chat metadata
CREATE TABLE telegram_chats (
    id SERIAL PRIMARY KEY,
    chat_id VARCHAR(255) UNIQUE NOT NULL,
    chat_name VARCHAR(500),
    chat_type VARCHAR(50) CHECK (chat_type IN ('private', 'group', 'supergroup', 'channel')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_messages INTEGER DEFAULT 0,
    recent_messages_count INTEGER DEFAULT 0,
    summary_uploaded BOOLEAN DEFAULT false,
    summary_path VARCHAR(1000)
);

-- Create telegram_messages table for recent messages (last 30 days)
CREATE TABLE telegram_messages (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER NOT NULL REFERENCES telegram_chats(id) ON DELETE CASCADE,
    msg_id VARCHAR(255) NOT NULL,
    sender_alias VARCHAR(255) NOT NULL,
    sender_id VARCHAR(255),
    message_type VARCHAR(50) DEFAULT 'text',
    text_content TEXT,
    raw_data JSONB,
    sent_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    search_vector TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', COALESCE(text_content, ''))) STORED,
    content_embedding VECTOR(1536),
    UNIQUE(chat_id, msg_id)
);

-- Create telegram_user_aliases table for pseudonymization
CREATE TABLE telegram_user_aliases (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER NOT NULL REFERENCES telegram_chats(id) ON DELETE CASCADE,
    original_user_id VARCHAR(255) NOT NULL,
    original_username VARCHAR(255),
    alias VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(chat_id, original_user_id)
);

-- Create indexes for performance
CREATE INDEX idx_telegram_messages_chat_id ON telegram_messages(chat_id);
CREATE INDEX idx_telegram_messages_sent_at ON telegram_messages(sent_at);
CREATE INDEX idx_telegram_messages_sender_alias ON telegram_messages(sender_alias);
CREATE INDEX idx_telegram_messages_search_vector ON telegram_messages USING GIN(search_vector);
CREATE INDEX idx_telegram_messages_content_embedding ON telegram_messages USING ivfflat (content_embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_telegram_user_aliases_chat_id ON telegram_user_aliases(chat_id);
CREATE INDEX idx_telegram_user_aliases_original_user_id ON telegram_user_aliases(original_user_id);
CREATE INDEX idx_telegram_user_aliases_alias ON telegram_user_aliases(alias);

-- Enable Row Level Security (RLS) for telegram tables
ALTER TABLE telegram_chats ENABLE ROW LEVEL SECURITY;
ALTER TABLE telegram_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE telegram_user_aliases ENABLE ROW LEVEL SECURITY;

-- Create policies for telegram_chats
CREATE POLICY "Admins can manage all telegram chats" ON telegram_chats
    FOR ALL
    USING (auth.role() = 'authenticated');

-- Create policies for telegram_messages
CREATE POLICY "Users can view messages in chats they have access to" ON telegram_messages
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM telegram_chats tc
            WHERE tc.id = telegram_messages.chat_id
        )
    );

CREATE POLICY "Admins can insert telegram messages" ON telegram_messages
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Admins can update telegram messages" ON telegram_messages
    FOR UPDATE
    USING (auth.role() = 'authenticated');

-- Create policies for telegram_user_aliases
CREATE POLICY "Users can view aliases in chats they have access to" ON telegram_user_aliases
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM telegram_chats tc
            WHERE tc.id = telegram_user_aliases.chat_id
        )
    );

CREATE POLICY "Admins can manage telegram aliases" ON telegram_user_aliases
    FOR ALL
    USING (auth.role() = 'authenticated');

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_telegram_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for telegram_chats
CREATE TRIGGER update_telegram_chats_updated_at 
    BEFORE UPDATE ON telegram_chats 
    FOR EACH ROW 
    EXECUTE FUNCTION update_telegram_updated_at_column();

-- Create function to update search vector for messages
CREATE OR REPLACE FUNCTION update_telegram_messages_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector = to_tsvector('english', COALESCE(NEW.text_content, ''));
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for search vector
CREATE TRIGGER update_telegram_messages_search_vector 
    BEFORE INSERT OR UPDATE ON telegram_messages 
    FOR EACH ROW 
    EXECUTE FUNCTION update_telegram_messages_search_vector();

-- Create function to update chat message counts
CREATE OR REPLACE FUNCTION update_telegram_chat_counts()
RETURNS TRIGGER AS $$
BEGIN
    -- Update total messages count
    UPDATE telegram_chats 
    SET total_messages = (
        SELECT COUNT(*) FROM telegram_messages tm 
        WHERE tm.chat_id = NEW.chat_id
    ),
    recent_messages_count = (
        SELECT COUNT(*) FROM telegram_messages tm 
        WHERE tm.chat_id = NEW.chat_id 
        AND tm.sent_at >= NOW() - INTERVAL '30 days'
    )
    WHERE id = NEW.chat_id;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for chat counts
CREATE TRIGGER update_telegram_chat_counts_on_message
    AFTER INSERT OR UPDATE ON telegram_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_telegram_chat_counts();

-- Grant permissions to authenticated users
GRANT SELECT, INSERT, UPDATE, DELETE ON telegram_chats TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON telegram_messages TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON telegram_user_aliases TO authenticated;

-- Grant sequence permissions
GRANT USAGE, SELECT ON SEQUENCE telegram_chats_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE telegram_messages_id_seq TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE telegram_user_aliases_id_seq TO authenticated;