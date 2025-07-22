"""
Scaffold: Seed assessments demo data.

Run via:
  docker exec migration_backend python app/scripts/seed_assessments.py [--force]
"""
import argparse
import asyncio
import logging
import os
import random
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

async def seed_assessments(session, force: bool):
    if force:
        await session.execute(text("DELETE FROM assessments WHERE title LIKE 'MOCK:%'"))
        logger.info("Existing mock assessments removed.")

    # Retrieve the most recent migration to attach assessments to
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
        logger.warning("No migrations found – skipping assessments seeding.")
        return

    migration_id = row[0]

    # Fetch up to 5 mock assets for asset-level assessments
    asset_rows = await session.execute(
        text(
            """
            SELECT id
            FROM assets
            WHERE is_mock = TRUE
            LIMIT 5
            """
        )
    )
    asset_ids = [r[0] for r in asset_rows]

    now = datetime.utcnow()
    inserted = 0

    # Migration-level assessments
    migration_assessments = [
        {
            "asset_id": None,
            "assessment_type": "risk_assessment",
            "status": "completed",
            "title": "MOCK: Migration Risk Assessment",
            "description": "Mock risk assessment for entire migration.",
            "overall_score": 78.5,
            "risk_level": "medium",
            "confidence_level": 0.85,
            "recommended_strategy": None,
        },
        {
            "asset_id": None,
            "assessment_type": "cost_analysis",
            "status": "completed",
            "title": "MOCK: Migration Cost Analysis",
            "description": "Mock cost analysis for migration.",
            "overall_score": 82.0,
            "risk_level": "low",
            "confidence_level": 0.9,
            "recommended_strategy": None,
        },
    ]

    # Asset-level 6R analyses
    strategies = ["rehost", "replatform", "refactor", "retain", "retire", "repurchase"]
    asset_assessments = []
    for asset_id in asset_ids:
        asset_assessments.append(
            {
                "asset_id": asset_id,
                "assessment_type": "six_r_analysis",
                "status": "completed",
                "title": f"MOCK: 6R Analysis for Asset {asset_id}",
                "description": "Mock 6R analysis for asset.",
                "overall_score": round(random.uniform(60, 95), 2),
                "risk_level": random.choice(["low", "medium", "high"]),
                "confidence_level": round(random.uniform(0.7, 0.95), 2),
                "recommended_strategy": random.choice(strategies),
            }
        )

    all_assessments = migration_assessments + asset_assessments

    for a in all_assessments:
        await session.execute(
            text(
                """
                INSERT INTO assessments (
                    id,
                    migration_id,
                    asset_id,
                    assessment_type,
                    status,
                    title,
                    description,
                    overall_score,
                    risk_level,
                    confidence_level,
                    recommended_strategy,
                    created_at
                ) VALUES (
                    gen_random_uuid(),
                    :migration_id,
                    :asset_id,
                    :assessment_type,
                    :status,
                    :title,
                    :description,
                    :overall_score,
                    :risk_level,
                    :confidence_level,
                    :recommended_strategy,
                    :created_at
                )
                """
            ),
            {
                "migration_id": str(migration_id),
                "asset_id": str(a["asset_id"]) if a["asset_id"] else None,
                "assessment_type": a["assessment_type"],
                "status": a["status"],
                "title": a["title"],
                "description": a["description"],
                "overall_score": a["overall_score"],
                "risk_level": a["risk_level"],
                "confidence_level": a["confidence_level"],
                "recommended_strategy": a["recommended_strategy"],
                "created_at": now,
            },
        )
        inserted += 1

    logger.info(f"Inserted {inserted} mock assessment rows for migration {migration_id}.")

async def main(force: bool):
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Required modules missing – run inside backend container.")
        return

    # init_db removed – rely on Alembic migrations for schema setup
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await seed_assessments(session, force)
        await session.commit()
    logger.info("Assessments seeding completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed assessments demo data.")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(force=args.force))
