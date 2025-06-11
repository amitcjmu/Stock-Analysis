"""
Scaffold: Seed sample data_quality_issues linked to assets.

Run via:
  docker exec migration_backend python app/scripts/seed_data_quality_issues.py [--force]
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
    from app.core.database import AsyncSessionLocal, init_db
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_issues(session, force: bool):
    if force:
        await session.execute(text("DELETE FROM data_quality_issues WHERE is_mock = TRUE"))
        logger.info("Existing mock data_quality_issues removed.")

    # TODO: Insert sample issues referencing assets
    logger.info("TODO: Implement data quality issues seeding.")

async def main(force: bool):
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Run inside backend container with app modules available.")
        return
    await init_db()
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await seed_issues(session, force)
        await session.commit()
    logger.info("Data quality issues seeding completed (placeholder).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed sample data_quality_issues.")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(force=args.force))
