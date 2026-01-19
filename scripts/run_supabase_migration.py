#!/usr/bin/env python3
"""
Run Supabase Migration Script
Creates all tables from the existing migration files using MCP credentials.
"""

import os
import sys
import json
import httpx

# Supabase configuration from environment
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    print("Please set these environment variables:")
    print('  export SUPABASE_URL="https://your-project.supabase.co"')
    print('  export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"')
    sys.exit(1)

# Read the complete schema migration
MIGRATION_FILE = "supabase_migrations/011_complete_schema_with_users.sql"

if not os.path.exists(MIGRATION_FILE):
    print(f"ERROR: Migration file not found: {MIGRATION_FILE}")
    sys.exit(1)

with open(MIGRATION_FILE
