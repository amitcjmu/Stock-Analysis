"""
Flow Finalization Module

Handles flow completion, user approval, and finalization logic.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FlowFinalizer:
    """Handles flow finalization and completion"""

    def __init__(self, state, state_manager):
        """
        Initialize flow finalizer

        Args:
            state: The flow state object
            state_manager: StateManager instance for state operations
        """
        self.state = state
        self.state_manager = state_manager

    async def pause_for_user_approval(self, previous_result: str) -> None:
        """
        Pause flow for user approval

        Args:
            previous_result: Result from previous phase
        """
        logger.info("⏸️ Pausing flow for user approval in attribute mapping phase")

        # Prepare approval context
        approval_context = self.state_manager.prepare_approval_context()

        # Update state
        self.state.status = "waiting_for_user_approval"
        self.state.current_phase = "attribute_mapping"
        self.state.awaiting_user_approval = True
        self.state.user_approval_data = approval_context

        # DELTA TEAM FIX: Route approval pause state through Master Flow Orchestrator
        logger.info("📋 Delegating approval pause state to Master Flow Orchestrator")
        # await self.state_manager.safe_update_flow_state()  # DISABLED - use MFO instead

        logger.info("⏸️ Flow successfully paused - waiting for user approval")

    async def finalize_flow(self, previous_result: str) -> str:
        """
        Finalize the discovery flow

        Args:
            previous_result: Result from previous phase

        Returns:
            Final status string
        """
        try:
            logger.info(f"🔍 Finalizing discovery flow: {self.state.flow_id}")

            # Create flow summary
            summary = self.state_manager.create_flow_summary()

            # Update final state
            self.state.discovery_summary = summary
            self.state.final_result = "completed"
            self.state.status = "completed"
            self.state.current_phase = "completed"
            self.state.completed_at = datetime.utcnow().isoformat()
            self.state.progress_percentage = 100.0

            # Update phase completion
            self.state.phase_completion["finalization"] = True

            # Calculate final metrics
            self._calculate_final_metrics()

            # DELTA TEAM FIX: Route all database updates through Master Flow Orchestrator
            logger.info(
                "📋 Delegating finalization state updates to Master Flow Orchestrator"
            )
            # Note: Actual state updates should be coordinated through MFO
            # await self.state_manager.safe_update_flow_state()  # DISABLED - use MFO instead
            # await self._update_master_flow_status("completed")  # DISABLED - use MFO instead

            logger.info("✅ Discovery flow completed successfully")
            return "discovery_completed"

        except Exception as e:
            logger.error(f"❌ Discovery flow finalization failed: {e}")
            self.state_manager.add_error("finalization", str(e))
            self.state.status = "failed"
            self.state.final_result = "discovery_failed"
            # Mark as completed even if failed, to indicate the flow has ended
            self.state.completed_at = datetime.utcnow().isoformat()

            # DELTA TEAM FIX: Route failure state updates through Master Flow Orchestrator
            logger.info(
                "📋 Delegating failure state updates to Master Flow Orchestrator"
            )
            # Note: Error state updates should be coordinated through MFO
            # try:
            #     await self.state_manager.safe_update_flow_state()  # DISABLED - use MFO instead
            #     await self._update_master_flow_status("failed")    # DISABLED - use MFO instead
            # except Exception as update_error:
            #     logger.error(f"❌ Failed to update flow state in database: {update_error}")

            return "discovery_failed"

    async def _update_master_flow_status(self, status: str) -> None:
        """Update master flow table status"""
        try:
            from app.core.context import RequestContext
            from app.core.database import AsyncSessionLocal
            from app.repositories.crewai_flow_state_extensions_repository import (
                CrewAIFlowStateExtensionsRepository,
            )

            async with AsyncSessionLocal() as db:
                context = RequestContext(
                    client_account_id=self.state.client_account_id,
                    engagement_id=self.state.engagement_id,
                    user_id=self.state.user_id,
                    flow_id=self.state.flow_id,
                )

                master_repo = CrewAIFlowStateExtensionsRepository(db, context)
                await master_repo.update_flow_status(
                    flow_id=self.state.flow_id,
                    status=status,
                    phase_data={
                        "completed_at": self.state.completed_at,
                        "final_result": self.state.final_result,
                        "total_assets": self.state.total_assets,
                        "total_dependencies": len(
                            self.state.dependencies.get(
                                "app_server_dependencies", {}
                            ).get("hosting_relationships", [])
                        ),
                        "total_insights": self.state.total_insights,
                    },
                )

                await db.commit()
                logger.info(f"✅ Updated master flow status to: {status}")

        except Exception as e:
            logger.warning(f"Failed to update master flow status: {e}")
            # Don't fail the flow if master update fails

    def _calculate_final_metrics(self) -> None:
        """Calculate final flow metrics"""
        if self.state.created_at:
            try:
                # Parse the created_at string back to datetime for calculation
                created_datetime = datetime.fromisoformat(
                    self.state.created_at.replace("Z", "+00:00")
                )
                duration = (datetime.utcnow() - created_datetime).total_seconds()
                self.state.execution_time_seconds = duration
            except (ValueError, AttributeError) as e:
                logger.warning(f"Could not calculate execution time: {e}")
                self.state.execution_time_seconds = 0.0

        # Count total insights
        self.state.total_insights = len(self.state.agent_insights)

        # Count total clarifications
        self.state.total_clarifications = len(self.state.user_clarifications)

        # Average confidence score
        if self.state.agent_confidences:
            try:
                # Convert string values to float if needed
                scores = []
                for score in self.state.agent_confidences.values():
                    if isinstance(score, str):
                        # Try to parse as float
                        scores.append(float(score))
                    else:
                        scores.append(score)

                if scores:
                    avg_confidence = sum(scores) / len(scores)
                    # Store in metadata since average_confidence field doesn't exist
                    self.state.metadata["average_confidence"] = avg_confidence
                else:
                    self.state.metadata["average_confidence"] = 0.0
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not calculate average confidence: {e}")
                self.state.metadata["average_confidence"] = 0.0
