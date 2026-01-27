#!/bin/bash

echo "🚀 Setting up Meilisearch..."

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start Meilisearch container
echo "📦 Starting Meilisearch container..."
docker-compose up -d meilisearch

# Wait for Meilisearch to be ready
echo "⏳ Waiting for Meilisearch to start..."
sleep 5

# Health check
echo "🏥 Checking Meilisearch health..."
for i in {1..30}; do
    if curl -s http://localhost:7700/health > /dev/null; then
        echo "✅ Meilisearch is ready!"
        break
    fi
    
    if [ $i -eq 30 ]; then
        echo "❌ Meilisearch failed to start"
        exit 1
    fi
    
    echo "  Attempt $i/30..."
    sleep 2
done

echo ""
echo "✅ Setup complete!"
echo ""
echo "📍 Meilisearch is running at: http://localhost:7700"
echo ""
echo "📚 Documentation: https://docs.meilisearch.com"
echo ""
echo "Next steps:"
echo "  1. Run: npm run dev"
echo "  2. Create a post with title and text"
echo "  3. Start typing in another post"
echo "  4. See related posts appear in real-time!"
