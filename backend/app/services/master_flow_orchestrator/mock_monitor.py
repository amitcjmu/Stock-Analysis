"""
Mock Performance Monitor to avoid psutil dependency
"""

import uuid
from typing import Any, Dict, Optional


class MockFlowPerformanceMonitor:
    """Mock implementation to avoid psutil dependency"""

    def start_operation(
        self,
        flow_id: str,
        operation_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        return f"mock-{uuid.uuid4()}"

    def end_operation(
        self,
        tracking_id: str,
        success: bool = True,
        result_metadata: Optional[Dict[str, Any]] = None,
    ):
        return None

    def get_flow_performance_summary(self, flow_id: str) -> Dict[str, Any]:
        return {
            "flow_id": flow_id,
            "total_operations": 0,
            "message": "Performance monitoring disabled",
        }

    def get_system_performance_overview(self) -> Dict[str, Any]:
        return {"status": "disabled", "message": "Performance monitoring unavailable"}

    def record_audit_event(self, audit_entry: Dict[str, Any]):
        pass

    def clear_flow_metrics(self, flow_id: str):
        """Clear all metrics for a specific flow"""
        pass
