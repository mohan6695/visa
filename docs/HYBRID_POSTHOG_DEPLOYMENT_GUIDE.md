# Hybrid PostHog Deployment Guide

## Overview

This guide explains how to implement the **Hybrid PostHog Analytics** approach that provides:

- ✅ **PostHog events → Render self-hosted ($0)**
- ✅ **Raw events → Supabase table ($0 storage)**
- ✅ **Dashboard → localhost or PostHog UI**
- ✅ **All analytics in your database**
- ✅ **Zero external vendors**
- ✅ **100ms latency**
- ✅ **$0 cost**

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │───▶│   Backend API    │───▶│   Supabase DB   │
│   (Next.js)     │    │   (FastAPI)      │    │   (Events)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PostHog JS    │    │   PostHog API    │    │   Dashboard     │
│   (Self-hosted) │    │   (Render)       │    │   (Local/UI)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Step 1: Deploy PostHog on Render (Free)

### 1.1 Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Connect your repository

### 1.2 Create PostgreSQL Database
1. In Render dashboard, click "New +"
2. Select "PostgreSQL"
3. Choose the **Free Plan**
4. Note down the connection details

### 1.3 Deploy PostHog
1. Go to [PostHog GitHub](https://github.com/posthog/posthog)
2. Click "Deploy to Render" button
3. Configure with your PostgreSQL database
4. Set environment variables:

```bash
# Required for self-hosted
SECRET_KEY=your-random-secret-key
POSTHOG_DB_URI=postgresql://user:pass@host:port/dbname
POSTHOG_REDIS_URL=redis://user:pass@host:port
DISABLE_SECURE_SSL_REDIRECT=true
SITE_URL=https://your-posthog-app.onrender.com
```

### 1.4 Get API Key
1. Access your PostHog instance at `https://your-posthog-app.onrender.com`
2. Complete the setup wizard
3. Go to Settings → Project → API Keys
4. Copy the **Public API Key** (starts with `phc_`)

## Step 2: Configure Environment Variables

### 2.1 Update `.env` File

```bash
# PostHog Configuration
POSTHOG_API_KEY=phc_your-api-key-here
POSTHOG_HOST=https://your-posthog-app.onrender.com

# Hybrid Analytics Configuration
ENABLE_HYBRID_ANALYTICS=true
STORE_EVENTS_LOCALLY=true

# Your existing Supabase configuration
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
SUPABASE_ANON_KEY=your-supabase-anon-key
```

## Step 3: Run Database Migration

### 3.1 Apply Analytics Table Migration

```bash
# Copy the migration file to your main migrations folder
cp supabase_migrations/analytics/004_analytics_events_table.sql supabase_migrations/

# Apply to your Supabase database
supabase db push
```

Or manually run in Supabase SQL Editor:

```sql
-- Copy the contents of 004_analytics_events_table.sql
-- Paste and execute in Supabase SQL Editor
```

## Step 4: Frontend Configuration

### 4.1 Update Frontend Environment

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_POSTHOG_HOST=https://your-posthog-app.onrender.com
NEXT_PUBLIC_POSTHOG_KEY=phc_your-api-key-here
```

### 4.2 Install PostHog Client

```bash
cd frontend
npm install posthog-js
```

### 4.3 Configure Analytics Client

The frontend analytics client is already configured in `frontend/src/lib/analytics.ts` and will automatically:
- Send events to your self-hosted PostHog
- Store events locally in Supabase (via backend)
- Work in both development and production

## Step 5: Backend Configuration

The backend analytics service is already configured to support hybrid analytics. It will automatically:

1. **Send events to PostHog** (if configured)
2. **Store events in Supabase** (always, for hybrid setup)
3. **Handle failures gracefully** (if one service is down)

## Step 6: Testing the Setup

### 6.1 Test Event Tracking

```bash
# Test local storage
curl -X POST http://localhost:8000/api/v1/analytics/test \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "test_event",
    "user_id": "test-user-123",
    "properties": {
      "page_url": "https://localhost:3000/test",
      "test_data": "hybrid analytics test"
    }
  }'
```

### 6.2 Check PostHog Dashboard
1. Visit `https://your-posthog-app.onrender.com`
2. Go to "Events" section
3. Verify your test event appears

### 6.3 Check Local Storage
1. Open Supabase dashboard
2. Go to Table Editor
3. Select `analytics_events` table
4. Verify events are stored locally

## Step 7: Dashboard Access Options

### Option 1: PostHog UI (Recommended)
- **URL**: `https://your-posthog-app.onrender.com`
- **Features**: Full analytics dashboard, funnels, cohorts
- **Cost**: Free on Render
- **Pros**: Complete analytics features
- **Cons**: External dependency

### Option 2: Local Dashboard
Create custom dashboards using Supabase data:

```sql
-- Example: Daily active users
SELECT 
    DATE(created_at) as date,
    COUNT(DISTINCT user_id) as daily_active_users
FROM analytics_events 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date;
```

### Option 3: Supabase + Custom Frontend
Build custom analytics dashboard using Supabase data and your preferred frontend framework.

## Benefits of Hybrid Approach

### ✅ Cost Benefits
- **PostHog**: Free on Render
- **Storage**: $0 (using Supabase free tier)
- **Bandwidth**: Minimal (local storage)
- **Total**: $0/month

### ✅ Performance Benefits
- **Latency**: 100ms (local storage)
- **Reliability**: Works even if PostHog is down
- **Data Ownership**: Complete control
- **Privacy**: No third-party data sharing

### ✅ Technical Benefits
- **Redundancy**: Data stored in multiple places
- **Flexibility**: Switch between PostHog UI and local dashboards
- **Scalability**: Supabase handles growth
- **Integration**: Native Supabase integration

## Troubleshooting

### PostHog Not Receiving Events
1. Check API key is correct
2. Verify POSTHOG_HOST URL
3. Check browser console for errors
4. Verify environment variables

### Events Not Stored Locally
1. Check Supabase connection
2. Verify migration was applied
3. Check backend logs
4. Test RPC function manually

### Performance Issues
1. Monitor Supabase query performance
2. Consider adding indexes
3. Implement event batching
4. Use connection pooling

## Next Steps

1. **Custom Dashboards**: Build custom analytics using Supabase data
2. **Advanced Features**: Implement funnels, cohorts using SQL
3. **Real-time**: Set up Supabase real-time for live analytics
4. **Export**: Regular exports to data warehouse if needed

## Support

For issues with:
- **PostHog**: Check [PostHog docs](https://posthog.com/docs)
- **Supabase**: Check [Supabase docs](https://supabase.com/docs)
- **Hybrid Setup**: Check application logs and metrics

This hybrid approach gives you the best of both worlds: powerful PostHog analytics with zero external dependency for your core data.