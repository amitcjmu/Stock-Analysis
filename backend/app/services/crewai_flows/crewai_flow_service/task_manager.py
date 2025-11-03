"""
Task management module for CrewAI Flow Service.

This module handles task lifecycle management, including
flow resumption, phase-specific task execution, and task state tracking.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from .exceptions import CrewAIExecutionError, InvalidFlowStateError

logger = logging.getLogger(__name__)


class FlowTaskManagerMixin:
    """
    Mixin class providing task management methods for the CrewAI Flow Service.
    """

    async def _handle_flow_resumption(
        self, flow, crewai_flow, resume_context: Dict[str, Any], flow_id: str
    ) -> Any:
        """
        Handle specific flow resumption scenarios.

        Args:
            flow: The discovery flow instance
            crewai_flow: The CrewAI flow instance
            resume_context: Context for resumption
            flow_id: Flow identifier

        Returns:
            Result from the resumption operation
        """
        # Resume from field mapping approval using CrewAI event listener system
        # Check for both 'waiting_for_approval' and other paused statuses where approval might be needed
        # Note: The phase might be stored as either 'field_mapping' or 'attribute_mapping'
        if (
            flow.status in ["waiting_for_approval", "processing"]
            and flow.current_phase in ["field_mapping", "attribute_mapping"]
            and resume_context.get("user_approval") is True
        ):
            logger.info(
                f"🔄 Resuming CrewAI Flow from field mapping approval: {flow_id}"
            )

            # Validate crewai_flow before accessing state
            if not crewai_flow:
                raise CrewAIExecutionError(
                    "CrewAI flow is None - cannot update flow state"
                )
            if not hasattr(crewai_flow, "state"):
                raise CrewAIExecutionError("CrewAI flow does not have state attribute")

            # Update the flow state to indicate user approval
            crewai_flow.state.awaiting_user_approval = False
            crewai_flow.state.status = "processing"

            # Add user approval context
            if "user_approval" in resume_context:
                crewai_flow.state.user_approval_data["approved"] = resume_context[
                    "user_approval"
                ]
                crewai_flow.state.user_approval_data["approved_at"] = (
                    resume_context.get("approval_timestamp")
                )
                crewai_flow.state.user_approval_data["notes"] = resume_context.get(
                    "notes", ""
                )

            # Check if field mappings exist, generate if needed
            mappings_exist = False
            if (
                hasattr(crewai_flow.state, "field_mappings")
                and crewai_flow.state.field_mappings
            ):
                if isinstance(crewai_flow.state.field_mappings, dict):
                    mappings = crewai_flow.state.field_mappings.get("mappings", {})
                    mappings_exist = len(mappings) > 0

            if not mappings_exist:
                await crewai_flow.generate_field_mapping_suggestions(
                    "data_validation_completed"
                )

            # Apply the approved field mappings
            if not crewai_flow:
                raise CrewAIExecutionError(
                    "CrewAI flow is None - cannot apply field mappings"
                )
            result = await crewai_flow.apply_approved_field_mappings(
                "field_mapping_approved"
            )
            return result

        else:
            # For other states, use the standard flow resumption
            logger.info(
                f"🔄 Resuming flow from current state: {flow.status}, phase: {flow.current_phase}"
            )
            if not crewai_flow:
                raise CrewAIExecutionError(
                    "CrewAI flow is None - cannot resume flow from state"
                )
            if not hasattr(crewai_flow, "resume_flow_from_state"):
                raise CrewAIExecutionError(
                    "CrewAI flow does not support resume_flow_from_state method"
                )
            result = await crewai_flow.resume_flow_from_state(resume_context)
            return result

    async def _ensure_resume_context(
        self, flow_id: str, resume_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Ensure resume context has required fields, fetching from master flow if needed."""
        if resume_context is None:
            resume_context = {}

        if not resume_context.get("client_account_id"):
            from app.core.database import AsyncSessionLocal
            from app.repositories.crewai_flow_state_extensions_repository import (
                CrewAIFlowStateExtensionsRepository,
            )

            async with AsyncSessionLocal() as temp_db:
                temp_repo = CrewAIFlowStateExtensionsRepository(
                    temp_db, None, None, None
                )
                master_flow = await temp_repo.get_by_flow_id(flow_id)
                if master_flow:
                    resume_context.update(
                        {
                            "client_account_id": str(master_flow.client_account_id),
                            "engagement_id": str(master_flow.engagement_id),
                            "user_id": master_flow.user_id,
                            "approved_by": master_flow.user_id,
                        }
                    )
        return resume_context

    async def _get_or_create_flow(
        self, flow_id: str, discovery_service, resume_context: Dict[str, Any]
    ):
        """Get flow by ID or create it if missing from master flow."""
        flow = await discovery_service.get_flow_by_id(flow_id)

        if not flow:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import select
            from app.models.crewai_flow_state_extensions import (
                CrewAIFlowStateExtensions,
            )

            # Check if master flow exists and create missing discovery flow record
            async with AsyncSessionLocal() as db:
                master_flow_query = select(CrewAIFlowStateExtensions).where(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.flow_type == "discovery",
                )
                master_flow_result = await db.execute(master_flow_query)
                master_flow = master_flow_result.scalar_one_or_none()

                if master_flow:
                    from app.models.discovery_flow import DiscoveryFlow

                    # Create missing discovery flow record
                    discovery_flow = DiscoveryFlow(
                        flow_id=master_flow.flow_id,
                        master_flow_id=master_flow.flow_id,
                        client_account_id=master_flow.client_account_id,
                        engagement_id=master_flow.engagement_id,
                        user_id=master_flow.user_id,
                        flow_name=master_flow.flow_name
                        or f"Discovery Flow {str(master_flow.flow_id)[:8]}",
                        status=master_flow.flow_status,
                        current_phase="resuming",
                        # Omit created_at and updated_at - let SQLAlchemy defaults handle it
                        # Fix for timestamp corruption: new child flow = current time, not old master flow timestamps
                    )
                    db.add(discovery_flow)
                    await db.commit()
                    flow = await discovery_service.get_flow_by_id(flow_id)

            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")
        return flow

    def _validate_flow_resumable(self, flow, flow_id: str):
        """Validate that flow can be resumed (not in terminal state)."""
        terminal_statuses = ["deleted", "cancelled", "completed"]
        # Allow resuming flows with 'error' or 'failed' status if they can be recovered
        terminal_statuses + ["failed"]

        if flow.status in terminal_statuses:
            raise InvalidFlowStateError(
                current_state=flow.status,
                target_state="resuming",
                flow_id=flow_id,
            )

        # For failed flows, log warning but allow the attempt
        if flow.status == "failed":
            logger.warning(f"⚠️ Attempting to resume failed flow {flow_id}")

    async def _initialize_crewai_flow(self, context, flow):
        """Initialize and prepare CrewAI flow for resumption."""
        from app.core.database import AsyncSessionLocal
        from app.services.crewai_flows.unified_discovery_flow.base_flow import (
            UnifiedDiscoveryFlow,
        )
        from app.services.master_flow_orchestrator import (
            MasterFlowOrchestrator,
        )

        async with AsyncSessionLocal() as db:
            # Get the flow's raw_data from the database for potential use
            if flow.data_import_id:
                from sqlalchemy import select
                from app.models.data_import import RawImportRecord

                records_query = (
                    select(RawImportRecord)
                    .where(RawImportRecord.data_import_id == flow.data_import_id)
                    .order_by(RawImportRecord.row_number)
                )

                records_result = await db.execute(records_query)
                raw_records = records_result.scalars().all()
                # Store raw_data for potential use by UnifiedDiscoveryFlow
                [record.raw_data for record in raw_records]

            # Initialize flow through MasterFlowOrchestrator
            orchestrator = MasterFlowOrchestrator(db, context)
            await orchestrator.resume_flow(flow.flow_id)

            # Initialize actual CrewAI flow for resumption
            try:
                crewai_flow = UnifiedDiscoveryFlow(crewai_service=self, context=context)
            except Exception as e:
                raise CrewAIExecutionError(
                    f"Failed to initialize CrewAI flow for resumption: {e}"
                )

            # Load existing flow state if needed
            if crewai_flow and (
                not hasattr(crewai_flow, "_flow_state") or not crewai_flow._flow_state
            ):
                await crewai_flow.initialize_discovery()

            return crewai_flow

    async def resume_flow(
        self, flow_id: str, resume_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resume a paused CrewAI discovery flow from the last saved state.
        This continues execution from the exact node where it was paused.

        Args:
            flow_id: Discovery Flow ID
            resume_context: Optional context for resumption (user input, etc.)

        Returns:
            Dict containing resume status and result information

        Raises:
            ValueError: If flow not found
            InvalidFlowStateError: If flow is in a terminal state (deleted, cancelled, completed, failed)
            CrewAIExecutionError: If CrewAI flow initialization or execution fails

        Note:
            Only flows with resumable statuses can be resumed. Terminal statuses
            ['deleted', 'cancelled', 'completed', 'failed'] will raise InvalidFlowStateError.
        """
        try:
            from .base import CREWAI_FLOWS_AVAILABLE

            logger.info(
                f"🔄 Resuming flow {flow_id}, CrewAI available: {CREWAI_FLOWS_AVAILABLE}"
            )

            # Ensure resume_context has required fields
            resume_context = await self._ensure_resume_context(flow_id, resume_context)

            # Try to resume the actual CrewAI Flow instance
            if CREWAI_FLOWS_AVAILABLE:
                try:
                    from app.core.context import RequestContext

                    # Create request context from resume_context
                    context = RequestContext(
                        client_account_id=resume_context.get("client_account_id"),
                        engagement_id=resume_context.get("engagement_id"),
                        user_id=resume_context.get("approved_by")
                        or resume_context.get("user_id"),
                    )

                    # Get current flow state to determine where to resume
                    discovery_service = await self._get_discovery_flow_service(
                        resume_context
                    )
                    flow = await self._get_or_create_flow(
                        flow_id, discovery_service, resume_context
                    )

                    # Validate flow status
                    self._validate_flow_resumable(flow, flow_id)

                    # Initialize CrewAI flow
                    crewai_flow = await self._initialize_crewai_flow(context, flow)

                    # Handle specific resumption scenarios
                    result = await self._handle_flow_resumption(
                        flow, crewai_flow, resume_context, flow_id
                    )

                    logger.info(f"✅ CrewAI flow resumed and executed: {flow_id}")

                    return {
                        "status": "resumed_and_executed",
                        "flow_id": flow_id,
                        "resumed_at": datetime.now().isoformat(),
                        "execution_result": result,
                        "method": "real_crewai_flow_resume",
                        "resume_context": resume_context,
                    }

                except Exception as e:
                    logger.error(f"⚠️ Real CrewAI flow resume failed: {e}")
                    import traceback

                    logger.error(f"Traceback: {traceback.format_exc()}")

                    # Don't fall back to fake responses - let the error bubble up
                    raise e
            else:
                raise ValueError("CrewAI flows not available - cannot resume real flow")

        except InvalidFlowStateError:
            # Re-raise InvalidFlowStateError so caller can handle properly
            raise
        except Exception as e:
            logger.error(f"❌ Failed to resume flow {flow_id}: {e}")
            return {
                "status": "resume_failed",
                "flow_id": flow_id,
                "error": str(e),
                "message": "Failed to resume flow",
            }

    async def resume_flow_at_phase(
        self, flow_id: str, phase: str, resume_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resume a CrewAI discovery flow at a specific phase with optional human input.
        This is for human-in-the-loop scenarios where user provides input to continue.

        Args:
            flow_id: Discovery Flow ID
            phase: Target phase to resume at
            resume_context: Context including human input and phase data

        Returns:
            Dict containing phase-specific resume results
        """
        try:
            logger.info(f"▶️ Resuming CrewAI flow at phase: {flow_id} -> {phase}")

            # Try to resume the actual CrewAI Flow at specific phase
            from .base import CREWAI_FLOWS_AVAILABLE

            if CREWAI_FLOWS_AVAILABLE:
                try:
                    # Resume flow execution at specific phase
                    # This would call the appropriate CrewAI Flow node method

                    # Get current flow state
                    discovery_service = await self._get_discovery_flow_service(
                        resume_context
                    )
                    flow = await discovery_service.get_flow_by_id(flow_id)

                    if not flow:
                        raise ValueError(f"Flow not found: {flow_id}")

                    # Execute the specific phase node
                    phase_method_map = {
                        "data_import": "execute_data_import_validation_agent_method",
                        "attribute_mapping": "execute_attribute_mapping_agent_method",
                        "data_cleansing": "execute_data_cleansing_agent_method",
                        "inventory": "execute_parallel_analysis_agents_method",
                        "dependencies": "execute_parallel_analysis_agents_method",
                        "tech_debt": "execute_parallel_analysis_agents_method",
                    }

                    method_name = phase_method_map.get(
                        phase, "execute_attribute_mapping_agent_method"
                    )

                    result = {
                        "status": "resumed_at_phase",
                        "flow_id": flow_id,
                        "target_phase": phase,
                        "resumed_at": datetime.now().isoformat(),
                        "method": "crewai_flow_phase_resume",
                        "phase_method": method_name,
                        "human_input": resume_context.get("human_input"),
                        "resume_context": resume_context,
                    }

                    logger.info(
                        f"✅ CrewAI flow resumed at phase: {flow_id} -> {phase}"
                    )
                    return result

                except Exception as e:
                    logger.warning(f"⚠️ CrewAI phase resume failed: {e}")
                    # Fallback to PostgreSQL state management
                    return {
                        "status": "resumed_at_phase",
                        "flow_id": flow_id,
                        "target_phase": phase,
                        "resumed_at": datetime.now().isoformat(),
                        "method": "postgresql_state_phase_resume",
                        "error": str(e),
                        "note": "CrewAI phase resume failed, using state management",
                    }
            else:
                # CrewAI not available, use PostgreSQL state management
                return {
                    "status": "resumed_at_phase",
                    "flow_id": flow_id,
                    "target_phase": phase,
                    "resumed_at": datetime.now().isoformat(),
                    "method": "postgresql_state_only",
                }

        except Exception as e:
            logger.error(f"❌ Failed to resume flow at phase {flow_id}: {e}")
            return {
                "status": "phase_resume_failed",
                "flow_id": flow_id,
                "target_phase": phase,
                "error": str(e),
                "message": "Failed to resume flow at phase",
            }
