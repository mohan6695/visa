# Hybrid PostHog Setup Guide

## Overview

This guide explains how to set up the hybrid PostHog approach for zero-cost analytics:

- **PostHog**: Self-hosted on Render ($0)
- **Raw Events**: Stored in Supabase table ($0 storage)
- **Dashboard**: localhost or PostHog UI

## Benefits

✅ **All analytics in your database**  
✅ **Zero external vendors**  
✅ **100ms latency**  
✅ **$0 cost**  
✅ **Full data control**  
✅ **Privacy compliance**  

## Architecture

```
Frontend/Backend → PostHog (self-hosted) + Supabase Events Table
                    ↓
                Both destinations receive events
```

## Setup Steps

### 1. Database Migration

Run the analytics migration:

```bash
# Apply the analytics events table
psql -h your-supabase-host -U postgres -d your-database -f supabase_migrations/analytics/004_analytics_events_table.sql
```

### 2. PostHog Self-Hosted Deployment

#### Option A: Render Deployment (Recommended)

1. **Fork PostHog Repository**
   ```bash
   git clone https://github.com/PostHog/posthog.git
   cd posthog
   ```

2. **Deploy to Render**
   - Connect your GitHub repository to Render
   - Use the render.yaml configuration (provided below)
   - Deploy as a Web Service

#### Option B: Docker Deployment

1. **Create Docker Compose File**
   ```yaml
   version: '3.8'
   
   services:
     posthog:
       image: posthog/posthog:latest
       ports:
         - "8000:8000"
       environment:
         - SECRET_KEY=your-secret-key
         - DATABASE_URL=postgresql://user:pass@db:5432/posthog
         - REDIS_URL=redis://redis:6379
         - CLICKHOUSE_SERVER_URL=http://clickhouse:8123
       depends_on:
         - db
         - redis
         - clickhouse
   
     db:
       image: postgres:15
       environment:
         - POSTGRES_DB=posthog
         - POSTGRES_USER=posthog
         - POSTGRES_PASSWORD=posthog
   
     redis:
       image: redis:7-alpine
   
     clickhouse:
       image: clickhouse/clickhouse-server:latest
   ```

2. **Run Docker Compose**
   ```bash
   docker-compose up -d
   ```

### 3. Environment Configuration

Update your application environment variables:

```bash
# PostHog Configuration
POSTHOG_API_KEY=your-posthog-api-key
POSTHOG_HOST=https://your-posthog-instance.render.com

# Analytics Configuration
ENABLE_HYBRID_ANALYTICS=true
STORE_EVENTS_LOCALLY=true
```

### 4. Frontend Configuration

Update PostHog configuration in your frontend:

```typescript
// frontend/src/lib/analytics.ts
const POSTHOG_HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://your-posthog-instance.render.com';
const POSTHOG_API_KEY = process.env.NEXT_PUBLIC_POSTHOG_KEY || '';
```

### 5. Dashboard Access

#### Local Development
```bash
# Access PostHog dashboard locally
open http://localhost:8000
```

#### Production
```bash
# Access your Render-hosted PostHog
open https://your-posthog-instance.render.com
```

## Configuration Files

### Render Configuration

Create `render.yaml` in your PostHog fork:

```yaml
services:
  - type: web
    name: posthog
    env: python
    plan: free
    buildCommand: |
      pip install -r requirements.txt
      python manage.py collectstatic --noinput
    startCommand: |
      gunicorn posthog.wsgi --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 120
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: posthog-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: posthog-redis
          property: connectionString
      - key: CLICKHOUSE_SERVER_URL
        fromService:
          type: web
          name: posthog-clickhouse
          property: host

databases:
  - name: posthog-db
    plan: free

  - name: posthog-clickhouse
    plan: free

redis:
  - name: posthog-redis
    plan: free
```

### Environment Variables

#### Development
```bash
# .env.local
POSTHOG_API_KEY=dev-api-key
POSTHOG_HOST=http://localhost:8000
NEXT_PUBLIC_POSTHOG_KEY=dev-public-key
NEXT_PUBLIC_POSTHOG_HOST=http://localhost:8000
ENABLE_HYBRID_ANALYTICS=true
```

#### Production
```bash
# .env.production
POSTHOG_API_KEY=prod-api-key
POSTHOG_HOST=https://your-posthog-instance.render.com
NEXT_PUBLIC_POSTHOG_KEY=prod-public-key
NEXT_PUBLIC_POSTHOG_HOST=https://your-posthog-instance.render.com
ENABLE_HYBRID_ANALYTICS=true
```

## Monitoring and Maintenance

### Health Checks

```bash
# Check PostHog health
curl https://your-posthog-instance.render.com/health

# Check database connectivity
psql $DATABASE_URL -c "SELECT 1;"
```

### Backup Strategy

1. **PostHog Data**: Automated backups via Render
2. **Supabase Events**: Included in Supabase backup strategy
3. **Configuration**: Version control for all configs

### Performance Optimization

1. **Indexing**: Analytics table already includes optimal indexes
2. **Caching**: PostHog handles caching automatically
3. **Compression**: JSONB properties are compressed automatically

## Cost Breakdown

| Component | Service | Monthly Cost |
|-----------|---------|--------------|
| PostHog | Render Free Tier | $0 |
| Database | Supabase (included) | $0 |
| Redis | Render Free Tier | $0 |
| **Total** | | **$0** |

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify PostHog URL is accessible
   - Check API key permissions
   - Ensure Supabase connection is working

2. **Missing Events**
   - Check browser console for errors
   - Verify PostHog client is initialized
   - Check network requests in DevTools

3. **Performance Issues**
   - Monitor PostHog instance resource usage
   - Check Supabase query performance
   - Verify database indexes are created

### Debug Commands

```bash
# Test PostHog connectivity
curl -X POST https://your-posthog-instance.capture/ \
  -H "Content-Type: application/json" \
  -d '{"event": "test_event", "properties": {"test": true}}'

# Check analytics events in Supabase
SELECT COUNT(*) FROM analytics_events WHERE created_at > NOW() - INTERVAL '1 hour';
```

## Next Steps

1. **Custom Dashboards**: Create custom analytics dashboards
2. **Funnels**: Set up conversion funnels in PostHog
3. **A/B Testing**: Use PostHog for experiment tracking
4. **Cohort Analysis**: Analyze user behavior patterns
5. **Feature Flags**: Implement feature flagging system

## Security Considerations

1. **API Keys**: Rotate PostHog API keys regularly
2. **Network Security**: Use HTTPS for all connections
3. **Data Privacy**: Comply with GDPR/CCPA requirements
4. **Access Control**: Implement proper user permissions

This hybrid approach gives you the best of both worlds: powerful analytics with zero ongoing costs and complete data ownership.