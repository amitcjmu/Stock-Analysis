"""
CrewAI Flow Framework Package

Phase 2 implementation of proper CrewAI Flow patterns with @start and @listen decorators.
Replaces manual orchestration with event-driven flow control.

Components:
- BaseDiscoveryFlow: Base class for all discovery flows
- UnifiedDiscoveryFlow: Main discovery flow with proper decorators
- FlowManager: Lifecycle management for flows
- FlowEventBus: Event-driven coordination and monitoring
"""

from .base_flow import BaseDiscoveryFlow, BaseFlowState
from .discovery_flow import UnifiedDiscoveryFlow, DiscoveryFlowState
from .manager import FlowManager, flow_manager
from .events import FlowEventBus, FlowEvent, flow_event_bus

__all__ = [
    'BaseDiscoveryFlow', 
    'BaseFlowState',
    'UnifiedDiscoveryFlow',
    'DiscoveryFlowState', 
    'FlowManager',
    'flow_manager',
    'FlowEventBus',
    'FlowEvent',
    'flow_event_bus'
]