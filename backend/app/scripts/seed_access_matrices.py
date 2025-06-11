"""
Scaffold: Seed client_access & engagement_access matrices for demo users.

Run via:
  docker exec migration_backend python app/scripts/seed_access_matrices.py [--force]
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

async def seed_access(session, force: bool):
    if force:
        await session.execute(text("DELETE FROM engagement_access WHERE is_mock = TRUE"))
        await session.execute(text("DELETE FROM client_access WHERE is_mock = TRUE"))
        logger.info("Existing mock access matrices removed.")

    # TODO: Insert client & engagement access rows for demo users
    logger.info("TODO: Implement access matrices seeding.")

async def main(force: bool):
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Missing modules – run inside backend container.")
        return
    await init_db()
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await seed_access(session, force)
        await session.commit()
    logger.info("Access matrices seeding complete (placeholder).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed client & engagement access matrices.")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(force=args.force))
