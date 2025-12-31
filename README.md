# Visa Community Platform - Chat Feature Implementation

This document provides a comprehensive guide for the implemented chat feature using Supabase Realtime and pgvector for Q&A functionality.

## 🏗️ Architecture Overview

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

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js (for frontend development)
- Python 3.10+ (for backend development)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd visa-community-platform
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**
   ```bash
   # Connect to PostgreSQL and run the migration
   docker-compose exec postgres psql -U postgres -d visa_community -f supabase_migrations/001_chat_schema.sql
   ```

### Development Setup

#### Backend Development

1. **Install Python dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run the backend server**
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Frontend Development

1. **Install Node.js dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Run the frontend development server**
   ```bash
   npm run dev
   ```

## 📊 Database Schema

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

The migration script (`supabase_migrations/001_chat_schema.sql`) includes:
- Table creation with proper constraints
- Index creation for performance
- Row Level Security (RLS) policies
- Triggers for automatic updates
- Permission grants

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/visa_community

# Redis
REDIS_URL=redis://localhost:6379

# Supabase
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-anon-key

# AI Providers
AI_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key
OPENROUTER_API_KEY=your-openrouter-api-key
OLLAMA_URL=http://localhost:11434
```

### Supabase Setup

1. **Create a Supabase project**
2. **Enable pgvector extension**
3. **Set up Row Level Security (RLS)**
4. **Configure Realtime subscriptions**

### Redis Setup

Redis is used for:
- Aggressive caching of AI answers (70-90% cost reduction)
- User presence tracking
- Rate limiting
- Session management

## 🤖 AI Integration

### Supported Providers

1. **Groq**: High-throughput, low-cost models
2. **OpenRouter**: Access to multiple AI models
3. **Ollama**: Local AI models
4. **Together AI**: Alternative cloud provider

### Caching Strategy

- **Cache TTL**: 1-6 hours based on content freshness
- **Cache Keys**: Hash-based for question normalization
- **Hit Rate**: Expected 70-90% for repeated questions
- **Cost Reduction**: 70-90% compared to uncached AI usage

### Multi-Tier Access

- **Free Tier**: Cached answers only
- **Premium Tier**: Real-time AI with full context
- **Context Optimization**: Summaries + recent messages

## 🌐 API Endpoints

### Chat Endpoints

- `GET /api/v1/chat/history` - Get chat history
- `POST /api/v1/chat/send` - Send chat message
- `GET /api/v1/chat/members` - Get community members
- `GET /api/v1/chat/online-status` - Get online users
- `POST /api/v1/chat/mark-read` - Mark message as read
- `GET /api/v1/chat/unread-count` - Get unread count
- `GET /api/v1/chat/search` - Search chat messages
- `GET /api/v1/chat/activity` - Get recent activity

### AI Endpoints

- `POST /api/v1/ai/answer` - Answer question with RAG
- `GET /api/v1/ai/search` - Semantic search
- `POST /api/v1/ai/summarize` - Thread summarization
- `GET /api/v1/ai/cost-estimate` - Cost estimation
- `GET /api/v1/ai/cache-status` - Check cache status
- `GET /api/v1/ai/providers` - Get available providers

### Health Check Endpoints

- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/detailed` - Detailed health metrics
- `GET /api/v1/health/cache` - Cache-specific health
- `GET /api/v1/health/ai` - AI service health
- `GET /api/v1/health/chat` - Chat service health

## 🎨 Frontend Components

### GroupChat Component

Real-time chat interface with:
- WebSocket connections via Supabase Realtime
- Message history loading
- Typing indicators
- Presence tracking
- Read receipts
- Message reactions

### QAComponent

AI-powered Q&A interface with:
- Question input and submission
- Answer display with source attribution
- Search functionality
- Question history
- Cache status indicators

## 📈 Monitoring and Observability

### Health Checks

Comprehensive health check endpoints provide:
- Service status (database, Redis, Supabase)
- Performance metrics
- Cache hit rates
- AI provider status
- Feature availability

### Metrics

Key metrics to monitor:
- Real-time connection count
- Message throughput (messages/second)
- AI API usage and costs
- Cache hit rates
- Database query performance

### Logging

Structured logging with:
- Request/response logging
- Error tracking
- Performance metrics
- Security events

## 🚀 Deployment

### Docker Compose

The provided `docker-compose.yml` includes:
- Backend API service
- Frontend application
- PostgreSQL database
- Redis cache
- Ollama for local AI (optional)
- Nginx reverse proxy (production profile)
- Prometheus and Grafana (monitoring profile)

### Production Deployment

1. **Use production profiles**
   ```bash
   docker-compose --profile production up -d
   ```

2. **Configure SSL/TLS**
   - Update nginx configuration
   - Add SSL certificates
   - Configure domain names

3. **Set up monitoring**
   ```bash
   docker-compose --profile monitoring up -d
   ```

### Scaling

#### Horizontal Scaling

- **Backend**: Multiple FastAPI instances behind load balancer
- **Database**: Read replicas for query scaling
- **Redis**: Cluster setup for distributed caching
- **Frontend**: CDN for static assets

#### Supabase Scaling

- **Starter Plan**: $25/month (25M rows, 500GB storage)
- **Pro Plan**: $50/month (100M rows, 2TB storage)
- **Enterprise**: Custom pricing for millions of users

## 🔒 Security

### Row Level Security (RLS)

All chat tables use RLS policies:
- Users can only access messages in groups they belong to
- Read receipts are user-specific
- Presence tracking respects privacy settings

### Authentication

- JWT-based authentication
- Supabase Auth integration
- Role-based access control
- Secure password hashing

### Data Privacy

- Message content is encrypted in transit
- Embeddings are stored securely
- Cache keys don't expose sensitive information

## 🧪 Testing

### Unit Tests

```bash
cd backend
pytest tests/
```

### Integration Tests

```bash
cd backend
pytest tests/integration/
```

### Frontend Tests

```bash
cd frontend
npm test
```

## 📚 Documentation

- [CHAT_ARCHITECTURE_IMPLEMENTATION.md](CHAT_ARCHITECTURE_IMPLEMENTATION.md) - Complete implementation guide
- [API Documentation](docs/api.md) - Detailed API specifications
- [Deployment Guide](docs/deployment.md) - Production deployment steps

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Submit a pull request

## 🐛 Bug Reports

Please use the GitHub issue tracker to report bugs with:
- Detailed description of the issue
- Steps to reproduce
- Expected vs. actual behavior
- Environment information

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Supabase for real-time database capabilities
- pgvector for semantic search functionality
- Redis for high-performance caching
- FastAPI for modern Python web framework
- Next.js for React-based frontend framework

## 📞 Support

For support and questions:
- Create a GitHub issue
- Join our Discord community
- Email us at support@visa-community.com