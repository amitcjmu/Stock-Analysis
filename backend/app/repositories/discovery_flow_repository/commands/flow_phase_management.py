"""
Phase management operations.

Handles phase completion status updates and progress tracking.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, update

from app.core.utils.uuid_helpers import convert_uuids_to_str
from app.models.discovery_flow import DiscoveryFlow
from .flow_base import FlowCommandsBase


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

        # Map phase names to boolean fields (Discovery flow phases only)
        # CC FIX: Removed tech_debt_assessment - it belongs to Collection flow
        phase_field_map = {
            "data_import": "data_import_completed",
            "field_mapping": "field_mapping_completed",
            "data_cleansing": "data_cleansing_completed",
            "asset_inventory": "asset_inventory_completed",
            "dependency_analysis": "dependency_analysis_completed",
        }

        # Prepare update values
        update_values: Dict[str, Any] = {}

        # Update phase completion boolean
        if phase in phase_field_map and completed:
            update_values[phase_field_map[phase]] = True

        # Update current phase
        update_values["current_phase"] = phase
        update_values["updated_at"] = datetime.utcnow()

        # CC FIX: Update status field per ADR-012 (Master Flow lifecycle only)
        # Status transitions: initialized → running (NOT phase-based statuses)
        # Phase tracking uses current_phase field and {phase}_completed booleans
        current_status = await self._get_current_flow_status(flow_id)
        new_status = self._determine_status_from_phase(phase, completed, current_status)
        if new_status != current_status:
            update_values["status"] = new_status
            logger.info(
                f"🔄 Status transition for flow {flow_id}: {current_status} → {new_status}"
            )

        # 🔧 CC FIX: Update phases_completed field with list of completed phases
        completed_phases = await self._get_completed_phases_list(
            flow_id, phase, completed
        )
        update_values["phases_completed"] = completed_phases

        # Update phase and agent state data
        if data or agent_insights:
            # Get existing flow to merge state data
            existing_flow = await self.flow_queries.get_by_flow_id(flow_id)
            if existing_flow:
                state_data: Dict[str, Any] = existing_flow.crewai_state_data or {}

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

        # Phase weights (Discovery flow phases only)
        # CC FIX: Removed tech_debt_assessment - it belongs to Collection flow
        phase_weights = {
            "data_import": 20.0,
            "field_mapping": 20.0,
            "data_cleansing": 20.0,
            "asset_inventory": 20.0,
            "dependency_analysis": 20.0,
        }

        # Calculate total progress
        total_progress = 0.0

        # Add progress for completed phases (Discovery flow only)
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

        # If current phase is completed but not yet reflected in booleans
        if phase_completed and current_phase in phase_weights:
            phase_field_map = {
                "data_import": flow.data_import_completed,
                "field_mapping": flow.field_mapping_completed,
                "data_cleansing": flow.data_cleansing_completed,
                "asset_inventory": flow.asset_inventory_completed,
                "dependency_analysis": flow.dependency_analysis_completed,
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
            # Define the required phases for completion (Discovery flow phases only)
            # CC FIX: Removed tech_debt_assessment - it belongs to Collection flow, not Discovery flow
            required_phases = {
                "data_import": flow.data_import_completed,
                "field_mapping": flow.field_mapping_completed,
                "data_cleansing": flow.data_cleansing_completed,
                "asset_inventory": flow.asset_inventory_completed,
                "dependency_analysis": flow.dependency_analysis_completed,
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

                # 🔧 CC FIX: Explicitly update status to "completed" here
                # This ensures the status transitions properly to completed when all phases are done
                from sqlalchemy import update as sql_update

                stmt = (
                    sql_update(DiscoveryFlow)
                    .where(
                        and_(
                            DiscoveryFlow.flow_id
                            == self._ensure_uuid(str(flow.flow_id)),
                            DiscoveryFlow.client_account_id == self.client_account_id,
                            DiscoveryFlow.engagement_id == self.engagement_id,
                        )
                    )
                    .values(
                        status="completed",
                        progress_percentage=100.0,
                        updated_at=datetime.utcnow(),
                    )
                )
                await self.db.execute(stmt)
                # 🔧 CC FIX: Remove duplicate commit - transaction boundary managed by caller
                # This ensures atomicity with the parent update_phase_completion transaction
                # await self.db.commit()  # REMOVED to prevent double commit

                # Update master flow state separately
                await self._update_master_flow_completion(str(flow.flow_id))
                return True

            return False

        except Exception as e:
            logger.error(
                f"❌ Error checking flow completion readiness for {flow.flow_id}: {e}"
            )
            return False

    async def _get_current_flow_status(self, flow_id: str) -> str:
        """Get the current status of the flow"""
        flow = await self.flow_queries.get_by_flow_id(flow_id)
        return str(flow.status) if flow and flow.status else "initialized"

    def _determine_status_from_phase(
        self, phase: str, completed: bool, current_status: str
    ) -> str:
        """
        CC FIX: Per ADR-012, status reflects Master Flow lifecycle, NOT phases.

        Master Flow lifecycle statuses (ADR-012):
        - initialized: Flow created but not started
        - running: Flow actively executing phases
        - paused: User-initiated pause (e.g., waiting for conflict resolution)
        - completed: All phases finished
        - failed: Flow encountered unrecoverable error
        - deleted: Flow marked for deletion

        Phase tracking is handled via:
        - current_phase field (string): which phase we're in
        - {phase}_completed boolean flags: phase completion status
        - assessment_ready boolean flag: ready for assessment handoff

        Phase-based statuses (assessment_ready, data_gathering, planning, discovery)
        do NOT belong in the status field and violate architectural separation.
        """
        # Terminal states - never change these
        if current_status in ["completed", "complete", "failed", "deleted"]:
            return current_status

        # User-initiated states - preserve unless phase triggers change
        if current_status == "paused":
            # Keep paused unless explicitly transitioning
            return current_status

        # Transition from initialized to running when first phase starts
        if current_status == "initialized":
            return "running"

        # For all other cases (including "active"), keep as running during phase execution
        # The "completed" transition happens in _check_and_complete_flow_if_ready()
        return "running"

    async def _get_completed_phases_list(
        self, flow_id: str, current_phase: str, phase_completed: bool
    ) -> List[str]:
        """Get list of completed phases for the phases_completed field"""
        flow = await self.flow_queries.get_by_flow_id(flow_id)
        if not flow:
            return []

        completed_phases = []

        # Check each phase completion boolean
        if flow.data_import_completed:
            completed_phases.append("data_import")
        if flow.field_mapping_completed:
            completed_phases.append("field_mapping")
        if flow.data_cleansing_completed:
            completed_phases.append("data_cleansing")
        if flow.asset_inventory_completed:
            completed_phases.append("asset_inventory")
        if flow.dependency_analysis_completed:
            completed_phases.append("dependency_analysis")

        # Add current phase if it's being marked as completed
        if phase_completed and current_phase not in completed_phases:
            completed_phases.append(current_phase)

        return completed_phases
