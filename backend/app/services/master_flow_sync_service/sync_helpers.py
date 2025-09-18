"""Helper methods for synchronization operations."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
import logging

from app.schemas.flow_sync import FlowIssue
from app.models import CollectionFlow, AssessmentFlow

logger = logging.getLogger(__name__)


class SyncHelpers:
    """Helper methods for flow synchronization."""

    def __init__(self, mapper, database):
        self.mapper = mapper
        self.database = database

    def _check_collection_sync_issues(
        self,
        collection_flow: CollectionFlow,
        master_status: str,
        master_progress: float,
        master_phase: Optional[str],
    ) -> List[FlowIssue]:
        """Check for synchronization issues between master and collection flows"""
        issues = []

        # Map master status to collection status
        expected_status = self.mapper.map_master_to_child_status(master_status)

        # Check status mismatch
        if collection_flow.status != expected_status:
            issues.append(
                FlowIssue(
                    issue_type="status_mismatch",
                    description=(
                        f"Collection flow status '{collection_flow.status}' "
                        f"doesn't match expected '{expected_status}'"
                    ),
                    severity="high",
                    suggested_action=f"Update collection flow status to '{expected_status}'",
                )
            )

        # Check progress difference
        collection_progress = collection_flow.progress_percentage or 0
        progress_diff = abs(master_progress - collection_progress)
        if progress_diff > 5.0:  # Allow 5% tolerance
            issues.append(
                FlowIssue(
                    issue_type="progress_mismatch",
                    description=f"Progress difference of {progress_diff:.1f}% detected",
                    severity="medium",
                    suggested_action="Sync progress from master flow",
                )
            )

        # Check phase mismatch
        if master_phase and collection_flow.current_phase != master_phase:
            issues.append(
                FlowIssue(
                    issue_type="phase_mismatch",
                    description=(
                        f"Phase mismatch: collection='{collection_flow.current_phase}', "
                        f"master='{master_phase}'"
                    ),
                    severity="medium",
                    suggested_action=f"Update collection flow phase to '{master_phase}'",
                )
            )

        return issues

    async def _sync_master_with_collection(
        self,
        collection_flow_id: UUID,
        master_status: str,
        master_progress: float,
        master_phase: Optional[str],
        error_message: Optional[str] = None,
    ):
        """Sync master flow data to collection flow"""
        update_fields = {
            "status": self.mapper.map_master_to_child_status(master_status),
            "progress_percentage": master_progress,
            "updated_at": datetime.utcnow(),
        }

        if master_phase:
            update_fields["current_phase"] = master_phase

        if error_message:
            update_fields["error_message"] = error_message

        await self.database.update_collection_flow(collection_flow_id, update_fields)

        logger.info(
            f"Synchronized collection flow {collection_flow_id} with master flow data"
        )

    def _check_assessment_sync_issues(
        self,
        assessment_flow: AssessmentFlow,
        master_status: str,
        master_progress: float,
        master_phase: Optional[str],
    ) -> List[FlowIssue]:
        """Check for synchronization issues between master and assessment flows"""
        issues = []

        # Map master status to assessment status
        expected_status = self.mapper.map_master_to_child_status(master_status)

        # Check status mismatch
        if assessment_flow.status != expected_status:
            issues.append(
                FlowIssue(
                    issue_type="status_mismatch",
                    description=(
                        f"Assessment flow status '{assessment_flow.status}' "
                        f"doesn't match expected '{expected_status}'"
                    ),
                    severity="high",
                    suggested_action=f"Update assessment flow status to '{expected_status}'",
                )
            )

        # Check progress difference
        assessment_progress = assessment_flow.progress or 0
        progress_diff = abs(master_progress - assessment_progress)
        if progress_diff > 5.0:  # Allow 5% tolerance
            issues.append(
                FlowIssue(
                    issue_type="progress_mismatch",
                    description=f"Progress difference of {progress_diff:.1f}% detected",
                    severity="medium",
                    suggested_action="Sync progress from master flow",
                )
            )

        # Check phase mismatch
        if master_phase and assessment_flow.current_phase != master_phase:
            issues.append(
                FlowIssue(
                    issue_type="phase_mismatch",
                    description=(
                        f"Phase mismatch: assessment='{assessment_flow.current_phase}', "
                        f"master='{master_phase}'"
                    ),
                    severity="medium",
                    suggested_action=f"Update assessment flow phase to '{master_phase}'",
                )
            )

        return issues

    async def _sync_master_with_assessment(
        self,
        assessment_flow_id: UUID,
        master_status: str,
        master_progress: float,
        master_phase: Optional[str],
        error_message: Optional[str] = None,
    ):
        """Sync master flow data to assessment flow"""
        update_fields = {
            "status": self.mapper.map_master_to_child_status(master_status),
            "progress": master_progress,
            "updated_at": datetime.utcnow(),
        }

        if master_phase:
            update_fields["current_phase"] = master_phase

        if error_message:
            update_fields["error_message"] = error_message

        await self.database.update_assessment_flow(assessment_flow_id, update_fields)

        logger.info(
            f"Synchronized assessment flow {assessment_flow_id} with master flow data"
        )
