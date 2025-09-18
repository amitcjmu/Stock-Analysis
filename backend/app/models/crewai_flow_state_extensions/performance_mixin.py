"""
Performance and Analytics Mixin for CrewAI Flow State Extensions

This mixin handles performance tracking, phase execution timing,
and comprehensive performance analytics functionality.
"""

from datetime import datetime


class PerformanceMixin:
    """Mixin for performance tracking and analytics functionality."""

    def update_phase_execution_time(self, phase: str, execution_time_ms: float):
        """Update phase execution time"""
        if not self.phase_execution_times:
            self.phase_execution_times = {}

        self.phase_execution_times[phase] = {
            "execution_time_ms": execution_time_ms,
            "completed_at": datetime.now().isoformat(),
        }

    def get_performance_summary(self) -> dict:
        """Get comprehensive performance summary"""
        return {
            "total_phases": len(self.phase_execution_times or {}),
            "total_execution_time_ms": sum(
                phase.get("execution_time_ms", 0)
                for phase in (self.phase_execution_times or {}).values()
            ),
            "agent_collaboration_entries": len(self.agent_collaboration_log or []),
            "learning_patterns_count": len(self.learning_patterns or []),
            "user_feedback_count": len(self.user_feedback_history or []),
            "memory_usage": self.memory_usage_metrics or {},
            "crew_coordination": self.crew_coordination_analytics or {},
            "phase_transitions_count": len(self.phase_transitions or []),
            "error_count": len(self.error_history or []),
            "retry_count": self.retry_count,
        }
