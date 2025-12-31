# Backend API - Visa Community Platform

This is the backend API for the Visa Community Platform, built with FastAPI and designed to support chat functionality, AI-powered Q&A, and Supabase integration.

## 🚀 Features

- **Real-time Chat**: WebSocket-based chat with Supabase Realtime
- **AI-Powered Q&A**: Semantic search and RAG (Retrieval-Augmented Generation)
- **Supabase Integration**: Seamless integration with Supabase for storage and real-time features
- **Redis Caching**: Aggressive caching for performance optimization
- **PostgreSQL with pgvector**: Vector embeddings for semantic search
- **Authentication**: JWT-based authentication with role-based access control
- **Monitoring**: Comprehensive health checks and metrics

## 🛠️ Tech Stack

- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **Supabase**: Real-time database and storage
- **Redis**: Caching and real-time features
- **pgvector**: Vector embeddings for semantic search
- **Docker**: Containerization
- **PostgreSQL**: Primary database

## 📦 Installation

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- PostgreSQL (for development)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd visa-community-platform/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations**
   ```bash
   # Connect to PostgreSQL and run migrations
   psql -U postgres -d visa_community -f ../supabase_migrations/001_chat_schema.sql
   ```

6. **Start the development server**
   ```bash
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Docker

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **View logs**
   ```bash
   docker-compose logs -f backend
   ```

## 🔧 Configuration

### Environment Variables

Key configuration options:

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

# Security
SECRET_KEY=your-secret-key
```

### Supabase Setup

1. **Create Supabase project**
2. **Enable pgvector extension**
3. **Set up Row Level Security (RLS)**
4. **Configure Realtime subscriptions**

## 📚 API Endpoints

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

### Supabase Posts Endpoints

- `POST /api/v1/supabase/posts` - Get posts from Supabase
- `GET /api/v1/supabase/posts/{post_id}` - Get post by ID
- `POST /api/v1/supabase/posts/similar` - Get similar posts
- `POST /api/v1/supabase/posts/vote` - Vote on post
- `GET /api/v1/supabase/posts/stats` - Get post statistics
- `GET /api/v1/supabase/posts/categories` - Get post categories

### Health Check Endpoints

- `GET /health` - Basic health check
- `GET /api/v1/health` - Detailed health check
- `GET /api/v1/health/cache` - Cache-specific health
- `GET /api/v1/health/ai` - AI service health
- `GET /api/v1/health/chat` - Chat service health

## 🗄️ Database Schema

### Core Tables

- **users**: User accounts and profiles
- **communities**: Community groups by country/topic
- **posts**: Community discussion posts
- **comments**: Post comments and chat messages
- **group_messages**: Dedicated chat messages
- **message_read_receipts**: Read receipts tracking
- **user_presence**: Online user tracking
- **group_message_likes**: Message reactions

### Supabase Tables

- **recent_h1b_posts**: Posts from Supabase bucket
- **comments**: Post comments
- **post_votes**: Post voting system

## 🔐 Authentication

The API uses JWT-based authentication:

1. **Login**: `POST /api/v1/auth/login`
2. **Register**: `POST /api/v1/auth/register`
3. **Token**: Include `Authorization: Bearer <token>` in requests

## 🤖 AI Integration

### Supported Providers

1. **Groq**: High-throughput, low-cost models
2. **OpenRouter**: Access to multiple AI models
3. **Ollama**: Local AI models

### Caching Strategy

- **Cache TTL**: 1-6 hours based on content freshness
- **Hit Rate**: Expected 70-90% for repeated questions
- **Cost Reduction**: 70-90% compared to uncached AI usage

## 📊 Monitoring

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

## 🚀 Deployment

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

## 🧪 Testing

### Unit Tests

```bash
pytest tests/
```

### Integration Tests

```bash
pytest tests/integration/
```

### Test Configuration

Set up test environment:
```bash
cp .env.test.example .env.test
# Edit .env.test with test configuration
```

## 🐛 Debugging

### Common Issues

1. **Database Connection**: Check `DATABASE_URL` configuration
2. **Redis Connection**: Verify `REDIS_URL` and Redis server status
3. **Supabase Connection**: Ensure Supabase URL and keys are correct
4. **AI Provider**: Check API keys and provider availability

### Logs

View application logs:
```bash
docker-compose logs -f backend
```

### Health Checks

Check service health:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health
```

## 📝 Development

### Code Style

- Use `black` for code formatting
- Use `flake8` for linting
- Use `mypy` for type checking

```bash
black src/
flake8 src/
mypy src/
```

### Database Migrations

Use Alembic for database migrations:
```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Adding New Endpoints

1. Create endpoint in `src/api/v1/endpoints/`
2. Add to `src/api/v1/endpoints/__init__.py`
3. Update OpenAPI documentation

## 📞 Support

For support and questions:
- Create a GitHub issue
- Join our Discord community
- Email us at support@visa-community.com

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.