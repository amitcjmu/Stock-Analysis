#!/usr/bin/env python3
"""
Script to manually trigger field mapping phase for a stuck discovery flow
"""
import asyncio
import logging
import sys
import uuid
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models.discovery_flow import DiscoveryFlow  # noqa: E402
from app.models.data_import import ImportFieldMapping, RawImportRecord  # noqa: E402
from sqlalchemy import select  # noqa: E402
from datetime import datetime  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FLOW_ID = "8f0da8e1-0715-4f4c-a896-686c01a3f527"
DATA_IMPORT_ID = "ea00b3a6-0960-478d-9f4d-c56a0e5da76a"
CLIENT_ACCOUNT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


async def trigger_field_mapping():
    """Manually create field mappings for the discovery flow"""

    async with AsyncSessionLocal() as db:
        try:
            # Get raw import records
            query = select(RawImportRecord).where(
                RawImportRecord.data_import_id == uuid.UUID(DATA_IMPORT_ID)
            )
            result = await db.execute(query)
            raw_records = result.scalars().all()

            if not raw_records:
                logger.error("No raw import records found")
                return

            logger.info(f"Found {len(raw_records)} raw import records")

            # Get field names from first record
            first_record = raw_records[0].raw_data
            field_names = list(first_record.keys()) if first_record else []

            logger.info(f"Detected fields: {field_names}")

            # Define critical field mappings
            field_mappings = {
                "Asset Name": "name",
                "Asset Type": "asset_type",
                "Environment": "environment",
                "IP Address": "ip_address",
                "Operating System": "operating_system",
                "Location": "location",
                "Status": "status",
                "Business Owner": "owner",
                "CPU": "cpu_cores",
                "Memory GB": "memory_gb",
                "Storage GB": "storage_gb",
                "Application": "application",
            }

            # Create field mapping records
            created_count = 0
            for source_field, target_field in field_mappings.items():
                if source_field in field_names:
                    # Check if mapping already exists
                    existing_query = select(ImportFieldMapping).where(
                        ImportFieldMapping.data_import_id == uuid.UUID(DATA_IMPORT_ID),
                        ImportFieldMapping.source_field == source_field,
                    )
                    existing_result = await db.execute(existing_query)
                    existing = existing_result.scalar_one_or_none()

                    if not existing:
                        mapping = ImportFieldMapping(
                            id=uuid.uuid4(),
                            data_import_id=uuid.UUID(DATA_IMPORT_ID),
                            master_flow_id=uuid.UUID(FLOW_ID),
                            client_account_id=CLIENT_ACCOUNT_ID,
                            source_field=source_field,
                            target_field=target_field,
                            match_type="agent",
                            confidence_score=0.9,
                            status="suggested",
                            suggested_by="manual_fix",
                            transformation_rules={
                                "method": "direct_mapping",
                                "created_at": datetime.utcnow().isoformat(),
                            },
                        )
                        db.add(mapping)
                        created_count += 1
                        logger.info(
                            f"Created mapping: {source_field} -> {target_field}"
                        )

            # Update discovery flow status
            disc_query = select(DiscoveryFlow).where(
                DiscoveryFlow.master_flow_id == uuid.UUID(FLOW_ID)
            )
            disc_result = await db.execute(disc_query)
            discovery_flow = disc_result.scalar_one_or_none()

            if discovery_flow:
                discovery_flow.current_phase = "field_mapping"
                discovery_flow.field_mapping_completed = True
                discovery_flow.status = "active"
                discovery_flow.field_mappings = field_mappings
                logger.info("Updated discovery flow status")

            await db.commit()
            logger.info(f"✅ Created {created_count} field mappings successfully")

            # Verify the mappings were created
            verify_query = select(ImportFieldMapping).where(
                ImportFieldMapping.data_import_id == uuid.UUID(DATA_IMPORT_ID)
            )
            verify_result = await db.execute(verify_query)
            verified = verify_result.scalars().all()

            logger.info(f"✅ Verified {len(verified)} field mappings in database:")
            for mapping in verified:
                logger.info(
                    f"  - {mapping.source_field} -> {mapping.target_field} (confidence: {mapping.confidence_score})"
                )

        except Exception as e:
            logger.error(f"Error: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(trigger_field_mapping())
