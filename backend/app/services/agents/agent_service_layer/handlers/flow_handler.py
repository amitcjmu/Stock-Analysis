"""
Flow handler for agent service layer flow management operations.
"""

import logging
from typing import Any, Dict, List

from app.core.context import RequestContext

# Import modular components
from .flow_handler_status import FlowHandlerStatus
from .flow_handler_navigation import FlowHandlerNavigation
from .flow_handler_validation import FlowHandlerValidation

logger = logging.getLogger(__name__)


class FlowHandler:
    """Handles flow management operations for the agent service layer."""

    def __init__(self, context: RequestContext):
        self.context = context
        # Initialize modular handlers
        self.status_handler = FlowHandlerStatus(context)
        self.navigation_handler = FlowHandlerNavigation(context)
        self.validation_handler = FlowHandlerValidation(context)

    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Delegate to status handler"""
        return await self.status_handler.get_flow_status(flow_id)

    async def get_navigation_guidance(
        self, flow_id: str, current_phase: str
    ) -> Dict[str, Any]:
        """Delegate to navigation handler"""
        return await self.navigation_handler.get_navigation_guidance(
            flow_id, current_phase
        )

    async def validate_phase_completion(
        self, flow_id: str, phase: str
    ) -> Dict[str, Any]:
        """Delegate to validation handler"""
        return await self.validation_handler.validate_phase_completion(flow_id, phase)

    async def get_active_flows(self) -> List[Dict[str, Any]]:
        """Delegate to validation handler"""
        return await self.validation_handler.get_active_flows()

    async def validate_phase_transition(
        self, flow_id: str, from_phase: str, to_phase: str
    ) -> Dict[str, Any]:
        """Delegate to validation handler"""
        return await self.validation_handler.validate_phase_transition(
            flow_id, from_phase, to_phase
        )


# Helper methods moved to flow_handler_helpers.py
