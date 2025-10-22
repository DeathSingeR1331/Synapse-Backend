#!/usr/bin/env python3
"""
Simple migration script for Railway deployment.
This script can be run directly in the Railway environment.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    print("=== Railway Database Migration ===")
    
    # Check if we're in Railway environment
    if not os.getenv('RAILWAY_ENVIRONMENT'):
        print("ERROR: This script must be run in Railway environment")
        return 1
    
    # Check database connection
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        return 1
    
    print(f"Database URL: {database_url[:50]}...")
    
    try:
        # Import and run alembic
        from alembic.config import Config
        from alembic import command
        
        print("Running database migrations...")
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        
        print("✅ Migrations completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
