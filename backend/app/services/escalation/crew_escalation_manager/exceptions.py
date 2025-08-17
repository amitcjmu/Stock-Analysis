"""
Escalation-specific exceptions and error utilities for CrewEscalationManager.
"""

from typing import Optional, Dict, Any


class EscalationError(Exception):
    """Base exception for all escalation-related errors."""

    def __init__(
        self,
        message: str,
        escalation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.escalation_id = escalation_id
        self.context = context or {}
        super().__init__(message)


class CrewExecutionError(EscalationError):
    """Exception raised when crew execution fails."""

    def __init__(
        self,
        message: str,
        crew_type: str,
        escalation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.crew_type = crew_type
        super().__init__(message, escalation_id, context)


class CollaborationError(EscalationError):
    """Exception raised during crew collaboration processes."""

    def __init__(
        self,
        message: str,
        collaboration_strategy: str,
        escalation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.collaboration_strategy = collaboration_strategy
        super().__init__(message, escalation_id, context)


class DelegationError(EscalationError):
    """Exception raised during crew delegation processes."""

    def __init__(
        self,
        message: str,
        delegation_type: str,
        escalation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.delegation_type = delegation_type
        super().__init__(message, escalation_id, context)


class ProgressTrackingError(EscalationError):
    """Exception raised when progress tracking fails."""

    pass


class StrategicCrewError(EscalationError):
    """Exception raised when strategic crew operations fail."""

    def __init__(
        self,
        message: str,
        crew_type: str,
        escalation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.crew_type = crew_type
        super().__init__(message, escalation_id, context)


class EscalationNotFoundError(EscalationError):
    """Exception raised when an escalation is not found."""

    pass


class InvalidEscalationStateError(EscalationError):
    """Exception raised when an escalation is in an invalid state for the requested operation."""

    def __init__(
        self, message: str, current_state: str, escalation_id: Optional[str] = None
    ):
        self.current_state = current_state
        super().__init__(message, escalation_id)
