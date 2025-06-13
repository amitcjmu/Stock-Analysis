"""
Scaffold: Seed sample data_quality_issues linked to assets.

Run via:
  docker exec migration_backend python app/scripts/seed_data_quality_issues.py [--force]
"""
import asyncio
import logging
import os
import sys
import argparse
from datetime import datetime
from sqlalchemy import text
import uuid
import json
import random

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from app.core.database import AsyncSessionLocal
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_issues(session, force: bool):
    if force:
        # Delete previously seeded mock rows identified by the reasoning prefix
        await session.execute(text("DELETE FROM data_quality_issues WHERE reasoning LIKE 'MOCK:%'"))
        logger.info("Existing mock data_quality_issues removed.")

    # -------------------------------------------------------------------
    # Helper: ensure at least one mock DataImport + RawImportRecord exists
    # -------------------------------------------------------------------
    async def _ensure_mock_import() -> tuple[str, str]:
        """Return a (data_import_id, raw_record_id) tuple, creating mock rows if needed."""
        # Try to get an existing mock import
        result = await session.execute(
            text("SELECT id FROM data_imports WHERE is_mock = TRUE LIMIT 1")
        )
        row = result.first()
        if row:
            data_import_id = row[0]
            # Try to get a raw record under it
            rr_res = await session.execute(
                text("SELECT id FROM raw_import_records WHERE data_import_id = :di LIMIT 1"),
                {"di": str(data_import_id)},
            )
            rr_row = rr_res.first()
            if rr_row:
                return str(data_import_id), str(rr_row[0])

        # Need to create both import + raw record
        user_row = await session.execute(text("SELECT id FROM users LIMIT 1"))
        user_id = user_row.scalar_one_or_none()
        if not user_id:
            logger.warning("No users found – cannot create mock import; skipping issue seeding.")
            return None, None  # Will skip later

        data_import_id = str(uuid.uuid4())
        await session.execute(
            text(
                """
                INSERT INTO data_imports (
                    id, import_name, import_type, source_filename, imported_by,
                    status, is_mock, created_at
                ) VALUES (
                    :id, 'Mock CMDB Import', 'cmdb', 'mock_cmdb.csv', :imported_by,
                    'completed', TRUE, :created_at
                )
                """
            ),
            {"id": data_import_id, "imported_by": str(user_id), "created_at": datetime.utcnow()},
        )

        raw_record_id = str(uuid.uuid4())
        await session.execute(
            text(
                """
                INSERT INTO raw_import_records (
                    id, data_import_id, row_number, raw_data, is_processed, is_valid,
                    created_at
                ) VALUES (
                    :id, :di, 1, :raw_data, FALSE, FALSE, :created_at
                )
                """
            ),
            {
                "id": raw_record_id,
                "di": data_import_id,
                "raw_data": json.dumps({"hostname": "unknown"}),
                "created_at": datetime.utcnow(),
            },
        )
        logger.info("Created mock data_import %s and raw_record %s", data_import_id, raw_record_id)
        return data_import_id, raw_record_id

    data_import_id, raw_record_id = await _ensure_mock_import()
    if not data_import_id:
        logger.warning("DataQualityIssue seeding skipped – no data import context available.")
        return

    # -------------------------------------------------------------------
    # Create sample DataQualityIssue rows
    # -------------------------------------------------------------------
    # Prepend 'MOCK:' so we can reliably delete in future runs without requiring schema changes
    sample_issues = [
        {
            "issue_type": "missing_value",
            "field_name": "hostname",
            "severity": "high",
            "reasoning": "MOCK: Hostname missing from record.",
        },
        {
            "issue_type": "invalid_format",
            "field_name": "ip_address",
            "severity": "medium",
            "reasoning": "MOCK: IP address not in valid IPv4/IPv6 format.",
        },
        {
            "issue_type": "inconsistent_data",
            "field_name": "os_version",
            "severity": "low",
            "reasoning": "MOCK: OS version appears inconsistent with reported operating system.",
        },
    ]

    now = datetime.utcnow()
    inserted = 0
    for si in sample_issues:
        await session.execute(
            text(
                """
                INSERT INTO data_quality_issues (
                    id, data_import_id, raw_record_id, issue_type, field_name,
                    severity, reasoning, status, detected_at
                ) VALUES (
                    :id, :di, :rr, :issue_type, :field_name,
                    :severity, :reasoning, 'detected', :detected_at
                ) ON CONFLICT DO NOTHING
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "di": data_import_id,
                "rr": raw_record_id,
                "issue_type": si["issue_type"],
                "field_name": si.get("field_name"),
                "severity": si.get("severity", "medium"),
                "reasoning": si.get("reasoning"),
                "detected_at": now,
            },
        )
        inserted += 1

    logger.info("Inserted %d mock data quality issues.", inserted)

async def main(force: bool):
    if not DEPENDENCIES_AVAILABLE:
        logger.error("Run inside backend container with app modules available.")
        return
    # init_db removed – rely on Alembic migrations
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await seed_issues(session, force)
        await session.commit()
    logger.info("Data quality issues seeding completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed sample data_quality_issues.")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(force=args.force))
