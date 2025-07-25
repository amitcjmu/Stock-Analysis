"""
Master Flow Orchestrator Internal Sync Agent

Implements ADR-012: Flow Status Management Separation
Handles terminal state synchronization (completed, failed, deleted) based on
child flow status and database state validation.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.core.context import RequestContext
from app.core.exceptions import FlowNotFoundError
from app.repositories.assessment_flow_repository import AssessmentFlowRepository
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class MFOSyncAgent:
    """
    Master Flow Orchestrator Internal Sync Agent

    Responsible for:
    1. Monitoring child flow completion status
    2. Validating database state changes are complete
    3. Updating master flow status for terminal states
    4. Handling cross-flow transitions
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.master_repo = CrewAIFlowStateExtensionsRepository(
            db, context.client_account_id, context.engagement_id, context.user_id
        )
        self._child_repos = {}

    def _get_child_repo(self, flow_type: str):
        """Get appropriate child flow repository"""
        if flow_type not in self._child_repos:
            if flow_type == "discovery":
                self._child_repos[flow_type] = DiscoveryFlowRepository(
                    self.db,
                    self.context.client_account_id,
                    self.context.engagement_id,
                    self.context.user_id,
                )
            elif flow_type == "assessment":
                self._child_repos[flow_type] = AssessmentFlowRepository(
                    self.db,
                    self.context.client_account_id,
                    self.context.engagement_id,
                    self.context.user_id,
                )
            else:
                raise ValueError(f"Unsupported flow type: {flow_type}")

        return self._child_repos[flow_type]

    async def reconcile_master_status(self, master_flow_id: str) -> Dict[str, Any]:
        """
        Reconcile master flow status based on child flow completion and database state

        This is called periodically or triggered by child flow completion events
        """
        logger.info(f"🔄 [MFOSyncAgent] Reconciling master status: {master_flow_id}")

        try:
            # Get master flow
            master_flow = await self.master_repo.get_by_flow_id(master_flow_id)
            if not master_flow:
                raise FlowNotFoundError(master_flow_id)

            # Get child flow
            child_repo = self._get_child_repo(master_flow.flow_type)
            child_flow = await child_repo.get_by_flow_id(master_flow_id)
            if not child_flow:
                logger.warning(
                    f"⚠️ [MFOSyncAgent] Child flow not found: {master_flow_id}"
                )
                return {"success": False, "error": "Child flow not found"}

            # Determine master status based on child flow and database state
            new_master_status = await self._determine_master_status(
                master_flow, child_flow
            )

            # Update master flow if status changed
            if new_master_status != master_flow.flow_status:
                await self.master_repo.update_flow_status(
                    flow_id=master_flow_id,
                    status=new_master_status,
                    metadata={
                        "operation": "sync_agent_reconciliation",
                        "previous_status": master_flow.flow_status,
                        "child_status": child_flow.status,
                        "reconciled_at": datetime.utcnow().isoformat(),
                    },
                )

                logger.info(
                    f"✅ [MFOSyncAgent] Master status updated: {master_flow_id} -> {new_master_status}"
                )

                return {
                    "success": True,
                    "status_changed": True,
                    "previous_status": master_flow.flow_status,
                    "new_status": new_master_status,
                    "child_status": child_flow.status,
                }
            else:
                logger.info(
                    f"ℹ️ [MFOSyncAgent] No status change needed: {master_flow_id}"
                )
                return {
                    "success": True,
                    "status_changed": False,
                    "current_status": master_flow.flow_status,
                    "child_status": child_flow.status,
                }

        except Exception as e:
            logger.error(
                f"❌ [MFOSyncAgent] Reconciliation failed: {master_flow_id} - {e}"
            )
            return {"success": False, "error": str(e)}

    async def _determine_master_status(self, master_flow, child_flow) -> str:
        """
        Determine master flow status based on child flow status and database state

        ADR-012: Master flow handles lifecycle, child flow handles operations
        """
        # If master flow is deleted, don't change it
        if master_flow.flow_status == "deleted":
            return "deleted"

        # Check database state completion
        db_state_complete = await self._verify_db_state_complete(
            master_flow.flow_id, master_flow.flow_type
        )

        # Decision logic based on child flow status
        if child_flow.status == "completed":
            if db_state_complete:
                return "completed"
            else:
                logger.warning(
                    f"⚠️ [MFOSyncAgent] Child completed but DB state incomplete: {master_flow.flow_id}"
                )
                return "failed"  # Child says complete but data not persisted

        elif child_flow.status == "failed":
            return "failed"

        elif child_flow.status in ["active", "processing"]:
            return "running"

        elif child_flow.status == "paused":
            return "paused"

        elif child_flow.status == "waiting_for_approval":
            return "paused"  # Map user approval to paused in master

        else:
            # Unknown child status, keep current master status
            logger.warning(
                f"⚠️ [MFOSyncAgent] Unknown child status: {child_flow.status}"
            )
            return master_flow.flow_status

    async def _verify_db_state_complete(self, flow_id: str, flow_type: str) -> bool:
        """
        Verify that all expected database changes have been completed

        This checks that the flow has actually persisted its results to the database
        """
        try:
            if flow_type == "discovery":
                return await self._verify_discovery_db_state(flow_id)
            elif flow_type == "assessment":
                return await self._verify_assessment_db_state(flow_id)
            else:
                logger.warning(
                    f"⚠️ [MFOSyncAgent] Unknown flow type for DB verification: {flow_type}"
                )
                return True  # Assume complete if we don't know how to verify

        except Exception as e:
            logger.error(
                f"❌ [MFOSyncAgent] DB state verification failed: {flow_id} - {e}"
            )
            return False

    async def _verify_discovery_db_state(self, flow_id: str) -> bool:
        """Verify discovery flow database state completion"""
        try:
            from app.models.asset import Asset
            from app.models.discovery_flow import DiscoveryFlow
            from sqlalchemy import func, select

            # Check if discovery flow exists and has completed phases
            discovery_query = select(DiscoveryFlow).where(
                DiscoveryFlow.flow_id == flow_id
            )
            discovery_result = await self.db.execute(discovery_query)
            discovery_flow = discovery_result.scalar_one_or_none()

            if not discovery_flow:
                return False

            # Check if assets were created (if asset_inventory phase completed)
            if discovery_flow.asset_inventory_completed:
                assets_query = select(func.count(Asset.id)).where(
                    Asset.client_account_id == self.context.client_account_id,
                    Asset.engagement_id == self.context.engagement_id,
                )
                assets_result = await self.db.execute(assets_query)
                assets_count = assets_result.scalar()

                if assets_count == 0:
                    logger.warning(
                        f"⚠️ [MFOSyncAgent] Asset inventory marked complete but no assets found: {flow_id}"
                    )
                    return False

            # Check if data cleansing results exist (if data_cleansing phase completed)
            if discovery_flow.data_cleansing_completed:
                # Add check for cleansing results in flow state or separate table
                pass

            return True

        except Exception as e:
            logger.error(
                f"❌ [MFOSyncAgent] Discovery DB state verification failed: {flow_id} - {e}"
            )
            return False

    async def _verify_assessment_db_state(self, flow_id: str) -> bool:
        """Verify assessment flow database state completion"""
        try:
            from app.models.assessment_flow import AssessmentFlow
            from sqlalchemy import select

            # Check if assessment flow exists and has completed phases
            assessment_query = select(AssessmentFlow).where(
                AssessmentFlow.id == flow_id
            )
            assessment_result = await self.db.execute(assessment_query)
            assessment_flow = assessment_result.scalar_one_or_none()

            if not assessment_flow:
                return False

            # Add specific assessment completion checks
            # (e.g., SixR decisions, tech debt analysis, etc.)

            return True

        except Exception as e:
            logger.error(
                f"❌ [MFOSyncAgent] Assessment DB state verification failed: {flow_id} - {e}"
            )
            return False

    async def handle_child_flow_completion(
        self, flow_id: str, child_status: str
    ) -> Dict[str, Any]:
        """
        Handle child flow completion events

        Called when a child flow reports completion or failure
        """
        logger.info(
            f"📢 [MFOSyncAgent] Handling child flow completion: {flow_id} -> {child_status}"
        )

        if child_status in ["completed", "failed"]:
            # Trigger reconciliation for terminal states
            return await self.reconcile_master_status(flow_id)
        else:
            # Non-terminal states don't require master flow updates
            return {"success": True, "action": "no_master_update_required"}

    async def monitor_flows_health(self) -> Dict[str, Any]:
        """
        Monitor overall flow health and identify inconsistencies

        This can be called periodically to detect and fix issues
        """
        logger.info("🔍 [MFOSyncAgent] Monitoring flow health")

        try:
            # Get all active master flows
            from app.models.crewai_flow_state_extensions import (
                CrewAIFlowStateExtensions,
            )
            from sqlalchemy import select

            master_flows_query = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.client_account_id
                == self.context.client_account_id,
                CrewAIFlowStateExtensions.engagement_id == self.context.engagement_id,
                CrewAIFlowStateExtensions.flow_status.in_(
                    ["running", "paused", "completed", "failed"]
                ),
            )

            master_flows_result = await self.db.execute(master_flows_query)
            master_flows = master_flows_result.scalars().all()

            health_report = {
                "total_flows": len(master_flows),
                "inconsistencies": [],
                "reconciled_flows": [],
            }

            for master_flow in master_flows:
                try:
                    # Check for inconsistencies
                    child_repo = self._get_child_repo(master_flow.flow_type)
                    child_flow = await child_repo.get_by_flow_id(master_flow.flow_id)

                    if not child_flow:
                        health_report["inconsistencies"].append(
                            {
                                "flow_id": master_flow.flow_id,
                                "issue": "child_flow_missing",
                                "master_status": master_flow.flow_status,
                            }
                        )
                        continue

                    # Check if reconciliation is needed
                    expected_status = await self._determine_master_status(
                        master_flow, child_flow
                    )
                    if expected_status != master_flow.flow_status:
                        # Reconcile the flow
                        reconcile_result = await self.reconcile_master_status(
                            master_flow.flow_id
                        )
                        if reconcile_result["success"]:
                            health_report["reconciled_flows"].append(
                                {
                                    "flow_id": master_flow.flow_id,
                                    "previous_status": master_flow.flow_status,
                                    "new_status": expected_status,
                                }
                            )
                        else:
                            health_report["inconsistencies"].append(
                                {
                                    "flow_id": master_flow.flow_id,
                                    "issue": "reconciliation_failed",
                                    "error": reconcile_result.get("error"),
                                }
                            )

                except Exception as e:
                    health_report["inconsistencies"].append(
                        {
                            "flow_id": master_flow.flow_id,
                            "issue": "health_check_failed",
                            "error": str(e),
                        }
                    )

            logger.info(f"✅ [MFOSyncAgent] Health monitoring complete: {health_report}")
            return health_report

        except Exception as e:
            logger.error(f"❌ [MFOSyncAgent] Health monitoring failed: {e}")
            return {"success": False, "error": str(e)}


# Factory function for dependency injection
async def get_mfo_sync_agent(db: AsyncSession, context: RequestContext) -> MFOSyncAgent:
    """Factory function to create MFOSyncAgent with proper dependencies"""
    return MFOSyncAgent(db, context)
