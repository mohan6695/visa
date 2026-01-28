#!/bin/bash

echo "📤 Uploading seed data..."

# Upload to R2
wrangler r2 object put data-pipeline/seed-posts.json --file scripts/seed-data.json

# Trigger processing
WORKER_URL="https://visa-1.YOUR_SUBDOMAIN.workers.dev"
curl -X GET "$WORKER_URL/run"

echo "✅ Data uploaded and queued!"
