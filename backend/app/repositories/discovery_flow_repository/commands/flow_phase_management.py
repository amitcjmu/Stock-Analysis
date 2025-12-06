"""Phase management operations - refactored per Issue #108."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, update

from app.core.utils.uuid_helpers import convert_uuids_to_str
from app.models.discovery_flow import DiscoveryFlow
from .flow_base import FlowCommandsBase

logger = logging.getLogger(__name__)

# Phase field mapping (Discovery flow phases only)
PHASE_FIELD_MAP: Dict[str, str] = {
    "data_import": "data_import_completed",
    "field_mapping": "field_mapping_completed",
    "data_cleansing": "data_cleansing_completed",
    "asset_inventory": "asset_inventory_completed",
    "dependency_analysis": "dependency_analysis_completed",
}

# Phase weights for progress (Discovery v3.0.0 - 5 phases @ 20% each)
PHASE_WEIGHTS: Dict[str, float] = {
    "data_import": 20.0,
    "data_validation": 20.0,
    "field_mapping": 20.0,
    "data_cleansing": 20.0,
    "asset_inventory": 20.0,
}

# Processing statistics fields to extract to root level
PROCESSING_FIELDS: List[str] = [
    "records_processed",
    "records_total",
    "records_valid",
    "records_failed",
]


class FlowPhaseManagementCommands(FlowCommandsBase):
    """Handles phase management operations."""

    async def update_phase_completion(
        self,
        flow_id: str,
        phase: str,
        data: Optional[Dict[str, Any]] = None,
        completed: bool = False,
        agent_insights: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[DiscoveryFlow]:
        """Update phase completion status and data."""
        flow_uuid = self._ensure_uuid(flow_id)

        # Prepare base update values
        update_values = await self._prepare_base_update_values(
            flow_id, phase, completed
        )

        # Merge state data if provided
        if data or agent_insights:
            state_data = await self._merge_state_data(
                flow_id, phase, data, agent_insights
            )
            if state_data is not None:
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

        # Get updated flow and invalidate cache
        updated_flow = await self.flow_queries.get_by_flow_id(flow_id)
        if updated_flow:
            await self._invalidate_flow_cache(updated_flow)

        # Add master flow enrichment and check for auto-completion
        if completed and updated_flow:
            await self._add_master_flow_enrichment(
                flow_id, phase, progress, data, agent_insights
            )
            try:
                await self._check_and_complete_flow_if_ready(updated_flow)
            except Exception as e:
                logger.error(f"Error during flow completion check: {e}")

        return updated_flow

    async def _prepare_base_update_values(
        self, flow_id: str, phase: str, completed: bool
    ) -> Dict[str, Any]:
        """Prepare base update values for a phase update."""
        update_values: Dict[str, Any] = {
            "current_phase": phase,
            "updated_at": datetime.utcnow(),
        }

        if phase in PHASE_FIELD_MAP and completed:
            update_values[PHASE_FIELD_MAP[phase]] = True

        # Handle status transition per ADR-012
        current_status = await self._get_current_flow_status(flow_id)
        new_status = self._determine_status_from_phase(phase, completed, current_status)
        if new_status != current_status:
            update_values["status"] = new_status
            logger.info(f"Status transition: {current_status} -> {new_status}")

        update_values["phases_completed"] = await self._get_completed_phases_list(
            flow_id, phase, completed
        )
        return update_values

    async def _merge_state_data(
        self,
        flow_id: str,
        phase: str,
        data: Optional[Dict[str, Any]],
        agent_insights: Optional[List[Dict[str, Any]]],
    ) -> Optional[Dict[str, Any]]:
        """Merge phase data and agent insights into existing state data."""
        existing_flow = await self.flow_queries.get_by_flow_id(flow_id)
        if not existing_flow:
            return None

        state_data: Dict[str, Any] = existing_flow.crewai_state_data or {}

        if data:
            state_data[phase] = data
            for field in PROCESSING_FIELDS:
                if field in data:
                    state_data[field] = data[field]

        if agent_insights:
            existing_insights = state_data.get("agent_insights", [])
            existing_insights.extend(agent_insights)
            state_data["agent_insights"] = existing_insights

        return state_data

    async def _add_master_flow_enrichment(
        self,
        flow_id: str,
        phase: str,
        progress: float,
        data: Optional[Dict[str, Any]],
        agent_insights: Optional[List[Dict[str, Any]]],
    ) -> None:
        """Add enrichment data to the master flow record after phase completion."""
        try:
            from app.repositories.crewai_flow_state_extensions_repository import (
                CrewAIFlowStateExtensionsRepository,
            )

            master_repo = CrewAIFlowStateExtensionsRepository(
                db=self.db,
                client_account_id=self.client_account_id,
                engagement_id=self.engagement_id,
                user_id=None,
            )

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

            logger.debug(f"Added master flow enrichment for phase {phase}")
        except Exception as e:
            logger.warning(f"Failed to add master flow enrichment: {e}")

    async def _calculate_progress(
        self, flow_id: str, current_phase: str, phase_completed: bool
    ) -> float:
        """Calculate overall progress percentage."""
        flow = await self.flow_queries.get_by_flow_id(flow_id)
        if not flow:
            return 0.0

        total = 0.0
        if flow.data_import_completed:
            total += PHASE_WEIGHTS["data_import"]
        if flow.data_validation_completed:
            total += PHASE_WEIGHTS["data_validation"]
        if flow.field_mapping_completed:
            total += PHASE_WEIGHTS["field_mapping"]
        if flow.data_cleansing_completed:
            total += PHASE_WEIGHTS["data_cleansing"]
        if flow.asset_inventory_completed:
            total += PHASE_WEIGHTS["asset_inventory"]

        # Add current phase if completed but not yet reflected
        if phase_completed and current_phase in PHASE_WEIGHTS:
            phase_map = {
                "data_import": flow.data_import_completed,
                "data_validation": flow.data_validation_completed,
                "field_mapping": flow.field_mapping_completed,
                "data_cleansing": flow.data_cleansing_completed,
                "asset_inventory": flow.asset_inventory_completed,
            }
            if not phase_map.get(current_phase, False):
                total += PHASE_WEIGHTS[current_phase]

        return min(100.0, round(total, 1))

    async def _check_and_complete_flow_if_ready(self, flow: DiscoveryFlow) -> bool:
        """Check if all required phases are complete and auto-complete the flow."""
        try:
            required_phases = {
                "data_import": flow.data_import_completed,
                "data_validation": flow.data_validation_completed,
                "field_mapping": flow.field_mapping_completed,
                "data_cleansing": flow.data_cleansing_completed,
                "asset_inventory": flow.asset_inventory_completed,
            }
            all_complete = all(required_phases.values())

            logger.info(
                f"Flow {flow.flow_id} phases: {required_phases}, "
                f"all_complete={all_complete}, status={flow.status}"
            )

            if all_complete and flow.status not in ["complete", "completed"]:
                await self._execute_flow_completion(flow)
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking flow completion: {e}")
            return False

    async def _execute_flow_completion(self, flow: DiscoveryFlow) -> None:
        """Execute the flow completion process."""
        logger.info(f"Auto-completing flow {flow.flow_id}")

        from .flow_completion import FlowCompletionCommands
        from sqlalchemy import update as sql_update

        completion_commands = FlowCompletionCommands(
            self.db, self.client_account_id, self.engagement_id
        )
        await completion_commands.mark_flow_complete(str(flow.flow_id))

        stmt = (
            sql_update(DiscoveryFlow)
            .where(
                and_(
                    DiscoveryFlow.flow_id == self._ensure_uuid(str(flow.flow_id)),
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
        await self._update_master_flow_completion(str(flow.flow_id))

    async def _get_current_flow_status(self, flow_id: str) -> str:
        """Get the current status of the flow."""
        flow = await self.flow_queries.get_by_flow_id(flow_id)
        return str(flow.status) if flow and flow.status else "initialized"

    def _determine_status_from_phase(
        self, phase: str, completed: bool, current_status: str
    ) -> str:
        """Determine the new status based on phase update (per ADR-012)."""
        # Terminal/user-initiated states - never change
        if current_status in ["completed", "complete", "failed", "deleted", "paused"]:
            return current_status
        # Transition from initialized to running when first phase starts
        if current_status == "initialized":
            return "running"
        return "running"

    async def _get_completed_phases_list(
        self, flow_id: str, current_phase: str, phase_completed: bool
    ) -> List[str]:
        """Get list of completed phases for the phases_completed field."""
        flow = await self.flow_queries.get_by_flow_id(flow_id)
        if not flow:
            return []

        completed_phases = []
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

        if phase_completed and current_phase not in completed_phases:
            completed_phases.append(current_phase)

        return completed_phases
