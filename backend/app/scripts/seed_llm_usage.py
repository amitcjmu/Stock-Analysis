"""
Scaffold: Seed llm_model_pricing, llm_usage_logs & llm_usage_summary demo data.

Run via:
  docker exec migration_backend python app/scripts/seed_llm_usage.py [--force]
"""
import argparse
import asyncio
import logging
import os
import sys

from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from app.core.database import AsyncSessionLocal
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_llm_usage(session, force: bool):
    if force:
        await session.execute(text("DELETE FROM llm_usage_logs WHERE is_mock = TRUE"))
        await session.execute(text("DELETE FROM llm_usage_summary WHERE is_mock = TRUE"))
        await session.execute(text("DELETE FROM llm_model_pricing WHERE is_mock = TRUE"))
        logger.info("Existing mock LLM usage data removed.")

    # TODO: Insert model pricing, logs, and usage summary rows
    logger.info("TODO: Implement LLM usage seeding.")

async def main(force: bool):
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Missing application modules – run in backend container.")
        return

    # init_db removed – rely on Alembic migrations
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await seed_llm_usage(session, force)
        await session.commit()
    logger.info("LLM usage seeding complete (placeholder).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed LLM model pricing and usage data.")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(force=args.force))
