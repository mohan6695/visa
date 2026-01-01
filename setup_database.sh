#!/bin/bash
# Script to apply all database migrations for the visa chat app

set -e

echo "🚀 Applying Database Migrations for Visa Chat App"
echo "================================================"

# Check if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo "❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set"
    echo "Please export these environment variables:"
    echo "export SUPABASE_URL='https://your-project.supabase.co'"
    echo "export SUPABASE_SERVICE_ROLE_KEY='your-service-role-key'"
    exit 1
fi

echo "✅ Environment variables configured"
echo "📡 Supabase URL: $SUPABASE_URL"

# Array of migration files in order
MIGRATIONS=(
    "supabase_migrations/001_chat_schema.sql"
    "supabase_migrations/002_telegram_chat_schema.sql" 
    "supabase_migrations/003_visa_chat_schema.sql"
    "supabase_migrations/004_visa_functions.sql"
)

echo ""
echo "📋 Running migrations in order:"
for i in "${!MIGRATIONS[@]}"; do
    migration="${MIGRATIONS[$i]}"
    echo "$((i+1)). $(basename "$migration")"
done

echo ""
echo "🔄 Applying migrations..."

# Apply each migration
for migration in "${MIGRATIONS[@]}"; do
    echo "⏳ Running: $(basename "$migration")"
    
    if [ ! -f "$migration" ]; then
        echo "❌ Migration file not found: $migration"
        exit 1
    fi
    
    # Read the SQL file and send it to Supabase
    SQL_CONTENT=$(cat "$migration")
    
    # Use curl to execute the SQL via Supabase REST API
    RESPONSE=$(curl -s -X POST \
        "$SUPABASE_URL/rest/v1/rpc/exec_sql" \
        -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
        -H "Content-Type: application/json" \
        -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
        -d "{\"query\": $(echo "$SQL_CONTENT" | jq -Rs .)}")
    
    # Check if the migration was successful
    if echo "$RESPONSE" | grep -q '"error"'; then
        echo "❌ Error applying migration $(basename "$migration"):"
        echo "$RESPONSE" | jq '.error'
        exit 1
    else
        echo "✅ Successfully applied: $(basename "$migration")"
    fi
    
    echo ""
done

echo "🎉 All migrations applied successfully!"
echo ""
echo "📊 Database is now ready with:"
echo "   • Core chat and messaging schema"
echo "   • Telegram integration tables"
echo "   • Visa-specific features (posts, tags, presence)"
echo "   • Essential PostgreSQL functions"
echo "   • Row Level Security (RLS) policies"
echo ""
echo "🔧 Next steps:"
echo "   1. Deploy the FastAPI backend"
echo "   2. Configure frontend connection"
echo "   3. Set up Redis for caching"
echo "   4. Test the API endpoints"