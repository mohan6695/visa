#!/usr/bin/env python3
"""
Run Supabase visa database migration
"""
import os
import sys
import asyncio
from pathlib import Path

# Add current directory to path to import the database module
sys.path.insert(0, str(Path(__file__).parent))

from supabase_migrations.visa_chat_schema import run_migration

def main():
    """Run the visa database migration"""
    try:
        print("🚀 Starting visa database migration...")
        asyncio.run(run_migration())
        print("✅ Migration completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()