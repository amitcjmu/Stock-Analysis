"""
Collaboration and Memory Management Mixin for CrewAI Flow State Extensions

This mixin handles agent collaboration logging, memory usage tracking,
and learning pattern management functionality.
"""

from datetime import datetime


class CollaborationMixin:
    """Mixin for agent collaboration and memory management functionality."""

    def add_agent_collaboration_entry(
        self, agent_name: str, action: str, details: dict
    ):
        """Add entry to agent collaboration log"""
        if not self.agent_collaboration_log:
            self.agent_collaboration_log = []

        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent_name,
            "action": action,
            "details": details,
        }

        self.agent_collaboration_log.append(entry)

        # Keep only last 100 entries
        if len(self.agent_collaboration_log) > 100:
            self.agent_collaboration_log = self.agent_collaboration_log[-100:]

    def update_memory_usage_metrics(self, metrics: dict):
        """Update memory usage metrics"""
        if not self.memory_usage_metrics:
            self.memory_usage_metrics = {}

        self.memory_usage_metrics.update(
            {"last_updated": datetime.now().isoformat(), **metrics}
        )

    def add_learning_pattern(self, pattern_type: str, pattern_data: dict):
        """Add learning pattern"""
        if not self.learning_patterns:
            self.learning_patterns = []

        pattern = {
            "timestamp": datetime.now().isoformat(),
            "type": pattern_type,
            "data": pattern_data,
        }

        self.learning_patterns.append(pattern)

        # Keep only last 50 patterns
        if len(self.learning_patterns) > 50:
            self.learning_patterns = self.learning_patterns[-50:]

    def add_user_feedback(self, feedback_type: str, feedback_data: dict):
        """Add user feedback to history"""
        if not self.user_feedback_history:
            self.user_feedback_history = []

        feedback = {
            "timestamp": datetime.now().isoformat(),
            "type": feedback_type,
            "data": feedback_data,
        }

        self.user_feedback_history.append(feedback)

        # Keep only last 30 feedback entries
        if len(self.user_feedback_history) > 30:
            self.user_feedback_history = self.user_feedback_history[-30:]
