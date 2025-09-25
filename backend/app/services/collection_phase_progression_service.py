"""
Collection Phase Progression Service

Handles automatic phase progression for collection flows that are stuck
due to missing trigger mechanisms between phases.

This service detects collection flows stuck in platform_detection phase
and automatically advances them to the next phase (automated_collection).
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_flow import (
    CollectionFlow,
    CollectionFlowStatus,
    CollectionPhase,
)
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.api.v1.endpoints.collection_mfo_utils import (
    execute_mfo_phase,
    sync_collection_child_flow_state,
)

logger = logging.getLogger(__name__)


class CollectionPhaseProgressionService:
    """Service to handle automatic collection flow phase progression"""

    def __init__(self, db_session: AsyncSession, context: RequestContext):
        self.db_session = db_session
        self.context = context

    async def find_stuck_flows(self) -> List[CollectionFlow]:
        """Find collection flows stuck in platform_detection phase"""
        try:
            # Look for flows that have been in platform_detection for too long
            # and should be progressed to automated_collection
            stmt = select(CollectionFlow).where(
                CollectionFlow.client_account_id == self.context.client_account_id,
                CollectionFlow.engagement_id == self.context.engagement_id,
                CollectionFlow.current_phase == CollectionPhase.ASSET_SELECTION.value,
                CollectionFlow.status == CollectionFlowStatus.ASSET_SELECTION.value,
                CollectionFlow.master_flow_id.isnot(None),  # Must have MFO integration
            )

            result = await self.db_session.execute(stmt)
            stuck_flows = result.scalars().all()

            logger.info(
                f"Found {len(stuck_flows)} flows potentially stuck in platform_detection"
            )
            return list(stuck_flows)

        except Exception as e:
            logger.error(f"Error finding stuck flows: {e}")
            return []

    async def check_platform_detection_complete(self, flow: CollectionFlow) -> bool:
        """Check if platform detection phase is actually complete"""
        try:
            # Check if the MFO flow exists and has platform detection results
            if not flow.master_flow_id:
                return False

            stmt = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_id == flow.master_flow_id
            )
            result = await self.db_session.execute(stmt)
            master_flow = result.scalar_one_or_none()

            if not master_flow:
                logger.warning(f"No master flow found for {flow.flow_id}")
                return False

            # Check if platform detection has results in phase_state
            phase_state = master_flow.phase_state or {}
            platform_results = phase_state.get("platform_detection", {})

            # Consider complete if platform detection has run and produced results
            has_platforms = bool(platform_results.get("platforms", []))
            has_recommendations = bool(
                platform_results.get("adapter_recommendations", [])
            )

            logger.info(
                f"Flow {flow.flow_id} platform detection status: "
                f"has_platforms={has_platforms}, has_recommendations={has_recommendations}"
            )

            return has_platforms or has_recommendations

        except Exception as e:
            logger.error(
                f"Error checking platform detection completion for {flow.flow_id}: {e}"
            )
            return False

    async def advance_to_next_phase(
        self, flow: CollectionFlow, target_phase: str
    ) -> Dict[str, Any]:
        """Advance a flow to the next phase"""
        try:
            logger.info(
                f"Advancing collection flow {flow.flow_id} from {flow.current_phase} to {target_phase}"
            )

            if not flow.master_flow_id:
                raise ValueError(f"Flow {flow.flow_id} has no master_flow_id")

            # Execute the next phase through MFO
            execution_result = await execute_mfo_phase(
                db=self.db_session,
                context=self.context,
                flow_id=str(flow.master_flow_id),
                phase_name=target_phase,
                phase_input={},
            )

            # Sync the child flow state
            await sync_collection_child_flow_state(
                db=self.db_session,
                context=self.context,
                master_flow_id=flow.master_flow_id,
                phase_result=execution_result,
            )

            logger.info(f"Successfully advanced flow {flow.flow_id} to {target_phase}")

            return {
                "status": "success",
                "flow_id": str(flow.flow_id),
                "previous_phase": flow.current_phase,
                "new_phase": target_phase,
                "execution_result": execution_result,
            }

        except Exception as e:
            logger.error(f"Error advancing flow {flow.flow_id} to {target_phase}: {e}")
            return {"status": "failed", "flow_id": str(flow.flow_id), "error": str(e)}

    async def process_stuck_flows(self) -> Dict[str, Any]:
        """Process all stuck flows and attempt to advance them"""
        try:
            stuck_flows = await self.find_stuck_flows()

            results = {
                "total_flows_checked": len(stuck_flows),
                "flows_advanced": 0,
                "flows_skipped": 0,
                "flows_failed": 0,
                "details": [],
            }

            for flow in stuck_flows:
                try:
                    # Check if platform detection is actually complete
                    if await self.check_platform_detection_complete(flow):
                        # Advance to automated_collection phase
                        result = await self.advance_to_next_phase(
                            flow, "automated_collection"
                        )

                        if result["status"] == "success":
                            results["flows_advanced"] += 1
                        else:
                            results["flows_failed"] += 1

                        results["details"].append(result)

                    else:
                        logger.info(
                            f"Flow {flow.flow_id} platform detection not complete, skipping"
                        )
                        results["flows_skipped"] += 1
                        results["details"].append(
                            {
                                "status": "skipped",
                                "flow_id": str(flow.flow_id),
                                "reason": "platform_detection_not_complete",
                            }
                        )

                except Exception as e:
                    logger.error(f"Error processing flow {flow.flow_id}: {e}")
                    results["flows_failed"] += 1
                    results["details"].append(
                        {
                            "status": "failed",
                            "flow_id": str(flow.flow_id),
                            "error": str(e),
                        }
                    )

            logger.info(
                f"Phase progression complete: {results['flows_advanced']} advanced, "
                f"{results['flows_skipped']} skipped, {results['flows_failed']} failed"
            )

            return results

        except Exception as e:
            logger.error(f"Error processing stuck flows: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "total_flows_checked": 0,
                "flows_advanced": 0,
                "flows_skipped": 0,
                "flows_failed": 0,
                "details": [],
            }

    async def advance_specific_flow(
        self, flow_id: str, target_phase: str
    ) -> Dict[str, Any]:
        """Advance a specific flow to a target phase"""
        try:
            # Find the flow
            stmt = select(CollectionFlow).where(
                CollectionFlow.flow_id == UUID(flow_id),
                CollectionFlow.client_account_id == self.context.client_account_id,
                CollectionFlow.engagement_id == self.context.engagement_id,
            )
            result = await self.db_session.execute(stmt)
            flow = result.scalar_one_or_none()

            if not flow:
                return {
                    "status": "failed",
                    "flow_id": flow_id,
                    "error": "Flow not found or access denied",
                }

            return await self.advance_to_next_phase(flow, target_phase)

        except Exception as e:
            logger.error(f"Error advancing specific flow {flow_id}: {e}")
            return {"status": "failed", "flow_id": flow_id, "error": str(e)}
