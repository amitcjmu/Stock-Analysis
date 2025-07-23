"""
Discovery Flow Service Module

Modularized discovery flow service functionality with clear separation:
- core/: Core flow management and lifecycle operations
- managers/: Specialized managers for assets and summaries
- integrations/: CrewAI integration and legacy system bridges
- models/: Pydantic schemas and data models
- utils/: Utility functions and helpers
"""

from .core.flow_manager import FlowManager
from .discovery_flow_integration_service import DiscoveryFlowIntegrationService

# Main service classes that replace the original monolithic services
from .discovery_flow_service import DiscoveryFlowService
from .integrations.crewai_integration import CrewAIIntegrationService
from .managers.asset_manager import AssetManager
from .managers.summary_manager import SummaryManager
from .models.flow_schemas import (
    AssetValidationRequest,
    CrewAIStateSync,
    FlowCreationRequest,
    FlowResponse,
    FlowSummaryResponse,
    PhaseCompletionRequest,
)
from .utils.flow_utils import (
    FlowPhase,
    FlowStatus,
    ValidationStatus,
    calculate_progress_percentage,
    validate_flow_id,
    validate_phase_name,
)

__all__ = [
    # Core components
    "FlowManager",
    "AssetManager",
    "SummaryManager",
    "CrewAIIntegrationService",
    # Main service classes (backward compatibility)
    "DiscoveryFlowService",
    "DiscoveryFlowIntegrationService",
    # Schemas
    "FlowCreationRequest",
    "PhaseCompletionRequest",
    "FlowSummaryResponse",
    "AssetValidationRequest",
    "CrewAIStateSync",
    "FlowResponse",
    # Utilities
    "validate_flow_id",
    "validate_phase_name",
    "calculate_progress_percentage",
    "FlowPhase",
    "ValidationStatus",
    "FlowStatus",
]
