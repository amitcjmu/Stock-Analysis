"""
CrewAI Flow Service - Modularized Enterprise Architecture

This package provides a modularized CrewAI Flow Service that bridges CrewAI flows
with the V2 Discovery Flow architecture. The service is split into focused modules
for better maintainability while ensuring zero breaking changes.

Modules:
- base.py: Core service class, initialization, and constants
- orchestrator.py: Main service class with flow orchestration
- execution.py: Flow execution engine methods
- state_manager.py: State transitions and persistence
- task_manager.py: Task lifecycle management
- monitoring.py: Flow monitoring and metrics
- validators.py: Input/output validation
- exceptions.py: Flow-specific exceptions

Usage:
    The main CrewAIFlowService class can be imported exactly as before:

    ```python
    from app.services.crewai_flow_service import CrewAIFlowService
    ```

    Or using the factory function:

    ```python
    from app.services.crewai_flow_service import get_crewai_flow_service
    ```

Key Features:
- Zero breaking changes - all existing imports continue to work
- Enterprise-grade modularization with focused responsibilities
- Conditional CrewAI imports handled properly across all modules
- Multi-tenant isolation through context-aware repositories
- Graceful fallback when CrewAI flows unavailable
"""

# Import the main service class for backward compatibility
from .orchestrator import CrewAIFlowService

# Import the factory function
from .base import get_crewai_flow_service

# Import conditional availability flag
from .base import CREWAI_FLOWS_AVAILABLE

# Import exceptions for convenience
from .exceptions import CrewAIExecutionError, InvalidFlowStateError

# Import additional components that might be needed
from .base import CrewAIFlowServiceBase
from .execution import FlowExecutionMixin
from .monitoring import FlowMonitoringMixin
from .state_manager import FlowStateManagerMixin
from .task_manager import FlowTaskManagerMixin
from .validators import FlowValidationMixin

# Export all public components
__all__ = [
    # Main service class - primary export for backward compatibility
    "CrewAIFlowService",
    # Factory function
    "get_crewai_flow_service",
    # Availability flag
    "CREWAI_FLOWS_AVAILABLE",
    # Exceptions
    "CrewAIExecutionError",
    "InvalidFlowStateError",
    # Base and mixin classes (for advanced usage)
    "CrewAIFlowServiceBase",
    "FlowExecutionMixin",
    "FlowMonitoringMixin",
    "FlowStateManagerMixin",
    "FlowTaskManagerMixin",
    "FlowValidationMixin",
]
