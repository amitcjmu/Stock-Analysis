"""
Flow Intelligence Knowledge Base
Comprehensive knowledge for the Flow Processing Agent

This knowledge base provides the agent with:
- Complete flow definitions and phases
- Success criteria for each phase
- Navigation paths and user actions
- Service mappings for validation
- Context requirements for multi-tenant operations
"""

# Re-export all items for backward compatibility
from .flow_intelligence_context import (
    AGENT_INTELLIGENCE,
    CONTEXT_SERVICES,
    NAVIGATION_RULES,
)
from .flow_intelligence_definitions import (
    FLOW_DEFINITIONS,
)
from .flow_intelligence_enums import (
    ActionType,
    FlowType,
    PhaseStatus,
)
from .flow_intelligence_utils import (
    get_flow_definition,
    get_navigation_path,
    get_next_phase,
    get_phase_definition,
    get_success_criteria,
    get_system_actions,
    get_user_actions,
    get_validation_services,
)

# Expose all symbols for backward compatibility
__all__ = [
    # Enums
    "FlowType",
    "PhaseStatus",
    "ActionType",
    # Constants
    "FLOW_DEFINITIONS",
    "CONTEXT_SERVICES",
    "NAVIGATION_RULES",
    "AGENT_INTELLIGENCE",
    # Functions
    "get_flow_definition",
    "get_phase_definition",
    "get_next_phase",
    "get_navigation_path",
    "get_validation_services",
    "get_success_criteria",
    "get_user_actions",
    "get_system_actions",
]
