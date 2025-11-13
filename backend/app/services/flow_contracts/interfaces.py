"""
Flow Orchestration Interfaces

Defines abstract interfaces for flow orchestration to enable dependency injection
and break circular dependencies between MasterFlowOrchestrator and other services.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple


class IFlowOrchestrator(ABC):
    """
    Interface for flow orchestration operations.

    This interface defines the contract for flow orchestrators, allowing
    services to depend on the interface rather than concrete implementations.
    This breaks circular dependencies while maintaining type safety.
    """

    @abstractmethod
    async def create_flow(
        self,
        flow_type: str,
        flow_name: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None,
        initial_state: Optional[Dict[str, Any]] = None,
        _retry_count: int = 0,
        atomic: bool = False,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Create a new flow of any type.

        Args:
            flow_type: Type of flow to create
            flow_name: Optional name for the flow
            configuration: Optional configuration dict
            initial_state: Optional initial state dict
            _retry_count: Internal retry counter
            atomic: Whether to use atomic operations

        Returns:
            Tuple of (flow_id, flow_data)
        """
        pass

    @abstractmethod
    async def execute_phase(
        self,
        flow_id: str,
        phase_name: str,
        phase_input: Optional[Dict[str, Any]] = None,
        validation_overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a specific phase of a flow.

        Args:
            flow_id: Master flow ID to execute
            phase_name: Name of the phase to execute
            phase_input: Optional input data for the phase
            validation_overrides: Optional validation overrides

        Returns:
            Phase execution result dict
        """
        pass

    @abstractmethod
    async def resume_flow(
        self,
        flow_id: str,
        resume_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Resume a paused or failed flow.

        Args:
            flow_id: Master flow ID to resume
            resume_context: Optional context for resuming

        Returns:
            Resume result dict
        """
        pass

    @abstractmethod
    async def delete_flow(self, flow_id: str) -> Dict[str, Any]:
        """
        Delete a flow and its associated data.

        Args:
            flow_id: Master flow ID to delete

        Returns:
            Deletion result dict
        """
        pass

    @abstractmethod
    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """
        Get the current status of a flow.

        Args:
            flow_id: Master flow ID to check

        Returns:
            Flow status dict
        """
        pass
