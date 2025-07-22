"""
Flow State Transition Utilities

Centralized utilities for handling flow state transitions and validation.
Helps prevent "Cannot transition from initialized to active" type errors.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.exceptions import InvalidFlowStateError
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = logging.getLogger(__name__)


class FlowStateTransitionValidator:
    """
    Centralized validation for flow state transitions.
    Handles both status transitions (initialized -> active) and phase transitions (initialization -> data_import).
    """
    
    # Valid flow statuses from database schema
    VALID_FLOW_STATUSES = [
        "initialized", "active", "processing", "paused", 
        "completed", "failed", "cancelled", "waiting_for_approval"
    ]
    
    # Valid phases from flow state validator
    VALID_PHASES = [
        "initialization", "data_import", "field_mapping", "data_cleansing",
        "asset_creation", "asset_inventory", "dependency_analysis", 
        "tech_debt_analysis", "completed"
    ]
    
    # Statuses that allow resumption
    RESUMABLE_STATUSES = ["initialized", "paused", "waiting_for_approval"]
    
    # Terminal statuses that don't allow resumption
    TERMINAL_STATUSES = ["completed", "failed", "cancelled"]
    
    @classmethod
    def can_resume_flow(
        cls, 
        master_flow: CrewAIFlowStateExtensions,
        debug_logging: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive check if a flow can be resumed.
        
        Returns:
            Dict with 'can_resume' boolean and 'reason' string
        """
        flow_id = str(master_flow.flow_id)
        flow_status = master_flow.flow_status
        persistence_data = master_flow.flow_persistence_data or {}
        
        if debug_logging:
            logger.info(f"🔍 Flow {flow_id} resumption check:")
            logger.info(f"  - flow_status: {flow_status}")
            logger.info(f"  - persistence_data keys: {list(persistence_data.keys())}")
        
        # Check 1: Flow status is resumable
        if flow_status in cls.RESUMABLE_STATUSES:
            return {"can_resume": True, "reason": f"Flow status '{flow_status}' is resumable"}
        
        # Check 2: Flow is awaiting user approval
        is_awaiting_approval = persistence_data.get("awaiting_user_approval", False)
        if is_awaiting_approval:
            return {"can_resume": True, "reason": "Flow is awaiting user approval"}
        
        # Check 3: Flow is paused for approval
        completion_data = str(persistence_data.get("completion", ""))
        if "paused_for" in completion_data:
            return {"can_resume": True, "reason": "Flow is paused for approval"}
        
        # Check 4: Flow has been reset (common after data linkage fixes)
        persistence_status = persistence_data.get("status", "")
        if persistence_status == "reset":
            return {"can_resume": True, "reason": "Flow has been reset and can be restarted"}
        
        # Check 5: Terminal statuses cannot be resumed
        if flow_status in cls.TERMINAL_STATUSES:
            return {"can_resume": False, "reason": f"Flow status '{flow_status}' is terminal"}
        
        # Check 6: Handle edge cases for "active" and "processing" flows
        if flow_status in ["active", "processing"]:
            return {"can_resume": True, "reason": f"Flow status '{flow_status}' can continue execution"}
        
        # Default: Unknown status, be permissive but log warning
        logger.warning(f"⚠️ Unknown flow status '{flow_status}' for flow {flow_id}, allowing resumption")
        return {"can_resume": True, "reason": f"Unknown status '{flow_status}' - allowing resumption"}
    
    @classmethod
    def validate_status_transition(
        cls,
        current_status: str,
        target_status: str,
        flow_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate flow status transitions (e.g., initialized -> active).
        
        Returns:
            Dict with 'valid' boolean and 'error' string if invalid
        """
        context = context or {}
        
        logger.info(f"🔄 Status transition validation: {flow_id}")
        logger.info(f"  - current_status: {current_status}")
        logger.info(f"  - target_status: {target_status}")
        
        # Check if statuses are valid
        if current_status not in cls.VALID_FLOW_STATUSES:
            return {
                "valid": False, 
                "error": f"Invalid current status: {current_status}"
            }
        
        if target_status not in cls.VALID_FLOW_STATUSES:
            return {
                "valid": False, 
                "error": f"Invalid target status: {target_status}"
            }
        
        # Define valid transitions
        valid_transitions = {
            "initialized": ["active", "processing", "paused", "failed", "cancelled"],
            "active": ["processing", "paused", "completed", "failed", "cancelled", "waiting_for_approval"],
            "processing": ["active", "paused", "completed", "failed", "cancelled", "waiting_for_approval"],
            "paused": ["active", "processing", "cancelled", "failed"],
            "waiting_for_approval": ["active", "processing", "paused", "cancelled", "failed"],
            "completed": [],  # Terminal state
            "failed": ["initialized", "active"],  # Can restart from failed
            "cancelled": ["initialized", "active"]  # Can restart from cancelled
        }
        
        allowed_targets = valid_transitions.get(current_status, [])
        
        if target_status in allowed_targets:
            return {"valid": True, "error": None}
        
        # Special case: Allow same status (no-op transition)
        if current_status == target_status:
            return {"valid": True, "error": None}
        
        # Special case: Resumption context allows more transitions
        if context.get("is_resumption", False):
            logger.info(f"⚡ Allowing transition during resumption: {current_status} -> {target_status}")
            return {"valid": True, "error": None}
        
        return {
            "valid": False,
            "error": f"Cannot transition from {current_status} to {target_status}"
        }
    
    @classmethod
    def safe_resume_flow(
        cls,
        master_flow: CrewAIFlowStateExtensions,
        target_status: str = "active"
    ) -> Dict[str, Any]:
        """
        Safely attempt to resume a flow with comprehensive validation.
        
        Returns:
            Dict with 'success' boolean and either 'result' or 'error'
        """
        flow_id = str(master_flow.flow_id)
        
        try:
            # Check if flow can be resumed
            resume_check = cls.can_resume_flow(master_flow)
            if not resume_check["can_resume"]:
                raise InvalidFlowStateError(
                    current_state=master_flow.flow_status,
                    target_state=target_status,
                    flow_id=flow_id
                )
            
            # Validate status transition
            transition_check = cls.validate_status_transition(
                current_status=master_flow.flow_status,
                target_status=target_status,
                flow_id=flow_id,
                context={"is_resumption": True}
            )
            
            if not transition_check["valid"]:
                raise InvalidFlowStateError(
                    current_state=master_flow.flow_status,
                    target_state=target_status,
                    flow_id=flow_id
                )
            
            logger.info(f"✅ Flow {flow_id} can be safely resumed: {resume_check['reason']}")
            
            return {
                "success": True,
                "result": {
                    "can_resume": True,
                    "reason": resume_check["reason"],
                    "current_status": master_flow.flow_status,
                    "target_status": target_status,
                    "validated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Flow {flow_id} cannot be resumed: {e}")
            return {
                "success": False,
                "error": str(e),
                "current_status": master_flow.flow_status,
                "target_status": target_status
            }


def safe_flow_resume_wrapper(resume_func):
    """
    Decorator to wrap flow resume functions with comprehensive state validation.
    """
    async def wrapper(*args, **kwargs):
        try:
            return await resume_func(*args, **kwargs)
        except InvalidFlowStateError as e:
            # Add more context to state transition errors
            logger.error(f"❌ Flow state transition error: {e}")
            logger.error(f"   Current state: {e.details.get('current_state', 'unknown')}")
            logger.error(f"   Target state: {e.details.get('target_state', 'unknown')}")
            logger.error(f"   Flow ID: {e.flow_id}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error in flow resume: {e}")
            raise
    
    return wrapper