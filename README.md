# Visa Community Platform - Astro Edition

> **Migrated from Next.js to Astro** with Cloudflare Pages/Workers/R2 compatibility

A modern visa information and community platform built with Astro, optimized for edge deployment on Cloudflare infrastructure.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10+ (for backend)
- Docker and Docker Compose (optional)

### Development

```bash
# Install dependencies
npm install

# Start Astro dev server
npm run dev

# Start backend (in another terminal)
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload
```

Visit **http://localhost:4321** to see the application.

### Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## 🏗️ Architecture

### Frontend (Astro)
- **Framework**: Astro v5 with React islands
- **Styling**: Tailwind CSS
- **Deployment**: Cloudflare Pages
- **Adapter**: `@astrojs/cloudflare` (server-side rendering)

### Backend (FastAPI)
- **Framework**: FastAPI with Supabase
- **Database**: PostgreSQL with pgvector
- **Caching**: Redis
- **AI Providers**: Groq, OpenRouter (Ollama removed)

### Infrastructure
- **Hosting**: Cloudflare Pages (frontend) + Workers (API)
- **Storage**: Cloudflare R2
- **Cache**: Cloudflare KV
- **Database**: Supabase PostgreSQL

## 📦 Tech Stack

### Core Dependencies
- **astro** - Modern static site generator
- **@astrojs/react** - React integration for Astro
- **@astrojs/tailwind** - Tailwind CSS integration
- **@astrojs/cloudflare** - Cloudflare Pages adapter
- **react** & **react-dom** - For interactive components
- **@supabase/supabase-js** - Supabase client
- **@tanstack/react-query** - Data fetching and caching
- **zustand** - State management
- **wrangler** - Cloudflare CLI for deployment

### Backend
- **FastAPI** - Modern Python web framework
- **Supabase** - PostgreSQL database
- **Redis** - High-performance caching
- **pgvector** - Semantic search capabilities

## 🌐 Deployment

### Cloudflare Pages

1crypto **Deploy to Cloudflare:**
   ```bash
   npm run deploy
   ```

2. **Configure environment variables** in Cloudflare dashboard:
   ```
   SUPABASE_URL=your-supabase-url
   SUPABASE_KEY=your-supabase-key
   GROQ_API_KEY=your-groq-api-key
   OPENROUTER_API_KEY=your-openrouter-api-key
   R2_ACCESS_KEY_ID=your-r2-access-key
   R2_SECRET_ACCESS_KEY=your-r2-secret-key
   ```

3. **Create R2 bucket** named `visa-platform-storage`

4. **Create KV namespace** for caching and update `wrangler.toml`

### Backend Deployment

```bash
# Using Docker Compose
docker-compose up -d

# Or deploy to your preferred platform (Render, Railway, etc.)
```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# AI Provider (groq or openrouter)
AI_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key
OPENROUTER_API_KEY=your-openrouter-api-key

# Supabase
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key

# Cloudflare
CLOUDFLARE_ACCOUNT_ID=your-account-id
R2_BUCKET_NAME=visa-platform-storage
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key

# Redis
REDIS_URL=redis://localhost:6379
```

### Wrangler Configuration

Edit `wrangler.toml` to customize:
- R2 bucket bindings
- KV namespace bindings  
- Build settings
- Environment variables

## 📁 Project Structure

```
visa-1/
├── src/
│   ├── components/        # Astro & React components
│   │   └── ads/          # Ad components (AdBanner, AdSidebar, etc.)
│   ├── layouts/          # Page layouts
│   ├── pages/            # Astro pages (file-based routing)
│   ├── styles/           # Global styles
│   └── lib/              # Utilities and helpers
├── backend/              # FastAPI backend
│   ├── src/
│   │   ├── api/         # API endpoints
│   │   ├── services/    # Business logic (AI, embeddings, etc.)
│   │   └── core/        # Configuration
│   └── tests/           # Backend tests
├── public/              # Static assets
├── dist/                # Build output (for deployment)
├── astro.config.mjs     # Astro configuration
├── wrangler.toml        # Cloudflare configuration
├── tailwind.config.mjs  # Tailwind configuration
└── docker-compose.yml   # Docker services
```

## 🤖 AI Integration

The platform uses cloud-based AI providers for Q&A functionality:

### Supported Providers

1. **Groq** (Recommended)
   - Fast inference with LLaMA models
   - Cost-effective pricing
   - Set `AI_PROVIDER=groq`

2. **OpenRouter**
   - Access to multiple AI models
   - Flexible model selection
   - Set `AI_PROVIDER=openrouter`

**Note:** Ollama (local AI) has been removed in this version. All AI processing now uses cloud providers.

### Caching Strategy

- **Redis caching** for Q&A responses (1-6 hour TTL)
- **70-90% cache hit rate** for common questions
- **Significant cost reduction** through aggressive caching

## 📦 R2 to Supabase Pipeline

A Cloudflare Workers-based pipeline to process and migrate data from R2 storage to Supabase:

### Features

- **Batch Processing**: Handles large files by splitting into smaller batches (under 128KB limit)
- **Queue System**: Uses Cloudflare Queues for reliable processing
- **KV Tracking**: Keeps track of processed files using Cloudflare KV
- **Error Handling**: Retries failed operations and provides detailed logging

### Deploy Pipeline Worker

```bash
# Set secrets
wrangler secret put SUPABASE_SERVICE_ROLE_KEY

