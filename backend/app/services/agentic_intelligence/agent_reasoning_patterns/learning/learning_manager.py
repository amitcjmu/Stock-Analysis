"""
Continuous Learning Manager Module

This module manages continuous learning across multiple reasoning sessions,
tracks learning progress and coordinates pattern evolution.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ContinuousLearningManager:
    """
    Manages continuous learning across multiple reasoning sessions.
    Tracks learning progress and coordinates pattern evolution.
    """

    def __init__(
        self, memory_manager, client_account_id: uuid.UUID, engagement_id: uuid.UUID
    ):
        self.memory_manager = memory_manager
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.logger = logger
        self.learning_sessions = []

    async def start_learning_session(self, session_context: Dict[str, Any]) -> str:
        """Start a new learning session"""
        session_id = str(uuid.uuid4())
        session = {
            "session_id": session_id,
            "start_time": datetime.utcnow().isoformat(),
            "context": session_context,
            "patterns_discovered": [],
            "feedback_received": [],
            "performance_metrics": {
                "accuracy_scores": [],
                "confidence_levels": [],
                "pattern_applications": 0,
            },
        }
        self.learning_sessions.append(session)
        return session_id

    async def end_learning_session(self, session_id: str) -> Dict[str, Any]:
        """End a learning session and generate learning summary"""
        session = next(
            (s for s in self.learning_sessions if s["session_id"] == session_id), None
        )
        if not session:
            return {}

        session["end_time"] = datetime.utcnow().isoformat()

        # Calculate session metrics
        performance = session["performance_metrics"]
        avg_accuracy = (
            sum(performance["accuracy_scores"]) / len(performance["accuracy_scores"])
            if performance["accuracy_scores"]
            else 0.0
        )
        avg_confidence = (
            sum(performance["confidence_levels"])
            / len(performance["confidence_levels"])
            if performance["confidence_levels"]
            else 0.0
        )

        learning_summary = {
            "session_id": session_id,
            "duration_minutes": self._calculate_session_duration(session),
            "patterns_discovered": len(session["patterns_discovered"]),
            "feedback_instances": len(session["feedback_received"]),
            "average_accuracy": avg_accuracy,
            "average_confidence": avg_confidence,
            "learning_progress": self._assess_learning_progress(session),
        }

        return learning_summary

    def _calculate_session_duration(self, session: Dict[str, Any]) -> float:
        """Calculate session duration in minutes"""
        try:
            start_time = datetime.fromisoformat(session["start_time"])
            end_time = datetime.fromisoformat(
                session.get("end_time", datetime.utcnow().isoformat())
            )
            duration = (end_time - start_time).total_seconds() / 60
            return round(duration, 2)
        except (ValueError, TypeError):
            return 0.0

    def _assess_learning_progress(self, session: Dict[str, Any]) -> str:
        """Assess learning progress for the session"""
        patterns_count = len(session["patterns_discovered"])
        feedback_count = len(session["feedback_received"])

        if patterns_count >= 3 and feedback_count >= 2:
            return "excellent"
        elif patterns_count >= 1 or feedback_count >= 1:
            return "good"
        else:
            return "minimal"
