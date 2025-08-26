"""
Workflow Models for Enhanced Collection Orchestrator

This module contains the data models, enums, and progress tracking classes
used by the enhanced collection orchestrator for workflow state management.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Set

logger = logging.getLogger(__name__)


class WorkflowPhase(str, Enum):
    """Enhanced workflow phases for collection orchestration"""

    INITIAL = "initial"
    COLLECTING_BASIC = "collecting_basic"
    COLLECTING_DETAILED = "collecting_detailed"
    REVIEWING = "reviewing"
    COMPLETE = "complete"


class QuestionnaireType(str, Enum):
    """Types of questionnaires in the collection workflow"""

    BOOTSTRAP = "bootstrap"
    DETAILED = "detailed"
    FOLLOWUP = "followup"
    VALIDATION = "validation"


class WorkflowProgress:
    """Tracks workflow progress and state transitions"""

    def __init__(self):
        self.workflow_phase = WorkflowPhase.INITIAL
        self.questionnaire_submissions: Dict[str, Dict[str, Any]] = {}
        self.completed_phases: Set[WorkflowPhase] = set()
        self.bootstrap_completed = False
        self.detailed_collection_started = False
        self.review_phase_entered = False
        self.last_progression_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize workflow progress to dictionary"""
        return {
            "workflow_phase": self.workflow_phase.value,
            "questionnaire_submissions": self.questionnaire_submissions,
            "completed_phases": [phase.value for phase in self.completed_phases],
            "bootstrap_completed": self.bootstrap_completed,
            "detailed_collection_started": self.detailed_collection_started,
            "review_phase_entered": self.review_phase_entered,
            "last_progression_time": (
                self.last_progression_time.isoformat()
                if self.last_progression_time
                else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowProgress":
        """Deserialize workflow progress from dictionary"""
        progress = cls()
        progress.workflow_phase = WorkflowPhase(
            data.get("workflow_phase", WorkflowPhase.INITIAL)
        )
        progress.questionnaire_submissions = data.get("questionnaire_submissions", {})
        progress.completed_phases = {
            WorkflowPhase(phase) for phase in data.get("completed_phases", [])
        }
        progress.bootstrap_completed = data.get("bootstrap_completed", False)
        progress.detailed_collection_started = data.get(
            "detailed_collection_started", False
        )
        progress.review_phase_entered = data.get("review_phase_entered", False)

        last_progression_str = data.get("last_progression_time")
        if last_progression_str:
            try:
                progress.last_progression_time = datetime.fromisoformat(
                    last_progression_str
                )
            except ValueError:
                logger.warning(
                    f"Invalid last_progression_time format: {last_progression_str}"
                )

        return progress
