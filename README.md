# Visa Platform

A modern visa information platform built with Next.js, TypeScript, and Cloudflare Workers.

## Features

- **Post management**: Create, read, update, and delete visa-related posts
- **Clustering**: AI-powered post clustering using Cloudflare Workers AI
- **Analytics**: Platform analytics using Supabase and Cloudflare Workers
- **Search**: Semantic search using pgvector and Cloudflare Workers AI
- **Storage**: R2 bucket integration for content storage
- **Authentication**: Supabase authentication
- **AI Integration**: Cloudflare Workers AI for embeddings and clustering

## Tech Stack

- **Frontend**: Next.js 16, TypeScript, Tailwind CSS
- **Backend**: Cloudflare Workers, Supabase
- **Database**: Supabase PostgreSQL (with pgvector extension)
- **Storage**: Cloudflare R2
- **AI**: Cloudflare Workers AI (@cf/baai/bge-small-en-v1.5, @cf/meta/llama-3.2-1b-instruct)
- **Search**: pgvector (PostgreSQL extension)

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Cloudflare account
- Supabase account

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/mohan6695/visa.git
   cd visa-1
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env.local
   ```
   Fill in the values in `.env.local` with your Cloudflare and Supabase credentials.

4. **Start the development server**:
   ```bash
   npm run dev
   ```

### Environment Variables

- **SUPABASE_URL**: Your Supabase project URL
- **SUPABASE_SERVICE_ROLE_KEY**: Your Supabase service role key
- **CF_ACCOUNT_ID**: Your Cloudflare account ID
- **CF_API_TOKEN**: Your Cloudflare API token
- **MEILISEARCH_HOST**: Your MeiliSearch host (optional)
- **MEILISEARCH_API_KEY**: Your MeiliSearch API key (optional)

## Project Structure

```
visa-1/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── cache/
│   │   │   ├── clusters/
│   │   │   ├── posts/
│   │   │   ├── queue/
│   │   │   ├── r2-delete/
│   │   │   ├── r2-fetch/
│   │   │   ├── r2-upload/
│   │   │   ├── search/
│   │   │   └── v1/
│   │   ├── post/
│   │   └── usa-posts/
│   ├── components/
│   │   ├── LandingPage.tsx
│   │   ├── USAPostsPage.tsx
│   │   └── ads/
│   ├── lib/
│   │   ├── cluster-service-v2.ts
│   │   ├── cluster-service.ts
│   │   ├── r2-client.ts
│   │   ├── supabase.ts
│   │   └── types.ts
│   └── data/
├── public/
├── workers/
│   ├── clustering.ts
│   ├── mcp_server.ts
│   └── queue-handler.ts
├── .gitignore
├── astro-scripts-guide
├── astro.config.mjs
├── astro-to-nextjs-migration-check.md
├── complete-implementation.md
├── docker-compose.yml
├── index.html
├── next-env.d.ts
├── next.config.js
├── package-lock.json
├── package.json
├── README.md
├── render.yaml
├── tailwind.config.mjs
├── tsconfig.json
├── wrangler.clustering.toml
├── wrangler.mcp.toml
├── wrangler.temp.toml
├── wrangler.toml
└── wrangler.worker.toml
```

## API Routes

### Posts

- `GET /api/posts`: Get all posts
- `POST /api/posts`: Create a new post
- `GET /api/posts/:id`: Get a single post
- `PUT /api/posts/:id`: Update a post
- `DELETE /api/posts/:id`: Delete a post

### Clusters

- `GET /api/clusters`: Get all clusters
- `POST /api/queue/cluster`: Queue a post for clustering

### R2 Storage

- `POST /api/r2-upload`: Upload a file to R2
- `GET /api/r2-fetch/:key`: Fetch a file from R2
- `DELETE /api/r2-delete/:key`: Delete a file from R2

### Search

- `GET /api/search/:query`: Search for posts

### Cache

- `GET /api/cache/get/:key`: Get a value from the cache

## Workers

### Clustering Worker

The clustering worker runs on a cron schedule to automatically cluster posts. It uses Cloudflare Workers AI to generate embeddings and cluster posts based on their content.

### MCP Server

The MCP server exposes tools for semantic search, analytics, and clustering. It implements the Model Context Protocol (MCP) over HTTP/SSE.

### Queue Handler

The queue handler processes messages from Cloudflare Queues to handle post clustering and other tasks.

## Deployment

### Cloudflare Pages

1. **Build the app**:
   ```bash
   npm run build
   ```

2. **Deploy to Cloudflare Pages**:
   ```bash
   npm run deploy
   ```

### Cloudflare Workers

1. **Deploy the clustering worker**:
   ```bash
   wrangler deploy --config wrangler.clustering.toml
   ```

2. **Deploy the MCP server**:
   ```bash
   wrangler deploy --config wrangler.mcp.toml
   ```

3. **Deploy the queue handler**:
   ```bash
   wrangler deploy --config wrangler.worker.toml
   ```

## Contributing

1. **Fork the repository**:
   ```bash
   git fork https://github.com/mohan6695/visa.git
   ```

2. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature
   ```

3. **Make changes**:
   ```bash
   # Make your changes
   git status
   git add .
   git commit -m "Add your commit message"
   ```

4. **Push changes**:
   ```bash
   git push origin feature/your-feature
   ```

5. **Create a pull request**:
   Go to the repository on GitHub and create a pull request.

## License

This project is licensed under the MIT License.
