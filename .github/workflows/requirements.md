1. Product Overview
Build a visa Q&A and group chat web app with:
* Realtime group chats and StackOverflow-style posts.
* Premium subscription (Stripe) with extra features.
* Very low latency (<600ms P99) using Groq + Redis + Supabase.
* Strong security, privacy, anti-scraping, and analytics.
Primary region: India (Visakhapatnam), but app is global.

2. Core Tech Stack
2.1 Backend / DB
* Supabase Pro
    * Postgres with pgvector for semantic/hybrid search.
    * Realtime WebSockets for chat and presence.
    * Row-Level Security (RLS) for multi-tenant groups.
    * Edge Functions (Deno) + pg_cron for scheduled jobs.
* Groq (prod LLM)
    * Use Llama‑3.1‑70B or Qwen‑3‑32B on Groq for:
        * Chat answers / RAG reasoning.
        * Zero-shot tagging / light classification.
* Redis (Upstash)
    * Semantic / prompt cache for LLM responses and search results.
    * Aim for ≥80–85% cache hit rate.
* Render (or similar)
    * Host a FastAPI backend that:
        * Talks to Supabase, Redis, Groq.
        * Exposes HTTP endpoints for chat, search, premium checks, admin.
2.2 Frontend
* Next.js 16 (App Router)
    * React Server Components where possible (minimal hydration).
    * Next/Image for all images, lazy loaded.
    * Hosted on Cloudflare Pages for edge delivery and low TTFB.
* UI
    * Tailwind CSS, purged to keep CSS around 12 KB.
    * TanStack Virtual (or similar) for virtualized chat lists and media galleries.
2.3 Analytics / Payments / Ads
* Stripe
    * Subscriptions for premium tiers (₹/USD; monthly).
    *     * Webhook via Supabase Edge Function to set profiles.is_premium.
* PostHog (self-hosted)
    * Hosted on Render or similar, not sending data to third-party SaaS.
    * Auto-capture events, funnels, click tracking, heatmaps.
    * Store events in own DB (or keep in PostHog’s own DB; but no sending to big SaaS analytics if possible).
* Google Ads
    * Display ads to free users only.
    * Hide ads for premium users.

3. Domain Model & DB Schema (Supabase)
3.1 Auth / Profiles
* auth.users (Supabase default).
* profiles:
    * id (uuid, PK, references auth.users.id).
    * group_id (uuid, current default group).
    * is_premium (boolean, default false).
    * stripe_customer_id (text).
    * stripe_subscription_id (text).
    * daily_posts (int, default 0) – for free user quota.
3.2 Groups, Posts, Comments, Presence
* groups:
    * id (uuid, PK).
    * name (text).
    * user_count (int, default 0).
    * active_count (int, default 0).
    * created_at (timestamptz).
* posts (StackOverflow-style Q&A / long messages):
    * id (uuid, PK).
    * group_id (uuid → groups.id).
    * author_id (uuid → auth.users.id).
    * content (text).
    * embedding (vector, for pgvector).
    * upvotes (int, default 0).
    * downvotes (int, default 0).
    * score (generated: upvotes - downvotes).
    * watermark_hash (text, generated with md5(content+author+created_at)).
    * created_at (timestamptz default now).
* comments (nested, unlimited):
    * id (uuid, PK).
    * post_id (uuid → posts.id).
    * parent_id (uuid → comments.id, nullable).
    * author_id (uuid → auth.users.id).
    * content (text).
    * upvotes (int, default 0).
    * created_at (timestamptz default now).
* user_presence:
    * user_id (uuid, PK → auth.users.id).
    * group_id (uuid → groups.id).
    * last_seen (timestamptz).
    * is_active (boolean).
3.3 Tags & Auto Classification
* tags:
    * id (serial, PK).
    * name (text) – e.g. "H1B", "DS160", "interview", "lottery" (include Hindi variants).
    * embedding (vector).
    * category (text – e.g. visa_type, document, process).
* post_tags (many-to-many):
    * post_id (uuid → posts.id).
    * tag_id (int → tags.id).
    * PK: (post_id, tag_id).
3.4 External Posts Pipeline
* external_posts_staging:
    * id (uuid, PK).
    * content (text).
    * embedding (vector).
    * source (text).
    * cluster_id (uuid, for grouping).
    * created_at (timestamptz).
* external_posts_live:
    * cluster_id (uuid, PK).
    * best_content (text).
    * similarity_score (float).
    * sources (text[]).
    * created_at (timestamptz).
