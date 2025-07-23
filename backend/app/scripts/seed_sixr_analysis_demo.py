"""
Scaffold: Seed demo SixR analysis, iterations, responses & recommendations.

Run via:
  docker exec migration_backend python app/scripts/seed_sixr_analysis_demo.py [--force]

Notes:
- Requires existing SixR master questions and parameters.
- Must reference a valid engagement & assets belonging to a client account.
- Uses ContextAwareRepository pattern (TODO: integrate repository once models available).
"""

import argparse
import asyncio
import logging
import os
import sys
from typing import Dict

from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from app.core.database import AsyncSessionLocal

    # from app.repositories.context_aware import SixRAnalysisRepository  # TODO
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Demo analysis definitions (placeholder data)
# ---------------------------------------------------------------------------
ANALYSIS_META: Dict[str, str] = {
    "name": "Demo SixR Readiness",
    "description": "Sample SixR analysis for demo engagement",
    "status": "completed",
}


# ---------------------------------------------------------------------------
async def seed_analysis(session, force: bool):
    """Inserts a single demo analysis with one iteration and mock responses."""
    if force:
        await session.execute(
            text("DELETE FROM sixr_recommendations WHERE is_mock = TRUE")
        )
        await session.execute(
            text("DELETE FROM sixr_question_responses WHERE is_mock = TRUE")
        )
        await session.execute(text("DELETE FROM sixr_iterations WHERE is_mock = TRUE"))
        await session.execute(text("DELETE FROM sixr_analyses WHERE is_mock = TRUE"))
        logger.info("Existing mock SixR analysis data removed.")

    # TODO: Look up client_account_id, engagement_id, and asset list

    # TODO: Insert analysis, iteration, responses, recommendations
    logger.info("TODO: Implement SixR analysis seeding once models & repo ready.")


# ---------------------------------------------------------------------------
async def main(force: bool):
    if not DEPENDENCIES_AVAILABLE:
        logger.error("App dependencies not found – run inside backend container.")
        return

    # init_db removed – rely on Alembic migrations
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await seed_analysis(session, force)
        await session.commit()
    logger.info("SixR demo analysis seeding complete (placeholder).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo SixR analysis data.")
    parser.add_argument(
        "--force", action="store_true", help="Delete existing mock rows before seeding"
    )
    args = parser.parse_args()

    asyncio.run(main(force=args.force))
