#!/usr/bin/env python3
"""
Simple migration runner for Railway deployment
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

async def run_migrations():
    """Run Alembic migrations programmatically."""
    try:
        from alembic.config import Config
        from alembic import command
        
        # Get the backend directory
        backend_dir = Path(__file__).parent
        alembic_ini = backend_dir / "alembic.ini"
        
        if not alembic_ini.exists():
            print("❌ alembic.ini not found")
            return False
        
        # Create Alembic configuration
        alembic_cfg = Config(str(alembic_ini))
        
        # Set the database URL
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)
            print(f"✅ Database URL set for migrations")
        
        # Run upgrade to head
        print("⬆️ Upgrading database to latest version...")
        command.upgrade(alembic_cfg, "head")
        
        print("✅ Migrations completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_migrations())
    sys.exit(0 if success else 1)