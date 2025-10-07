"""
Base classes and utility functions for Collection Flow Cleanup Service
"""

import logging
from datetime import datetime

from app.models.collection_flow import CollectionFlow, CollectionFlowStatus

logger = logging.getLogger(__name__)


class CleanupUtils:
    """Utility functions for cleanup operations"""

    @staticmethod
    def calculate_flow_size(flow: CollectionFlow) -> int:
        """Calculate estimated size of flow data in bytes"""
        size = 0

        # Base flow data
        size += len(str(flow.flow_metadata)) if flow.flow_metadata else 0
        size += len(str(flow.collection_config)) if flow.collection_config else 0
        size += len(str(flow.phase_state)) if flow.phase_state else 0
        size += len(str(flow.user_inputs)) if flow.user_inputs else 0
        size += len(str(flow.phase_results)) if flow.phase_results else 0
        size += len(str(flow.agent_insights)) if flow.agent_insights else 0
        size += len(str(flow.collected_platforms)) if flow.collected_platforms else 0
        size += len(str(flow.collection_results)) if flow.collection_results else 0
        size += len(str(flow.gap_analysis_results)) if flow.gap_analysis_results else 0
        size += len(str(flow.error_details)) if flow.error_details else 0

        # Text fields
        size += len(flow.flow_name) if flow.flow_name else 0
        size += len(flow.error_message) if flow.error_message else 0

        # Related records (estimated)
        if hasattr(flow, "data_gaps") and flow.data_gaps:
            size += len(flow.data_gaps) * 500  # Estimate 500 bytes per gap analysis

        if hasattr(flow, "questionnaire_responses") and flow.questionnaire_responses:
            size += (
                len(flow.questionnaire_responses) * 1000
            )  # Estimate 1KB per response

        return size

    @staticmethod
    def is_cleanup_candidate(flow: CollectionFlow, current_time: datetime) -> bool:
        """Determine if a flow is a candidate for cleanup"""
        age_days = (current_time - flow.updated_at).days

        # Failed flows older than 7 days
        if flow.status == CollectionFlowStatus.FAILED.value and age_days > 7:
            return True

        # Cancelled flows older than 30 days
        if flow.status == CollectionFlowStatus.CANCELLED.value and age_days > 30:
            return True

        # Completed flows older than 90 days
        if flow.status == CollectionFlowStatus.COMPLETED.value and age_days > 90:
            return True

        # Stale incomplete flows (no update in 7+ days)
        # Per ADR-012: Check lifecycle states (not phase-based states)
        if (
            flow.status
            in [
                CollectionFlowStatus.INITIALIZED.value,
                CollectionFlowStatus.RUNNING.value,
                CollectionFlowStatus.PAUSED.value,
            ]
            and age_days > 7
        ):
            return True

        return False

    @staticmethod
    def get_cleanup_reason(flow: CollectionFlow, current_time: datetime) -> str:
        """Get the reason why a flow is recommended for cleanup"""
        age_days = (current_time - flow.updated_at).days

        if flow.status == CollectionFlowStatus.FAILED.value:
            return f"Failed flow, {age_days} days old"
        elif flow.status == CollectionFlowStatus.CANCELLED.value:
            return f"Cancelled flow, {age_days} days old"
        elif flow.status == CollectionFlowStatus.COMPLETED.value:
            return f"Completed flow, {age_days} days old"
        else:
            return f"Stale incomplete flow, no activity for {age_days} days"
