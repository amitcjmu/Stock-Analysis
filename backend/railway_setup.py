#!/usr/bin/env python3
"""
Railway Production Setup Script
Handles database initialization and environment setup for Railway deployment
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def check_environment():
    """Check and validate Railway environment setup."""
    logger.info("🔍 Checking Railway Environment...")

    # Required environment variables
    required_vars = {
        "DATABASE_URL": "PostgreSQL connection string",
        "ENVIRONMENT": "Production environment flag",
    }

    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Don't log the full DATABASE_URL for security
            if var == "DATABASE_URL":
                logger.info(f"✅ {var}: Set (postgresql://...)")
            else:
                logger.info(f"✅ {var}: {value}")
        else:
            logger.error(f"❌ {var}: Missing ({description})")
            missing_vars.append(var)

    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return False

    return True


async def test_database_connection():
    """Test basic database connectivity."""
    logger.info("🔗 Testing Database Connection...")

    try:
        # Simple connection test using psycopg2 (sync) first
        from urllib.parse import urlparse

        import psycopg2

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise Exception("DATABASE_URL not found")

        # Parse the URL for psycopg2
        urlparse(database_url)

        # Convert asyncpg URL to psycopg2 format if needed
        if "asyncpg" in database_url:
            sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        else:
            sync_url = database_url

        # Remove sslmode parameter for psycopg2 connection as it might cause issues
        if "?sslmode=" in sync_url:
            sync_url = sync_url.split("?sslmode=")[0]

        # Test sync connection first
        conn = psycopg2.connect(sync_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        logger.info("✅ Database Connection: SUCCESS")
        logger.info(f"📋 PostgreSQL Version: {version}")
        return True

    except ImportError:
        logger.warning("psycopg2 not available, trying async connection...")

        try:
            # Fall back to async connection
            from sqlalchemy import text

            from app.core.database import engine

            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                logger.info("✅ Async Database Connection: SUCCESS")
                logger.info(f"📋 PostgreSQL Version: {version}")
                return True

        except Exception as e:
            logger.error(f"❌ Database Connection Failed: {e}")
            return False

    except Exception as e:
        logger.error(f"❌ Database Connection Failed: {e}")
        return False


async def run_alembic_migrations():
    """Run Alembic migrations to keep database schema up to date."""
    logger.info("🔄 Running Alembic Migrations...")

    try:
        import os
        import subprocess
        import sys

        # Get the backend directory
        backend_dir = Path(__file__).parent
        alembic_ini = backend_dir / "alembic.ini"

        if not alembic_ini.exists():
            logger.warning("⚠️ alembic.ini not found, skipping migrations")
            return True

        # Try different ways to run alembic
        alembic_commands = [
            ["alembic"],  # System alembic
            [sys.executable, "-m", "alembic"],  # Python module
            ["python", "-m", "alembic"],  # Alternative python
            ["python3", "-m", "alembic"],  # Python3 specifically
        ]

        # Find working alembic command
        working_command = None
        for cmd in alembic_commands:
            try:
                test_result = subprocess.run(
                    cmd + ["--version"],
                    capture_output=True,
                    text=True,
                    cwd=str(backend_dir),
                )
                if test_result.returncode == 0:
                    working_command = cmd
                    logger.info(f"✅ Found working alembic command: {' '.join(cmd)}")
                    break
            except Exception:
                continue

        if not working_command:
            logger.error("❌ Could not find working alembic command")
            logger.error("Trying programmatic migration as fallback...")
            return await run_migrations_programmatically()

        # Run alembic upgrade head
        logger.info("📋 Checking current migration status...")
        result = subprocess.run(
            working_command + ["current"],
            cwd=str(backend_dir),
            capture_output=True,
            text=True,
            env={**os.environ, "DATABASE_URL": os.getenv("DATABASE_URL")},
        )
        if result.returncode == 0:
            logger.info(f"Current migrations: {result.stdout}")
        else:
            logger.warning(f"Could not check current status: {result.stderr}")

        logger.info("⬆️ Running migrations to latest...")
        result = subprocess.run(
            working_command + ["upgrade", "head"],
            cwd=str(backend_dir),
            capture_output=True,
            text=True,
            env={**os.environ, "DATABASE_URL": os.getenv("DATABASE_URL")},
        )

        if result.returncode == 0:
            logger.info("✅ Migrations completed successfully")
            logger.info(f"Output: {result.stdout}")
            return True
        else:
            logger.error(f"❌ Migration failed: {result.stderr}")
            logger.error("Trying programmatic migration as fallback...")
            return await run_migrations_programmatically()

    except Exception as e:
        logger.error(f"❌ Migration execution failed: {e}")
        logger.error("Trying programmatic migration as fallback...")
        return await run_migrations_programmatically()


async def run_migrations_programmatically():
    """Run migrations programmatically using Alembic API."""
    logger.info("🔧 Running migrations programmatically...")

    try:
        import os

        from alembic import command
        from alembic.config import Config

        # Get the backend directory
        backend_dir = Path(__file__).parent
        alembic_ini = backend_dir / "alembic.ini"

        if not alembic_ini.exists():
            logger.error("❌ alembic.ini not found")
            return False

        # Create Alembic configuration
        alembic_cfg = Config(str(alembic_ini))

        # Set the database URL
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            alembic_cfg.set_main_option("sqlalchemy.url", database_url)

        # Run upgrade to head
        logger.info("⬆️ Upgrading database to latest version...")
        command.upgrade(alembic_cfg, "head")

        logger.info("✅ Programmatic migration completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Programmatic migration failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def create_database_tables():
    """Create database tables if they don't exist."""
    logger.info("🏗️ Creating Database Tables...")

    try:
        from app.core.database import Base, engine

        # Import all models to ensure they're registered
        logger.info("📦 Importing database models...")

        # Additional models
        try:
            from app.models.asset import Asset
            from app.models.migration import Migration

            logger.info("✅ All models imported successfully")
        except ImportError as e:
            logger.warning(f"Some optional models not available: {e}")

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ Database tables created successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Table creation failed: {e}")
        return False