3.5 Analytics (Optional in DB)
If we pipe PostHog events into Supabase:
* analytics_events:
    * id (uuid, PK).
    * event (text).
    * properties (jsonb).
    * user_id (uuid).
    * group_id (uuid).
    * ip_address (text).
    * geo (jsonb).
    * created_at (timestamptz).

4. Security, RLS, and Multi-Tenancy
4.1 RLS Requirements
Enable RLS on all sensitive tables. Key policies:
* posts:
    * Users can only see posts for their group unless they are premium:
        * Free: group_id = auth.jwt()->>'group_id'.
        * Premium: may access wider scopes (for premium search use case).
* comments:
    * Restrict via post_id join to posts that belong to user’s group.
* user_presence:
    * Users can only read their own presence or aggregated values via views.
    * Optional: RLS to restrict row-level access.
* profiles:
    * User can read/update only their own profile (id = auth.uid()).
    * is_premium only set via backend / webhook (no direct client control).
4.2 Auth & Authorization
* Use Supabase Auth with JWT.
* * JWT must contain group_id claim.
* Backend APIs double-check that URL group_id matches JWT group_id.
* Premium-only endpoints check profiles.is_premium.

5. Premium Features & Billing
5.1 Premium Feature Set
* Free users:
    * Max 10 posts per day (profiles.daily_posts).
    * Can search only within their own group.
    * See ads (Google Ads in sidebar / top/bottom).
* Premium users:
    * Unlimited posts (no daily cap).
    * Can search relevant conversations across all groups (or across their organization).
    * Ad-free experience.
    * Optionally, “Group leader” tier with advanced analytics and featured placement.
5.2 Implementation Requirements
* Stripe integration:
    * Backend endpoint to create Stripe checkout sessions.
    * Supabase Edge Function Stripe webhook:
        * On customer.subscription.created and updated:
            * Set is_premium = true / false and store stripe_subscription_id.
* Quota RLS:
    * RLS policy on posts for insert:
        * Allow if user is premium OR daily_posts < 10.
    * Nightly pg_cron job to reset daily_posts for non-premium users.
* Frontend:
    * Upgrade button and visual Premium badge.
    *     * Hide ads when is_premium.

6. Latency & Performance Requirements
6.1 Latency Targets
* End-to-end P99 latency <600ms for uncached requests.
* Perceived latency ~300ms due to streaming responses.
* For cached responses: target <10ms.
6.2 Caching
* Use Redis semantic cache:
    * Key: chat:{group_id}:{semantic_hash(question)}.
    * 80–85% hit rate target.
    * TTL ~1–2 hours.
* On cache hit:
    * Return cached response immediately (no Groq / pgvector call).
* On miss:
    * Run full pipeline: pgvector → Groq streaming.
    * Store full response in cache afterward.
6.3 Search
* Implement hybrid search RPC in Supabase:
    * Input: query_embedding, match_query, group_id.
    * Combine cosine similarity on embedding and text search (BM25).
    * P99 target: ≤40ms.
6.4 Frontend Performance
* Use virtualized message lists with TanStack Virtual.
* Enable lazy loading:
    * Components: next/dynamic and React Suspense.
    * Media: Next/Image with placeholder and lazy default.
* Bundle target:
    * Initial JS + CSS ~20–60 KB total after tree-shaking.

7. Realtime Features
7.1 Group Chat
* Realtime posts (or separate messages table if needed).
* Subscribe to Supabase Realtime channel:
    * New messages.
    * Edited/deleted messages sometimes.
7.2 Presence & Active User Counts
* user_presence updated from frontend every 30 seconds.
* Trigger / scheduled job updates groups.active_count based on last_seen > now() - 5 minutes.
* Frontend displays:
    * Total members (groups.user_count).
    * Current active (groups.active_count).
* Live updates via Realtime subscription on groups.

8. Automatic Tagging & Clustering
8.1 Groq Zero-Shot Tagging
* When a new post is created:
    * Trigger Supabase Edge Function auto-tag.
    * Edge Function calls Groq (fast model like Llama‑3.1‑8B or Qwen variant) to classify into 1–3 tags from the tags table.
    * Insert selected tags into post_tags.
* Response format from LLM: strict JSON { "tags": ["H1B", "interview"] }.
8.2 Similarity-Based Tag Inheritance
* Secondary trigger (or function) that:
    * Finds similar posts via pgvector (cosine > 0.85).
    * Inherits their tags to the new post.
    * Limit inherited tags to 3.
8.3 Latency Requirements
* Total additional latency on post-create path:
    * Should not block user. Do tagging asynchronously:
        * Post is saved and visible immediately.
        * Tags appear after ~100–200ms.

