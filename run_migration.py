#!/usr/bin/env python3
"""
Run Supabase migration to create all required tables
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from supabase import create_client
from dotenv import load_dotenv

def run_migration():
    """Execute the SQL migration against Supabase"""
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        print("\nTo set them, run:")
        print('  export SUPABASE_URL="https://your-project.supabase.co"')
        print('  export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"')
        return False
    
    try:
        print(f"Connecting to Supabase: {supabase_url[:50]}...")
        
        # Initialize client
        supabase = create_client(supabase_url, supabase_key)
        
        # Read migration file
        migration_file = Path(__file__).parent / "supabase_migrations" / "COMPLETE_SCHEMA.sql"
        
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print(f"✅ Loaded migration file ({len(migration_sql)} chars)")
        print("\n⚠️  Note: Supabase Python client doesn't support direct SQL execution.")
        print("   Please run the migration using one of these methods:\n")
        print("   1. Copy the SQL from supabase_migrations/COMPLETE_SCHEMA.sql")
        print("   2. Paste it into Supabase Dashboard > SQL Editor")
        print("   3. Click 'Run'\n")
        print("   OR use Supabase CLI:")
        print("   supabase db push\n")
        
        # Save migration to a file they can reference
        output_file = Path(__file__).parent / "supabase_migrations" / "MIGRATION_READY_TO_RUN.sql"
        with open(output_file, 'w') as f:
            f.write(migration_sql)
        print(f"✅ Migration file saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
