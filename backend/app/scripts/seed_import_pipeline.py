"""
Scaffold: Seed mock import sessions, field mappings & processing steps.

Run via:
  docker exec migration_backend python app/scripts/seed_import_pipeline.py [--force]
"""
import asyncio
import logging
import os
import sys
import argparse
from datetime import datetime
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from app.core.database import AsyncSessionLocal
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_import_pipeline(session, force: bool):
    if force:
        await session.execute(text("DELETE FROM import_processing_steps WHERE is_mock = TRUE"))
        await session.execute(text("DELETE FROM import_field_mappings WHERE is_mock = TRUE"))
        await session.execute(text("DELETE FROM data_import_sessions WHERE is_mock = TRUE"))
        await session.execute(text("DELETE FROM data_imports WHERE is_mock = TRUE"))
        logger.info("Existing mock import pipeline data removed.")

    # TODO: Insert a sample import session with steps and learned mappings
    logger.info("TODO: Implement import pipeline seeding.")

async def main(force: bool):
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Missing application modules – run inside backend container.")
        return

    # init_db removed – rely on Alembic migrations
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await seed_import_pipeline(session, force)
        await session.commit()
    logger.info("Import pipeline seeding complete (placeholder).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed import pipeline demo data.")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(force=args.force))
