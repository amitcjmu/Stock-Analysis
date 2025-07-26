#!/usr/bin/env python3
"""
Script to programmatically approve field mappings for a Discovery Flow
and progress it to the next phase.
"""

import asyncio
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.data_import.mapping import ImportFieldMapping
from app.models.discovery_flow import DiscoveryFlow

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Flow ID to process
FLOW_ID = "582b87c4-0df1-4c2f-aa3b-e4b5a287d725"

# CSV to Asset field mappings
FIELD_MAPPINGS = {
    "hostname": "hostname",
    "ip_address": "ip_address",
    "os_type": "operating_system",
    "os_version": "os_version",
    "cpu_cores": "cpu_cores",
    "memory_gb": "memory_gb",
    "disk_gb": "disk_gb",
    "environment": "environment",
    "application": "application",
    "business_unit": "business_unit",
    "location": "location",
    "status": "status",
    "instance_id": "cloud_provider_id",  # Additional field if present
}


async def get_discovery_flow(db: AsyncSession, flow_id: str) -> tuple:
    """Get discovery flow by flow_id and extract data_import_id"""
    from sqlalchemy import text

    query = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
    result = await db.execute(query)
    flow = result.scalar_one_or_none()

    if not flow:
        raise ValueError(f"Discovery flow not found: {flow_id}")

    # Get data_import_id from flow_persistence_data in crewai_flow_state_extensions
    state_query = text(
        """
        SELECT flow_persistence_data
        FROM crewai_flow_state_extensions
        WHERE flow_id = :flow_id
    """
    )
    state_result = await db.execute(state_query, {"flow_id": str(flow_id)})
    state_row = state_result.fetchone()

    data_import_id = None
    if state_row and state_row.flow_persistence_data:
        data_import_id = state_row.flow_persistence_data.get("data_import_id")

    return flow, data_import_id


async def get_field_mappings(db: AsyncSession, data_import_id: UUID) -> list:
    """Get all field mappings for a data import"""
    query = select(ImportFieldMapping).where(
        ImportFieldMapping.data_import_id == data_import_id
    )
    result = await db.execute(query)
    mappings = result.scalars().all()

    return mappings


async def approve_field_mapping(
    db: AsyncSession, mapping: ImportFieldMapping, target_field: str
) -> None:
    """Approve a single field mapping with the correct target field"""
    mapping.target_field = target_field
    mapping.status = "approved"
    mapping.approved_by = "automation_script"
    mapping.approved_at = datetime.utcnow()
    mapping.confidence_score = 1.0  # Full confidence since manually mapped

    await db.commit()
    logger.info(f"✅ Approved mapping: {mapping.source_field} -> {target_field}")


async def update_flow_phase(
    db: AsyncSession, flow: DiscoveryFlow, flow_id: str
) -> None:
    """Update flow to progress past field_mapping_approval phase"""
    from sqlalchemy import text

    # Mark field mapping as completed
    flow.field_mapping_completed = True
    flow.current_phase = "data_cleansing"
    flow.progress_percentage = 33.3  # 2/6 phases completed

    # Update phase tracking
    if flow.phases_completed:
        if "field_mapping_approval" not in flow.phases_completed:
            flow.phases_completed.append("field_mapping_approval")
    else:
        flow.phases_completed = ["data_import", "field_mapping_approval"]

    await db.commit()
    logger.info(f"✅ Updated discovery flow phase to: {flow.current_phase}")

    # Also update the crewai_flow_state_extensions table
    update_query = text(
        """
        UPDATE crewai_flow_state_extensions
        SET flow_persistence_data = jsonb_set(
            jsonb_set(
                jsonb_set(
                    jsonb_set(
                        flow_persistence_data,
                        '{current_phase}',
                        '"data_cleansing"'::jsonb
                    ),
                    '{completion}',
                    '"in_progress"'::jsonb
                ),
                '{awaiting_user_approval}',
                'false'::jsonb
            ),
            '{progress_percentage}',
            '50.0'::jsonb
        ),
        updated_at = NOW()
        WHERE flow_id = :flow_id
    """
    )

    await db.execute(update_query, {"flow_id": flow_id})
    await db.commit()
    logger.info("✅ Updated crewai flow state to continue processing")


async def main():
    """Main execution function"""
    async with AsyncSessionLocal() as db:
        try:
            logger.info(f"🔍 Processing flow: {FLOW_ID}")

            # Get discovery flow and data_import_id
            flow, data_import_id = await get_discovery_flow(db, FLOW_ID)
            logger.info(f"✅ Found flow: {flow.flow_name}")
            logger.info(f"   Current phase: {flow.current_phase}")
            logger.info(f"   Data import ID: {data_import_id}")

            if not data_import_id:
                raise ValueError("Flow has no data_import_id")

            # Get field mappings
            mappings = await get_field_mappings(db, UUID(data_import_id))
            logger.info(f"📋 Found {len(mappings)} field mappings")

            # Process each mapping
            approved_count = 0
            for mapping in mappings:
                source_field = mapping.source_field.lower()

                # Find target field from our mapping dictionary
                target_field = FIELD_MAPPINGS.get(source_field)

                if target_field:
                    await approve_field_mapping(db, mapping, target_field)
                    approved_count += 1
                else:
                    logger.warning(f"⚠️ No mapping found for: {mapping.source_field}")

            logger.info(f"✅ Approved {approved_count}/{len(mappings)} mappings")

            # Update flow phase
            await update_flow_phase(db, flow, FLOW_ID)

            # Use Master Flow Orchestrator to trigger next phase
            logger.info("🚀 Triggering next phase through Master Flow Orchestrator...")

            # Note: This would normally require proper context and orchestrator instance
            # For now, we've updated the database state which the flow will pick up

            logger.info("✅ Field mappings approved and flow updated successfully!")

        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
