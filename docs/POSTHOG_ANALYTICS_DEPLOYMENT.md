# PostHog Analytics - Deployment Guide

## Overview

This guide explains how to deploy the **Hybrid PostHog Analytics** system, which combines self-hosted PostHog on Render with local event storage in Supabase for a zero-cost, high-performance solution.

## Architecture

```
Frontend / Backend
     │
     ├──▶ PostHog (Self-hosted on Render)
     │    └── Dashboard & Advanced Analytics
     │
     └──▶ Supabase Database
          └── Raw Events Table (Local Backup)
```

## Prerequisites

- **Render Account**: For hosting PostHog (Free Tier).
- **Supabase Project**: For local event storage.
- **GitHub Account**: To fork the PostHog repository.

## Step 1: Deploy PostHog (Self-Hosted)

### 1.1 Create Render Database
1. Go to [render.com](https://render.com) and create a **New PostgreSQL** database.
2. Choose the **Free Plan**.
3. Note the `Internal DB URL` and `External DB URL`.

### 1.2 Deploy PostHog Instance
1. Fork the [PostHog repository](https://github.com/PostHog/posthog).
2. Create a **New Web Service** on Render connected to your fork.
3. Use the following environment variables:
   - `SECRET_KEY`: (Generate a random string)
   - `DATABASE_URL`: (Your Render Postgres Internal URL)
   - `REDIS_URL`: (Create a free Redis instance on Render and link it)
   - `DISABLE_SECURE_SSL_REDIRECT`: `true`

### 1.3 Configure API Keys
1. Access your deployed PostHog instance (e.g., `https://your-app.onrender.com`).
2. Go to **Project Settings** -> **API Keys**.
3. Copy your **Project API Key**.

---

## Step 2: Configure Application

### 2.1 Backend Environment
Update your `.env` file with the PostHog details:

```bash
# PostHog Configuration
POSTHOG_API_KEY=phc_your_api_key
POSTHOG_HOST=https://your-app.onrender.com

# Hybrid Analytics Settings
ENABLE_HYBRID_ANALYTICS=true
STORE_EVENTS_LOCALLY=true
```

### 2.2 Database Setup
Run the SQL migration to create the local events table in Supabase:

```bash
# Apply migration
psql $SUPABASE_DB_URL -f supabase_migrations/analytics/004_analytics_events_table.sql
```

---

## Step 3: Verify Deployment

### 3.1 Test Event Logging
Send a test event via the API:

```bash
curl -X POST http://localhost:8000/api/v1/analytics/test \
  -H "Content-Type: application/json" \
  -d '{
    "event": "deployment_test",
    "properties": {"status": "success"}
  }'
```

### 3.2 Check Data Destinations
1. **PostHog Dashboard**: Verify the event appears in "Live Events".
2. **Supabase Table**: Query the `analytics_events` table:
   ```sql
   SELECT * FROM analytics_events ORDER BY created_at DESC LIMIT 1;
   ```

---

## Troubleshooting

### Events not showing in PostHog
- Verify `POSTHOG_HOST` is accessible from your backend.
- Check that the `POSTHOG_API_KEY` is correct.
- Ensure the Render service is healthy (check logs).

### Events not in Supabase
- Verify `STORE_EVENTS_LOCALLY=true` is set.
- Check database permissions for the backend role.

## Cost Estimation

| Component | Service | Cost |
|-----------|---------|------|
| PostHog App | Render Web Service (Free) | $0 |
| PostHog DB | Render PostgreSQL (Free) | $0 |
| PostHog Redis | Render Redis (Free) | $0 |
| Local Storage | Supabase (Free Tier) | $0 |
| **Total** | | **$0/mo** |

## Next Steps

1. Create custom dashboards in PostHog.
2. Set up retention policies for local Supabase data.
3. Implement funnel analysis for key user flows.
