"""
Flow Management Module

Handles flow lifecycle operations like pause, resume, and info retrieval.
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class FlowManager:
    """Manages flow lifecycle operations"""
    
    def __init__(self, state, state_manager, flow_management):
        """
        Initialize flow manager
        
        Args:
            state: The flow state object
            state_manager: StateManager instance
            flow_management: UnifiedFlowManagement instance
        """
        self.state = state
        self.state_manager = state_manager
        self.flow_management = flow_management
    
    async def pause_flow(self, reason: str = "user_requested") -> Dict[str, Any]:
        """
        Pause the discovery flow
        
        Args:
            reason: Reason for pausing the flow
            
        Returns:
            Pause operation result
        """
        logger.info(f"⏸️ Pausing flow: {reason}")
        self.state.status = "paused"
        self.state.pause_reason = reason
        self.state.paused_at = datetime.utcnow()
        
        await self.state_manager.safe_update_flow_state()
        return self.flow_management.pause_flow(reason)
    
    async def resume_flow_from_state(self, resume_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resume flow from saved state
        
        Args:
            resume_context: Context for resuming the flow
            
        Returns:
            Resume operation result
        """
        logger.info("▶️ Resuming flow from saved state")
        
        # Clear pause-related fields
        self.state.status = "running"
        self.state.pause_reason = None
        self.state.paused_at = None
        self.state.resumed_at = datetime.utcnow()
        
        await self.state_manager.safe_update_flow_state()
        return self.flow_management.resume_flow_from_state(resume_context)
    
    def get_flow_info(self) -> Dict[str, Any]:
        """
        Get comprehensive flow information
        
        Returns:
            Flow information including status, progress, and summary
        """
        return {
            "flow_id": self.state.flow_id,
            "session_id": self.state.session_id,
            "status": self.state.status,
            "current_phase": self.state.current_phase,
            "progress": self.state_manager.calculate_progress(),
            "summary": self.state_manager.create_flow_summary(),
            "created_at": self.state.created_at if self.state.created_at else None,
            "updated_at": self.state.updated_at if self.state.updated_at else None,
            "phase_completion": self.state.phase_completion,
            "total_assets": self.state.total_assets,
            "errors": self.state.errors,
            "warnings": self.state.warnings
        }
    
    async def handle_user_approval(self, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle user approval for paused flows
        
        Args:
            approval_data: User approval data
            
        Returns:
            Approval handling result
        """
        logger.info(f"👤 Processing user approval for flow: {self.state.flow_id}")
        
        # Update state with approval
        self.state.user_approvals = self.state.user_approvals or []
        self.state.user_approvals.append({
            "phase": self.state.current_phase,
            "timestamp": datetime.utcnow().isoformat(),
            "data": approval_data
        })
        
        # Clear waiting status
        self.state.status = "running"
        self.state.user_approval_context = None
        
        await self.state_manager.safe_update_flow_state()
        
        return {
            "status": "approved",
            "flow_id": self.state.flow_id,
            "phase": self.state.current_phase
        }