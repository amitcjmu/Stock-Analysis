"""
Scaffold: Seed baseline migration wave plans.

Run via:
  docker exec migration_backend python app/scripts/seed_wave_plans.py [--force]
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

# ---------------------------------------------------------------------------
async def seed_wave_plans(session, force: bool):
    if force:
        await session.execute(text("DELETE FROM wave_plans WHERE is_mock = TRUE"))
        logger.info("Existing mock wave plans removed.")

    # TODO: select engagement id; insert default wave plan rows.
    logger.info("TODO: Implement wave plan seed logic.")

# ---------------------------------------------------------------------------
async def main(force: bool):
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Missing app modules – execute within backend container.")
        return

    await init_db()
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await seed_wave_plans(session, force)
        await session.commit()
    logger.info("Wave plan seeding completed (placeholder).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed baseline wave plans.")
    parser.add_argument("--force", action="store_true", help="Delete existing mock rows before seeding")
    args = parser.parse_args()

    asyncio.run(main(force=args.force))
