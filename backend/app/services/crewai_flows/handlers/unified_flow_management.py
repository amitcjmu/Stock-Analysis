"""
Unified Flow Management
Handles flow management operations for the Unified Discovery Flow.
Extracted from unified_discovery_flow.py for better modularity.
"""

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class UnifiedFlowManagement:
    """
    Manages flow state, resumption, and management operations for the Unified Discovery Flow.
    Handles flow control, state validation, and management information.
    """
    
    def __init__(self, state):
        """Initialize flow management with state reference"""
        self.state = state
    
    def pause_flow(self, reason: str = "user_requested"):
        """Pause the discovery flow with proper state preservation"""
        logger.info(f"🔄 Pausing flow at phase: {self.state.current_phase}, reason: {reason}")
        
        self.state.status = "paused"
        self.state.log_entry(f"Flow paused: {reason}")
        self.state.updated_at = datetime.utcnow().isoformat()
        
        # TODO: Persist current state to database
        # await self._persist_state_to_database()
        
        return f"Flow paused at phase: {self.state.current_phase}"

    def resume_flow_from_state(self, resume_context: Dict[str, Any]):
        """Resume flow from persisted state with CrewAI Flow continuity"""
        logger.info(f"🔄 Resuming flow from phase: {self.state.current_phase}")
        
        # Validate state integrity
        if not self._validate_resumption_state():
            self.state.add_error("flow_resumption", "State validation failed")
            return "Flow resumption failed: Invalid state"
        
        # TODO: Restore agent memory and knowledge base
        # await self._restore_agent_memory()
        # await self._restore_knowledge_base()
        
        # Continue from current phase
        self.state.status = "running"
        self.state.log_entry("Flow resumed from persisted state")
        self.state.updated_at = datetime.utcnow().isoformat()
        
        # Determine next action based on current phase
        next_action = self._get_next_action_for_phase(self.state.current_phase)
        
        return f"Flow resumed at phase: {self.state.current_phase}. Next action: {next_action}"

    def get_flow_management_info(self) -> Dict[str, Any]:
        """Get comprehensive flow information for management UI"""
        return {
            "flow_id": self.state.flow_id,
            "current_phase": self.state.current_phase,
            "status": self.state.status,
            "progress_percentage": self.state.progress_percentage,
            "phase_completion": self.state.phase_completion,
            "can_resume": self._can_resume(),
            "deletion_impact": self._get_deletion_impact(),
            "agent_insights": self.state.agent_insights[-5:] if self.state.agent_insights else [],  # Last 5 insights
            "recent_errors": self.state.errors[-3:] if self.state.errors else [],  # Last 3 errors
            "recent_warnings": self.state.warnings[-3:] if self.state.warnings else [],  # Last 3 warnings
            "created_at": self.state.created_at,
            "updated_at": self.state.updated_at,
            "estimated_remaining_time": self._estimate_remaining_time(),
            "crew_status": self.state.crew_status,
            "database_integration_status": self.state.database_integration_status
        }

    def _validate_resumption_state(self) -> bool:
        """Validate that the flow state is valid for resumption"""
        try:
            # Check basic state integrity
            if not self.state.flow_id or not self.state.current_phase:
                return False
            
            # Check phase dependencies
            phase_completion = self.state.phase_completion
            current_phase = self.state.current_phase
            
            # Validate phase progression
            if current_phase == "data_cleansing" and not phase_completion.get("field_mapping", False):
                return False
            
            if current_phase == "asset_inventory" and not phase_completion.get("data_cleansing", False):
                return False
            
            if current_phase == "dependency_analysis" and not phase_completion.get("asset_inventory", False):
                return False
            
            if current_phase == "tech_debt_analysis" and not phase_completion.get("dependency_analysis", False):
                return False
            
            # Check for critical errors
            if self.state.errors:
                critical_errors = [e for e in self.state.errors if e.get('severity') == 'critical']
                if critical_errors:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"State validation failed: {e}")
            return False

    def _can_resume(self) -> bool:
        """Check if flow can be resumed"""
        if self.state.status not in ['paused', 'failed', 'running']:
            return False
        
        return self._validate_resumption_state()

    def _get_deletion_impact(self) -> Dict[str, Any]:
        """Get information about what would be deleted if this flow is removed"""
        return {
            "flow_phase": self.state.current_phase,
            "progress_percentage": self.state.progress_percentage,
            "data_to_delete": {
                "workflow_state": 1,
                "assets_created": len(self.state.database_assets_created),
                "field_mappings": 1 if self.state.field_mappings else 0,
                "cleaned_data_records": len(self.state.cleaned_data),
                "agent_insights": len(self.state.agent_insights),
                "shared_memory_refs": 1 if self.state.shared_memory_id else 0
            },
            "estimated_cleanup_time": self._estimate_cleanup_time(),
            "data_recovery_possible": False,  # Deletion is permanent
            "warning": "All flow data and progress will be permanently lost"
        }

    def _get_next_action_for_phase(self, phase: str) -> str:
        """Determine the next action based on current phase"""
        phase_actions = {
            "initialization": "Start field mapping analysis",
            "field_mapping": "Execute field mapping crew",
            "data_cleansing": "Execute data cleansing crew", 
            "asset_inventory": "Execute asset inventory crew",
            "dependency_analysis": "Execute dependency analysis crew",
            "tech_debt_analysis": "Execute technical debt analysis crew",
            "completed": "Flow already completed"
        }
        return phase_actions.get(phase, "Continue workflow execution")

    def _estimate_remaining_time(self) -> str:
        """Estimate remaining time based on current progress"""
        progress = self.state.progress_percentage
        if progress >= 100:
            return "Completed"
        elif progress >= 80:
            return "5-10 minutes"
        elif progress >= 60:
            return "10-15 minutes"
        elif progress >= 40:
            return "15-20 minutes"
        elif progress >= 20:
            return "20-25 minutes"
        else:
            return "25-30 minutes"

    def _estimate_cleanup_time(self) -> str:
        """Estimate time required for cleanup operations"""
        asset_count = len(self.state.database_assets_created)
        data_records = len(self.state.cleaned_data)
        
        if asset_count > 1000 or data_records > 5000:
            return "10-15 seconds"
        elif asset_count > 100 or data_records > 1000:
            return "5-10 seconds"
        else:
            return "< 5 seconds" 