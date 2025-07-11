"""
Flow Status Calculator

This module provides complex status determination logic for discovery flows,
including progress calculation, phase analysis, and status aggregation.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class StatusCalculator:
    """Utility class for complex flow status determination and calculation"""
    
    PHASE_ORDER = [
        "data_import",
        "field_mapping", 
        "data_cleansing",
        "asset_inventory",
        "dependency_analysis",
        "tech_debt_assessment"
    ]
    
    TOTAL_PHASES = len(PHASE_ORDER)
    
    @staticmethod
    def calculate_current_phase(flow) -> Tuple[str, int]:
        """
        Calculate the current phase and steps completed for a discovery flow.
        
        Returns:
            Tuple of (current_phase, steps_completed)
        """
        try:
            current_phase = "unknown"
            steps_completed = 0
            
            if not flow.data_import_completed:
                current_phase = "data_import"
                steps_completed = 0
            elif not flow.field_mapping_completed:
                current_phase = "field_mapping"
                steps_completed = 1
            elif not flow.data_cleansing_completed:
                current_phase = "data_cleansing"
                steps_completed = 2
            elif not flow.asset_inventory_completed:
                current_phase = "asset_inventory"
                steps_completed = 3
            elif not flow.dependency_analysis_completed:
                current_phase = "dependency_analysis"
                steps_completed = 4
            elif not flow.tech_debt_assessment_completed:
                current_phase = "tech_debt_assessment"
                steps_completed = 5
            else:
                current_phase = "completed"
                steps_completed = 6
            
            return current_phase, steps_completed
        except Exception as e:
            logger.error(f"Error calculating current phase: {e}")
            return "unknown", 0
    
    @staticmethod
    def build_phase_completion_dict(flow) -> Dict[str, bool]:
        """Build phase completion dictionary from flow model"""
        try:
            return {
                "data_import": flow.data_import_completed,
                "field_mapping": flow.field_mapping_completed,
                "data_cleansing": flow.data_cleansing_completed,
                "asset_inventory": flow.asset_inventory_completed,
                "dependency_analysis": flow.dependency_analysis_completed,
                "tech_debt_assessment": flow.tech_debt_assessment_completed
            }
        except Exception as e:
            logger.error(f"Error building phase completion dict: {e}")
            return {phase: False for phase in StatusCalculator.PHASE_ORDER}
    
    @staticmethod
    def calculate_progress_percentage(flow, current_phase: str = None) -> float:
        """
        Calculate progress percentage based on completed phases and current phase.
        
        Args:
            flow: The discovery flow model
            current_phase: Optional current phase override
            
        Returns:
            Progress percentage (0-100)
        """
        try:
            phase_completion = StatusCalculator.build_phase_completion_dict(flow)
            completed_phases = sum(1 for v in phase_completion.values() if v)
            total_phases = StatusCalculator.TOTAL_PHASES
            
            # Use existing progress if available
            actual_progress = flow.progress_percentage or 0
            
            # If we're in field mapping phase and have data imported, ensure minimum progress
            if (flow.data_import_completed and 
                (current_phase in ["field_mapping", "attribute_mapping"] or 
                 flow.current_phase in ["field_mapping", "attribute_mapping"])):
                # At least 1 phase complete (data import) + partial progress for field mapping
                min_progress = (1.0 / total_phases) * 100  # 16.7% for data import
                if not flow.field_mapping_completed:
                    min_progress += (0.5 / total_phases) * 100  # Add 8.3% for in-progress field mapping
                actual_progress = max(actual_progress, min_progress)
            elif completed_phases > 0:
                # Calculate progress based on completed phases
                calculated_progress = (completed_phases / total_phases) * 100
                actual_progress = max(actual_progress, calculated_progress)
            
            return actual_progress
        except Exception as e:
            logger.error(f"Error calculating progress percentage: {e}")
            return 0.0
    
    @staticmethod
    def get_next_phase(current_phase: str) -> Optional[str]:
        """Get the next phase in the sequence"""
        try:
            if current_phase == "completed":
                return None
            
            if current_phase in StatusCalculator.PHASE_ORDER:
                current_index = StatusCalculator.PHASE_ORDER.index(current_phase)
                if current_index < len(StatusCalculator.PHASE_ORDER) - 1:
                    return StatusCalculator.PHASE_ORDER[current_index + 1]
            
            return None
        except Exception as e:
            logger.error(f"Error getting next phase: {e}")
            return None
    
    @staticmethod
    def determine_final_status(flow_status: str, awaiting_approval: bool = False, 
                              progress_percentage: float = 0) -> str:
        """
        Determine the final status based on flow state and conditions.
        
        Args:
            flow_status: Current flow status
            awaiting_approval: Whether flow is awaiting user approval
            progress_percentage: Current progress percentage
            
        Returns:
            Final determined status
        """
        try:
            # Preserve special statuses like waiting_for_approval
            if flow_status == "active" and not awaiting_approval:
                return "processing"
            elif progress_percentage >= 100 and flow_status not in ["paused", "waiting_for_approval", "waiting_for_user_approval"]:
                return "completed"
            elif flow_status in ["running", "active", "initialized"] and flow_status not in ["paused", "waiting_for_approval", "waiting_for_user_approval"]:
                return "processing"
            
            # Keep status as-is for: failed, paused, waiting_for_approval, waiting_for_user_approval, completed, deleted
            return flow_status
        except Exception as e:
            logger.error(f"Error determining final status: {e}")
            return "unknown"
    
    @staticmethod
    def calculate_processing_status(flow, phase: str = None) -> Dict[str, Any]:
        """
        Calculate comprehensive processing status for real-time monitoring.
        
        Args:
            flow: The discovery flow model
            phase: Optional specific phase to check
            
        Returns:
            Processing status dictionary
        """
        try:
            current_phase, steps_completed = StatusCalculator.calculate_current_phase(flow)
            progress_percentage = StatusCalculator.calculate_progress_percentage(flow, current_phase)
            phase_completion = StatusCalculator.build_phase_completion_dict(flow)
            
            # Use provided phase or calculated phase
            processing_phase = phase or current_phase
            
            return {
                "flow_id": str(flow.flow_id),
                "phase": processing_phase,
                "status": flow.status,
                "progress_percentage": progress_percentage,
                "progress": progress_percentage,
                "records_processed": getattr(flow, 'records_processed', 0),
                "records_total": getattr(flow, 'records_total', 0),
                "records_failed": getattr(flow, 'records_failed', 0),
                "validation_status": {
                    "format_valid": True,
                    "security_scan_passed": True,
                    "data_quality_score": 1.0,
                    "issues_found": []
                },
                "agent_status": getattr(flow, 'agent_status', {}),
                "recent_updates": [],
                "estimated_completion": None,
                "last_update": flow.updated_at.isoformat() if flow.updated_at else "",
                "phases": phase_completion,
                "current_phase": current_phase,
                "steps_completed": steps_completed,
                "total_steps": StatusCalculator.TOTAL_PHASES
            }
        except Exception as e:
            logger.error(f"Error calculating processing status: {e}")
            return {
                "flow_id": str(flow.flow_id) if hasattr(flow, 'flow_id') else "unknown",
                "phase": phase or "unknown",
                "status": "error",
                "progress_percentage": 0.0,
                "error": str(e)
            }
    
    @staticmethod
    def analyze_flow_state(flow, extensions=None) -> Dict[str, Any]:
        """
        Analyze comprehensive flow state including extensions data.
        
        Args:
            flow: The discovery flow model
            extensions: Optional CrewAI flow state extensions
            
        Returns:
            Comprehensive flow state analysis
        """
        try:
            current_phase, steps_completed = StatusCalculator.calculate_current_phase(flow)
            progress_percentage = StatusCalculator.calculate_progress_percentage(flow, current_phase)
            phase_completion = StatusCalculator.build_phase_completion_dict(flow)
            
            # Extract agent insights from flow state
            agent_insights = []
            if flow.crewai_state_data and "agent_insights" in flow.crewai_state_data:
                agent_insights = flow.crewai_state_data["agent_insights"]
            
            # Get awaiting_user_approval status
            awaiting_approval = False
            if flow.crewai_state_data:
                awaiting_approval = flow.crewai_state_data.get("awaiting_user_approval", False)
            
            # Merge extensions data if available
            if extensions and extensions.flow_persistence_data:
                persistence_data = extensions.flow_persistence_data
                
                # Update agent insights from extensions if not found in flow
                if not agent_insights and "agent_insights" in persistence_data:
                    agent_insights = persistence_data.get("agent_insights", [])
                
                # Update phase completion from extensions
                if "phase_completion" in persistence_data:
                    phase_completion.update(persistence_data["phase_completion"])
                    steps_completed = len([p for p in phase_completion.values() if p])
            
            # Determine final status
            final_status = StatusCalculator.determine_final_status(
                flow.status, awaiting_approval, progress_percentage
            )
            
            return {
                "flow_id": str(flow.flow_id),
                "status": final_status,
                "current_phase": current_phase,
                "progress_percentage": progress_percentage,
                "awaiting_user_approval": awaiting_approval,
                "phase_completion": phase_completion,
                "agent_insights": agent_insights,
                "steps_completed": steps_completed,
                "total_steps": StatusCalculator.TOTAL_PHASES,
                "next_phase": StatusCalculator.get_next_phase(current_phase),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error analyzing flow state: {e}")
            return {
                "flow_id": str(flow.flow_id) if hasattr(flow, 'flow_id') else "unknown",
                "status": "error",
                "error": str(e),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def is_flow_resumable(flow) -> bool:
        """Check if a flow can be resumed"""
        try:
            return flow.status in ['paused', 'waiting_for_approval', 'waiting_for_user_approval']
        except Exception as e:
            logger.error(f"Error checking if flow is resumable: {e}")
            return False
    
    @staticmethod
    def can_flow_be_deleted(flow) -> bool:
        """Check if a flow can be deleted"""
        try:
            return flow.status not in ['deleted', 'deleting']
        except Exception as e:
            logger.error(f"Error checking if flow can be deleted: {e}")
            return False
    
    @staticmethod
    def get_flow_health_score(flow) -> float:
        """
        Calculate a health score for the flow (0-1).
        
        Args:
            flow: The discovery flow model
            
        Returns:
            Health score between 0 and 1
        """
        try:
            score = 1.0
            
            # Penalty for error states
            if flow.status in ['failed', 'error']:
                score *= 0.2
            elif flow.status in ['paused', 'waiting_for_approval']:
                score *= 0.8
            
            # Bonus for progress
            progress_percentage = StatusCalculator.calculate_progress_percentage(flow)
            progress_bonus = min(progress_percentage / 100, 0.3)
            score += progress_bonus
            
            # Penalty for age (flows older than 7 days get slight penalty)
            if flow.created_at:
                age_days = (datetime.utcnow() - flow.created_at).days
                if age_days > 7:
                    age_penalty = min(age_days / 30, 0.2)  # Max 20% penalty
                    score -= age_penalty
            
            return max(0.0, min(1.0, score))
        except Exception as e:
            logger.error(f"Error calculating flow health score: {e}")
            return 0.5  # Default neutral score