#!/bin/bash

echo "🚀 Deploying Full Stack AI Stack Overflow..."

# Backend
echo "📦 Deploying Workers..."
cd backend
wrangler deploy
WORKER_URL=$(wrangler deploy --dry-run 2>&1 | grep "Deployed to" | awk '{print $4}')
echo "✅ Backend: $WORKER_URL"
cd ..

# Frontend env
cd frontend
echo "PUBLIC_WORKER_URL=$WORKER_URL" >> .env
echo "PUBLIC_SUPABASE_URL=$PUBLIC_SUPABASE_URL" >> .env
echo "PUBLIC_SUPABASE_ANON_KEY=$PUBLIC_SUPABASE_ANON_KEY" >> .env

# Build
npm run build

# Deploy to Pages
echo "📱 Deploying Astro to Pages..."
npx wrangler pages deploy dist --project-name=ai-stackoverflow

echo "✅ Full stack deployed!"
echo "Frontend: ai-stackoverflow.pages.dev"
echo "Backend: $WORKER_URL"
