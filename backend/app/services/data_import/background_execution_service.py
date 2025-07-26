"""
Background Execution Service Module

Handles background execution including:
- Async flow execution management
- Background task scheduling
- Long-running operation handling
- Progress tracking and monitoring
"""

import asyncio
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.core.exceptions import FlowError
from app.core.logging import get_logger

logger = get_logger(__name__)


class BackgroundExecutionService:
    """
    Manages background execution of flows and long-running operations.
    """

    def __init__(self, db: AsyncSession, client_account_id: str):
        self.db = db
        self.client_account_id = client_account_id

    async def start_background_flow_execution(
        self, flow_id: str, file_data: List[Dict[str, Any]], context: RequestContext
    ) -> None:
        """
        Start CrewAI flow execution in background after successful database commit.

        This function runs the actual CrewAI flow kickoff after all database operations
        have been committed atomically. It uses fresh database sessions since it runs
        independently from the main transaction.

        Args:
            flow_id: The master flow ID to execute
            file_data: Raw import data for the flow
            context: Request context for the flow
        """
        try:
            logger.info(f"🚀 Starting background flow execution for {flow_id}")

            # Create the background task
            asyncio.create_task(self._run_discovery_flow(flow_id, file_data, context))
            logger.info(f"✅ Background flow execution task created for {flow_id}")

        except Exception as e:
            logger.error(f"❌ Failed to start background flow execution: {e}")
            raise FlowError(f"Failed to start background execution: {str(e)}")

    async def _run_discovery_flow(
        self, flow_id: str, file_data: List[Dict[str, Any]], context: RequestContext
    ) -> None:
        """
        Run the actual CrewAI discovery flow in the background.

        Args:
            flow_id: The master flow ID to execute
            file_data: Raw import data for the flow
            context: Request context for the flow
        """
        try:
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
                await self._update_flow_status(
                    flow_id=flow_id,
                    status="processing",
                    phase_data={"message": "Background CrewAI flow execution starting"},
                    context=context,
                )

            # Use new phase controller instead of flow.kickoff() to prevent automatic execution
            logger.info(f"🚀 Starting controlled phase-by-phase execution for {flow_id}")
            from app.services.crewai_flows.unified_discovery_flow.phase_controller import (
                PhaseController,
            )

            phase_controller = PhaseController(discovery_flow)
            result = await phase_controller.start_flow_execution()

            logger.info(f"✅ Discovery Flow phase execution completed: {result.status}")
            logger.info(f"📍 Current phase: {result.phase.value}")
            logger.info(f"⏸️ Requires user input: {result.requires_user_input}")

            # Update final status based on result
            final_status, phase_data = self._determine_final_status_from_phase_result(
                result
            )
            await self._update_flow_status(
                flow_id=flow_id,
                status=final_status,
                phase_data=phase_data,
                context=context,
            )

        except Exception as e:
            logger.error(f"❌ Background flow execution failed for {flow_id}: {e}")

            # Update status to failed
            await self._update_flow_status(
                flow_id=flow_id,
                status="failed",
                phase_data={"error": str(e)},
                context=context,
            )

    def _determine_final_status(self, result: Any) -> tuple[str, Dict[str, Any]]:
        """
        Determine the final status and phase data based on flow result.

        Args:
            result: Result from the flow execution

        Returns:
            Tuple of (status, phase_data)
        """
        if result in [
            "paused_for_field_mapping_approval",
            "awaiting_user_approval_in_attribute_mapping",
        ]:
            return "waiting_for_approval", {
                "completion": result,
                "current_phase": "attribute_mapping",
                "progress_percentage": 60.0,
                "awaiting_user_approval": True,
            }
        elif result in ["discovery_completed"]:
            return "completed", {
                "completion": result,
                "current_phase": "completed",
                "progress_percentage": 100.0,
            }
        else:
            return "processing", {
                "completion": result,
                "current_phase": "processing",
                "progress_percentage": 30.0,
            }

    def _determine_final_status_from_phase_result(
        self, result
    ) -> tuple[str, Dict[str, Any]]:
        """
        Determine the final status and phase data based on PhaseExecutionResult.

        Args:
            result: PhaseExecutionResult from phase controller

        Returns:
            Tuple of (status, phase_data)
        """
        if result.requires_user_input:
            return "waiting_for_approval", {
                "completion": result.status,
                "current_phase": result.phase.value,
                "progress_percentage": self._calculate_progress_percentage(
                    result.phase
                ),
                "awaiting_user_approval": True,
                "phase_data": result.data,
            }
        elif result.status == "failed":
            return "failed", {
                "completion": result.status,
                "current_phase": result.phase.value,
                "error": result.data.get("error", "Unknown error"),
                "phase_data": result.data,
            }
        elif result.status == "completed" and result.phase.value == "finalization":
            return "completed", {
                "completion": "discovery_completed",
                "current_phase": "completed",
                "progress_percentage": 100.0,
                "phase_data": result.data,
            }
        else:
            return "processing", {
                "completion": result.status,
                "current_phase": result.phase.value,
                "progress_percentage": self._calculate_progress_percentage(
                    result.phase
                ),
                "phase_data": result.data,
            }

    def _calculate_progress_percentage(self, phase) -> float:
        """Calculate progress percentage based on current phase"""
        phase_progress_map = {
            "initialization": 10.0,
            "data_import_validation": 20.0,
            "field_mapping_suggestions": 30.0,
            "field_mapping_approval": 40.0,
            "data_cleansing": 50.0,
            "asset_inventory": 70.0,
            "dependency_analysis": 85.0,
            "tech_debt_assessment": 90.0,
            "finalization": 100.0,
        }
        return phase_progress_map.get(phase.value, 30.0)

    async def _update_flow_status(
        self,
        flow_id: str,
        status: str,
        phase_data: Dict[str, Any],
        context: RequestContext,
    ) -> None:
        """
        Update the flow status in the database.

        Args:
            flow_id: The flow ID to update
            status: New status for the flow
            phase_data: Phase data to update
            context: Request context
        """
        try:
            async with AsyncSessionLocal() as fresh_db:
                from app.repositories.crewai_flow_state_extensions_repository import (
                    CrewAIFlowStateExtensionsRepository,
                )

                fresh_repo = CrewAIFlowStateExtensionsRepository(
                    fresh_db,
                    context.client_account_id,
                    context.engagement_id,
                    context.user_id,
                )

                await fresh_repo.update_flow_status(
                    flow_id=flow_id, status=status, phase_data=phase_data
                )
                await fresh_db.commit()

        except Exception as e:
            logger.error(f"❌ Failed to update flow status: {e}")

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
        Monitor flow progress and update status periodically.

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
                        # Check flow status
                        async with AsyncSessionLocal() as fresh_db:
                            from app.repositories.crewai_flow_state_extensions_repository import (
                                CrewAIFlowStateExtensionsRepository,
                            )

                            repo = CrewAIFlowStateExtensionsRepository(
                                fresh_db,
                                context.client_account_id,
                                context.engagement_id,
                                context.user_id,
                            )

                            flow_state = await repo.get_flow_state(flow_id)

                            if flow_state and flow_state.status in [
                                "completed",
                                "failed",
                                "cancelled",
                            ]:
                                logger.info(
                                    f"✅ Flow {flow_id} monitoring complete: {flow_state.status}"
                                )
                                break

                            logger.debug(
                                f"🔄 Flow {flow_id} status: {flow_state.status if flow_state else 'unknown'}"
                            )

                        await asyncio.sleep(check_interval)

                    except Exception as e:
                        logger.error(f"❌ Error monitoring flow {flow_id}: {e}")
                        await asyncio.sleep(check_interval)

            asyncio.create_task(monitor_loop())
            logger.info(f"✅ Flow monitoring started for {flow_id}")

        except Exception as e:
            logger.error(f"❌ Failed to start flow monitoring: {e}")

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
            await self._update_flow_status(
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

    async def resume_flow_from_user_input(
        self,
        flow_id: str,
        user_input: Dict[str, Any],
        context: RequestContext,
        resume_phase: str = "field_mapping_approval",
    ) -> bool:
        """
        Resume a paused flow with user input.

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
                await self._update_flow_status(
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
            final_status, phase_data = self._determine_final_status_from_phase_result(
                result
            )
            await self._update_flow_status(
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
            await self._update_flow_status(
                flow_id=flow_id,
                status="failed",
                phase_data={"error": f"Resume failed: {str(e)}"},
                context=context,
            )
            return False

    async def get_execution_status(
        self, flow_id: str, context: RequestContext
    ) -> Optional[Dict[str, Any]]:
        """
        Get the current execution status of a flow.

        Args:
            flow_id: The flow ID to check
            context: Request context

        Returns:
            Dict containing execution status information
        """
        try:
            async with AsyncSessionLocal() as fresh_db:
                from app.repositories.crewai_flow_state_extensions_repository import (
                    CrewAIFlowStateExtensionsRepository,
                )

                repo = CrewAIFlowStateExtensionsRepository(
                    fresh_db,
                    context.client_account_id,
                    context.engagement_id,
                    context.user_id,
                )

                flow_state = await repo.get_flow_state(flow_id)

                if flow_state:
                    return {
                        "flow_id": flow_id,
                        "status": flow_state.status,
                        "phase_data": flow_state.phase_data,
                        "created_at": (
                            flow_state.created_at.isoformat()
                            if flow_state.created_at
                            else None
                        ),
                        "updated_at": (
                            flow_state.updated_at.isoformat()
                            if flow_state.updated_at
                            else None
                        ),
                    }

                return None

        except Exception as e:
            logger.error(f"❌ Failed to get execution status: {e}")
            return None
