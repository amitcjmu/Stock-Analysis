#!/usr/bin/env python3
"""
Fix missing alembic_version table issue.
This script creates the alembic_version table if it doesn't exist
and sets the appropriate migration version.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the parent directory to sys.path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.core.config import settings  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_alembic_version():
    """Create alembic_version table and set current migration."""
    # Create engine
    engine = create_async_engine(
        settings.database_url_async,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

    async with engine.begin() as conn:
        try:
            # Check if alembic_version table exists in any schema
            result = await conn.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE (table_schema = 'migration' OR table_schema = 'public')
                    AND table_name = 'alembic_version'
                );
            """
                )
            )
            table_exists = result.scalar()

            if not table_exists:
                logger.info("Creating alembic_version table...")

                # Create migration schema if it doesn't exist
                await conn.execute(text("CREATE SCHEMA IF NOT EXISTS migration"))

                # Create the alembic_version table in migration schema
                await conn.execute(
                    text(
                        """
                    CREATE TABLE migration.alembic_version (
                        version_num VARCHAR(32) NOT NULL,
                        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                    );
                """
                    )
                )

                logger.info("✅ Created alembic_version table")
            else:
                logger.info("alembic_version table already exists")

            # Check current version (try migration schema first)
            current_version = None
            allowed_schemas = {"migration", "public"}

            for schema in ["migration", "public"]:
                try:
                    if schema not in allowed_schemas:
                        continue
                    # Safe: schema name validated against allowlist
                    result = await conn.execute(
                        text(
                            f"SELECT version_num FROM {schema}.alembic_version LIMIT 1;"
                        )  # nosec B608
                    )
                    current_version = result.scalar()
                    if current_version:
                        logger.info(
                            f"Found version in {schema} schema: {current_version}"
                        )
                        break
                except Exception:
                    continue

            if current_version:
                logger.info(f"Current migration version: {current_version}")
            else:
                # Set to the latest migration based on existing tables
                # Since RLS tables exist, we know at least migration 019 has run
                latest_version = "019_implement_row_level_security"

                logger.info(f"Setting migration version to: {latest_version}")
                await conn.execute(
                    text(
                        "INSERT INTO migration.alembic_version (version_num) VALUES (:version)"
                    ),
                    {"version": latest_version},
                )
                logger.info("✅ Migration version set successfully")

            # Verify (check both schemas)
            for schema in ["migration", "public"]:
                try:
                    result = await conn.execute(
                        text(
                            f"SELECT version_num FROM {schema}.alembic_version;"
                        )  # nosec B608
                    )
                    version = result.scalar()
                    if version:
                        logger.info(
                            f"✅ Final migration version in {schema} schema: {version}"
                        )
                        break
                except Exception:
                    continue

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
