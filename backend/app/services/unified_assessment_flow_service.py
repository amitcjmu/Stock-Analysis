"""
Assessment Flow Service - Main Service Implementation

This service provides the main interface for executing assessment flows
through the CrewAI UnifiedAssessmentFlow. It follows the same patterns
as the discovery flow service and integrates with the Master Flow Orchestrator.

Key responsibilities:
- Initialize and execute UnifiedAssessmentFlow instances
- Manage assessment flow state through PostgreSQL persistence
- Handle pause/resume functionality for user input phases
- Provide status checking and flow management
- Delegate to real CrewAI agents for assessment intelligence
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.crewai_flows.unified_assessment_flow import (
    UnifiedAssessmentFlow,
)
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

# from app.services.crewai_flows.persistence.postgres_store import PostgresStore  # Handled by master orchestrator

logger = logging.getLogger(__name__)


class AssessmentFlowService:
    """
    Main Assessment Flow Service that delegates to UnifiedAssessmentFlow

    This service provides the interface between the Master Flow Orchestrator
    and the actual CrewAI UnifiedAssessmentFlow implementation.

    Updated to properly integrate with MFO instead of managing flows in memory.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """Initialize the assessment flow service"""
        self.db = db
        self.context = context
        # DEPRECATED: Legacy _active_flows for backward compatibility during migration
        # TODO: Remove once all callers updated to use MFO directly
        self._active_flows: Dict[str, UnifiedAssessmentFlow] = {}
        logger.info("✅ Assessment Flow Service initialized with MFO integration")

    async def create_assessment_flow(
        self,
        selected_application_ids: List[str],
        flow_name: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new assessment flow through Master Flow Orchestrator

        Args:
            selected_application_ids: Applications from Discovery inventory to assess
            flow_name: Optional human-readable name for the flow
            configuration: Optional flow configuration

        Returns:
            Dictionary with master_flow_id and initial status
        """
        try:
            logger.info(
                f"🚀 Creating assessment flow for {len(selected_application_ids)} applications through MFO"
            )

            # Prepare initial data for the assessment flow
            initial_data = {
                "selected_application_ids": selected_application_ids,
                "flow_name": flow_name
                or f"Assessment Flow - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                "configuration": configuration or {},
                "service_instance": self,  # Pass service reference for CrewAI flow creation
            }

            # Initialize through Master Flow Orchestrator
            orchestrator = MasterFlowOrchestrator(self.db, self.context)

            master_flow_id, flow_details = await orchestrator.create_flow(
                flow_type="assessment",
                flow_name=flow_name
                or f"Assessment Flow - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                configuration=configuration or {},
                initial_data=initial_data,
            )

            logger.info(
                f"✅ Assessment flow registered with MFO: master_flow_id={master_flow_id}"
            )

            return {
                "master_flow_id": str(master_flow_id),
                "flow_id": str(master_flow_id),  # For backward compatibility
                "status": "initialized",
                "selected_applications": len(selected_application_ids),
                "created_at": datetime.utcnow().isoformat(),
                "message": "Assessment flow created through Master Flow Orchestrator",
                "flow_details": flow_details,
            }

        except Exception as e:
            logger.error(f"❌ Failed to create assessment flow through MFO: {e}")
            raise RuntimeError(f"Assessment flow creation failed: {str(e)}")

    async def get_flow_status(self, master_flow_id: str) -> Dict[str, Any]:
        """
        Get the current status of an assessment flow through MFO

        Args:
            master_flow_id: Master flow identifier from MFO

        Returns:
            Dictionary with current flow status and details
        """
        try:
            logger.info(
                f"📊 Getting status for assessment flow {master_flow_id} through MFO"
            )

            # Get status through Master Flow Orchestrator
            orchestrator = MasterFlowOrchestrator(self.db, self.context)

            # Get comprehensive flow status from MFO
            flow_status = await orchestrator.get_flow_status(master_flow_id)

            if not flow_status or flow_status.get("status") == "not_found":
                return {
                    "master_flow_id": master_flow_id,
                    "flow_id": master_flow_id,  # For backward compatibility
                    "flow_status": "not_found",
                    "message": "Assessment flow not found",
                }

            # Return MFO status with assessment-specific formatting for backward compatibility
            return {
                "master_flow_id": master_flow_id,
                "flow_id": master_flow_id,  # For backward compatibility
                "flow_status": flow_status.get("status", "unknown"),
                "current_phase": flow_status.get("current_phase"),
                "progress": flow_status.get("progress", 0),
                "selected_applications": flow_status.get("metadata", {}).get(
                    "selected_applications_count", 0
                ),
                "apps_ready_for_planning": flow_status.get("metadata", {}).get(
                    "apps_ready_for_planning", 0
                ),
                "phase_results": flow_status.get("phase_results", {}),
                "user_input_required": flow_status.get("status")
                == "paused_for_user_input",
                "pause_points": flow_status.get("pause_points", {}),
                "last_user_interaction": flow_status.get("last_user_interaction"),
                "created_at": flow_status.get("created_at"),
                "updated_at": flow_status.get("updated_at"),
                "errors": flow_status.get("errors", []),
                "flow_details": flow_status,  # Include full MFO status
            }

        except Exception as e:
            logger.error(f"❌ Failed to get assessment flow status through MFO: {e}")
            return {
                "master_flow_id": master_flow_id,
                "flow_id": master_flow_id,  # For backward compatibility
                "flow_status": "error",
                "error": str(e),
            }

    async def resume_flow(
        self,
        master_flow_id: str,
        resume_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Resume a paused assessment flow through MFO

        Args:
            master_flow_id: Master flow identifier from MFO
            resume_context: Context and user input for resuming

        Returns:
            Dictionary with resume operation result
        """
        try:
            logger.info(f"🔄 Resuming assessment flow {master_flow_id} through MFO")

            # Resume flow through Master Flow Orchestrator
            orchestrator = MasterFlowOrchestrator(self.db, self.context)

            # Prepare resume context with assessment-specific data
            if resume_context is None:
                resume_context = {}
                logger.info(
                    f"🔍 resume_context was None for assessment flow {master_flow_id}, using empty dict"
                )

            # Resume the flow through MFO
            resume_result = await orchestrator.resume_flow(
                master_flow_id, resume_context
            )

            logger.info(
                f"✅ Assessment flow {master_flow_id} resumed successfully through MFO"
            )

            return {
                "master_flow_id": master_flow_id,
                "flow_id": master_flow_id,  # For backward compatibility
                "status": resume_result.get("status", "resumed"),
                "current_phase": resume_result.get("current_phase"),
                "resumed_at": datetime.utcnow().isoformat(),
                "resume_details": resume_result,
            }

        except Exception as e:
            logger.error(
                f"❌ Failed to resume assessment flow {master_flow_id} through MFO: {e}"
            )
            raise RuntimeError(f"Assessment flow resume failed: {str(e)}")

    async def advance_flow_phase(
        self,
        master_flow_id: str,
        next_phase: str,
        phase_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Advance assessment flow to a specific phase through MFO

        Args:
            master_flow_id: Master flow identifier from MFO
            next_phase: Name of the phase to advance to
            phase_input: Optional input data for the phase

        Returns:
            Dictionary with advancement result
        """
        try:
            logger.info(
                f"⏭️ Advancing assessment flow {master_flow_id} to phase {next_phase} through MFO"
            )

            # Execute phase through Master Flow Orchestrator
            orchestrator = MasterFlowOrchestrator(self.db, self.context)

            # Execute the phase through MFO
            result = await orchestrator.execute_phase(
                flow_id=master_flow_id, phase_name=next_phase, phase_input=phase_input
            )

            logger.info(
                f"✅ Assessment flow {master_flow_id} advanced to {next_phase} through MFO"
            )

            return {
                "master_flow_id": master_flow_id,
                "flow_id": master_flow_id,  # For backward compatibility
                "phase": next_phase,
                "status": result.get("status", "completed"),
                "result": result,
                "advanced_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(
                f"❌ Failed to advance assessment flow {master_flow_id} to {next_phase} through MFO: {e}"
            )
            raise RuntimeError(f"Phase advancement failed: {str(e)}")

    async def list_active_flows(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List active assessment flows through MFO

        Args:
            limit: Maximum number of flows to return

        Returns:
            List of active assessment flows
        """
        try:
            logger.info(
                f"📋 Listing active assessment flows for tenant {self.context.client_account_id} through MFO"
            )

            # Get flows through Master Flow Orchestrator
            orchestrator = MasterFlowOrchestrator(self.db, self.context)

            # Get all flows and filter for assessment type
            all_flows = await orchestrator.list_flows(
                limit=limit * 2
            )  # Get more to account for filtering

            assessment_flows = []
            count = 0

            for flow in all_flows:
                if count >= limit:
                    break

                # Filter for assessment flows
                if flow.get("flow_type") == "assessment":
                    assessment_flows.append(
                        {
                            "master_flow_id": flow.get("flow_id"),
                            "flow_id": flow.get(
                                "flow_id"
                            ),  # For backward compatibility
                            "flow_name": flow.get(
                                "flow_name", f"Assessment {flow.get('flow_id')}"
                            ),
                            "status": flow.get("status", "unknown"),
                            "current_phase": flow.get("current_phase"),
                            "progress": flow.get("progress", 0),
                            "selected_applications": flow.get("metadata", {}).get(
                                "selected_applications_count", 0
                            ),
                            "created_at": flow.get("created_at"),
                            "updated_at": flow.get("updated_at"),
                        }
                    )
                    count += 1

            logger.info(
                f"✅ Found {len(assessment_flows)} active assessment flows through MFO"
            )

            return assessment_flows

        except Exception as e:
            logger.error(f"❌ Failed to list active assessment flows through MFO: {e}")
            return []

    async def delete_flow(self, master_flow_id: str) -> Dict[str, Any]:
        """
        Delete an assessment flow through MFO

        Args:
            master_flow_id: Master flow identifier from MFO

        Returns:
            Dictionary with deletion result
        """
        try:
            logger.info(f"🗑️ Deleting assessment flow {master_flow_id} through MFO")

            # Delete flow through Master Flow Orchestrator
            orchestrator = MasterFlowOrchestrator(self.db, self.context)

            # Delete the flow through MFO (soft delete by default)
            delete_result = await orchestrator.delete_flow(
                flow_id=master_flow_id,
                soft_delete=True,
                reason="Assessment flow deletion requested",
            )

            # Clean up legacy active flows if present
            if master_flow_id in self._active_flows:
                del self._active_flows[master_flow_id]
                logger.info(f"Removed {master_flow_id} from legacy active flows")

            logger.info(
                f"✅ Assessment flow {master_flow_id} deleted successfully through MFO"
            )

            return {
                "master_flow_id": master_flow_id,
                "flow_id": master_flow_id,  # For backward compatibility
                "deleted": delete_result.get("deleted", True),
                "deleted_at": datetime.utcnow().isoformat(),
                "delete_details": delete_result,
            }

        except Exception as e:
            logger.error(
                f"❌ Failed to delete assessment flow {master_flow_id} through MFO: {e}"
            )
            raise RuntimeError(f"Assessment flow deletion failed: {str(e)}")
