## Tech Stack Comparison – 500K vs 2M Users

| Component | 500K Users | 2M Users |
|-----------|-----------|----------|
| **Frontend** | Next.js + React Query + Tailwind on Vercel Pro (or Render Static); global CDN, preview deployments. | Next.js + React Query + Tailwind on Vercel Pro/Enterprise (or higher-tier Render Static); more bandwidth and concurrent builds. |
| **API Gateway** | FastAPI (single app, no separate gateway); 2–3 small Render web services handling REST/WS, auth, basic rate limiting. | FastAPI behind Render HTTP with optional Kong; 4–8 Render web services, better routing, auth, and centralized rate limiting/versioning. |
| **Application** | FastAPI + Pydantic + SQLAlchemy; 2–4 Render services for core logic (posts, comments, visas, groups). | FastAPI + Pydantic + SQLAlchemy; 6–12 Render services, separated by concern (read-heavy vs write-heavy, AI endpoints, admin). |
| **Chat Bot** | Local LLM (e.g., Llama 3 8B) + pgvector; 1–2 medium Render instances (CPU or small GPU) for RAG Q&A and summaries. | Local LLMs (Llama 3 8B / larger variants) + pgvector; 2–4 larger Render instances (CPU or GPU), horizontal scaling and answer caching. |
| **Database (Primary)** | Supabase Postgres Pro; disk scaled to ~50–100 GB; partition by country_id; pgvector enabled for embeddings. | Supabase Postgres Pro / early Enterprise; disk ~100–200 GB; partition by country_id and/or visa_type; more RAM/CPU for heavier load. |
| **Database (Read)** | 1–2 Supabase read replicas for feeds and heavy reads. | 2–4 Supabase read replicas in key regions to reduce latency and offload primary. |
| **Cache** | Single small Redis instance/cluster (Upstash or Render) for hot feeds, sessions, and rate limits; aggressive TTLs. | Small Redis Cluster (2–3 nodes) for feeds, sessions, rate limits, AI response cache; aim for high cache hit rate for hot countries. |
| **Search** | One small Meilisearch instance on Render for full-text search; filter by country/visa type. | 2–3 Meilisearch instances on Render; shard by country or run a beefier node for higher QPS. |
| **Realtime** | Supabase Realtime enabled on Pro; channels per community for live threads and notifications. | Supabase Realtime on Pro/Enterprise; tuned channels and event throttling for more active communities. |
| **Queue / Workers** | BullMQ or Celery/RQ + Redis; 1 small Render worker + cron for embeddings, summaries, indexing. | BullMQ or Celery/RQ + Redis; 2–3 dedicated Render workers + cron; separate queues for AI-heavy vs light jobs. |
| **Storage** | Supabase Storage (~100 GB) for images/docs; DB only holds metadata. | Supabase Storage scaled up plus optional R2/S3; lifecycle rules for old media and cold storage. |
| **Monitoring** | Prometheus + Grafana Cloud or Render metrics; free/low tier; alerts on P95 latency and error spikes. | Prometheus + Grafana Cloud/APM; possibly paid tier; dashboards for API latency, DB CPU/IO, cache hit rate, AI error rates. |
| **CI/CD** | GitHub Actions (free); dev/prod workflows; tests + basic checks before deploy. | GitHub Actions with stricter checks (required reviews, migrations), optional blue/green or canary deploy strategies
