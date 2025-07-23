"""
Seed script for Six R Questions and Parameters.

Usage:
    docker exec migration_backend python app/scripts/seed_sixr_questions.py [--force]
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import text

# Adjust path for module imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from app.core.database import AsyncSessionLocal

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print(
        "Required application modules missing – ensure you are running inside the backend container."
    )

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# Mock catalog definitions – replace with real catalogue when available
# ---------------------------------------------------------------------------
QUESTIONS: List[Dict[str, Any]] = [
    {
        "question_id": "Q001",
        "question_text": "Is this workload customer-facing?",
        "question_type": "boolean",
        "category": "business",
        "active": True,
        "display_order": 1,
    },
    # Add additional master questions here ...
]

PARAMETERS: List[Dict[str, Any]] = [
    {
        "parameter_key": "boolean_yes_score",
        "value": 1,
        "description": "Score when answer is yes for boolean questions",
    },
    # Additional scoring parameters ...
]


# ---------------------------------------------------------------------------
# Seeder implementation helpers
# ---------------------------------------------------------------------------
async def seed_questions(session, force: bool):
    if force:
        # Remove existing records when --force flag provided
        await session.execute(text("DELETE FROM sixr_questions"))
        logger.info("Existing questions removed.")

    for q in QUESTIONS:
        await session.execute(
            text(
                """
                INSERT INTO sixr_questions (id, question_id, question_text, question_type, category, active, created_at)
                VALUES (gen_random_uuid(), :question_id, :question_text, :question_type, :category, :active, :created_at)
                ON CONFLICT (question_id) DO NOTHING
                """
            ),
            {
                **q,
                "created_at": datetime.utcnow(),
            },
        )


async def seed_parameters(session, force: bool):
    if force:
        await session.execute(text("DELETE FROM sixr_parameters"))
        logger.info("Existing parameters removed.")

    for p in PARAMETERS:
        await session.execute(
            text(
                """
                INSERT INTO sixr_parameters (id, parameter_key, value, description, created_at)
                VALUES (gen_random_uuid(), :parameter_key, :value, :description, :created_at)
                ON CONFLICT (parameter_key) DO NOTHING
                """
            ),
            {
                **p,
                "created_at": datetime.utcnow(),
            },
        )


# ---------------------------------------------------------------------------
async def main(force: bool):
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Dependencies missing – aborting seeding.")
        return

    # init_db call removed – rely on Alembic migrations for schema setup
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await seed_questions(session, force)
            await seed_parameters(session, force)
        await session.commit()
    logger.info("SixR questions & parameters seeding complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed SixR master questions and parameters."
    )
    parser.add_argument(
        "--force", action="store_true", help="Delete existing rows before seeding"
    )
    args = parser.parse_args()

    asyncio.run(main(force=args.force))
