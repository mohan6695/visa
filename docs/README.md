# RAG Chatbot - Quick Start

## 📥 Files Downloaded

You have **10 production-ready files** ready to paste into Cursor:

### Worker Files (Backend)
1. **wrangler.toml** - Cloudflare Worker configuration
2. **package-worker.json** - Rename to package.json
3. **src-index.ts** - Rename to src/index.ts (main handler)
4. **src-ask.ts** - Rename to src/ask.ts (RAG query logic)
5. **src-ingestion.ts** - Rename to src/ingestion.ts (scheduled ingestion)

### Frontend Files (UI)
6. **api-chat-route.ts** - Rename to app/api/chat/route.ts
7. **ChatbotUI.tsx** - React component
8. **ChatbotUI.module.css** - Styling

### Database & Config
9. **supabase_schema.sql** - Copy-paste into Supabase SQL editor
10. **env.example** - Rename to .env.local and fill in values
11. **SETUP_GUIDE.md** - Complete setup instructions

---

## 🚀 5-Minute Quickstart

### Step 1: Create Worker Project
```bash
mkdir rag-chatbot && cd rag-chatbot/worker
npm init -y
# Paste wrangler.toml content
# Paste package-worker.json → rename to package.json
mkdir -p src
# Paste src-index.ts → src/index.ts
# Paste src-ask.ts → src/ask.ts
# Paste src-ingestion.ts → src/ingestion.ts
```

### Step 2: Fill Environment Variables
Edit `wrangler.toml` with:
- `SUPABASE_URL` = your Supabase URL
- `SUPABASE_KEY` = your Supabase anon key
- `MEILISEARCH_URL` = your Meilisearch URL
- `MEILISEARCH_KEY` = your Meilisearch key
- `GROQ_API_KEY` = your Groq API key
- KV namespace ID from Cloudflare

### Step 3: Deploy Worker
```bash
npm install
npm run deploy
# Note the URL: https://rag-chatbot.your-domain.workers.dev
```

### Step 4: Setup Database
- Go to Supabase → SQL Editor
- Paste entire `supabase_schema.sql` and execute

### Step 5: Create Next.js Frontend
```bash
cd ../web
npx create-next-app@latest . --typescript
mkdir -p app/api/chat components
# Paste api-chat-route.ts → app/api/chat/route.ts
# Paste ChatbotUI.tsx → components/ChatbotUI.tsx
# Paste ChatbotUI.module.css → components/ChatbotUI.module.css
# Paste env.example → .env.local
```

### Step 6: Configure Frontend
Edit `.env.local`:
```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-key
NEXT_PUBLIC_WORKER_URL=https://rag-chatbot.your-domain.workers.dev
```

### Step 7: Run & Test
```bash
npm install
npm run dev
# Visit http://localhost:3000 and test the chatbot
```

---

## 📊 Architecture Summary

```
User Query (Next.js)
       ↓
Cloudflare Worker (edge, <50ms)
       ├→ Auth check
       ├→ Rate limiting (KV)
       ├→ Generate embedding (Workers AI)
       └→ Call Meilisearch
              ├→ Hybrid search (BM25 + vector)
              └→ Call Groq LLM
                     └→ Return answer + sources
       ↓
Response to user (<500ms total latency)
```

## 💰 Monthly Cost Breakdown

| Service | Cost | Details |
|---------|------|---------|
| **Groq API** | $0.70 | Llama 3.1 8B, ~10.5M tokens |
| **Cloudflare Workers** | $5 | Fixed subscription |
| **Cloudflare KV** | $0.50 | Rate limiting |
| **Meilisearch** | FREE | Self-hosted on Render |
| **Supabase** | $25 | Database + auth |
| **R2 Storage** | $2-5 | Post storage |
| **Total** | **$33-35/mo** | All-in for production |

---

## 🔑 API Keys You Need

1. **Groq** - https://console.groq.com/keys
2. **Supabase** - Project Settings → API
3. **Meilisearch** - Your instance dashboard
4. **Cloudflare** - Account ID + API Token

---

## ✅ Verification Checklist

After deployment:

```bash
# Check Worker health
curl https://rag-chatbot.your-domain.workers.dev/health

# Check Meilisearch index exists
curl http://your-meilisearch:7700/indexes/posts \
  -H "Authorization: Bearer YOUR_KEY"

# Test chatbot API
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"test","group_id":1}'
```

---

## 📝 What Happens Next

### Ingestion (Automatic, Daily at 2 AM UTC)
1. Fetch updated posts from Supabase
2. Chunk into 1500-char pieces
3. Generate embeddings (Cloudflare Workers AI)
4. Upsert to Meilisearch

### Query (Per User Request)
1. User asks question in UI
2. Send to Next.js API route
3. Worker calls Meilisearch for hybrid search
4. Worker calls Groq for LLM generation
5. Return answer + post sources
6. Log to Supabase for analytics

---

## 🎯 Next: Customization Ideas

- [ ] Add conversation history
- [ ] Implement feedback collection
- [ ] Add admin dashboard
- [ ] Monitor analytics
- [ ] A/B test chunking strategies
- [ ] Fine-tune prompt engineering
- [ ] Add semantic search reranking
- [ ] Multi-language support

---

## 📞 Support

Refer to **SETUP_GUIDE.md** for:
- Detailed setup instructions
- Troubleshooting
- File-by-file mapping
- Cost calculations
- Testing procedures

All files are production-ready. Just paste into Cursor and deploy!

**Happy building! 🚀**
