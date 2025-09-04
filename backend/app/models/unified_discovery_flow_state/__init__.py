"""
Unified Discovery Flow State Package
Modularized implementation of the discovery flow state following CrewAI Flow documentation patterns.
"""

from .core_fields import CoreFieldsMixin
from .control_fields import ControlFieldsMixin
from .methods import FlowStateMethods
from .utils import UUIDEncoder, safe_uuid_to_str

__all__ = [
    "UnifiedDiscoveryFlowState",
    "UUIDEncoder",
    "safe_uuid_to_str",
]


class UnifiedDiscoveryFlowState(CoreFieldsMixin, ControlFieldsMixin, FlowStateMethods):
    """
    Single source of truth for Discovery Flow state.
    Follows CrewAI Flow documentation patterns from:
    https://docs.crewai.com/guides/flows/mastering-flow-state

    Consolidates all previous implementations:
    - backend/app/services/crewai_flows/models/flow_state.py
    - backend/app/schemas/flow_schemas.py
    - backend/app/schemas/flow_schemas_new.py
    - Multiple frontend state interfaces
    """

    pass
