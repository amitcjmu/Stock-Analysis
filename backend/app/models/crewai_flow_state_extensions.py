"""
CrewAI Flow State Extensions Model - Backward Compatibility Module

This module maintains backward compatibility while the implementation has been
modularized into separate mixins for better maintainability and compliance
with the pre-commit line limit requirements.

The modular implementation can be found in:
- app.models.crewai_flow_state_extensions.base_model
- app.models.crewai_flow_state_extensions.collaboration_mixin
- app.models.crewai_flow_state_extensions.flow_management_mixin
- app.models.crewai_flow_state_extensions.performance_mixin
- app.models.crewai_flow_state_extensions.serialization_mixin

All existing imports will continue to work without modification.
"""

# Re-export the modularized model for backward compatibility
from .crewai_flow_state_extensions.base_model import CrewAIFlowStateExtensions

# Preserve all public exports
__all__ = ["CrewAIFlowStateExtensions"]
