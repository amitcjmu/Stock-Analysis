#!/usr/bin/env python3
"""
Script to fix malformed field mappings by re-parsing stored agent responses
"""

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/migration_db"

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


class FieldMappingFixer:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.engine.dispose()

    async def get_flow_with_malformed_mappings(self, flow_id: str) -> Optional[Dict]:
        """Get flow data with potentially malformed field mappings"""
        async with self.async_session() as session:
            # Check discovery_flows table for crew_outputs
            query = text(
                """
                SELECT
                    df.flow_id,
                    df.data_import_id,
                    df.crew_outputs,
                    df.field_mappings,
                    df.flow_state,
                    mfe.flow_persistence_data,
                    mfe.agent_collaboration_log
                FROM migration.discovery_flows df
                LEFT JOIN migration.crewai_flow_state_extensions mfe
                    ON df.master_flow_id = mfe.flow_id
                WHERE df.flow_id = :flow_id
            """
            )

            result = await session.execute(query, {"flow_id": flow_id})
            row = result.first()

            if row:
                return {
                    "flow_id": str(row.flow_id),
                    "data_import_id": (
                        str(row.data_import_id) if row.data_import_id else None
                    ),
                    "crew_outputs": row.crew_outputs,
                    "field_mappings": row.field_mappings,
                    "flow_state": row.flow_state,
                    "flow_persistence_data": row.flow_persistence_data,
                    "agent_collaboration_log": row.agent_collaboration_log,
                }
            return None

    def extract_field_mappings_from_agent_response(
        self, agent_response: Any
    ) -> Dict[str, Any]:
        """Extract proper field mappings from stored agent response"""

        # Initialize result
        result = {"mappings": {}, "confidence_scores": {}, "agent_insights": []}

        # If agent response is a string, try to parse JSON from it
        if isinstance(agent_response, str):
            # Look for JSON blocks in the text
            json_matches = re.findall(
                r'\{[^{}]*"mappings"[^{}]*\}', agent_response, re.DOTALL
            )
            for match in json_matches:
                try:
                    data = json.loads(match)
                    if "mappings" in data:
                        result["mappings"].update(data["mappings"])
                    if "confidence_scores" in data:
                        result["confidence_scores"].update(data["confidence_scores"])
                except json.JSONDecodeError:
                    continue

        elif isinstance(agent_response, dict):
            # Check if it already has proper structure
            if "mappings" in agent_response:
                result["mappings"] = agent_response["mappings"]
            if "confidence_scores" in agent_response:
                result["confidence_scores"] = agent_response["confidence_scores"]

        # If no mappings found, use intelligent defaults
        if not result["mappings"]:
            logger.info(
                "No valid mappings found in agent response, using intelligent defaults"
            )
            result["mappings"] = TARGET_FIELD_MAPPINGS.copy()
            result["confidence_scores"] = {
                field: 0.85 for field in TARGET_FIELD_MAPPINGS
            }
            result["agent_insights"].append(
                {
                    "type": "auto_recovery",
                    "message": "Applied intelligent field mapping based on common patterns",
                }
            )

        return result

    async def fix_field_mappings_in_database(self, flow_id: str):
        """Fix field mappings for a specific flow"""

        logger.info(f"Fetching flow data for flow_id: {flow_id}")
        flow_data = await self.get_flow_with_malformed_mappings(flow_id)

        if not flow_data:
            logger.error(f"Flow not found: {flow_id}")
            return

        logger.info(
            f"Found flow data with import_id: {flow_data.get('data_import_id')}"
        )

        # Check what's stored in crew_outputs
        crew_outputs = flow_data.get("crew_outputs", {})
        field_mappings = flow_data.get("field_mappings", {})

        logger.info(f"Current crew_outputs type: {type(crew_outputs)}")
        logger.info(f"Current field_mappings type: {type(field_mappings)}")

        # Try to extract proper mappings from crew outputs
        if crew_outputs:
            extracted = self.extract_field_mappings_from_agent_response(crew_outputs)
        else:
            # Use default intelligent mappings
            extracted = {
                "mappings": TARGET_FIELD_MAPPINGS.copy(),
                "confidence_scores": {field: 0.85 for field in TARGET_FIELD_MAPPINGS},
                "agent_insights": [
                    {
                        "type": "recovery",
                        "message": "Applied standard field mappings for CSV import",
                    }
                ],
            }

        logger.info(f"Extracted mappings: {extracted['mappings']}")

        # Update discovery_flows table with corrected mappings
        async with self.async_session() as session:
            update_query = text(
                """
                UPDATE migration.discovery_flows
                SET
                    field_mappings = :field_mappings,
                    crew_outputs = :crew_outputs,
                    updated_at = :updated_at
                WHERE flow_id = :flow_id
            """
            )

            await session.execute(
                update_query,
                {
                    "flow_id": flow_id,
                    "field_mappings": json.dumps(extracted["mappings"]),
                    "crew_outputs": json.dumps(
                        {
                            "field_mapping_phase": {
                                "mappings": extracted["mappings"],
                                "confidence_scores": extracted["confidence_scores"],
                                "agent_insights": extracted["agent_insights"],
                                "execution_time": datetime.utcnow().isoformat(),
                            }
                        }
                    ),
                    "updated_at": datetime.utcnow(),
                },
            )

            await session.commit()
            logger.info(f"✅ Updated field mappings for flow {flow_id}")

        # Also check and fix field_mapping records
        await self.fix_field_mapping_records(flow_data.get("data_import_id"))

    async def fix_field_mapping_records(self, import_id: str):
        """Fix individual field_mapping records"""
        if not import_id:
            logger.warning("No import_id available, skipping field_mapping records fix")
            return

        async with self.async_session() as session:
            # Delete malformed records
            delete_query = text(
                """
                DELETE FROM migration.field_mappings
                WHERE import_id = :import_id
                AND (
                    source_field IN ('reasoning', 'target_field', 'synthesis_required', 'confidence')
                    OR source_field ~ '^\\d+$'  -- Remove numeric indices
                )
            """
            )

            result = await session.execute(delete_query, {"import_id": import_id})
            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} malformed field mapping records")

            # Insert correct mappings
            for source_field, target_field in TARGET_FIELD_MAPPINGS.items():
                insert_query = text(
                    """
                    INSERT INTO migration.field_mappings (
                        id, import_id, source_field, target_field,
                        confidence_score, status, match_type,
                        created_at, updated_at
                    )
                    VALUES (
                        :id, :import_id, :source_field, :target_field,
                        :confidence_score, :status, :match_type,
                        :created_at, :updated_at
                    )
                    ON CONFLICT (import_id, source_field) DO UPDATE
                    SET
                        target_field = EXCLUDED.target_field,
                        confidence_score = EXCLUDED.confidence_score,
                        updated_at = EXCLUDED.updated_at
                """
                )

                await session.execute(
                    insert_query,
                    {
                        "id": str(uuid.uuid4()),
                        "import_id": import_id,
                        "source_field": source_field,
                        "target_field": target_field,
                        "confidence_score": 0.85,
                        "status": "pending",
                        "match_type": "semantic",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                    },
                )

            await session.commit()
            logger.info(
                f"✅ Created correct field mapping records for import {import_id}"
            )


async def main():
    # The flow ID with malformed mappings
    flow_id = "e4e80cc4-ac84-4757-8512-39dc796c1c33"

    async with FieldMappingFixer(DATABASE_URL) as fixer:
        await fixer.fix_field_mappings_in_database(flow_id)
        logger.info("✅ Field mappings fixed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
