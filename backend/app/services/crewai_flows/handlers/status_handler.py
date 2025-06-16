"""
Status Handler for Discovery Flow
Handles flow status tracking and reporting
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class StatusHandler:
    """Handles flow status tracking and reporting"""
    
    def __init__(self):
        self.status_history = []
    
    def get_current_status(self, state, knowledge_bases: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive flow status"""
        status = {
            "session_id": state.session_id,
            "current_phase": state.current_phase,
            "overall_plan": state.overall_plan,
            "crew_status": state.crew_status,
            "phase_managers": state.phase_managers,
            "completion_percentage": self._calculate_completion_percentage(state),
            "shared_memory_id": state.shared_memory_id,
            "knowledge_bases": list(knowledge_bases.keys()),
            "errors": state.errors,
            "warnings": state.warnings,
            "flow_health": self._assess_flow_health(state),
            "next_actions": self._determine_next_actions(state)
        }
        
        # Store status in history
        self.status_history.append({
            "timestamp": state.updated_at,
            "phase": state.current_phase,
            "completion": status["completion_percentage"],
            "health": status["flow_health"]
        })
        
        return status
    
    def _calculate_completion_percentage(self, state) -> float:
        """Calculate overall completion percentage"""
        total_phases = 6  # field_mapping, data_cleansing, inventory_building, app_server_deps, app_app_deps, technical_debt
        completed_phases = len([status for status in state.crew_status.values() if status.get("status") == "completed"])
        return (completed_phases / total_phases) * 100.0
    
    def _assess_flow_health(self, state) -> Dict[str, Any]:
        """Assess overall flow health"""
        total_crews = 6
        completed_crews = len([status for status in state.crew_status.values() if status.get("status") == "completed"])
        failed_crews = len([status for status in state.crew_status.values() if status.get("status") == "failed"])
        
        health_score = (completed_crews / total_crews) * 100 if total_crews > 0 else 0
        
        if failed_crews == 0 and completed_crews == total_crews:
            health_status = "excellent"
        elif failed_crews == 0 and completed_crews > 0:
            health_status = "good"
        elif failed_crews <= 2:
            health_status = "fair"
        else:
            health_status = "poor"
        
        return {
            "status": health_status,
            "score": health_score,
            "completed_crews": completed_crews,
            "failed_crews": failed_crews,
            "total_errors": len(state.errors),
            "critical_issues": self._identify_critical_issues(state)
        }
    
    def _identify_critical_issues(self, state) -> List[Dict[str, Any]]:
        """Identify critical issues that need attention"""
        critical_issues = []
        
        # Check for field mapping failure
        field_mapping_status = state.crew_status.get("field_mapping", {})
        if field_mapping_status.get("status") == "failed":
            critical_issues.append({
                "type": "crew_failure",
                "crew": "field_mapping",
                "severity": "critical",
                "description": "Field mapping failed - foundation for all subsequent analysis compromised"
            })
        
        # Check for multiple crew failures
        failed_crews = [name for name, status in state.crew_status.items() if status.get("status") == "failed"]
        if len(failed_crews) >= 3:
            critical_issues.append({
                "type": "multiple_failures",
                "crews": failed_crews,
                "severity": "high",
                "description": f"Multiple crews failed: {', '.join(failed_crews)}"
            })
        
        # Check for no progress
        if state.current_phase == "initialization" and len(state.crew_status) == 0:
            critical_issues.append({
                "type": "no_progress",
                "severity": "medium",
                "description": "Flow has not progressed beyond initialization"
            })
        
        return critical_issues
    
    def _determine_next_actions(self, state) -> List[Dict[str, Any]]:
        """Determine recommended next actions"""
        next_actions = []
        
        # Based on current phase
        phase_actions = {
            "initialization": [
                {"action": "start_field_mapping", "description": "Begin field mapping crew execution"}
            ],
            "field_mapping": [
                {"action": "validate_mappings", "description": "Validate field mapping results"},
                {"action": "proceed_to_cleansing", "description": "Proceed to data cleansing phase"}
            ],
            "data_cleansing": [
                {"action": "validate_data_quality", "description": "Validate data quality metrics"},
                {"action": "proceed_to_inventory", "description": "Proceed to inventory building phase"}
            ],
            "inventory_building": [
                {"action": "validate_classification", "description": "Validate asset classification results"},
                {"action": "proceed_to_dependencies", "description": "Proceed to dependency analysis"}
            ],
            "app_server_dependencies": [
                {"action": "validate_hosting_relationships", "description": "Validate hosting relationships"},
                {"action": "proceed_to_app_dependencies", "description": "Proceed to app-app dependency analysis"}
            ],
            "app_app_dependencies": [
                {"action": "validate_integrations", "description": "Validate integration patterns"},
                {"action": "proceed_to_technical_debt", "description": "Proceed to technical debt assessment"}
            ],
            "technical_debt": [
                {"action": "validate_6r_preparation", "description": "Validate 6R strategy preparation"},
                {"action": "finalize_discovery", "description": "Finalize discovery integration"}
            ],
            "completed": [
                {"action": "review_results", "description": "Review discovery results"},
                {"action": "prepare_assessment", "description": "Prepare for Assessment Flow"}
            ]
        }
        
        current_actions = phase_actions.get(state.current_phase, [])
        next_actions.extend(current_actions)
        
        # Add error-specific actions
        if state.errors:
            next_actions.append({
                "action": "review_errors",
                "description": f"Review and address {len(state.errors)} errors"
            })
        
        return next_actions
    
    def get_status_history(self) -> List[Dict[str, Any]]:
        """Get status change history"""
        return self.status_history
    
    def get_phase_summary(self, state) -> Dict[str, Any]:
        """Get summary of all phases"""
        phases = ["field_mapping", "data_cleansing", "inventory_building", 
                 "app_server_dependencies", "app_app_dependencies", "technical_debt"]
        
        phase_summary = {}
        for phase in phases:
            crew_status = state.crew_status.get(phase, {})
            phase_summary[phase] = {
                "status": crew_status.get("status", "pending"),
                "manager": state.phase_managers.get(phase, "Unknown"),
                "completion_time": crew_status.get("completion_time"),
                "success_criteria_met": crew_status.get("success_criteria_met", False)
            }
        
        return phase_summary 