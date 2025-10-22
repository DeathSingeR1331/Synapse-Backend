#!/usr/bin/env python3
"""
Script to run database migrations on Railway deployment.
This script can be run locally with Railway CLI or as a one-time job.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from alembic.config import Config
from alembic import command
from src.core.config import settings

async def run_migrations():
    """Run database migrations."""
    print("🔧 Starting database migrations...")
    print(f"📊 Database DSN: {settings.DATABASE_DSN}")
    
    if not settings.DATABASE_DSN:
        print("❌ ERROR: DATABASE_DSN is not configured!")
        print("Please ensure your environment variables are set correctly.")
        return False
    
    try:
        # Create Alembic configuration
        alembic_cfg = Config("alembic.ini")
        
        # Run migrations
        print("🚀 Running 'alembic upgrade head'...")
        command.upgrade(alembic_cfg, "head")
        
        print("✅ Migrations completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_migrations())
    sys.exit(0 if success else 1)