9. External Content Pipeline
9.1 Requirements
* Non-prod (or background) pipeline that:
    * Daily (e.g., 2 AM IST) fetches external posts (Reddit/Twitter/LinkedIn or other sources).
    * Stores them in external_posts_staging.
    * Embeds them and clusters similar posts (by topic).
    *     * Writes cluster summaries to external_posts_live.
9.2 Implementation
* Use Supabase Edge Function fetch-external-posts.
* Schedule using pg_cron to call the Edge Function via HTTP once per day.
* Use LLM/embedding service to generate embeddings:
    * Could be OpenAI or other embedding model.
* Keep it cheap (<$50/month) and robust.

10. UI/UX Requirements
10.1 Layout
* Mobile-first design:
    * Simple column layout, large tap targets.
    * Top: group info + active users.
    * Middle: virtualized chat / posts.
    * Bottom: input area (chat / post editor).
* For desktop:
    * Sidebar: groups list, maybe trending tags.
    * Main pane: chat + posts.
10.2 StackOverflow-Style Posts
* Post card:
    * Upvote/downvote arrows with counts.
    * Score displayed (upvotes - downvotes).
    * Tags under the title/content.
    * Comments section (lazy loaded, virtualized for long threads).
10.3 Lazy Loading and Infinite Scroll
* Chats and posts:
    * Infinite scroll (load older items when scrolling upwards).
    * Virtualized lists for performance.
* Media:
    * Lazy load images, videos only when visible.
    * Use low-quality placeholders for images.

11. Security, Anti-Abuse & Legal
11.1 Security
* Use Supabase RLS everywhere.
* HTTPS enforced end-to-end.
* Use Cloudflare WAF:
    * Enable managed rules to block common attacks (SQLi/XSS).
    * Rate limiting: e.g., 100 requests/min per IP for write endpoints.
11.2 Anti-Scraping & Copyright
* Use Cloudflare anti-scraping / scrapewall style rules for bots.
* robots.txt:
    * Disallow internal chat paths to most bots.
    * Allow only selected search engines as needed.
* Add watermarking to content:
    * post_id_display like POST-xxxx-epoch visible in UI.
    * watermark_hash stored for legal trace.
* DMCA / takedown:
    * Expose a /dmca page with a simple form to submit complaints.
    * Backend endpoint logs a complaint and notifies admin.
11.3 Legal Text (Dev Support Only)
* Pages:
    * /privacy-policy
    * /terms
    * /disclaimer
    * /dmca
* Place disclaimers:
    * On all chat/post pages: “NOT LEGAL ADVICE” for visa content.
    * Explain that posts are user-generated, and not official immigration/visa advice.
(Actual legal language to be provided by a lawyer or templates; dev just needs to implement pages and links.)

12. Analytics & Growth
12.1 PostHog Integration
* Add PostHog JS snippet to frontend:
    * Autocapture pageviews, clicks, forms.
    * Custom events:
        * chat_message_sent
        * post_created
        * premium_upgrade_clicked
        * premium_purchase
* Use feature flags for:
    * Pricing experiments (e.g., ₹X vs ₹Y).
    * UI experiments (CTA placement).
12.2 Revenue Experiments (Support via flags)
* Need ability to:
    * Change premium price via feature flag.
    * Enable a “Group Leader” premium tier.
    * Track conversion funnels (visit → chat → premium).

13. Local Development Models (Cursor / 48 GB RAM)
13.1 For Dev Only (not prod)
* Use Qwen 3 32B (quantized, e.g., Q4) locally (via Ollama or similar) for:
    * Drafting prompts.
    * Prototyping RAG flows and classification.
    * Cursor / Kilocode integration.
13.2 Later Switch to Groq
* API abstraction for LLM calls:
    * Local dev: call Qwen3‑32B via Ollama or local HTTP endpoint.
    * Prod: call Groq’s HTTP API with same request schema.
* Keep interfaces compatible (messages array, temperature, max_tokens, etc).

14. Deployment & Monitoring
14.1 Environments
* dev, staging, prod Supabase projects.
* Separate Redis instances per env.
* Configuration via env vars.
14.2 Monitoring
* Use Supabase analytics for:
    * P99 latency for API functions.
    * DB usage & errors.
* Log LLM usage (tokens, success/fail).
* * Expose a lightweight /health endpoint on FastAPI.

Use this document as the single source of truth in Cursor.
Focus first on:
1. DB schema + RLS.
2. Core chat + posts + presence.
3. Groq + Redis integration for low-latency Q&A.
4. Premium + Stripe + simple upgrade flow.
Then layer in auto-tagging, external pipeline, analytics, and legal pages.


