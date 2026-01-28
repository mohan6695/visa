-- Create posts table
CREATE TABLE IF NOT EXISTS posts (
  id BIGSERIAL PRIMARY KEY,
  group_id BIGINT NOT NULL REFERENCES groups(id),
  author_id UUID NOT NULL REFERENCES auth.users(id),
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  tags TEXT[] DEFAULT '{}',
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

-- Create chat_logs table for tracking RAG queries
CREATE TABLE IF NOT EXISTS chat_logs (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id),
  group_id BIGINT NOT NULL REFERENCES groups(id),
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  used_post_ids BIGINT[] DEFAULT '{}',
  conversation_id TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX idx_posts_group_id ON posts(group_id);
CREATE INDEX idx_posts_updated_at ON posts(updated_at);
CREATE INDEX idx_chat_logs_user_id ON chat_logs(user_id);
CREATE INDEX idx_chat_logs_group_id ON chat_logs(group_id);
CREATE INDEX idx_chat_logs_conversation_id ON chat_logs(conversation_id);

-- Enable RLS (Row Level Security)
ALTER TABLE chat_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own chat logs"
  ON chat_logs FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Service can insert chat logs"
  ON chat_logs FOR INSERT
  WITH CHECK (true);
