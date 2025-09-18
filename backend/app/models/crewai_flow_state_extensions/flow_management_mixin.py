"""
Flow Management Mixin for CrewAI Flow State Extensions

This mixin handles phase transitions, error management, and flow hierarchy
management functionality.
"""

from datetime import datetime
from typing import Optional


class FlowManagementMixin:
    """Mixin for flow management and phase control functionality."""

    def add_phase_transition(self, phase: str, status: str, metadata: dict = None):
        """Add a phase transition record"""
        if not self.phase_transitions:
            self.phase_transitions = []

        transition = {
            "phase": phase,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }

        self.phase_transitions.append(transition)

    def add_error(self, phase: str, error: str, details: dict = None):
        """Add an error to the error history"""
        if not self.error_history:
            self.error_history = []

        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "error": error,
            "details": details or {},
            "retry_count": self.retry_count,
        }

        self.error_history.append(error_entry)

        # Keep only last 100 errors
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]

    def add_child_flow(self, child_flow_id: str):
        """Add a child flow ID"""
        if not self.child_flow_ids:
            self.child_flow_ids = []

        if child_flow_id not in self.child_flow_ids:
            self.child_flow_ids.append(child_flow_id)

    def remove_child_flow(self, child_flow_id: str):
        """Remove a child flow ID"""
        if self.child_flow_ids and child_flow_id in self.child_flow_ids:
            self.child_flow_ids.remove(child_flow_id)

    def update_flow_metadata(self, key: str, value):
        """Update a specific key in flow metadata"""
        if not self.flow_metadata:
            self.flow_metadata = {}

        self.flow_metadata[key] = value

    def get_current_phase(self) -> Optional[str]:
        """Get the current active phase from transitions"""
        if not self.phase_transitions:
            return None

        # Find the last active/processing phase
        for transition in reversed(self.phase_transitions):
            if transition.get("status") in ["active", "processing"]:
                return transition.get("phase")

        # If no active phase, return the last phase
        if self.phase_transitions:
            return self.phase_transitions[-1].get("phase")

        return None
