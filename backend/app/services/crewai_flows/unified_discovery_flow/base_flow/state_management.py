"""
State Management - Flow State and Context Management

Contains methods for managing flow state and context throughout the flow lifecycle.
"""

import logging
from typing import Any, Dict, Optional

from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

logger = logging.getLogger(__name__)


class StateManagementMethods:
    """Mixin class containing state management methods"""

    # ========================================
    # FLOW MANAGEMENT METHODS
    # ========================================

    async def pause_flow(self, reason: Optional[str] = None):
        """Pause the flow"""
        return await self.flow_manager.pause_flow(reason)

    async def resume_flow_from_state(self, resume_context: Dict[str, Any]):
        """Resume flow from saved state"""
        return await self.flow_manager.resume_flow_from_state(resume_context)

    def get_flow_info(self) -> Dict[str, Any]:
        """Get comprehensive flow information"""
        return self.flow_manager.get_flow_info()

    # Delegate data loading to utility class
    async def _load_raw_data_from_database(self, state: UnifiedDiscoveryFlowState):
        """Load raw data from database tables into flow state"""
        return await self.data_utils.load_raw_data_from_database(state)