# Deploy
wrangler deploy
```

### Usage

1. **Health Check**: `GET /health` - Verify worker is running
2. **List R2 Objects**: `GET /list` - List objects in the R2 bucket
3. **Process Files**: `GET /run` - Process all unprocessed `new_posts.json` files
4. **Automated Processing**: Runs every 6 hours via cron trigger

### Configuration

- `MAX_BATCH_SIZE`: 100KB per batch (configurable in `src/index.js`)
- `CRON_SCHEDULE`: `0 */6 * * *` (every 6 hours)
- **Bucket**: `data-pipeline` (configured in `wrangler.toml`)

## 🔬 Cloudflare Workers AI Clustering

Automatic post clustering using Cloudflare's AI infrastructure:

### How It Works

1. **Embeddings**: Cloudflare Workers AI (BGE model, 768-dim)
2. **Clustering**: Llama 3.2 analyzes posts and groups by topic
3. **Storage**: Supabase PostgreSQL with pgvector
4. **Automation**: Cron triggers every 15 minutes

### Deploy Clustering Worker

```bash
# Set secrets
wrangler secret put SUPABASE_URL
wrangler secret put SUPABASE_SERVICE_ROLE_KEY  
wrangler secret put CF_ACCOUNT_ID
wrangler secret put CF_API_TOKEN

# Deploy
wrangler deploy --config wrangler.clustering.toml
```

See [Cloudflare Clustering Deployment Guide](docs/CLOUDFLARE_CLUSTERING_DEPLOYMENT.md) for details.

### Benefits

- ✅ **No Ollama needed** - fully cloud-based
- ✅ **Automatic** - runs on schedule
- ✅ **Cost-effective** - ~$1-5/month for 10K posts
- ✅ **Scalable** - leverages Cloudflare's edge network

## 📊 Features

- ✅ **Visa Information** - Comprehensive visa requirements and country data
- ✅ **Real-time Chat** - Community discussions with Supabase Realtime
- ✅ **AI-Powered Q&A** - Intelligent answers using RAG (Retrieval-Augmented Generation)
- ✅ **Semantic Search** - pgvector-powered content search
- ✅ **Ad Monetization** - AdSense integration with 50%+ ad coverage
- ✅ **Subscription Management** - User tier management
- ✅ **Edge Deployment** - Optimized for Cloudflare's global network
- ✅ **Server-Side Rendering** - Fast initial page loads

## 🔐 Security

- **Row Level Security (RLS)** on all database tables
- **JWT authentication** via Supabase Auth
- **Security headers** configured (CSP, X-Frame-Options, etc.)
- **HTTPS only** in production
- **API rate limiting** (Redis-based)

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Build Verification
```bash
npm run build
```

## 📚 Documentation

- [Implementation Plan](/.gemini/antigravity/brain/8be1c08d-2619-4d90-b841-d19911febfd0/implementation_plan.md) - Migration strategy
- [Walkthrough](/.gemini/antigravity/brain/8be1c08d-2619-4d90-b841-d19911febfd0/walkthrough.md) - Detailed migration notes
- [Task Breakdown](/.gemini/antigravity/brain/8be1c08d-2619-4d90-b841-d19911febfd0/task.md) - Project tasks and progress

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Astro framework** for modern static site generation
- **Cloudflare** for edge infrastructure
- **Supabase** for real-time database capabilities
- **Groq** & **OpenRouter** for AI processing
- **Tailwind CSS** for styling

---

**Migration Notes:** This project was migrated from Next.js to Astro in January 2026. All Ollama dependencies were removed in favor of cloud-based AI providers. The application is now optimized for Cloudflare Pages/Workers/R2 deployment.