"""
Background Execution Service - Core Module

Main service class for background execution of flows and long-running operations.
Handles async flow execution management, background task scheduling, and monitoring.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.core.exceptions import FlowError
from app.core.logging import get_logger

from .utils import (
    determine_final_status_from_phase_result,
    update_flow_status,
    get_execution_status,
)

logger = get_logger(__name__)

# Global set to track background tasks
_background_tasks = set()


class BackgroundExecutionService:
    """
    Manages background execution of flows and long-running operations.

    This service provides:
    - Async flow execution in background tasks
    - Progress tracking and status updates
    - Flow resumption and cancellation
    - Delayed execution scheduling
    - Flow monitoring
    """

    def __init__(self, db: AsyncSession, client_account_id: str):
        """
        Initialize the background execution service.

        Args:
            db: Database session (for reference, background tasks use fresh sessions)
            client_account_id: Client account identifier for tenant scoping
        """
        self.db = db
        self.client_account_id = client_account_id

    async def start_background_flow_execution(
        self, flow_id: str, file_data: List[Dict[str, Any]], context: RequestContext
    ) -> None:
        """
        Start CrewAI flow execution in background with proper task tracking.

        Key features:
        1. Properly track background tasks to prevent garbage collection
        2. Add error handling to ensure tasks complete
        3. Ensure flow execution actually starts

        Args:
            flow_id: Master flow ID to execute
            file_data: Raw import data for the flow
            context: Request context with tenant information

        Raises:
            FlowError: If background execution fails to start
        """
        try:
            logger.info(f"🚀 Starting background flow execution for {flow_id}")

            # Create the background task with proper tracking
            task = asyncio.create_task(
                self._run_discovery_flow_with_error_handling(
                    flow_id, file_data, context
                )
            )

            # Add to global set to prevent garbage collection
            _background_tasks.add(task)

            # Remove from set when done
            task.add_done_callback(_background_tasks.discard)

            logger.info(
                f"✅ Background flow execution task created and tracked for {flow_id}"
            )

            # Give the task a moment to start (non-blocking)
            await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(
                f"❌ Failed to start background flow execution: {e}", exc_info=True
            )
            raise FlowError(f"Failed to start background execution: {str(e)}")

    async def _run_discovery_flow_with_error_handling(
        self, flow_id: str, file_data: List[Dict[str, Any]], context: RequestContext
    ) -> None:
        """
        Wrapper that ensures errors are logged and flow status is updated.

        Args:
            flow_id: Flow ID to execute
            file_data: Raw import data
            context: Request context
        """
        try:
            await self._run_discovery_flow(flow_id, file_data, context)
        except Exception as e:
            logger.error(
                f"❌ Critical error in background flow execution for {flow_id}: {e}",
                exc_info=True,
            )
            # Ensure we update the flow status even on failure
            try:
                await update_flow_status(
                    flow_id=flow_id,
                    status="failed",
                    phase_data={
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    context=context,
                )
            except Exception as status_error:
                logger.error(
                    f"❌ Failed to update flow status on error: {status_error}"
                )

    async def _run_discovery_flow(
        self, flow_id: str, file_data: List[Dict[str, Any]], context: RequestContext
    ) -> None:
        """
        Run the actual CrewAI discovery flow in the background.

        This method contains the critical bug fix that ensures CrewAI environment
        is properly configured before any CrewAI operations.

        Args:
            flow_id: The master flow ID to execute
            file_data: Raw import data for the flow
            context: Request context for the flow
        """
        logger.info("=" * 80)
        logger.info("=" * 80)
        logger.info(
            f"🔥🔥🔥 CREWAI DISCOVERY FLOW INITIALIZATION - FLOW ID: {flow_id} 🔥🔥🔥"
        )
        logger.info("=" * 80)
        logger.info("=" * 80)
        logger.info(f"📊 Processing {len(file_data)} records")

        # 🔧 CC FIX: Ensure CrewAI environment is configured before any CrewAI code runs
        # This prevents "OPENAI_API_KEY is required" errors in Railway/production
        from app.core.crewai_env_setup import ensure_crewai_environment

        ensure_crewai_environment()
        logger.info("✅ CrewAI environment configured for background execution")

        discovery_flow = None

        try:
            # Update status to indicate we're starting
            from datetime import datetime

            await update_flow_status(
                flow_id=flow_id,
                status="starting",
                phase_data={
                    "message": "Initializing discovery flow execution",
                    "timestamp": datetime.utcnow().isoformat(),
                },
                context=context,
            )

            logger.info(
                f"🎯 Background CrewAI Discovery Flow kickoff starting for {flow_id}"
            )

            # Create CrewAI service with fresh session (safe after commit)
            async with AsyncSessionLocal() as fresh_db:
                from app.services.crewai_flow_service import CrewAIFlowService
                from app.services.crewai_flows.unified_discovery_flow import (
                    create_unified_discovery_flow,
                )

                crewai_service = CrewAIFlowService(fresh_db)

                # Create the UnifiedDiscoveryFlow instance
                discovery_flow = create_unified_discovery_flow(
                    flow_id=flow_id,
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    user_id=context.user_id or "system",
                    raw_data=file_data,
                    metadata={
                        "source": "data_import_background",
                        "master_flow_id": flow_id,
                    },
                    crewai_service=crewai_service,
                    context=context,
                    master_flow_id=flow_id,
                )

                # Update flow status to processing
                await update_flow_status(
                    flow_id=flow_id,
                    status="processing",
                    phase_data={"message": "Background CrewAI flow execution starting"},
                    context=context,
                )

            # Use phase controller for controlled phase-by-phase execution
            logger.info("-" * 80)
            logger.info(
                f"🚀🚀🚀 STARTING CONTROLLED PHASE-BY-PHASE EXECUTION FOR FLOW: {flow_id}"
            )
            logger.info("-" * 80)
            from app.services.crewai_flows.unified_discovery_flow.phase_controller import (
                PhaseController,
            )

            phase_controller = PhaseController(discovery_flow)
            result = await phase_controller.start_flow_execution()

            logger.info(f"✅ Discovery Flow phase execution completed: {result.status}")
            logger.info(f"📍 Current phase: {result.phase.value}")
            logger.info(f"⏸️ Requires user input: {result.requires_user_input}")

            # Update final status based on result
            final_status, phase_data = determine_final_status_from_phase_result(result)
            await update_flow_status(
                flow_id=flow_id,
                status=final_status,
                phase_data=phase_data,
                context=context,
            )

        except Exception as e:
            logger.error(f"❌ Background flow execution failed for {flow_id}: {e}")

            # Update status to failed
            await update_flow_status(
                flow_id=flow_id,
                status="failed",
                phase_data={"error": str(e)},
                context=context,
            )

    async def resume_flow_from_user_input(
        self,
        flow_id: str,
        user_input: Dict[str, Any],
        context: RequestContext,
        resume_phase: str = "field_mapping_approval",
    ) -> bool:
        """
        Resume a paused flow with user input.

        This method contains the critical bug fix that ensures CrewAI environment
        is properly configured before resuming flow execution.

        Args:
            flow_id: The flow ID to resume
            user_input: User input data
            context: Request context
            resume_phase: Phase to resume from

        Returns:
            bool: True if resumed successfully
        """
        try:
            logger.info(
                f"🔄 Resuming flow {flow_id} from phase {resume_phase} with user input"
            )

            # 🔧 CC FIX: Ensure CrewAI environment is configured before resuming flow
            from app.core.crewai_env_setup import ensure_crewai_environment

            ensure_crewai_environment()
            logger.info("✅ CrewAI environment configured for flow resumption")

            # Create CrewAI service with fresh session
            async with AsyncSessionLocal() as fresh_db:
                from app.services.crewai_flow_service import CrewAIFlowService
                from app.services.crewai_flows.unified_discovery_flow import (
                    create_unified_discovery_flow,
                )
                from app.services.crewai_flows.unified_discovery_flow.phase_controller import (
                    FlowPhase,
                    PhaseController,
                )

                crewai_service = CrewAIFlowService(fresh_db)

                # Create the UnifiedDiscoveryFlow instance (will load existing state)
                discovery_flow = create_unified_discovery_flow(
                    flow_id=flow_id,
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    user_id=context.user_id or "system",
                    raw_data=[],  # Will be loaded from state
                    metadata={"source": "flow_resumption", "master_flow_id": flow_id},
                    crewai_service=crewai_service,
                    context=context,
                    master_flow_id=flow_id,
                )

                # Update flow status to processing
                await update_flow_status(
                    flow_id=flow_id,
                    status="processing",
                    phase_data={
                        "message": f"Resuming flow from {resume_phase} with user input"
                    },
                    context=context,
                )

            # Use phase controller to resume execution
            phase_controller = PhaseController(discovery_flow)

            # Map string phase names to FlowPhase enum
            phase_map = {
                "field_mapping_approval": FlowPhase.FIELD_MAPPING_APPROVAL,
                "data_cleansing": FlowPhase.DATA_CLEANSING,
                "finalization": FlowPhase.FINALIZATION,
            }

            resume_from_phase = phase_map.get(
                resume_phase, FlowPhase.FIELD_MAPPING_APPROVAL
            )

            # Resume with user input
            result = await phase_controller.resume_flow_execution(
                from_phase=resume_from_phase, user_input=user_input
            )

            logger.info(f"✅ Flow resumption completed: {result.status}")
            logger.info(f"📍 Current phase: {result.phase.value}")
            logger.info(f"⏸️ Requires user input: {result.requires_user_input}")

            # Update final status based on result
            final_status, phase_data = determine_final_status_from_phase_result(result)
            await update_flow_status(
                flow_id=flow_id,
                status=final_status,
                phase_data=phase_data,
                context=context,
            )

            logger.info(f"✅ Flow {flow_id} resumed successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to resume flow {flow_id}: {e}")

            # Update status to failed
            await update_flow_status(
                flow_id=flow_id,
                status="failed",
                phase_data={"error": f"Resume failed: {str(e)}"},
                context=context,
            )
            return False

    async def cancel_background_execution(
        self, flow_id: str, context: RequestContext
    ) -> bool:
        """
        Cancel a background execution.

        Args:
            flow_id: The flow ID to cancel
            context: Request context

        Returns:
            bool: True if cancelled successfully
        """
        try:
            logger.info(f"🚫 Cancelling background execution for {flow_id}")

            # Update flow status to cancelled
            await update_flow_status(
                flow_id=flow_id,
                status="cancelled",
                phase_data={"message": "Background execution cancelled"},
                context=context,
            )

            logger.info(f"✅ Background execution cancelled for {flow_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to cancel background execution: {e}")
            return False

    async def schedule_delayed_execution(
        self,
        flow_id: str,
        delay_seconds: int,
        file_data: List[Dict[str, Any]],
        context: RequestContext,
    ) -> None:
        """
        Schedule a delayed execution of a flow.

        Args:
            flow_id: The flow ID to execute
            delay_seconds: Delay in seconds before execution
            file_data: Raw import data for the flow
            context: Request context

        Raises:
            FlowError: If scheduling fails
        """
        try:
            logger.info(
                f"📅 Scheduling delayed execution for {flow_id} in {delay_seconds} seconds"
            )

            async def delayed_execution():
                await asyncio.sleep(delay_seconds)
                await self._run_discovery_flow(flow_id, file_data, context)

            asyncio.create_task(delayed_execution())
            logger.info(f"✅ Delayed execution scheduled for {flow_id}")

        except Exception as e:
            logger.error(f"❌ Failed to schedule delayed execution: {e}")
            raise FlowError(f"Failed to schedule delayed execution: {str(e)}")

    async def monitor_flow_progress(
        self, flow_id: str, context: RequestContext, check_interval: int = 30
    ) -> None:
        """
        Monitor flow progress and log status periodically.

        Args:
            flow_id: The flow ID to monitor
            context: Request context
            check_interval: Interval in seconds between checks
        """
        try:
            logger.info(f"👁️ Starting flow progress monitoring for {flow_id}")

            async def monitor_loop():
                while True:
                    try:
                        # Check flow status using the utility function
                        status_data = await get_execution_status(flow_id, context)

                        if status_data and status_data["status"] in [
                            "completed",
                            "failed",
                            "cancelled",
                        ]:
                            logger.info(
                                f"✅ Flow {flow_id} monitoring complete: {status_data['status']}"
                            )
                            break

                        logger.debug(
                            f"🔄 Flow {flow_id} status: {status_data['status'] if status_data else 'unknown'}"
                        )

                        await asyncio.sleep(check_interval)

                    except Exception as e:
                        logger.error(f"❌ Error monitoring flow {flow_id}: {e}")
                        await asyncio.sleep(check_interval)

            asyncio.create_task(monitor_loop())
            logger.info(f"✅ Flow monitoring started for {flow_id}")

        except Exception as e:
            logger.error(f"❌ Failed to start flow monitoring: {e}")

    async def get_execution_status(
        self, flow_id: str, context: RequestContext
    ) -> Optional[Dict[str, Any]]:
        """
        Get the current execution status of a flow.

        This is a convenience method that delegates to the utility function.

        Args:
            flow_id: The flow ID to check
            context: Request context

        Returns:
            Dict containing execution status information
        """
        return await get_execution_status(flow_id, context)
