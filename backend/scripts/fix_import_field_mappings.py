#!/usr/bin/env python3
"""
Script to fix malformed field mappings in import_field_mappings table
The issue: JSON properties were incorrectly parsed as source fields
"""

import asyncio
import logging
import uuid
from datetime import datetime

import asyncpg

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = "postgresql://postgres:postgres@localhost:5433/migration_db"

# Expected CSV fields based on the import
EXPECTED_CSV_FIELDS = [
    "App_ID",
    "App_Name",
    "App_Version",
    "Owner_Group",
    "Scan_Date",
    "Port_Usage",
    "Last_Update",
    "Dependency_List",
    "Scan_Status",
]

# Target field mappings (what they should map to)
TARGET_FIELD_MAPPINGS = {
    "App_ID": "application_id",
    "App_Name": "application_name",
    "App_Version": "version",
    "Owner_Group": "owner",
    "Scan_Date": "scan_date",
    "Port_Usage": "port",
    "Last_Update": "last_modified",
    "Dependency_List": "dependencies",
    "Scan_Status": "status",
}

# JSON properties that were incorrectly stored as source fields
MALFORMED_FIELDS = [
    "mappings",
    "reasoning",
    "requires_transformation",
    "synthesis_required",
    "target_field",
    "skipped_fields",
]


async def fix_import_field_mappings():
    """Fix the import_field_mappings table directly"""

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        # Get the import ID we need to fix
        import_id = "4532ddf6-d97c-49e2-be50-e32bafe913aa"

        logger.info(f"Fixing field mappings for import: {import_id}")

        # First, delete the malformed records
        delete_query = """
            DELETE FROM migration.import_field_mappings
            WHERE data_import_id = $1
            AND source_field = ANY($2::text[])
        """

        deleted = await conn.execute(delete_query, import_id, MALFORMED_FIELDS)
        logger.info(f"Deleted {deleted} malformed records")

        # Now update the existing CSV field mappings with correct target fields
        for source_field, target_field in TARGET_FIELD_MAPPINGS.items():
            # Check if the record exists
            exists = await conn.fetchval(
                """
                SELECT COUNT(*) FROM migration.import_field_mappings
                WHERE data_import_id = $1 AND source_field = $2
                """,
                import_id,
                source_field,
            )

            if exists > 0:
                # Update existing record
                update_query = """
                    UPDATE migration.import_field_mappings
                    SET
                        target_field = $3,
                        confidence_score = 0.85,
                        match_type = 'semantic',
                        status = 'pending',
                        updated_at = $4
                    WHERE data_import_id = $1 AND source_field = $2
                """
                await conn.execute(
                    update_query,
                    import_id,
                    source_field,
                    target_field,
                    datetime.utcnow(),
                )
                logger.info(f"Updated mapping: {source_field} -> {target_field}")
            else:
                # Insert new record if it doesn't exist
                insert_query = """
                    INSERT INTO migration.import_field_mappings (
                        id, data_import_id, source_field, target_field,
                        confidence_score, match_type, status,
                        client_account_id, master_flow_id,
                        created_at, updated_at
                    )
                    SELECT
                        $1, $2, $3, $4, 0.85, 'semantic', 'pending',
                        df.client_account_id, df.master_flow_id,
                        $5, $5
                    FROM migration.discovery_flows df
                    WHERE df.data_import_id = $2
                    LIMIT 1
                """
                await conn.execute(
                    insert_query,
                    str(uuid.uuid4()),
                    import_id,
                    source_field,
                    target_field,
                    datetime.utcnow(),
                )
                logger.info(f"Created mapping: {source_field} -> {target_field}")

        # Verify the fix
        result = await conn.fetch(
            """
            SELECT source_field, target_field, confidence_score
            FROM migration.import_field_mappings
            WHERE data_import_id = $1
            ORDER BY source_field
            """,
            import_id,
        )

        logger.info("✅ Fixed field mappings:")
        for row in result:
            logger.info(
                f"  {row['source_field']} -> {row['target_field']} (confidence: {row['confidence_score']})"
            )

    finally:
        await conn.close()


async def main():
    await fix_import_field_mappings()
    logger.info("✅ Field mappings fixed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
