"""
Collection Flow Rate Limiting Service
Provides rate limiting functionality for collection flow lifecycle operations
to prevent frequent status flips and maintain system stability.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from app.models.collection_flow import CollectionFlow

logger = logging.getLogger(__name__)


class CollectionFlowRateLimitingService:
    """Service for managing rate limits on collection flow operations."""

    def __init__(self, min_operation_interval_minutes: int = 5):
        """
        Initialize the rate limiting service.

        Args:
            min_operation_interval_minutes: Minimum minutes between auto-operations
        """
        self.min_operation_interval_minutes = min_operation_interval_minutes
        self.rate_limit_metadata_key = "rate_limiting"

    def check_rate_limit(
        self, flow: CollectionFlow, operation_type: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if an operation can be performed based on rate limiting rules.

        Args:
            flow: The collection flow to check
            operation_type: Type of operation being attempted (e.g., 'auto_complete', 'auto_cancel')

        Returns:
            Tuple of (can_proceed, reason_if_blocked)
        """
        if not flow.flow_metadata:
            # No metadata means no previous operations, allow
            return True, None

        rate_limit_data = flow.flow_metadata.get(self.rate_limit_metadata_key, {})
        last_operations = rate_limit_data.get("last_operations", {})
        last_operation_time = last_operations.get(operation_type)

        if not last_operation_time:
            # No previous operation of this type, allow
            return True, None

        try:
            last_op_dt = datetime.fromisoformat(last_operation_time)
            time_since_last = datetime.utcnow() - last_op_dt
            min_interval = timedelta(minutes=self.min_operation_interval_minutes)

            if time_since_last < min_interval:
                remaining_minutes = (
                    min_interval - time_since_last
                ).total_seconds() / 60
                minutes_ago = time_since_last.total_seconds() / 60
                reason = (
                    f"Rate limit active. Last {operation_type} operation was "
                    f"{minutes_ago:.1f} minutes ago. Must wait "
                    f"{remaining_minutes:.1f} more minutes."
                )
                return False, reason

        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid timestamp in rate limiting metadata: {e}")
            # If we can't parse the timestamp, allow the operation

        return True, None

    def update_operation_timestamp(
        self, flow: CollectionFlow, operation_type: str
    ) -> None:
        """
        Update the metadata to track when an operation was performed.

        Args:
            flow: The collection flow to update
            operation_type: Type of operation that was performed
        """
        if not flow.flow_metadata:
            flow.flow_metadata = {}

        if self.rate_limit_metadata_key not in flow.flow_metadata:
            flow.flow_metadata[self.rate_limit_metadata_key] = {}

        if "last_operations" not in flow.flow_metadata[self.rate_limit_metadata_key]:
            flow.flow_metadata[self.rate_limit_metadata_key]["last_operations"] = {}

        flow.flow_metadata[self.rate_limit_metadata_key]["last_operations"][
            operation_type
        ] = datetime.utcnow().isoformat()

        # Also track operation count for analytics
        count_key = f"{operation_type}_count"
        current_count = flow.flow_metadata[self.rate_limit_metadata_key].get(
            count_key, 0
        )
        flow.flow_metadata[self.rate_limit_metadata_key][count_key] = current_count + 1

    def get_rate_limit_config(self) -> dict:
        """Get the current rate limit configuration."""
        return {
            "min_interval_minutes": self.min_operation_interval_minutes,
            "description": f"Minimum {self.min_operation_interval_minutes} minutes between auto-operations",
        }
