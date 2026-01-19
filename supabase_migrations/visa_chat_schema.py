"""
Visa Chat Schema Migration
Creates tables for visa-related chat functionality in Supabase
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    """
    Run the visa chat schema migration
    """
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment")
        return False
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Read and execute the migration SQL
        migration_file = os.path.join(os.path.dirname(__file__), "003_visa_chat_schema.sql")
        
        with open(migration_file, 'r') as file:
            migration_sql = file.read()
        
        # Execute the migration
        # Note: Supabase Python client doesn't have direct SQL execution
        # We'll need to use the migration through RPC or direct SQL if available
        
        print("Migration file content:")
        print(migration_sql)
        print("\nNote: This migration should be run directly in Supabase SQL editor")
        print("Or through Supabase CLI with: supabase db push")
        
        return True
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    run_migration()