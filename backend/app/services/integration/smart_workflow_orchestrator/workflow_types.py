"""
Workflow Types and Enums for Smart Workflow Orchestrator

This module contains the core type definitions, enums, and context classes
used throughout the smart workflow orchestration system.

Generated with CC for ADCS end-to-end integration.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List
from uuid import UUID


class WorkflowPhase(Enum):
    """Workflow phases in the smart pipeline"""

    COLLECTION = "collection"
    DISCOVERY = "discovery"
    ASSESSMENT = "assessment"
    COMPLETED = "completed"

    @classmethod
    def get_phase_order(cls) -> Dict[str, int]:
        """Get explicit phase ordering to avoid string comparison brittleness"""
        return {
            cls.COLLECTION: 0,
            cls.DISCOVERY: 1,
            cls.ASSESSMENT: 2,
            cls.COMPLETED: 3,
        }

    def get_order_index(self) -> int:
        """Get the order index for this phase"""
        return self.get_phase_order().get(self, -1)

    def __le__(self, other) -> bool:
        """Less than or equal comparison based on explicit phase ordering"""
        if not isinstance(other, WorkflowPhase):
            return NotImplemented
        return self.get_order_index() <= other.get_order_index()

    def __lt__(self, other) -> bool:
        """Less than comparison based on explicit phase ordering"""
        if not isinstance(other, WorkflowPhase):
            return NotImplemented
        return self.get_order_index() < other.get_order_index()

    def __ge__(self, other) -> bool:
        """Greater than or equal comparison based on explicit phase ordering"""
        if not isinstance(other, WorkflowPhase):
            return NotImplemented
        return self.get_order_index() >= other.get_order_index()

    def __gt__(self, other) -> bool:
        """Greater than comparison based on explicit phase ordering"""
        if not isinstance(other, WorkflowPhase):
            return NotImplemented
        return self.get_order_index() > other.get_order_index()


class WorkflowTransition(Enum):
    """Valid workflow transitions"""

    COLLECTION_TO_DISCOVERY = "collection_to_discovery"
    DISCOVERY_TO_ASSESSMENT = "discovery_to_assessment"
    ASSESSMENT_TO_COMPLETED = "assessment_to_completed"
    # Recovery transitions
    DISCOVERY_TO_COLLECTION = "discovery_to_collection"
    ASSESSMENT_TO_DISCOVERY = "assessment_to_discovery"


class SmartWorkflowContext:
    """Context object that travels through the workflow phases"""

    def __init__(
        self,
        engagement_id: UUID,
        user_id: UUID,
        client_id: UUID,
        workflow_config: Dict[str, Any] = None,
    ):
        self.engagement_id = engagement_id
        self.user_id = user_id
        self.client_id = client_id
        self.workflow_config = workflow_config or {}
        self.created_at = datetime.utcnow()
        self.current_phase = WorkflowPhase.COLLECTION
        self.phase_history: List[Dict[str, Any]] = []
        self.data_quality_metrics: Dict[str, float] = {}
        self.confidence_scores: Dict[str, float] = {}
        self.error_log: List[Dict[str, Any]] = []

    def add_phase_entry(
        self, phase: WorkflowPhase, status: str, metadata: Dict[str, Any] = None
    ):
        """Add an entry to the phase history"""
        entry = {
            "phase": phase.value,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        self.phase_history.append(entry)

    def get_current_phase_data(self) -> Dict[str, Any]:
        """Get data for the current phase"""
        return {
            "phase": self.current_phase.value,
            "engagement_id": str(self.engagement_id),
            "user_id": str(self.user_id),
            "client_id": str(self.client_id),
            "confidence_scores": self.confidence_scores,
            "data_quality_metrics": self.data_quality_metrics,
        }
