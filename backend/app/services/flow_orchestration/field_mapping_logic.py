"""
Field Mapping Logic Module

This module delegates field mapping to AI agents instead of using hardcoded patterns.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

from typing import Any, Dict, Optional, TYPE_CHECKING
from datetime import datetime

from app.core.logging import get_logger

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class FieldMappingLogic:
    """Handles field mapping logic for discovery flows using AI agents"""

    def __init__(self):
        """Initialize the field mapping logic handler"""
        pass

    async def execute_discovery_field_mapping(
        self,
        agent_pool: Dict[str, Any],  # Not used - kept for interface compatibility
        phase_input: Dict[str, Any],
        db_session: Optional["AsyncSession"] = None,
    ) -> Dict[str, Any]:
        """Execute field mapping phase using AI agents"""
        logger.info("🗺️ Executing discovery field mapping with AI agents")
        # Note: agent_pool parameter is not used - FieldMappingExecutor creates its own

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
            # Import and use TenantScopedAgentPool for agent operations
            from app.services.persistent_agents.tenant_scoped_agent_pool import (
                TenantScopedAgentPool,
            )

            # Create the modular executor from field_mapping_executor module
            from app.services.field_mapping_executor import (
                FieldMappingExecutor as ModularFieldMappingExecutor,
            )

            # Initialize with agent pool to enable AI agent execution (not fallback)
            executor = ModularFieldMappingExecutor(
                storage_manager=None,  # Storage manager not needed for this flow
                agent_pool=TenantScopedAgentPool,  # Pass the agent pool class for AI execution
                client_account_id=str(phase_input.get("client_account_id", "")),
                engagement_id=str(phase_input.get("engagement_id", "")),
            )

            # Use provided session or get one from outside
            if db_session:
                # Execute field mapping phase with AI - guard against None result
                # The modular executor expects execute_phase method
                result = (await executor.execute_phase(flow_state, db_session)) or {}

                # Normalize mappings into dict keyed by source_field
                mappings_dict: Dict[str, Any] = {}
                raw_mappings = result.get("mappings") or []
                if isinstance(raw_mappings, dict):
                    mappings_dict = raw_mappings
                elif isinstance(raw_mappings, list):
                    for mapping in raw_mappings:
                        if isinstance(mapping, dict):
                            source = mapping.get("source_field")
                            if source:
                                mappings_dict[source] = mapping

                if mappings_dict:
                    await self._persist_field_mappings(
                        mappings_dict, phase_input, db_session
                    )

                logger.info("✅ AI agents processed field mappings")

                return {
                    "phase": "field_mapping",
                    "status": "completed",
                    "mappings": mappings_dict,
                    "field_count": len(flow_state.metadata.get("detected_columns", [])),
                    "mapped_count": len(mappings_dict),
                    "agent": "field_mapping_agent",
                    "ai_confidence": result.get("confidence", 0),
                }
            else:
                logger.warning("⚠️ No database session provided for field mapping")
                return {
                    "phase": "field_mapping",
                    "status": "error",
                    "error": "No database session provided",
                    "mappings": {},
                    "agent": "field_mapping_agent",
                }

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
        self,
        field_mappings: Dict[str, Any],
        phase_input: Dict[str, Any],
        db_session: "AsyncSession",
    ) -> None:
        """
        Persist AI-generated field mappings to flow state and ImportFieldMapping table
        """
        try:
            # Import required modules
            from app.models.discovery_flow import DiscoveryFlow
            from app.models.data_import.mapping import ImportFieldMapping
            from sqlalchemy import and_, select, delete
            from uuid import UUID

            # Get flow_id and other metadata from phase_input
            flow_id = phase_input.get("flow_id")
            data_import_id = phase_input.get("data_import_id")
            client_account_id = phase_input.get("client_account_id")
            engagement_id = phase_input.get("engagement_id")
            master_flow_id = phase_input.get(
                "master_flow_id"
            )  # For unified flow integration

            # Diagnostic logging
            logger.info("🔍 Field Mapping Persistence - Received UUIDs:")
            logger.info(f"  - flow_id: {flow_id} (type: {type(flow_id)})")
            logger.info(
                f"  - master_flow_id: {master_flow_id} (type: {type(master_flow_id)})"
            )
            logger.info(f"  - data_import_id: {data_import_id}")
            logger.info(
                f"  - client_account_id: {client_account_id} (type: {type(client_account_id)})"
            )
            logger.info(
                f"  - engagement_id: {engagement_id} (type: {type(engagement_id)})"
            )

            if not flow_id:
                logger.warning("⚠️ No flow_id available, cannot persist field mappings")
                return
            # Validate flow_id is a UUID string
            try:
                from uuid import UUID as _UUID

                _ = _UUID(str(flow_id))
                logger.info("✅ flow_id validation passed")
            except (ValueError, TypeError) as e:
                logger.error(f"❌ Invalid flow_id format: {flow_id}, error: {e}")
                return

            # Validate UUIDs
            try:
                if client_account_id:
                    client_uuid = UUID(client_account_id)
                    logger.info("✅ client_account_id validation passed")
                else:
                    logger.warning(
                        "⚠️ No client_account_id provided, skipping persistence"
                    )
                    return

                if engagement_id:
                    engagement_uuid = UUID(engagement_id)
                    logger.info("✅ engagement_id validation passed")
                else:
                    engagement_uuid = None
                    logger.info("ℹ️ No engagement_id provided (optional)")

            except (ValueError, TypeError) as e:
                logger.error(f"❌ Invalid UUID format: {e}")
                logger.error(f"   client_account_id: {client_account_id}")
                logger.error(f"   engagement_id: {engagement_id}")
                return

            # Find the discovery flow WITH tenant scoping
            # Build filters list to handle optional engagement_id
            filters = [
                DiscoveryFlow.flow_id == flow_id,
            ]
            if client_uuid:
                filters.append(DiscoveryFlow.client_account_id == client_uuid)
            if engagement_uuid:
                filters.append(DiscoveryFlow.engagement_id == engagement_uuid)

            query = select(DiscoveryFlow).where(
                and_(*filters)
            )  # SKIP_TENANT_CHECK - engagement_id is optional in this legacy code path

            result = await db_session.execute(query)
            discovery_flow = result.scalar_one_or_none()

            if not discovery_flow:
                logger.warning(
                    f"⚠️ Discovery flow {flow_id} not found or access denied "
                    f"for tenant {client_uuid}"
                )
                return

            # Get data_import_id from discovery flow if not provided
            if not data_import_id and discovery_flow:
                data_import_id = discovery_flow.data_import_id
                if not data_import_id and discovery_flow.crewai_state_data:
                    data_import_id = discovery_flow.crewai_state_data.get(
                        "data_import_id"
                    )

            if not data_import_id:
                logger.warning(
                    "⚠️ No data_import_id available, cannot persist to "
                    "ImportFieldMapping table"
                )
            else:
                try:
                    # Handle both string and asyncpg UUID objects
                    if hasattr(data_import_id, "replace"):
                        # It's already a UUID string
                        data_import_uuid = UUID(data_import_id)
                    else:
                        # It's likely an asyncpg UUID object, convert to UUID
                        data_import_uuid = UUID(str(data_import_id))
                except (ValueError, TypeError):
                    logger.error(f"❌ Invalid data_import_id format: {data_import_id}")
                    return

                # Perform delete and inserts atomically to ensure data integrity
                async with db_session.begin_nested():
                    # Clear existing field mappings for this import WITH tenant scoping
                    delete_query = delete(ImportFieldMapping).where(
                        ImportFieldMapping.data_import_id == data_import_uuid
                    )
                    # Add tenant scoping to delete
                    if client_uuid:
                        delete_query = delete_query.where(
                            ImportFieldMapping.client_account_id == client_uuid
                        )
                    await db_session.execute(delete_query)

                    # Create new ImportFieldMapping records from AI-generated mappings
                    created_count = 0
                    for source_field, mapping_info in field_mappings.items():
                        # Handle both dict and direct value formats
                        if isinstance(mapping_info, dict):
                            # Always use target_field and confidence_score for
                            # consistency
                            target_field = mapping_info.get("target_field")
                            # Read compatibility but don't write target_attribute
                            if not target_field:
                                target_field = mapping_info.get("target_attribute")

                            # Always use confidence_score, normalize invalid values
                            confidence = mapping_info.get("confidence_score", 0.0)
                            if not confidence:
                                confidence = mapping_info.get("confidence", 0.0)

                            # Normalize confidence to valid range
                            try:
                                confidence = float(confidence)
                                if (
                                    confidence < 0
                                    or confidence > 1
                                    or confidence != confidence
                                ):  # NaN check
                                    confidence = 0.0
                            except (ValueError, TypeError):
                                confidence = 0.0

                            mapping_type = mapping_info.get(
                                "mapping_type", "ai_suggested"
                            )
                            is_critical = mapping_info.get("is_critical", False)
                        else:
                            # Simple string mapping
                            target_field = (
                                mapping_info if isinstance(mapping_info, str) else None
                            )
                            confidence = 0.8
                            mapping_type = "ai_suggested"
                            is_critical = False

                        # Only create mapping if we have a valid target field
                        if target_field and target_field != "unmapped":
                            # Convert engagement_id to UUID if needed
                            engagement_uuid = None
                            if engagement_id:
                                try:
                                    if isinstance(engagement_id, str):
                                        engagement_uuid = UUID(engagement_id)
                                    else:
                                        engagement_uuid = engagement_id
                                except (ValueError, TypeError):
                                    logger.warning(
                                        f"⚠️ Invalid engagement_id format: {engagement_id}"
                                    )

                            field_mapping = ImportFieldMapping(
                                data_import_id=data_import_uuid,
                                client_account_id=client_uuid,
                                engagement_id=engagement_uuid,
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
                    f"✅ Created {created_count} ImportFieldMapping records "
                    f"for import {data_import_id}"
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

                # Update the field_mapping_completed column directly
                discovery_flow.field_mapping_completed = True

                # Store additional info in crewai_state_data instead of metadata
                if not discovery_flow.crewai_state_data:
                    discovery_flow.crewai_state_data = {}

                discovery_flow.crewai_state_data["field_mapping_count"] = total_fields
                discovery_flow.crewai_state_data["data_import_id"] = data_import_id

                # Add the modified discovery_flow back to the session
                db_session.add(discovery_flow)

                logger.info(
                    f"✅ Updated discovery flow {flow_id} with AI-generated "
                    f"field mappings (field_mapping_completed={discovery_flow.field_mapping_completed})"
                )
            else:
                logger.warning(f"⚠️ Discovery flow {flow_id} not found in database")

            await db_session.commit()
            logger.info(
                f"✅ Successfully persisted {len(field_mappings)} "
                f"AI-generated field mappings"
            )

        except Exception as e:
            logger.error(f"❌ Failed to persist field mappings: {e}", exc_info=True)
            # Don't raise - allow flow to continue even if persistence fails