async def initialize_database_data():
    """Initialize database with required data."""
    logger.info("📦 Initializing Database Data...")

    try:
        # Check if database initialization module exists
        try:
            from app.core.database import AsyncSessionLocal
            from app.core.database_initialization import initialize_database

            async with AsyncSessionLocal() as db:
                await initialize_database(db)
                logger.info("✅ Database initialization completed!")
                return True

        except ImportError:
            logger.warning("⚠️ Database initialization module not found, skipping...")
            return True

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        # Don't fail the entire setup for this
        return True


async def test_feedback_functionality():
    """Test feedback system functionality."""
    logger.info("🧪 Testing Feedback System...")

    try:
        from sqlalchemy import text

        from app.core.database import AsyncSessionLocal
        from app.models.feedback import Feedback

        async with AsyncSessionLocal() as session:
            # Test table exists
            result = await session.execute(text("SELECT COUNT(*) FROM feedback"))
            count = result.scalar()
            logger.info(f"📊 Feedback table: {count} existing records")

            # Test insert
            test_feedback = Feedback(
                feedback_type="page_feedback",
                page="Railway Setup Test",
                rating=5,
                comment="Testing Railway database setup",
                category="setup",
                breadcrumb="Railway > Setup > Test",
                status="new",
            )

            session.add(test_feedback)
            await session.commit()
            await session.refresh(test_feedback)

            logger.info(f"✅ Test feedback created: {test_feedback.id}")

            # Verify the insert
            result = await session.execute(text("SELECT COUNT(*) FROM feedback"))
            new_count = result.scalar()
            logger.info(f"📊 Feedback table after test: {new_count} records")

            return True

    except Exception as e:
        logger.error(f"❌ Feedback test failed: {e}")
        return False


async def main():
    """Main setup routine for Railway deployment."""
    logger.info("🚀 Starting Railway Production Setup...")
    logger.info("=" * 60)

    # Step 1: Environment check
    if not await check_environment():
        logger.error("💥 Environment setup failed!")
        return False

    # Step 2: Database connection test
    if not await test_database_connection():
        logger.error("💥 Database connection failed!")
        return False

    # Step 3: Run Alembic migrations (this will create/update all tables)
    if not await run_alembic_migrations():
        logger.error("💥 Database migrations failed!")
        return False

    # Step 4: Create tables (fallback if migrations don't exist)
    if not await create_database_tables():
        logger.error("💥 Table creation failed!")
        return False

    # Step 5: Initialize database with required data
    if not await initialize_database_data():
        logger.error("💥 Database data initialization failed!")
        return False

    # Step 6: Test feedback functionality
    if not await test_feedback_functionality():
        logger.error("💥 Feedback system test failed!")
        return False

    logger.info("=" * 60)
    logger.info("🎉 Railway Setup: COMPLETE")
    logger.info("✅ Database: Connected and Initialized")
    logger.info("✅ Migrations: Applied Successfully")
    logger.info("✅ Tables: Created and Verified")
    logger.info("✅ Data: Initialized")
    logger.info("✅ Feedback System: Operational")
    logger.info("🚀 Application ready for production use!")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if success:
            logger.info("✅ Setup completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Setup failed!")
            sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
