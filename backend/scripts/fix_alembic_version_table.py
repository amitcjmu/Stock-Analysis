#!/usr/bin/env python3
"""
Fix missing alembic_version table issue.
This script creates the alembic_version table if it doesn't exist
and sets the appropriate migration version.
"""

import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_alembic_version():
    """Create alembic_version table and set current migration."""
    # Create engine
    engine = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

    async with engine.begin() as conn:
        try:
            # Check if alembic_version table exists
            result = await conn.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'alembic_version'
                );
            """
                )
            )
            table_exists = result.scalar()

            if not table_exists:
                logger.info("Creating alembic_version table...")

                # Create the alembic_version table
                await conn.execute(
                    text(
                        """
                    CREATE TABLE alembic_version (
                        version_num VARCHAR(32) NOT NULL,
                        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                    );
                """
                    )
                )

                logger.info("✅ Created alembic_version table")
            else:
                logger.info("alembic_version table already exists")

            # Check current version
            result = await conn.execute(
                text("SELECT version_num FROM alembic_version LIMIT 1;")
            )
            current_version = result.scalar()

            if current_version:
                logger.info(f"Current migration version: {current_version}")
            else:
                # Set to the latest migration based on existing tables
                # Since RLS tables exist, we know at least migration 019 has run
                latest_version = "019_implement_row_level_security"

                logger.info(f"Setting migration version to: {latest_version}")
                await conn.execute(
                    text("INSERT INTO alembic_version (version_num) VALUES (:version)"),
                    {"version": latest_version},
                )
                logger.info("✅ Migration version set successfully")

            # Verify
            result = await conn.execute(
                text("SELECT version_num FROM alembic_version;")
            )
            version = result.scalar()
            logger.info(f"✅ Final migration version: {version}")

        except Exception as e:
            logger.error(f"Error: {e}")
            raise

    await engine.dispose()


async def main():
    """Main function."""
    logger.info("🔧 Starting alembic_version table fix...")
    try:
        await fix_alembic_version()
        logger.info("✅ Fix completed successfully!")
    except Exception as e:
        logger.error(f"❌ Fix failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
