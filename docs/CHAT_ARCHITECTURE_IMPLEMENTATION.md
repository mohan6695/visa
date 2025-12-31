# Chat Feature Architecture Implementation

## Overview

This document outlines the complete implementation plan for an economical chat feature using Supabase Realtime for group chat and pgvector for Q&A functionality, designed to scale to millions of users on a tight budget.

## Architecture Summary

### Core Components

1. **Supabase Realtime**: WebSocket-based real-time communication
2. **PostgreSQL with pgvector**: Database with semantic search capabilities
3. **Redis**: Caching layer for performance optimization
4. **AI Service**: Cost-effective AI answering with multiple provider support

### Technology Stack

- **Frontend**: Next.js with Supabase Realtime client
- **Backend**: FastAPI with Supabase integration
- **Database**: PostgreSQL with pgvector extension
- **Caching**: Redis for aggressive caching strategy
- **AI Providers**: Groq, OpenRouter, Together AI, or local Ollama

## Database Schema

### New Tables

#### `group_messages`
- Core table for chat messages
- Includes pgvector embeddings for semantic search
- Full-text search with TSVECTOR
- Optimized indexes for performance

#### `message_read_receipts`
- Tracks which messages users have read
- Enables unread message counting
- Supports read receipts functionality

#### `user_presence`
- Tracks user online status in groups
- Enables presence indicators
- Optimized for real-time updates

#### `group_message_likes`
- Message reaction system
- Supports engagement tracking
- Social features integration

### Migration Script

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create group messages table with all necessary fields
CREATE TABLE group_messages (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    content_html TEXT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    group_id INTEGER NOT NULL REFERENCES communities(id),
    message_type VARCHAR(20) DEFAULT 'text',
    status VARCHAR(20) DEFAULT 'published',
    like_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    search_vector TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    content_embedding VECTOR(1536)
);

