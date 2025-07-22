"""
Scaffold: Seed feedback & feedback_summaries demo data.

Run via:
  docker exec migration_backend python app/scripts/seed_feedback.py [--force]
"""
import argparse
import asyncio
import logging
import os
import sys
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

async def seed_feedback(session, force: bool):
    if force:
        await session.execute(text("DELETE FROM feedback_summaries WHERE is_mock = TRUE"))
        await session.execute(text("DELETE FROM feedback WHERE is_mock = TRUE"))
        logger.info("Existing mock feedback data removed.")

    # TODO: Insert sample feedback entries linked to assets / analyses
    logger.info("TODO: Implement feedback seeding.")

async def main(force: bool):
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Missing modules – run within backend container.")
        return

    # init_db removed – rely on Alembic migrations
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await seed_feedback(session, force)
        await session.commit()
    logger.info("Feedback seeding complete (placeholder).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed feedback demo data.")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(force=args.force))
