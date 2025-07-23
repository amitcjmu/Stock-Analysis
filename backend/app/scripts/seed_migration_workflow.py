"""
Scaffold: Seed migration_logs & workflow_progress demo data.

Run via:
  docker exec migration_backend python app/scripts/seed_migration_workflow.py [--force]
"""

import argparse
import asyncio
import logging
import os
import sys

from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from app.core.database import AsyncSessionLocal

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
async def seed_migration_workflow(session, force: bool):
    if force:
        await session.execute(text("DELETE FROM migration_logs WHERE is_mock = TRUE"))
        await session.execute(
            text("DELETE FROM workflow_progress WHERE is_mock = TRUE")
        )
        logger.info("Existing mock workflow data removed.")

    # TODO: Insert demo migration logs & workflow checkpoints (linked to waves/assets)
    logger.info("TODO: Implement migration workflow seeding.")


# ---------------------------------------------------------------------------
async def main(force: bool):
    if not DEPENDENCIES_AVAILABLE:
        logger.error("App modules missing – run inside backend container.")
        return

    # init_db removed – rely on Alembic migrations
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await seed_migration_workflow(session, force)
        await session.commit()
    logger.info("Migration workflow seeding completed (placeholder).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed migration logs & workflow progress."
    )
    parser.add_argument(
        "--force", action="store_true", help="Delete existing mock rows before seeding"
    )
    args = parser.parse_args()

    asyncio.run(main(force=args.force))
