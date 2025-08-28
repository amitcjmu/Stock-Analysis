"""
Phase management operations.

Handles phase completion status updates and progress tracking.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, update

from app.models.discovery_flow import DiscoveryFlow
from .flow_base import FlowCommandsBase


# 🔧 CC FIX: Import UUID conversion utility for JSON serialization safety
def convert_uuids_to_str(obj: Any) -> Any:
    """
    Recursively convert UUID objects to strings for JSON serialization.
    🔧 CC FIX: Prevents 'Object of type UUID is not JSON serializable' errors
    """
    import uuid

    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_uuids_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_uuids_to_str(item) for item in obj]
    return obj


logger = logging.getLogger(__name__)


class FlowPhaseManagementCommands(FlowCommandsBase):
    """Handles phase management operations"""

    async def update_phase_completion(  # noqa: C901
        self,
        flow_id: str,
        phase: str,
        data: Optional[Dict[str, Any]] = None,
        completed: bool = False,
        agent_insights: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[DiscoveryFlow]:
        """Update phase completion status and data"""

        # Ensure flow_id is UUID
        flow_uuid = self._ensure_uuid(flow_id)

        # Map phase names to boolean fields
        phase_field_map = {
            "data_import": "data_import_completed",
            "field_mapping": "field_mapping_completed",
            "data_cleansing": "data_cleansing_completed",
            "asset_inventory": "asset_inventory_completed",
            "dependency_analysis": "dependency_analysis_completed",
            "tech_debt_assessment": "tech_debt_assessment_completed",
        }

        # Prepare update values
        update_values = {}

        # Update phase completion boolean
        if phase in phase_field_map and completed:
            update_values[phase_field_map[phase]] = True

        # Update current phase
        update_values["current_phase"] = phase
        update_values["updated_at"] = datetime.utcnow()

        # Update phase and agent state data
        if data or agent_insights:
            # Get existing flow to merge state data
            existing_flow = await self.flow_queries.get_by_flow_id(flow_id)
            if existing_flow:
                state_data = existing_flow.crewai_state_data or {}

                # Update phase data
                if data:
                    state_data[phase] = data

                # Merge agent insights
                if agent_insights:
                    existing_insights = state_data.get("agent_insights", [])
                    existing_insights.extend(agent_insights)
                    state_data["agent_insights"] = existing_insights

                # Extract processing statistics to root level
                processing_fields = [
                    "records_processed",
                    "records_total",
                    "records_valid",
                    "records_failed",
                ]
                for field in processing_fields:
                    if data and field in data:
                        state_data[field] = data[field]

                # 🔧 CC FIX: Convert UUIDs to strings before storing in JSON field
                update_values["crewai_state_data"] = convert_uuids_to_str(state_data)

        # Calculate progress
        progress = await self._calculate_progress(flow_id, phase, completed)
        update_values["progress_percentage"] = progress

        # Execute update
        stmt = (
            update(DiscoveryFlow)
            .where(
                and_(
                    DiscoveryFlow.flow_id == flow_uuid,
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                )
            )
            .values(**update_values)
        )

        await self.db.execute(stmt)
        await self.db.commit()

        # Invalidate cache after update
        updated_flow = await self.flow_queries.get_by_flow_id(flow_id)
        if updated_flow:
            await self._invalidate_flow_cache(updated_flow)

        # CC: Add enrichment calls to master flow record after phase completion
        if completed and updated_flow:
            try:
                from app.repositories.crewai_flow_state_extensions_repository import (
                    CrewAIFlowStateExtensionsRepository,
                )

                master_repo = CrewAIFlowStateExtensionsRepository(
                    db=self.db,
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    user_id=None,  # No user context available in repository
                )

                # Add phase transition for completion
                await master_repo.add_phase_transition(
                    flow_id=flow_id,
                    phase=phase,
                    status="completed",
                    metadata={
                        "progress_percentage": progress,
                        "records_processed": (
                            data.get("records_processed") if data else None
                        ),
                        "has_agent_insights": bool(agent_insights),
                    },
                )

                # Record agent collaboration if insights were provided
                if agent_insights:
                    for insight in agent_insights:
                        await master_repo.append_agent_collaboration(
                            flow_id=flow_id,
                            entry={
                                "phase": phase,
                                "agent_insight": insight,
                                "insight_type": insight.get("type", "phase_completion"),
                            },
                        )

                logger.debug(
                    f"✅ [ENRICHMENT] Added master flow enrichment for phase {phase} completion"
                )

            except Exception as enrichment_error:
                logger.warning(
                    f"⚠️ [ENRICHMENT] Failed to add master flow enrichment: {enrichment_error}"
                )
                # Don't fail the main operation if enrichment fails

        # 🔧 CC FIX: Check if all required phases are complete and auto-complete flow
        if updated_flow and completed:
            try:
                await self._check_and_complete_flow_if_ready(updated_flow)
            except Exception as completion_error:
                logger.error(
                    f"❌ Error during flow completion check for {flow_id}: {completion_error}"
                )
                # Don't fail the main operation if completion check fails

        return updated_flow

    async def _calculate_progress(
        self, flow_id: str, current_phase: str, phase_completed: bool
    ) -> float:
        """Calculate overall progress percentage"""

        # Get current flow state
        flow = await self.flow_queries.get_by_flow_id(flow_id)
        if not flow:
            return 0.0

        # Phase weights
        phase_weights = {
            "data_import": 16.7,
            "field_mapping": 16.7,
            "data_cleansing": 16.6,
            "asset_inventory": 16.7,
            "dependency_analysis": 16.7,
            "tech_debt_assessment": 16.6,
        }

        # Calculate total progress
        total_progress = 0.0

        # Add progress for completed phases
        if flow.data_import_completed:
            total_progress += phase_weights["data_import"]
        if flow.field_mapping_completed:
            total_progress += phase_weights["field_mapping"]
        if flow.data_cleansing_completed:
            total_progress += phase_weights["data_cleansing"]
        if flow.asset_inventory_completed:
            total_progress += phase_weights["asset_inventory"]
        if flow.dependency_analysis_completed:
            total_progress += phase_weights["dependency_analysis"]
        if flow.tech_debt_assessment_completed:
            total_progress += phase_weights["tech_debt_assessment"]

        # If current phase is completed but not yet reflected in booleans
        if phase_completed and current_phase in phase_weights:
            phase_field_map = {
                "data_import": flow.data_import_completed,
                "field_mapping": flow.field_mapping_completed,
                "data_cleansing": flow.data_cleansing_completed,
                "asset_inventory": flow.asset_inventory_completed,
                "dependency_analysis": flow.dependency_analysis_completed,
                "tech_debt_assessment": flow.tech_debt_assessment_completed,
            }

            if not phase_field_map.get(current_phase, False):
                total_progress += phase_weights[current_phase]

        return min(100.0, round(total_progress, 1))

    async def _check_and_complete_flow_if_ready(self, flow: DiscoveryFlow) -> bool:
        """
        Check if all required phases are complete and automatically complete the flow.

        Args:
            flow: The discovery flow to check

        Returns:
            True if flow was completed, False otherwise
        """
        try:
            # Define the required phases for completion (all 6 phases per spec)
            required_phases = {
                "data_import": flow.data_import_completed,
                "field_mapping": flow.field_mapping_completed,
                "data_cleansing": flow.data_cleansing_completed,
                "asset_inventory": flow.asset_inventory_completed,
                "dependency_analysis": flow.dependency_analysis_completed,
                "tech_debt_assessment": flow.tech_debt_assessment_completed,
            }

            # Check if all required phases are complete
            all_phases_complete = all(required_phases.values())

            logger.info(
                f"🔍 Flow {flow.flow_id} phase completion status: {required_phases}, "
                f"all_complete={all_phases_complete}, current_status={flow.status}"
            )

            # Only complete if all phases are done and flow is not already complete
            if all_phases_complete and flow.status not in ["complete", "completed"]:
                logger.info(
                    f"🎯 Auto-completing flow {flow.flow_id} - all required phases complete"
                )
                # Import completion commands to avoid circular imports
                from .flow_completion import FlowCompletionCommands

                completion_commands = FlowCompletionCommands(
                    self.db, self.client_account_id, self.engagement_id
                )
                await completion_commands.mark_flow_complete(str(flow.flow_id))
                # Update master flow state separately
                await self._update_master_flow_completion(str(flow.flow_id))
                return True

            return False

        except Exception as e:
            logger.error(
                f"❌ Error checking flow completion readiness for {flow.flow_id}: {e}"
            )
            return False
