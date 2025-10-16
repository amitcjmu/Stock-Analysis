"""
Flow Handler Validation Operations
Handles flow validation and active flow operations
"""

import logging
from typing import Any, Dict, List

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

logger = logging.getLogger(__name__)


class FlowHandlerValidation:
    """Handles flow validation operations"""

    def __init__(self, context: RequestContext):
        self.context = context

    async def validate_phase_completion(
        self, flow_id: str, phase: str
    ) -> Dict[str, Any]:
        """Validate if a phase is properly completed"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id),
                )

                flow = await flow_repo.get_by_flow_id(flow_id)
                if not flow:
                    return {
                        "status": "error",
                        "error": "Flow not found",
                        "is_complete": False,
                    }

                # Check phase completion based on phase name
                # Per ADR-027: Discovery v3.0.0 has only 5 phases
                phase_completion_map = {
                    "data_import": flow.data_import_completed,
                    "data_validation": flow.data_validation_completed,
                    "field_mapping": flow.field_mapping_completed,
                    "data_cleansing": flow.data_cleansing_completed,
                    "asset_inventory": flow.asset_inventory_completed,
                }

                is_complete = phase_completion_map.get(phase, False)

                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "phase": phase,
                    "is_complete": is_complete,
                    "completion_details": {
                        "progress_percentage": flow.progress_percentage,
                        "last_updated": (
                            flow.updated_at.isoformat() if flow.updated_at else None
                        ),
                    },
                }

            except Exception as e:
                logger.error(f"Error validating phase completion: {e}")
                return {"status": "error", "error": str(e), "is_complete": False}

    async def get_active_flows(self) -> List[Dict[str, Any]]:
        """Get all active discovery flows"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id),
                )

                flows = await flow_repo.get_active_flows()

                flow_list = []
                for flow in flows:
                    flow_data = {
                        "flow_id": str(flow.flow_id),
                        "status": flow.status,
                        "current_phase": flow.get_current_phase(),
                        "next_phase": flow.get_next_phase(),
                        "progress": flow.progress_percentage,
                        "is_complete": flow.is_complete(),
                        "created_at": (
                            flow.created_at.isoformat() if flow.created_at else None
                        ),
                        "updated_at": (
                            flow.updated_at.isoformat() if flow.updated_at else None
                        ),
                    }
                    flow_list.append(flow_data)

                return flow_list

            except Exception as e:
                logger.error(f"Database error in get_active_flows: {e}")
                raise

    async def validate_phase_transition(
        self, flow_id: str, from_phase: str, to_phase: str
    ) -> Dict[str, Any]:
        """Validate if phase transition is allowed"""
        async with AsyncSessionLocal() as db:
            try:
                flow_repo = DiscoveryFlowRepository(
                    db=db,
                    client_account_id=str(self.context.client_account_id),
                    engagement_id=str(self.context.engagement_id),
                )

                flow = await flow_repo.get_by_flow_id(flow_id)
                if not flow:
                    return {
                        "status": "error",
                        "error": "Flow not found",
                        "transition_allowed": False,
                    }

                # Define phase order and dependencies
                phase_order = [
                    "data_import",
                    "field_mapping",
                    "data_cleansing",
                    "asset_inventory",
                    "dependency_analysis",
                    "tech_debt_assessment",
                ]

                # Check if transition is valid based on phase order
                try:
                    from_index = phase_order.index(from_phase)
                    to_index = phase_order.index(to_phase)
                except ValueError:
                    return {
                        "status": "error",
                        "error": "Invalid phase names",
                        "transition_allowed": False,
                    }

                # Only allow forward transitions and completion transitions
                transition_allowed = to_index >= from_index

                # Check if prerequisite phases are complete
                prerequisite_phases = phase_order[:to_index]
                phase_completion_map = {
                    "data_import": flow.data_import_completed,
                    "field_mapping": flow.field_mapping_completed,
                    "data_cleansing": flow.data_cleansing_completed,
                    "asset_inventory": flow.asset_inventory_completed,
                    "dependency_analysis": flow.dependency_analysis_completed,
                    "tech_debt_assessment": flow.tech_debt_assessment_completed,
                }

                incomplete_prerequisites = [
                    phase
                    for phase in prerequisite_phases
                    if not phase_completion_map.get(phase, False)
                ]

                if incomplete_prerequisites:
                    transition_allowed = False

                return {
                    "status": "success",
                    "flow_id": flow_id,
                    "from_phase": from_phase,
                    "to_phase": to_phase,
                    "transition_allowed": transition_allowed,
                    "incomplete_prerequisites": incomplete_prerequisites,
                    "validation_details": {
                        "phase_order_valid": to_index >= from_index,
                        "prerequisites_complete": len(incomplete_prerequisites) == 0,
                    },
                }

            except Exception as e:
                logger.error(f"Error validating phase transition: {e}")
                return {"status": "error", "error": str(e), "transition_allowed": False}
