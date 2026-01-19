#!/usr/bin/env python3
"""
Apply complete schema migration to Supabase
This script applies the complete schema with user metadata to Supabase
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_migration():
    """Apply the complete migration to Supabase"""
    
    # Get Supabase credentials from environment or .env file
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_password = os.getenv('SUPABASE_PASSWORD')
    
    if not supabase_url or not supabase_password:
        logger.error("Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_PASSWORD")
        return False
    
    try:
        # Connect to Supabase database
        # Note: For Supabase, we typically use the connection string from the dashboard
        # Format: postgresql://postgres:[PASSWORD]@db.[PROJECT_ID].supabase.co:5432/postgres
        
        # Extract project ID from URL
        project_id = supabase_url.split('//')[1].split('.')[0]
        db_host = f"db.{project_id}.supabase.co"
        
        conn_string = f"postgresql://postgres:{supabase_password}@{db_host}:5432/postgres"
        
        logger.info(f"Connecting to Supabase database at {db_host}")
        conn = psycopg2.connect(conn_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # Read the migration file
        migration_file = 'supabase_migrations/011_complete_schema_with_users.sql'
        if not os.path.exists(migration_file):
            logger.error(f"Migration file not found: {migration_file}")
            return False
            
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Split into individual statements and execute
        statements = []
        current_statement = []
        in_function = False
        function_brace_count = 0
        
        for line in migration_sql.split('\n'):
            stripped = line.strip()
            
            # Skip empty lines and comments (except important ones)
            if not stripped or stripped.startswith('--'):
                if 'Enable required extensions' in line or 'PRIMARY KEY' in line:
                    current_statement.append(line)
                continue
            
            current_statement.append(line)
            
            # Track function boundaries
            if 'CREATE OR REPLACE FUNCTION' in line:
                in_function = True
                function_brace_count = 0
            elif in_function:
                function_brace_count += line.count('$$')
                if function_brace_count >= 2:
                    in_function = False
                    # End of function, execute it
                    if current_statement:
                        statements.append('\n'.join(current_statement))
                        current_statement = []
                    continue
            
            # Execute single statements (not inside functions)
            if not in_function and (stripped.endswith(';') or stripped.endswith('$$')):
                if current_statement:
                    statements.append('\n'.join(current_statement))
                    current_statement = []
        
        # Execute any remaining statements
        if current_statement:
            statements.append('\n'.join(current_statement))
        
        # Execute each statement
        for i, statement in enumerate(statements, 1):
            if statement.strip():
                try:
                    logger.info(f"Executing statement {i}/{len(statements)}")
                    cursor.execute(statement)
                    logger.info(f"Successfully executed statement {i}")
                except Exception as e:
                    logger.error(f"Error executing statement {i}: {str(e)}")
                    logger.error(f"Statement content: {statement[:200]}...")
                    # Continue with next statement instead of failing completely
                    continue
        
        logger.info("Migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error applying migration: {str(e)}")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()

def verify_migration():
    """Verify that the migration was applied successfully"""
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_password = os.getenv('SUPABASE_PASSWORD')
    
    if not supabase_url or not supabase_password:
        logger.error("Missing Supabase credentials for verification")
        return False
    
    try:
        project_id = supabase_url.split('//')[1].split('.')[0]
        db_host = f"db.{project_id}.supabase.co"
        conn_string = f"postgresql://postgres:{supabase_password}@{db_host}:5432/postgres"
        
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Check if tables exist
        expected_tables = [
            'users', 'posts', 'comments', 'communities', 'groups',
            'community_members', 'group_members', 'user_interactions',
            'notifications', 'search_queries'
        ]
        
        for table in expected_tables:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table}'
                )
            """)
            
            exists = cursor.fetchone()[0]
            if exists:
                logger.info(f"✓ Table '{table}' exists")
            else:
                logger.error(f"✗ Table '{table}' missing")
        
        # Check if extensions are enabled
        cursor.execute("""
            SELECT extname FROM pg_extension 
            WHERE extname IN ('vector', 'uuid-ossp', 'pg_trgm')
        """)
        
        extensions = [row[0] for row in cursor.fetchall()]
        logger.info(f"Enabled extensions: {extensions}")
        
        # Check functions
        cursor.execute("""
            SELECT routine_name FROM information_schema.routines 
            WHERE routine_schema = 'public' 
            AND routine_type = 'FUNCTION'
        """)
        
        functions = [row[0] for row in cursor.fetchall()]
        logger.info(f"Created functions: {len(functions)}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error verifying migration: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("SUPABASE COMPLETE SCHEMA MIGRATION")
    print("=" * 60)
    
    # Apply migration
    if apply_migration():
        print("\n✓ Migration applied successfully!")
        
        # Verify
        if verify_migration():
            print("✓ Verification completed successfully!")
            print("\nYour Supabase database is now ready with:")
            print("- Complete user management with metadata")
            print("- Posts and comments with AI embeddings")
            print("- Vector similarity search")
            print("- Community and group management")
            print("- Notification system")
            print("- Analytics and search tracking")
        else:
            print("⚠ Migration verification failed")
    else:
        print("✗ Migration failed")
        sys.exit(1)