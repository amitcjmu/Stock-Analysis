#!/usr/bin/env python3
"""
Railway Database Migration and Initialization Fix

This script is specifically designed to fix database issues in Railway deployment.
It handles the common issues that prevent the application from starting properly.

Usage:
    python scripts/deployment/fix-railway-db.py [--force-reset]

Options:
    --force-reset: Drop all tables and recreate from scratch (destructive)
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import command
from alembic.config import Config

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import AsyncSessionLocal
from app.core.database_initialization import initialize_database

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RailwayDatabaseFixer:
    """Fix Railway database initialization issues"""

    def __init__(self, force_reset: bool = False):
        self.force_reset = force_reset
        self.database_url = os.getenv("DATABASE_URL")

        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        logger.info("Railway Database Fixer initialized")
        logger.info(f"Force reset mode: {self.force_reset}")

    async def check_database_connection(self) -> bool:
        """Test database connection"""
        logger.info("Testing database connection...")

        try:
            engine = create_async_engine(self.database_url)
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                result.scalar()
            await engine.dispose()
            logger.info("✅ Database connection successful!")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    async def install_extensions(self) -> None:
        """Install required PostgreSQL extensions"""
        logger.info("Installing PostgreSQL extensions...")

        try:
            engine = create_async_engine(self.database_url)
            async with engine.begin() as conn:
                # Install extensions
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))

                logger.info("✅ Extensions installed successfully!")
            await engine.dispose()
        except Exception as e:
            logger.error(f"❌ Failed to install extensions: {e}")
            raise

    async def check_alembic_version(self) -> Optional[str]:
        """Check current Alembic version"""
        try:
            engine = create_async_engine(self.database_url)
            async with engine.begin() as conn:
                # Check if alembic_version table exists
                result = await conn.execute(
                    text(
                        """
                    SELECT to_regclass('alembic_version') IS NOT NULL
                """
                    )
                )

                if not result.scalar():
                    logger.info("Alembic version table doesn't exist")
                    await engine.dispose()
                    return None

                # Get current version
                result = await conn.execute(
                    text("SELECT version_num FROM alembic_version")
                )
                version = result.scalar()
                logger.info(f"Current Alembic version: {version}")

            await engine.dispose()
            return version
        except Exception as e:
            logger.warning(f"Could not check Alembic version: {e}")
            return None

    async def reset_database(self) -> None:
        """Reset database by dropping all tables"""
        logger.info("🔥 Resetting database (dropping all tables)...")

        try:
            engine = create_async_engine(self.database_url)
            async with engine.begin() as conn:
                # Drop all tables in the current schema
                await conn.execute(
                    text(
                        """
                    DROP SCHEMA IF EXISTS migration CASCADE;
                    DROP SCHEMA IF EXISTS public CASCADE;
                    CREATE SCHEMA public;
                    CREATE SCHEMA migration;
                """
                    )
                )

                logger.info("✅ Database reset completed!")
            await engine.dispose()
        except Exception as e:
            logger.error(f"❌ Database reset failed: {e}")
            raise

    def run_migrations(self) -> None:
        """Run Alembic migrations"""
        logger.info("Running Alembic migrations...")

        try:
            # Get alembic config
            alembic_cfg_path = Path(__file__).parent.parent.parent / "alembic.ini"
            if not alembic_cfg_path.exists():
                raise FileNotFoundError(f"Alembic config not found: {alembic_cfg_path}")

            alembic_cfg = Config(str(alembic_cfg_path))
            alembic_cfg.set_main_option("sqlalchemy.url", self.database_url)

            # Stamp the database if no version exists, then upgrade
            try:
                command.upgrade(alembic_cfg, "head")
                logger.info("✅ Migrations completed successfully!")
            except Exception as migration_error:
                logger.warning(
                    f"Migration failed, trying to stamp first: {migration_error}"
                )
                try:
                    # Try to stamp the base version first
                    command.stamp(alembic_cfg, "base")
                    command.upgrade(alembic_cfg, "head")
                    logger.info("✅ Migrations completed after stamping!")
                except Exception as stamp_error:
                    logger.error(
                        f"❌ Migration failed even after stamping: {stamp_error}"
                    )
                    raise

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise

    async def initialize_data(self) -> None:
        """Initialize database with required data"""
        logger.info("Initializing database data...")

        try:
            async with AsyncSessionLocal() as db:
                await initialize_database(db)
            logger.info("✅ Database data initialization completed!")
        except Exception as e:
            logger.error(f"❌ Data initialization failed: {e}")
            raise

    async def validate_setup(self) -> Dict[str, Any]:
        """Validate database setup"""
        logger.info("Validating database setup...")

        validation = {
            "tables_exist": False,
            "admin_exists": False,
            "demo_data_exists": False,
            "table_count": 0,
            "errors": [],
        }

        try:
            async with AsyncSessionLocal() as db:
                # Check tables
                result = await db.execute(
                    text(
                        """
                    SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_schema IN ('migration', 'public')
                    AND table_type = 'BASE TABLE'
                """
                    )
                )
                validation["table_count"] = result.scalar()
                validation["tables_exist"] = validation["table_count"] > 10

                # Check admin
                try:
                    result = await db.execute(
                        text(
                            "SELECT COUNT(*) FROM users WHERE email = 'chocka@gmail.com'"
                        )
                    )
                    validation["admin_exists"] = result.scalar() > 0
                except Exception:
                    validation["admin_exists"] = False

                # Check demo data
                try:
                    result = await db.execute(
                        text(
                            "SELECT COUNT(*) FROM client_accounts WHERE name = 'Demo Corporation'"
                        )
                    )
                    validation["demo_data_exists"] = result.scalar() > 0
                except Exception:
                    validation["demo_data_exists"] = False

        except Exception as e:
            validation["errors"].append(str(e))

        return validation

    def print_validation_report(self, validation: Dict[str, Any]) -> None:
        """Print validation report"""
        logger.info("\n" + "=" * 50)
        logger.info("RAILWAY DATABASE VALIDATION REPORT")
        logger.info("=" * 50)

        overall_ok = (
            validation["tables_exist"]
            and validation["admin_exists"]
            and len(validation["errors"]) == 0
        )

        status = "✅ READY" if overall_ok else "❌ ISSUES FOUND"
        logger.info(f"Overall Status: {status}")
        logger.info(
            f"Tables: {'✅' if validation['tables_exist'] else '❌'} ({validation['table_count']} found)"
        )
        logger.info(f"Platform Admin: {'✅' if validation['admin_exists'] else '❌'}")
        logger.info(f"Demo Data: {'✅' if validation['demo_data_exists'] else '❌'}")

        if validation["errors"]:
            logger.error("Errors:")
            for error in validation["errors"]:
                logger.error(f"  - {error}")

        logger.info("=" * 50)

    async def run_fix_process(self) -> None:
        """Run the complete fix process"""
        logger.info("🚀 Starting Railway database fix process...")

        try:
            # Step 1: Test connection
            if not await self.check_database_connection():
                raise Exception("Cannot connect to database")

            # Step 2: Install extensions
            await self.install_extensions()

            # Step 3: Reset if requested
            if self.force_reset:
                await self.reset_database()

            # Step 4: Check current migration state
            current_version = await self.check_alembic_version()
            if current_version is None and not self.force_reset:
                logger.warning(
                    "No migration version found - database may need initialization"
                )

            # Step 5: Run migrations
            self.run_migrations()

            # Step 6: Initialize data
            await self.initialize_data()

            # Step 7: Validate
            validation = await self.validate_setup()
            self.print_validation_report(validation)

            if len(validation["errors"]) == 0 and validation["tables_exist"]:
                logger.info("🎉 Railway database fix completed successfully!")
            else:
                logger.error("⚠️  Fix completed with issues. Check validation report.")

        except Exception as e:
            logger.error(f"💥 Railway database fix failed: {e}")
            raise


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Fix Railway Database Issues")
    parser.add_argument(
        "--force-reset",
        action="store_true",
        help="Drop all tables and recreate (destructive)",
    )

    args = parser.parse_args()

    try:
        fixer = RailwayDatabaseFixer(force_reset=args.force_reset)
        await fixer.run_fix_process()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fix process failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
