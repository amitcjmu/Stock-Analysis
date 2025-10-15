"""
Flow Type Registry

Singleton registry for all flow type configurations.
Manages registration, validation, and retrieval of flow types.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

# Optional CrewAI import - not required for registry functionality
try:
    from crewai import Flow
except ImportError:
    Flow = None

logger = logging.getLogger(__name__)


class FlowCapability(Enum):
    """Supported flow capabilities"""

    PAUSE_RESUME = "pause_resume"
    ROLLBACK = "rollback"
    BRANCHING = "branching"
    ITERATIONS = "iterations"
    SCHEDULING = "scheduling"
    PARALLEL_EXECUTION = "parallel_execution"
    CHECKPOINTING = "checkpointing"


@dataclass
class RetryConfig:
    """Retry configuration for phases"""

    max_attempts: int = 3
    initial_delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0
    max_delay_seconds: float = 60.0
    retry_on_errors: List[Type[Exception]] = field(default_factory=lambda: [Exception])


@dataclass
class PhaseConfig:
    """Configuration for a flow phase"""

    name: str  # Unique phase identifier
    display_name: str  # Human-readable name
    description: str  # What this phase does
    required_inputs: List[str] = field(default_factory=list)
    optional_inputs: List[str] = field(default_factory=list)
    validators: List[str] = field(default_factory=list)
    pre_handlers: List[str] = field(default_factory=list)
    post_handlers: List[str] = field(default_factory=list)
    completion_handler: Optional[str] = None
    crew_config: Dict[str, Any] = field(default_factory=dict)
    can_pause: bool = True
    can_skip: bool = False
    can_rollback: bool = False
    requires_user_input: bool = (
        False  # True if phase needs user interaction before agent execution
    )
    retry_config: Optional[RetryConfig] = None
    timeout_seconds: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Additional fields for phase configuration
    outputs: List[str] = field(default_factory=list)
    expected_duration_minutes: Optional[int] = None
    parallel_execution: bool = False
    dependencies: List[str] = field(default_factory=list)
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    failure_conditions: Dict[str, Any] = field(default_factory=dict)

    # Legacy compatibility fields (ignored)
    order: Optional[int] = None
    required: Optional[bool] = None
    inputs: Optional[List[str]] = None
    timeout_minutes: Optional[int] = None

    def __post_init__(self):
        # Handle legacy timeout_minutes
        if self.timeout_minutes:
            self.timeout_seconds = self.timeout_minutes * 60

        # Handle expected_duration_minutes to timeout_seconds conversion if needed
        if self.expected_duration_minutes and not self.timeout_minutes:
            self.timeout_seconds = self.expected_duration_minutes * 60

        # Handle legacy inputs
        if self.inputs and not self.required_inputs:
            self.required_inputs = self.inputs

        # Handle legacy display_name
        if not self.display_name:
            self.display_name = self.name.replace("_", " ").title()


@dataclass
class FlowCapabilities:
    """Capabilities of a flow type"""

    supports_pause_resume: bool = True
    supports_rollback: bool = False
    supports_branching: bool = False
    supports_iterations: bool = True
    max_iterations: int = 10
    supports_scheduling: bool = False
    supports_parallel_phases: bool = False
    supports_checkpointing: bool = True
    required_permissions: List[str] = field(default_factory=list)

    # Additional capabilities for advanced flow features
    supports_parallel_execution: bool = False
    supports_phase_rollback: bool = False
    supports_incremental_execution: bool = False
    supports_failure_recovery: bool = False
    supports_real_time_monitoring: bool = False
    supports_dynamic_scaling: bool = False


@dataclass
class FlowTypeConfig:
    """Configuration for a flow type"""

    name: str  # e.g., "discovery"
    display_name: str  # e.g., "Discovery Flow"
    description: str  # Human-readable description
    version: str = "1.0.0"  # Flow version
    phases: List[PhaseConfig] = field(default_factory=list)
    crew_class: Optional[Type] = None  # Type[Flow] when CrewAI available
    output_schema: Optional[Type[BaseModel]] = None
    input_schema: Optional[Type[BaseModel]] = None
    capabilities: FlowCapabilities = field(default_factory=FlowCapabilities)
    default_configuration: Dict[str, Any] = field(default_factory=dict)
    initialization_handler: Optional[str] = None
    finalization_handler: Optional[str] = None
    error_handler: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    child_flow_service: Optional[Type] = None  # Service class for child flow operations

    def get_phase_config(self, phase_name: str) -> Optional[PhaseConfig]:
        """Get configuration for a specific phase"""
        return next((phase for phase in self.phases if phase.name == phase_name), None)

    def get_next_phase(self, current_phase: Optional[str]) -> Optional[str]:
        """Get the next phase in sequence"""
        if not current_phase:
            return self.phases[0].name if self.phases else None

        for i, phase in enumerate(self.phases):
            if phase.name == current_phase and i < len(self.phases) - 1:
                return self.phases[i + 1].name

        return None

    def get_phase_index(self, phase_name: str) -> int:
        """Get the index of a phase"""
        for i, phase in enumerate(self.phases):
            if phase.name == phase_name:
                return i
        return -1

    def is_phase_valid(self, phase_name: str) -> bool:
        """Check if a phase name is valid for this flow type

        Part of the MFO consolidation - validates that a phase exists
        in this flow type's configuration.
        """
        return any(phase.name == phase_name for phase in self.phases)

    def are_dependencies_satisfied(self, phase_name: str, master_flow: Any) -> bool:
        """Check if phase dependencies are satisfied

        Part of the MFO consolidation - ensures phases execute in order
        and dependencies are met before phase execution.

        Args:
            phase_name: Name of the phase to check
            master_flow: The master flow object containing flow state

        Returns:
            True if dependencies are satisfied or phase has no dependencies
        """
        # For now, return True to allow phase execution
        # The actual dependency checking is handled by the PhaseController
        # This method exists for MFO compatibility
        return True

    def validate(self) -> List[str]:
        """Validate the flow configuration"""
        errors = []

        if not self.name:
            errors.append("Flow name is required")

        if not self.phases:
            errors.append("At least one phase is required")

        # Check for duplicate phase names
        phase_names = [phase.name for phase in self.phases]
        if len(phase_names) != len(set(phase_names)):
            errors.append("Duplicate phase names found")

        # Validate each phase
        for phase in self.phases:
            if not phase.name:
                errors.append("Phase name is required")
            if not phase.display_name:
                errors.append(f"Phase {phase.name} display name is required")

        return errors


class FlowTypeRegistry:
    """
    Singleton registry for all flow type configurations.
    Thread-safe implementation using module-level instance.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FlowTypeRegistry, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._flow_types: Dict[str, FlowTypeConfig] = {}
            self._initialized = True
            logger.info("✅ Flow Type Registry initialized")

    def register(self, config: FlowTypeConfig) -> None:
        """
        Register a new flow type configuration

        Args:
            config: Flow type configuration to register

        Raises:
            ValueError: If configuration is invalid

        Note:
            Idempotent operation - if flow type is already registered with same version,
            it will be skipped silently. If different version, it will be updated.
        """
        # Validate configuration
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid flow configuration: {', '.join(errors)}")

        # Check for duplicate registration - make idempotent
        if config.name in self._flow_types:
            existing_config = self._flow_types[config.name]
            if existing_config.version == config.version:
                # Same version - skip silently (idempotent)
                logger.debug(
                    f"Flow type '{config.name}' v{config.version} already registered (skipping)"
                )
                return
            else:
                # Different version - update with warning
                logger.warning(
                    f"Updating flow type '{config.name}' from v{existing_config.version} to v{config.version}"
                )

        # Register or update the flow type
        self._flow_types[config.name] = config
        logger.info(f"✅ Registered flow type: {config.name} (v{config.version})")

    def unregister(self, flow_type: str) -> bool:
        """
        Unregister a flow type

        Args:
            flow_type: Name of flow type to unregister

        Returns:
            True if unregistered, False if not found
        """
        if flow_type in self._flow_types:
            del self._flow_types[flow_type]
            logger.info(f"🗑️ Unregistered flow type: {flow_type}")
            return True
        return False

    def get_flow_config(self, flow_type: str) -> FlowTypeConfig:
        """
        Get configuration for a flow type

        Args:
            flow_type: Name of the flow type

        Returns:
            Flow type configuration

        Raises:
            ValueError: If flow type not found
        """
        if flow_type not in self._flow_types:
            raise ValueError(f"Flow type '{flow_type}' is not registered")

        return self._flow_types[flow_type]

    def is_registered(self, flow_type: str) -> bool:
        """
        Check if a flow type is registered

        Args:
            flow_type: Name of the flow type

        Returns:
            True if registered, False otherwise
        """
        return flow_type in self._flow_types

    def list_flow_types(self) -> List[str]:
        """
        List all registered flow types

        Returns:
            List of flow type names
        """
        return list(self._flow_types.keys())

    def get_flow_types_by_capability(self, capability: FlowCapability) -> List[str]:
        """
        Get flow types that support a specific capability

        Args:
            capability: The capability to filter by

        Returns:
            List of flow type names that support the capability
        """
        result = []

        for flow_type, config in self._flow_types.items():
            capabilities = config.capabilities

            if (
                capability == FlowCapability.PAUSE_RESUME
                and capabilities.supports_pause_resume
            ):
                result.append(flow_type)
            elif (
                capability == FlowCapability.ROLLBACK and capabilities.supports_rollback
            ):
                result.append(flow_type)
            elif (
                capability == FlowCapability.BRANCHING
                and capabilities.supports_branching
            ):
                result.append(flow_type)
            elif (
                capability == FlowCapability.ITERATIONS
                and capabilities.supports_iterations
            ):
                result.append(flow_type)
            elif (
                capability == FlowCapability.SCHEDULING
                and capabilities.supports_scheduling
            ):
                result.append(flow_type)
            elif (
                capability == FlowCapability.PARALLEL_EXECUTION
                and capabilities.supports_parallel_phases
            ):
                result.append(flow_type)
            elif (
                capability == FlowCapability.CHECKPOINTING
                and capabilities.supports_checkpointing
            ):
                result.append(flow_type)

        return result

    def get_flow_types_by_tag(self, tag: str) -> List[str]:
        """
        Get flow types that have a specific tag

        Args:
            tag: Tag to filter by

        Returns:
            List of flow type names with the tag
        """
        return [
            flow_type
            for flow_type, config in self._flow_types.items()
            if tag in config.tags
        ]

    def get_all_configurations(self) -> Dict[str, FlowTypeConfig]:
        """
        Get all registered flow configurations

        Returns:
            Dictionary of all flow type configurations
        """
        return self._flow_types.copy()

    def clear(self) -> None:
        """
        Clear all registered flow types
        Used primarily for testing
        """
        self._flow_types.clear()
        logger.warning("⚠️ Flow Type Registry cleared")

    def get_registry_info(self) -> Dict[str, Any]:
        """
        Get information about the registry

        Returns:
            Registry statistics and metadata
        """
        return {
            "total_flow_types": len(self._flow_types),
            "flow_types": self.list_flow_types(),
            "capabilities_summary": {
                "pause_resume": len(
                    self.get_flow_types_by_capability(FlowCapability.PAUSE_RESUME)
                ),
                "rollback": len(
                    self.get_flow_types_by_capability(FlowCapability.ROLLBACK)
                ),
                "iterations": len(
                    self.get_flow_types_by_capability(FlowCapability.ITERATIONS)
                ),
                "scheduling": len(
                    self.get_flow_types_by_capability(FlowCapability.SCHEDULING)
                ),
                "checkpointing": len(
                    self.get_flow_types_by_capability(FlowCapability.CHECKPOINTING)
                ),
            },
            "versions": {
                flow_type: config.version
                for flow_type, config in self._flow_types.items()
            },
        }


# Global registry instance
flow_type_registry = FlowTypeRegistry()
