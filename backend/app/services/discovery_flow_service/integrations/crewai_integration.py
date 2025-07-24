"""
CrewAI integration service for bridging CrewAI flows with discovery flow database architecture.
"""

import logging
from typing import Any, Dict, List

from app.core.context import RequestContext
from app.models.discovery_flow import DiscoveryFlow
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.flow_manager import FlowManager

logger = logging.getLogger(__name__)


class CrewAIIntegrationService:
    """
    Integration service for bridging CrewAI flows with new database architecture.
    Handles the transition from existing unified flow to new tables.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.flow_manager = FlowManager(db, context)

    async def create_flow_from_crewai(
        self,
        crewai_flow_id: str,
        crewai_state: Dict[str, Any],
        raw_data: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None,
    ) -> DiscoveryFlow:
        """
        Create discovery flow from CrewAI flow initialization.
        Bridges CrewAI flow state with new database architecture.
        """
        try:
            logger.info(f"🔗 Creating discovery flow from CrewAI: {crewai_flow_id}")

            # Extract data import ID for linking
            data_import_id = self._extract_data_import_id(metadata, crewai_state)

            # Create discovery flow using CrewAI Flow ID as single source of truth
            flow = await self.flow_manager.create_discovery_flow(
                flow_id=crewai_flow_id,
                raw_data=raw_data,
                metadata=metadata,
                data_import_id=data_import_id,
                user_id=str(self.context.user_id),
            )

            # Store CrewAI flow state for persistence integration
            if crewai_state:
                await self._store_crewai_state(crewai_flow_id, crewai_state)

            logger.info(f"✅ Discovery flow created from CrewAI: {crewai_flow_id}")
            return flow

        except Exception as e:
            logger.error(f"❌ Failed to create flow from CrewAI {crewai_flow_id}: {e}")
            raise

    async def sync_crewai_state(
        self, flow_id: str, crewai_state: Dict[str, Any], phase: str = None
    ) -> DiscoveryFlow:
        """
        Sync CrewAI flow state with discovery flow database.
        Maintains hybrid persistence as described in the implementation plan.
        """
        try:
            logger.info(f"🔄 Syncing CrewAI state for flow: {flow_id}")

            current_phase = phase or crewai_state.get("current_phase", "data_import")

            # Extract phase-specific data from CrewAI state
            phase_data = self._extract_phase_data(crewai_state)

            # Update discovery flow with CrewAI state
            flow = await self.flow_manager.update_phase_completion(
                flow_id=flow_id,
                phase=current_phase,
                phase_data=phase_data,
                crew_status=crewai_state.get("crew_status", {}),
                agent_insights=crewai_state.get("agent_insights", []),
            )

            logger.info(f"✅ CrewAI state synced for flow: {flow_id}")
            return flow

        except Exception as e:
            logger.error(f"❌ Failed to sync CrewAI state for {flow_id}: {e}")
            raise

    async def export_flow_to_crewai(self, flow_id: str) -> Dict[str, Any]:
        """
        Export discovery flow data back to CrewAI format.
        Useful for CrewAI flow resumption and state reconstruction.
        """
        try:
            logger.info(f"📤 Exporting flow to CrewAI format: {flow_id}")

            # Get flow and assets
            flow = await self.flow_manager.get_flow_by_id(flow_id)
            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")

            # Build CrewAI compatible state
            crewai_export = {
                "flow_id": flow.flow_id,
                "data_import_id": flow.data_import_id,
                "current_phase": flow.get_next_phase(),
                "flow_status": flow.status,
                "progress_percentage": flow.progress_percentage,
                "phase_completion": {
                    "data_import": flow.data_import_completed,
                    "attribute_mapping": flow.attribute_mapping_completed,
                    "data_cleansing": flow.data_cleansing_completed,
                    "inventory": flow.inventory_completed,
                    "dependencies": flow.dependencies_completed,
                    "tech_debt": flow.tech_debt_completed,
                },
                "raw_data": flow.raw_data or [],
                "metadata": flow.metadata or {},
                "phase_data": self._extract_phase_data_for_export(flow),
                "crew_status": (
                    flow.crewai_state_data.get("crew_status", {})
                    if flow.crewai_state_data
                    else {}
                ),
                "agent_insights": (
                    flow.crewai_state_data.get("agent_insights", [])
                    if flow.crewai_state_data
                    else []
                ),
                "timestamps": {
                    "created_at": (
                        flow.created_at.isoformat() if flow.created_at else None
                    ),
                    "updated_at": (
                        flow.updated_at.isoformat() if flow.updated_at else None
                    ),
                    "completed_at": (
                        flow.completed_at.isoformat() if flow.completed_at else None
                    ),
                },
            }

            logger.info(f"✅ Flow exported to CrewAI format: {flow_id}")
            return crewai_export

        except Exception as e:
            logger.error(f"❌ Failed to export flow to CrewAI format {flow_id}: {e}")
            raise

    async def validate_crewai_state_sync(
        self, flow_id: str, crewai_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate that CrewAI state is properly synced with discovery flow database.
        Returns validation report with any discrepancies.
        """
        try:
            logger.info(f"🔍 Validating CrewAI state sync for flow: {flow_id}")

            # Get current flow state
            flow = await self.flow_manager.get_flow_by_id(flow_id)
            if not flow:
                return {
                    "is_synced": False,
                    "error": f"Flow not found in database: {flow_id}",
                    "discrepancies": [],
                }

            discrepancies = []

            # Check flow ID consistency
            crewai_flow_id = crewai_state.get("flow_id")
            if crewai_flow_id and crewai_flow_id != flow.flow_id:
                discrepancies.append(
                    {
                        "field": "flow_id",
                        "database_value": flow.flow_id,
                        "crewai_value": crewai_flow_id,
                        "severity": "high",
                    }
                )

            # Check phase completion consistency
            crewai_phases = crewai_state.get("phase_completion", {})
            db_phases = {
                "data_import": flow.data_import_completed,
                "attribute_mapping": flow.attribute_mapping_completed,
                "data_cleansing": flow.data_cleansing_completed,
                "inventory": flow.inventory_completed,
                "dependencies": flow.dependencies_completed,
                "tech_debt": flow.tech_debt_completed,
            }

            for phase, db_status in db_phases.items():
                crewai_status = crewai_phases.get(phase, False)
                if db_status != crewai_status:
                    discrepancies.append(
                        {
                            "field": f"phase_completion.{phase}",
                            "database_value": db_status,
                            "crewai_value": crewai_status,
                            "severity": "medium",
                        }
                    )

            # Check progress consistency
            crewai_progress = crewai_state.get("progress_percentage", 0)
            db_progress = flow.progress_percentage or 0
            if abs(crewai_progress - db_progress) > 5:  # Allow 5% tolerance
                discrepancies.append(
                    {
                        "field": "progress_percentage",
                        "database_value": db_progress,
                        "crewai_value": crewai_progress,
                        "severity": "low",
                    }
                )

            validation_result = {
                "is_synced": len(discrepancies) == 0,
                "discrepancies": discrepancies,
                "sync_quality": (
                    "excellent"
                    if len(discrepancies) == 0
                    else (
                        "good"
                        if len([d for d in discrepancies if d["severity"] == "high"])
                        == 0
                        else "poor"
                    )
                ),
                "last_database_update": (
                    flow.updated_at.isoformat() if flow.updated_at else None
                ),
                "validation_timestamp": (
                    logger.info.__self__.time()
                    if hasattr(logger.info.__self__, "time")
                    else "unknown"
                ),
            }

            logger.info(
                f"✅ CrewAI state validation completed for flow: {flow_id} - Synced: {validation_result['is_synced']}"
            )
            return validation_result

        except Exception as e:
            logger.error(f"❌ Failed to validate CrewAI state sync for {flow_id}: {e}")
            raise

    def _extract_data_import_id(
        self, metadata: Dict[str, Any], crewai_state: Dict[str, Any]
    ) -> str:
        """Extract data import ID from metadata or CrewAI state"""

        if metadata and "data_import_id" in metadata:
            return metadata["data_import_id"]
        elif crewai_state and "data_import_id" in crewai_state:
            return crewai_state["data_import_id"]

        return None

    def _extract_phase_data(self, crewai_state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract phase-specific data from CrewAI state"""

        phase_data = {}

        # Map CrewAI state fields to phase data
        field_mappings = {
            "field_mappings": "field_mappings",
            "cleaned_data": "cleaned_data",
            "asset_inventory": "asset_inventory",
            "dependencies": "dependencies",
            "technical_debt": "technical_debt",
            "raw_data": "raw_data",
        }

        for crewai_field, phase_field in field_mappings.items():
            if crewai_field in crewai_state:
                phase_data[phase_field] = crewai_state[crewai_field]

        # Add CrewAI state as metadata
        phase_data["crewai_state"] = crewai_state

        return phase_data

    async def _store_crewai_state(
        self, flow_id: str, crewai_state: Dict[str, Any]
    ) -> None:
        """Store CrewAI state in discovery flow"""

        try:
            # Update flow with CrewAI state information
            await self.flow_manager.flow_repo.update_phase_completion(
                flow_id=flow_id,
                phase="data_import",
                data={"crewai_state": crewai_state},
                crew_status=crewai_state.get("crew_status", {}),
                agent_insights=crewai_state.get("agent_insights", []),
            )

            logger.info(f"✅ CrewAI state stored for flow: {flow_id}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to store CrewAI state for {flow_id}: {e}")
            # Non-critical error, don't raise

    def _extract_phase_data_for_export(self, flow: DiscoveryFlow) -> Dict[str, Any]:
        """Extract phase data from flow for CrewAI export"""

        phase_data = {}

        # Extract from stored phase data
        if hasattr(flow, "data_import_data") and flow.data_import_data:
            phase_data.update(flow.data_import_data)

        if hasattr(flow, "attribute_mapping_data") and flow.attribute_mapping_data:
            phase_data.update(flow.attribute_mapping_data)

        if hasattr(flow, "data_cleansing_data") and flow.data_cleansing_data:
            phase_data.update(flow.data_cleansing_data)

        if hasattr(flow, "inventory_data") and flow.inventory_data:
            phase_data.update(flow.inventory_data)

        if hasattr(flow, "dependencies_data") and flow.dependencies_data:
            phase_data.update(flow.dependencies_data)

        if hasattr(flow, "tech_debt_data") and flow.tech_debt_data:
            phase_data.update(flow.tech_debt_data)

        # Add raw data if available
        if flow.raw_data:
            phase_data["raw_data"] = flow.raw_data

        return phase_data