-- Create indexes for performance
CREATE INDEX idx_group_messages_group_id ON group_messages(group_id);
CREATE INDEX idx_group_messages_content_embedding ON group_messages USING ivfflat (content_embedding vector_cosine_ops) WITH (lists = 100);
```

## Service Layer Implementation

### 1. Supabase Service (`backend/src/services/supabase_service.py`)

**Key Features:**
- Real-time channel subscriptions
- Message broadcasting
- Presence tracking
- Read receipts management

**API Methods:**
- `subscribe_to_group()`: Subscribe to group messages
- `send_group_message()`: Send messages via Supabase
- `get_group_history()`: Retrieve message history
- `mark_message_read()`: Track read messages
- `get_online_users()`: Get online user list

### 2. Embedding Service (`backend/src/services/embedding_service.py`)

**Key Features:**
- Semantic search across content
- Embedding generation and management
- Hybrid search (semantic + keyword)
- Batch processing for existing content

**API Methods:**
- `semantic_search_posts()`: Search posts by similarity
- `semantic_search_comments()`: Search comments by similarity
- `semantic_search_messages()`: Search messages by similarity
- `hybrid_search()`: Combined semantic and keyword search

### 3. AI Service (`backend/src/services/ai_service.py`)

**Key Features:**
- Aggressive caching strategy
- Multiple AI provider support
- Cost optimization
- Thread summarization

**API Methods:**
- `answer_question()`: RAG-based Q&A
- `search_relevant_content()`: Find relevant context
- `generate_context()`: Prepare AI model input
- `summarize_thread()`: Summarize long conversations

## Frontend Integration

### Real-time Chat Component

```typescript
// Group chat hook for real-time functionality
const useGroupChat = (groupId: number) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isOnline, setIsOnline] = useState<boolean>(false);
  
  useEffect(() => {
    // Subscribe to Supabase Realtime channel
    const channel = supabase
      .channel(`group:${groupId}`)
      .on('postgres_changes', {
        event: 'INSERT',
        schema: 'public',
        table: 'group_messages',
        filter: `group_id=eq.${groupId}`
      }, (payload) => {
        setMessages(prev => [...prev, payload.new]);
      })
      .subscribe();
    
    return () => supabase.removeChannel(channel);
  }, [groupId]);
};
```

### Q&A Component

```typescript
// AI-powered Q&A component
const useQAndA = (groupId: number) => {
  const [answer, setAnswer] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  
  const askQuestion = async (question: string) => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/ai/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, groupId })
      });
      const data = await response.json();
      setAnswer(data.answer);
    } catch (error) {
      console.error('Failed to get answer:', error);
    } finally {
      setIsLoading(false);
    }
  };
};
```

## Cost Optimization Strategies

### 1. Aggressive Caching

**Cache Strategy:**
- Cache answers by normalized question + group_id
- TTL: 1-6 hours based on content freshness
- Expected cache hit rate: 70-90%

**Redis Cache Keys:**
```
qa:{hash(question)}:{group_id} = {answer_data}
summary:{thread_id}:{group_id} = {summary_data}
```

### 2. Multi-Tier AI Access

**Free Tier:**
- Cached answers only
- Limited context
- Basic summarization

**Premium Tier:**
- Real-time AI with full context
- Richer responses
- Advanced features

### 3. Context Optimization

**Token Reduction:**
- Use summaries instead of full context
- Limit context to top N relevant items
- Smart content filtering

## Deployment Strategy

### Supabase Plan Selection

**Phase 1 (Startup):**
- **Starter Plan**: $25/month
- 25M rows, 500GB storage
- Suitable for initial user base

**Phase 2 (Growth):**
- **Pro Plan**: $50/month
- 100M rows, 2TB storage
- Enhanced performance features

**Phase 3 (Scale):**
- **Enterprise**: Custom pricing
- Millions of users
- Dedicated support

### Infrastructure Requirements

**Backend Services:**
- FastAPI application servers
- Redis cluster for caching
- Load balancer for traffic distribution

**Database:**
- PostgreSQL with pgvector extension
- Read replicas for query scaling
- Regular maintenance and optimization

## Monitoring and Maintenance

### Key Metrics

**Real-time Metrics:**
- Active WebSocket connections
- Message throughput (messages/second)
- AI API usage and costs
- Cache hit rates

**Performance Metrics:**
- Database query performance
- Supabase API response times
- Frontend load times
- Error rates

### Maintenance Tasks

**Daily:**
- Monitor cache hit rates
- Check AI API costs
- Review error logs

**Weekly:**
- Update embeddings for new content
- Optimize database indexes
- Review Supabase usage

**Monthly:**
- Analyze cost optimization opportunities
- Review scaling requirements
- Update AI model configurations

## Security Considerations

### Row Level Security (RLS)

All chat tables use RLS policies:
- Users can only access messages in groups they belong to
- Read receipts are user-specific
- Presence tracking respects privacy settings

### Data Privacy

- Message content is encrypted in transit
- Embeddings are stored securely
- Cache keys don't expose sensitive information

## Implementation Timeline

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Database schema migration
- [ ] Supabase service implementation
- [ ] Basic real-time chat functionality

### Phase 2: AI Integration (Week 3-4)
- [ ] Embedding service implementation
- [ ] AI service with caching
- [ ] Q&A functionality

### Phase 3: Frontend Integration (Week 5-6)
- [ ] Real-time chat UI components
- [ ] Q&A interface
- [ ] Presence indicators

### Phase 4: Optimization (Week 7-8)
- [ ] Performance optimization
- [ ] Cost monitoring setup
- [ ] Scaling preparation

## Success Metrics

### User Experience
- Chat message delivery time: < 1 second
- Q&A response time: < 5 seconds
- Cache hit rate: > 80%

### Cost Efficiency
- AI API costs: < $0.01 per active user/month
- Infrastructure costs: < $100/month for 10k users
- Scaling cost per million users: < $1000/month

### Performance
- Concurrent WebSocket connections: 100k+
- Database query response time: < 100ms
- Cache response time: < 10ms

This architecture provides a solid foundation for implementing economical chat features that can scale to millions of users while maintaining high performance and low costs.