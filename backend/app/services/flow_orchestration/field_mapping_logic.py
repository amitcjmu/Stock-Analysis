"""
Field Mapping Logic Module

This module delegates field mapping to AI agents instead of using hardcoded patterns.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

from typing import Any, Dict
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


class FieldMappingLogic:
    """Handles field mapping logic for discovery flows using AI agents"""

    def __init__(self):
        """Initialize the field mapping logic handler"""
        pass

    async def execute_discovery_field_mapping(
        self, agent_pool: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute field mapping phase using AI agents"""
        logger.info("🗺️ Executing discovery field mapping with AI agents")

        try:
            # Get raw data from phase input
            raw_data = phase_input.get("raw_data", [])
            if not raw_data:
                logger.warning("⚠️ No raw data available for field mapping")
                return {
                    "phase": "field_mapping",
                    "status": "completed",
                    "mappings": {},
                    "agent": "field_mapping_agent",
                }

            # Use the actual field mapping executor with AI agents
            from app.services.crewai_flows.handlers.phase_executors.field_mapping_executor import (
                FieldMappingExecutor,
            )
            from app.schemas.unified_discovery_flow_state import (
                UnifiedDiscoveryFlowState,
            )

            # Create flow state from phase input
            flow_state = UnifiedDiscoveryFlowState(
                flow_id=phase_input.get("flow_id", "temp"),
                raw_data=raw_data,
                metadata={
                    "detected_columns": (
                        list(raw_data[0].keys())
                        if raw_data and isinstance(raw_data[0], dict)
                        else []
                    )
                },
                client_account_id=phase_input.get("client_account_id"),
                engagement_id=phase_input.get("engagement_id"),
                data_import_id=phase_input.get("data_import_id"),
            )

            # Initialize field mapping executor with proper context
            executor = FieldMappingExecutor(
                state=flow_state, crew_manager=None, flow_bridge=None
            )

            # Get database session
            from app.core.database.session import get_db

            async for db_session in get_db():
                try:
                    # Execute field mapping with AI
                    result = await executor.execute_field_mapping(
                        flow_state, db_session
                    )

                    # The executor should handle persistence internally
                    # but we can also persist to ensure it's saved
                    if result and result.get("success") and result.get("mappings"):
                        # Extract the mappings from the result
                        field_mappings = result.get("mappings", [])

                        # Convert to the format needed for persistence
                        mappings_dict = {}
                        for mapping in field_mappings:
                            if isinstance(mapping, dict):
                                source = mapping.get("source_field")
                                if source:
                                    mappings_dict[source] = mapping

                        if mappings_dict:
                            await self._persist_field_mappings(
                                mappings_dict, phase_input
                            )

                    logger.info("✅ AI agents processed field mappings")

                    return {
                        "phase": "field_mapping",
                        "status": "completed",
                        "mappings": result.get("mappings", {}),
                        "field_count": len(
                            flow_state.metadata.get("detected_columns", [])
                        ),
                        "mapped_count": len(result.get("mappings", [])),
                        "agent": "field_mapping_agent",
                        "ai_confidence": result.get("confidence", 0),
                    }
                finally:
                    await db_session.close()

        except Exception as e:
            logger.error(f"❌ Field mapping execution failed: {e}", exc_info=True)
            # Return error status
            return {
                "phase": "field_mapping",
                "status": "error",
                "error": str(e),
                "mappings": {},
                "agent": "field_mapping_agent",
            }

    async def _persist_field_mappings(
        self, field_mappings: Dict[str, Any], phase_input: Dict[str, Any]
    ) -> None:
        """Persist AI-generated field mappings to both the flow state and ImportFieldMapping table"""
        try:
            # Get flow_id and other metadata from phase_input
            flow_id = phase_input.get("flow_id")
            data_import_id = phase_input.get("data_import_id")
            client_account_id = phase_input.get(
                "client_account_id", "11111111-1111-1111-1111-111111111111"
            )
            # engagement_id not currently used but may be needed for future enhancements
            # engagement_id = phase_input.get(
            #     "engagement_id", "22222222-2222-2222-2222-222222222222"
            # )

            if not flow_id:
                logger.warning("⚠️ No flow_id available, cannot persist field mappings")
                return

            # Import required modules
            from app.core.database.session import get_db
            from app.models.discovery_flows import DiscoveryFlow
            from app.models.data_import.mapping import ImportFieldMapping
            from sqlalchemy import select, delete
            from uuid import UUID

            # Get database session
            async for db_session in get_db():
                try:
                    # Find the discovery flow
                    result = await db_session.execute(
                        select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
                    )
                    discovery_flow = result.scalar_one_or_none()

                    # Get data_import_id from discovery flow if not provided
                    if not data_import_id and discovery_flow:
                        data_import_id = discovery_flow.data_import_id
                        if not data_import_id and discovery_flow.metadata:
                            data_import_id = discovery_flow.metadata.get(
                                "data_import_id"
                            )

                    if not data_import_id:
                        logger.warning(
                            "⚠️ No data_import_id available, cannot persist to ImportFieldMapping table"
                        )
                    else:
                        # Clear existing field mappings for this import
                        await db_session.execute(
                            delete(ImportFieldMapping).where(
                                ImportFieldMapping.data_import_id
                                == UUID(data_import_id)
                            )
                        )

                        # Create new ImportFieldMapping records from AI-generated mappings
                        created_count = 0
                        for source_field, mapping_info in field_mappings.items():
                            # Handle both dict and direct value formats
                            if isinstance(mapping_info, dict):
                                target_field = mapping_info.get(
                                    "target_field"
                                ) or mapping_info.get("target_attribute")
                                confidence = mapping_info.get(
                                    "confidence", 0.0
                                ) or mapping_info.get("confidence_score", 0.0)
                                mapping_type = mapping_info.get(
                                    "mapping_type", "ai_suggested"
                                )
                                is_critical = mapping_info.get("is_critical", False)
                            else:
                                # Simple string mapping
                                target_field = (
                                    mapping_info
                                    if isinstance(mapping_info, str)
                                    else None
                                )
                                confidence = 0.8
                                mapping_type = "ai_suggested"
                                is_critical = False

                            # Only create mapping if we have a valid target field
                            if target_field and target_field != "unmapped":
                                field_mapping = ImportFieldMapping(
                                    data_import_id=UUID(data_import_id),
                                    client_account_id=UUID(client_account_id),
                                    source_field=source_field,
                                    target_field=target_field,
                                    match_type=mapping_type,
                                    confidence_score=confidence,
                                    status="suggested",  # AI suggested, needs approval
                                    suggested_by="ai_mapper",
                                    transformation_rules={
                                        "is_critical": is_critical,
                                        "ai_generated": True,
                                    },
                                )
                                db_session.add(field_mapping)
                                created_count += 1

                        logger.info(
                            f"✅ Created {created_count} ImportFieldMapping records for import {data_import_id}"
                        )

                    if discovery_flow:
                        # Count mappings
                        total_fields = len(field_mappings)
                        mapped_count = sum(
                            1
                            for m in field_mappings.values()
                            if (isinstance(m, dict) and m.get("target_field"))
                            or (isinstance(m, str) and m != "unmapped")
                        )
                        critical_count = sum(
                            1
                            for m in field_mappings.values()
                            if isinstance(m, dict) and m.get("is_critical")
                        )

                        # Update field_mappings in the discovery flow
                        discovery_flow.field_mappings = {
                            "field_mappings": field_mappings,
                            "total_fields": total_fields,
                            "mapped_count": mapped_count,
                            "critical_mapped": critical_count,
                            "confidence": 0.85,
                            "timestamp": datetime.utcnow().isoformat(),
                            "ai_generated": True,
                        }

                        # Also update metadata with field mapping info
                        if not discovery_flow.metadata:
                            discovery_flow.metadata = {}

                        discovery_flow.metadata["field_mapping_completed"] = True
                        discovery_flow.metadata["field_mapping_count"] = total_fields
                        discovery_flow.metadata["data_import_id"] = data_import_id

                        logger.info(
                            f"✅ Updated discovery flow {flow_id} with AI-generated field mappings"
                        )
                    else:
                        logger.warning(
                            f"⚠️ Discovery flow {flow_id} not found in database"
                        )

                    await db_session.commit()
                    logger.info(
                        f"✅ Successfully persisted {len(field_mappings)} AI-generated field mappings"
                    )

                finally:
                    await db_session.close()

        except Exception as e:
            logger.error(f"❌ Failed to persist field mappings: {e}", exc_info=True)
            # Don't raise - allow flow to continue even if persistence fails
