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
from datetime import datetime, timedelta
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from app.core.database import AsyncSessionLocal
    from app.scripts.demo_context import get_demo_context
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
async def seed_wave_plans(session, force: bool):
    if force:
        await session.execute(text("DELETE FROM wave_plans WHERE wave_name LIKE 'MOCK:%'"))
        logger.info("Existing mock wave plans removed.")

    # Retrieve a migration to link wave plans to. Prefer the most recent mock migration if available.
    result = await session.execute(
        text(
            """
            SELECT id
            FROM migrations
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
    )
    row = result.first()
    if not row:
        logger.warning("No migrations found – wave plan seeding skipped.")
        return

    migration_id = row[0]

    # Fetch fixed demo tenant context
    context = await get_demo_context(session)
    client_account_id = context["client_account_id"]
    engagement_id = context["engagement_id"]

    # Define baseline wave plans
    wave_definitions = [
        {
            "wave_number": 1,
            "wave_name": "MOCK: Wave 1 - Pilot",
            "description": "Pilot migration of low-risk workloads.",
            "start_offset": 7,
            "end_offset": 37,
        },
        {
            "wave_number": 2,
            "wave_name": "MOCK: Wave 2 - Core Services",
            "description": "Migration of core application and database services.",
            "start_offset": 45,
            "end_offset": 105,
        },
        {
            "wave_number": 3,
            "wave_name": "MOCK: Wave 3 - Critical Production",
            "description": "Migration of business-critical production workloads.",
            "start_offset": 120,
            "end_offset": 220,
        },
    ]

    now = datetime.utcnow()
    inserted = 0
    for wd in wave_definitions:
        planned_start = now + timedelta(days=wd["start_offset"])
        planned_end = now + timedelta(days=wd["end_offset"])

        await session.execute(
            text(
                """
                INSERT INTO wave_plans (
                    id,
                    client_account_id,
                    engagement_id,
                    migration_id,
                    wave_number,
                    wave_name,
                    description,
                    planned_start_date,
                    planned_end_date,
                    status,
                    total_assets,
                    completed_assets,
                    created_at
                ) VALUES (
                    gen_random_uuid(),
                    :client_account_id,
                    :engagement_id,
                    :migration_id,
                    :wave_number,
                    :wave_name,
                    :description,
                    :planned_start_date,
                    :planned_end_date,
                    'planned',
                    0,
                    0,
                    :created_at
                ) ON CONFLICT (migration_id, wave_number) DO NOTHING
                """
            ),
            {
                "client_account_id": str(client_account_id),
                "engagement_id": str(engagement_id),
                "migration_id": str(migration_id),
                "wave_number": wd["wave_number"],
                "wave_name": wd["wave_name"],
                "description": wd["description"],
                "planned_start_date": planned_start,
                "planned_end_date": planned_end,
                "created_at": now,
            },
        )
        inserted += 1

    logger.info(f"Inserted {inserted} wave plan rows for migration {migration_id}.")

# ---------------------------------------------------------------------------
async def main(force: bool):
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Missing app modules – execute within backend container.")
        return

    # init_db removed – schema is managed via Alembic migrations
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await seed_wave_plans(session, force)
        await session.commit()
    logger.info("Wave plan seeding completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed baseline wave plans.")
    parser.add_argument("--force", action="store_true", help="Delete existing mock rows before seeding")
    args = parser.parse_args()

    asyncio.run(main(force=args.force))
