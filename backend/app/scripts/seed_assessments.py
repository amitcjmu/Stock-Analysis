"""
Scaffold: Seed assessments demo data.

Run via:
  docker exec migration_backend python app/scripts/seed_assessments.py [--force]
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

async def seed_assessments(session, force: bool):
    if force:
        await session.execute(text("DELETE FROM assessments WHERE is_mock = TRUE"))
        logger.info("Existing mock assessments removed.")

    # TODO: Insert placeholder assessment rows linked to assets / analyses
    logger.info("TODO: Implement assessments seeding.")

async def main(force: bool):
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Required modules missing – run inside backend container.")
        return

    await init_db()
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await seed_assessments(session, force)
        await session.commit()
    logger.info("Assessments seeding complete (placeholder).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed assessments demo data.")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(force=args.force))
