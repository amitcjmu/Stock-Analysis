"""
Core Master Flow Synchronization Service
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.context import RequestContext

from .models import FlowSyncStatus, SyncResult
from .database import FlowSyncDatabase
from .mappers import FlowStatusMapper
from .sync_helpers import SyncHelpers

logger = logging.getLogger(__name__)


class MasterFlowSyncService:
    """Service for maintaining master-child flow synchronization"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.database = FlowSyncDatabase(db, context)
        self.mapper = FlowStatusMapper()
        self.helpers = SyncHelpers(self.mapper, self.database)

    async def synchronize_collection_flow(
        self,
        collection_flow_id: UUID,
        master_flow_id: Optional[UUID] = None,
        force_sync: bool = False,
    ) -> FlowSyncStatus:
        """
        Synchronize a specific collection flow with its master flow.

        Args:
            collection_flow_id: ID of the collection flow to sync
            master_flow_id: Optional master flow ID (will be retrieved if not provided)
            force_sync: Whether to force synchronization even if flows appear in sync

        Returns:
            FlowSyncStatus with sync results and any issues found
        """
        collection_flows = await self.database.get_all_collection_flows()
        collection_flow = next(
            (cf for cf in collection_flows if cf.flow_id == collection_flow_id), None
        )

        if not collection_flow:
            logger.warning(f"Collection flow {collection_flow_id} not found")
            return FlowSyncStatus(
                master_flow_id=master_flow_id
                or UUID("00000000-0000-0000-0000-000000000000"),
                child_flow_id=collection_flow_id,
                child_flow_type="collection",
                is_synchronized=False,
                master_status="unknown",
                child_status="unknown",
                status_match=False,
                master_progress=0.0,
                child_progress=0.0,
                progress_diff=0.0,
                phase_match=False,
                issues=["Collection flow not found"],
            )

        # Get or determine master flow ID
        if not master_flow_id:
            master_flow_id = collection_flow.master_flow_id

        if not master_flow_id:
            logger.warning(
                f"No master flow ID for collection flow {collection_flow_id}"
            )
            return FlowSyncStatus(
                master_flow_id=UUID("00000000-0000-0000-0000-000000000000"),
                child_flow_id=collection_flow_id,
                child_flow_type="collection",
                is_synchronized=False,
                master_status="unknown",
                child_status=collection_flow.status,
                status_match=False,
                master_progress=0.0,
                child_progress=collection_flow.progress_percentage or 0.0,
                progress_diff=0.0,
                phase_match=False,
                issues=["No master flow ID available"],
            )

        # Check sync issues and create status
        sync_status = await self._check_sync_issues(collection_flow, master_flow_id)

        # Perform synchronization if needed
        if not sync_status.is_synchronized or force_sync:
            try:
                await self._sync_master_with_child(collection_flow, master_flow_id)
                sync_status.is_synchronized = True
                sync_status.last_sync_at = datetime.utcnow()
                logger.info(
                    f"Successfully synchronized collection flow {collection_flow_id} with master {master_flow_id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to sync collection flow {collection_flow_id}: {e}"
                )
                sync_status.issues.append(f"Synchronization failed: {str(e)}")

        return sync_status

    async def synchronize_assessment_flow(
        self,
        assessment_flow_id: UUID,
        master_flow_id: Optional[UUID] = None,
        force_sync: bool = False,
    ) -> FlowSyncStatus:
        """Synchronize a specific assessment flow with its master flow"""
        assessment_flows = await self.database.get_all_assessment_flows()
        assessment_flow = next(
            (af for af in assessment_flows if af.id == assessment_flow_id), None
        )

        if not assessment_flow:
            logger.warning(f"Assessment flow {assessment_flow_id} not found")
            return FlowSyncStatus(
                master_flow_id=master_flow_id
                or UUID("00000000-0000-0000-0000-000000000000"),
                child_flow_id=assessment_flow_id,
                child_flow_type="assessment",
                is_synchronized=False,
                master_status="unknown",
                child_status="unknown",
                status_match=False,
                master_progress=0.0,
                child_progress=0.0,
                progress_diff=0.0,
                phase_match=False,
                issues=["Assessment flow not found"],
            )

        # Get or determine master flow ID
        if not master_flow_id:
            master_flow_id = assessment_flow.master_flow_id

        if not master_flow_id:
            logger.warning(
                f"No master flow ID for assessment flow {assessment_flow_id}"
            )
            return FlowSyncStatus(
                master_flow_id=UUID("00000000-0000-0000-0000-000000000000"),
                child_flow_id=assessment_flow_id,
                child_flow_type="assessment",
                is_synchronized=False,
                master_status="unknown",
                child_status=assessment_flow.status,
                status_match=False,
                master_progress=0.0,
                child_progress=assessment_flow.progress or 0.0,
                progress_diff=0.0,
                phase_match=False,
                issues=["No master flow ID available"],
            )

        # Check sync issues and create status
        sync_status = await self.helpers._check_assessment_sync_issues(
            assessment_flow, master_flow_id
        )

        # Perform synchronization if needed
        if not sync_status.is_synchronized or force_sync:
            try:
                await self.helpers._sync_master_with_assessment(
                    assessment_flow, master_flow_id
                )
                sync_status.is_synchronized = True
                sync_status.last_sync_at = datetime.utcnow()
                logger.info(
                    f"Successfully synchronized assessment flow {assessment_flow_id} with master {master_flow_id}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to sync assessment flow {assessment_flow_id}: {e}"
                )
                sync_status.issues.append(f"Synchronization failed: {str(e)}")

        return sync_status

    async def synchronize_all_flows(self) -> SyncResult:
        """
        Synchronize all flows for the current tenant.

        Returns:
            SyncResult containing summary of synchronization operation
        """
        sync_result = SyncResult(
            success=True,
            flows_processed=0,
            flows_synchronized=0,
            issues_fixed=0,
            synchronized_at=datetime.utcnow(),
        )

        try:
            # Get all flows
            collection_flows = await self.database.get_all_collection_flows()
            assessment_flows = await self.database.get_all_assessment_flows()

            all_flows = collection_flows + assessment_flows
            sync_result.flows_processed = len(all_flows)

            # Synchronize each flow
            for flow in collection_flows:
                try:
                    sync_status = await self.synchronize_collection_flow(flow.flow_id)
                    sync_result.sync_statuses.append(sync_status)
                    if sync_status.is_synchronized:
                        sync_result.flows_synchronized += 1
                    if sync_status.issues:
                        sync_result.issues_fixed += len(sync_status.issues)
                except Exception as e:
                    logger.error(f"Failed to sync collection flow {flow.flow_id}: {e}")
                    sync_result.errors.append(str(e))
                    sync_result.success = False

            for flow in assessment_flows:
                try:
                    sync_status = await self.synchronize_assessment_flow(flow.id)
                    sync_result.sync_statuses.append(sync_status)
                    if sync_status.is_synchronized:
                        sync_result.flows_synchronized += 1
                    if sync_status.issues:
                        sync_result.issues_fixed += len(sync_status.issues)
                except Exception as e:
                    logger.error(f"Failed to sync assessment flow {flow.id}: {e}")
                    sync_result.errors.append(str(e))
                    sync_result.success = False

        except Exception as e:
            logger.error(f"Error during bulk synchronization: {e}")
            sync_result.success = False
            sync_result.errors.append(str(e))

        return sync_result

    async def sync_master_to_collection_flow(
        self, master_flow_id: str, collection_flow_id: str
    ):
        """
        Sync master flow changes back to collection flow.
        This is used after agent execution to update the Collection Progress Monitor.
        """
        logger.info(
            f"Syncing master flow {master_flow_id} to collection flow {collection_flow_id}"
        )

        # Get master flow
        master_flow = await self.database.get_master_flow(UUID(master_flow_id))
        if not master_flow:
            logger.warning(f"Master flow not found: {master_flow_id}")
            return

        # Map and update collection flow with master flow data
        # Per ADR-012: Child flows OWN their current_phase progression
        # Master flow only tracks high-level lifecycle status
        update_fields = {
            "status": self.mapper.map_master_to_child_status(master_flow.flow_status),
            "progress_percentage": self.mapper.extract_progress_from_metadata(
                master_flow.flow_metadata
            )
            or 0,
            # ADR-012: Do NOT overwrite current_phase - child flow owns operational phase
            # "current_phase": self.mapper.extract_phase_from_metadata(
            #     master_flow.flow_metadata
            # ),
            "updated_at": datetime.utcnow(),
        }

        # Add additional fields if master flow has them
        if hasattr(master_flow, "error_message") and master_flow.error_message:
            update_fields["error_message"] = master_flow.error_message

        # Sync error_details if available
        if hasattr(master_flow, "error_details") and master_flow.error_details:
            update_fields["error_details"] = master_flow.error_details

        await self.database.update_collection_flow(
            UUID(collection_flow_id), update_fields
        )

        logger.info(
            f"Successfully synced master flow {master_flow_id} to collection flow {collection_flow_id}"
        )

    # Private helper methods
    async def _check_sync_issues(
        self, collection_flow, master_flow_id: UUID
    ) -> FlowSyncStatus:
        """Check for synchronization issues between flows"""
        master_flow = await self.database.get_master_flow(master_flow_id)

        if not master_flow:
            return FlowSyncStatus(
                master_flow_id=master_flow_id,
                child_flow_id=collection_flow.flow_id,
                child_flow_type="collection",
                is_synchronized=False,
                master_status="unknown",
                child_status=collection_flow.status,
                status_match=False,
                master_progress=0.0,
                child_progress=collection_flow.progress_percentage or 0.0,
                progress_diff=collection_flow.progress_percentage or 0.0,
                phase_match=False,
                issues=["Master flow not found"],
                recommendations=["Create or restore master flow"],
            )

        # Compare statuses and build sync status
        status_match = self.mapper.status_compatible(
            master_flow.flow_status, collection_flow.status
        )
        master_progress = self.mapper.extract_progress_from_metadata(
            master_flow.flow_metadata
        )
        child_progress = collection_flow.progress_percentage or 0.0
        progress_diff = abs(master_progress - child_progress)

        issues = []
        recommendations = []

        if not status_match:
            issues.append(
                f"Status mismatch: master={master_flow.flow_status}, child={collection_flow.status}"
            )
            recommendations.append("Synchronize flow statuses")

        if progress_diff > 10.0:  # More than 10% difference
            issues.append(
                f"Progress mismatch: master={master_progress}%, child={child_progress}%"
            )
            recommendations.append("Update progress percentages")

        return FlowSyncStatus(
            master_flow_id=master_flow_id,
            child_flow_id=collection_flow.flow_id,
            child_flow_type="collection",
            is_synchronized=len(issues) == 0,
            master_status=master_flow.flow_status,
            child_status=collection_flow.status,
            status_match=status_match,
            master_progress=master_progress,
            child_progress=child_progress,
            progress_diff=progress_diff,
            master_phase=self.mapper.extract_phase_from_metadata(
                master_flow.flow_metadata
            ),
            child_phase=collection_flow.current_phase,
            phase_match=True,  # Simplified for now
            issues=issues,
            recommendations=recommendations,
        )

    async def _sync_master_with_child(self, collection_flow, master_flow_id: UUID):
        """Synchronize master flow with child flow data"""
        # Map child status to master status
        new_master_status = self.mapper.map_child_to_master_status(
            collection_flow.status
        )
        new_master_phase = self.mapper.map_child_to_master_phase(
            collection_flow.current_phase or ""
        )

        # Update master flow
        update_fields = {
            "flow_status": new_master_status,
            "current_phase": new_master_phase,
            "updated_at": datetime.utcnow(),
        }

        # Update flow metadata with progress
        if collection_flow.progress_percentage is not None:
            master_flow = await self.database.get_master_flow(master_flow_id)
            if master_flow and master_flow.flow_metadata:
                flow_metadata = master_flow.flow_metadata.copy()
            else:
                flow_metadata = {}

            flow_metadata["collection_progress"] = collection_flow.progress_percentage
            flow_metadata["child_flow_sync"] = datetime.utcnow().isoformat()
            update_fields["flow_metadata"] = flow_metadata

        await self.database.update_master_flow(master_flow_id, update_fields)

        logger.info(
            f"Updated master flow {master_flow_id}: status={new_master_status}, phase={new_master_phase}"
        )
