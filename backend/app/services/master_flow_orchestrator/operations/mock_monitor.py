"""
Mock Performance Monitor

Provides performance monitoring interface for flow operations.
"""

import logging
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class MockFlowPerformanceMonitor:
    """Mock performance monitor for flow operations"""

    def __init__(self):
        self.active_operations: Dict[str, Dict[str, Any]] = {}

    def start_operation(
        self,
        flow_id: str,
        operation_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start tracking an operation"""
        tracking_id = str(uuid4())

        self.active_operations[tracking_id] = {
            "flow_id": flow_id,
            "operation_type": operation_type,
            "metadata": metadata or {},
            "start_time": self._get_current_time(),
        }

        logger.debug(f"Started operation tracking: {tracking_id} ({operation_type})")
        return tracking_id

    def end_operation(self, tracking_id: str, success: bool = True) -> None:
        """End tracking an operation"""
        if tracking_id in self.active_operations:
            operation = self.active_operations[tracking_id]
            operation["end_time"] = self._get_current_time()
            operation["success"] = success
            operation["duration_ms"] = operation["end_time"] - operation["start_time"]

            logger.debug(
                f"Ended operation tracking: {tracking_id} "
                f"(duration: {operation['duration_ms']}ms, success: {success})"
            )

            # Clean up completed operation
            del self.active_operations[tracking_id]
        else:
            logger.warning(f"Attempted to end unknown operation: {tracking_id}")

    def _get_current_time(self) -> int:
        """Get current time in milliseconds"""
        import time

        return int(time.time() * 1000)
