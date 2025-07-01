"""
Flow Helpers

Utility functions for flow management operations.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class FlowHelpers:
    """Helper functions for flow operations"""
    
    @staticmethod
    def calculate_flow_progress(phases: Dict[str, bool]) -> float:
        """
        Calculate overall flow progress based on phase completion.
        
        Args:
            phases: Dictionary of phase names to completion status
            
        Returns:
            Progress percentage (0-100)
        """
        if not phases:
            return 0.0
            
        completed = sum(1 for completed in phases.values() if completed)
        total = len(phases)
        
        return (completed / total) * 100.0 if total > 0 else 0.0
    
    @staticmethod
    def determine_current_phase(phases: Dict[str, bool]) -> str:
        """
        Determine the current active phase based on completion status.
        
        Args:
            phases: Dictionary of phase names to completion status
            
        Returns:
            Name of current phase or "completed"
        """
        phase_order = [
            "data_import",
            "attribute_mapping", 
            "data_cleansing",
            "inventory",
            "dependencies",
            "tech_debt"
        ]
        
        for phase in phase_order:
            if phase in phases and not phases[phase]:
                return phase
                
        return "completed"
    
    @staticmethod
    def format_phase_name(phase: str) -> str:
        """
        Format phase name for display.
        
        Args:
            phase: Internal phase name
            
        Returns:
            Human-readable phase name
        """
        phase_names = {
            "data_import": "Data Import",
            "attribute_mapping": "Attribute Mapping",
            "field_mapping": "Field Mapping",
            "data_cleansing": "Data Cleansing",
            "inventory": "Asset Inventory",
            "dependencies": "Dependency Analysis",
            "tech_debt": "Technical Debt Assessment"
        }
        
        return phase_names.get(phase, phase.replace("_", " ").title())
    
    @staticmethod
    def validate_flow_data(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate flow data structure.
        
        Args:
            data: Flow data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not data:
            return False, "Flow data is required"
            
        if "flow_id" not in data:
            return False, "flow_id is required"
            
        if not isinstance(data.get("flow_id"), str):
            return False, "flow_id must be a string"
            
        return True, None
    
    @staticmethod
    def extract_agent_insights(state_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract agent insights from CrewAI state data.
        
        Args:
            state_data: CrewAI state data dictionary
            
        Returns:
            List of agent insight dictionaries
        """
        if not state_data or not isinstance(state_data, dict):
            return []
            
        # Direct agent_insights
        insights = state_data.get("agent_insights", [])
        if isinstance(insights, list):
            return insights
            
        # Check in phase-specific data
        phase_insights = []
        for phase in ["data_import", "attribute_mapping", "data_cleansing", "inventory", "dependencies", "tech_debt"]:
            phase_data = state_data.get(phase, {})
            if isinstance(phase_data, dict) and "insights" in phase_data:
                phase_insights.extend(phase_data["insights"])
                
        return phase_insights
    
    @staticmethod
    def safe_json_parse(json_str: str) -> Optional[Dict[str, Any]]:
        """
        Safely parse JSON string.
        
        Args:
            json_str: JSON string to parse
            
        Returns:
            Parsed dictionary or None if parsing fails
        """
        if not json_str:
            return None
            
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return None
    
    @staticmethod
    def format_timestamp(dt: Optional[datetime]) -> str:
        """
        Format datetime to ISO string.
        
        Args:
            dt: Datetime object
            
        Returns:
            ISO formatted string or empty string
        """
        if dt:
            return dt.isoformat()
        return ""
    
    @staticmethod
    def normalize_phase_name(phase: str) -> str:
        """
        Normalize phase name to standard format.
        
        Args:
            phase: Phase name to normalize
            
        Returns:
            Normalized phase name
        """
        # Map variations to standard names
        phase_mapping = {
            "field_mapping": "attribute_mapping",
            "field-mapping": "attribute_mapping",
            "attr_mapping": "attribute_mapping",
            "data-import": "data_import",
            "data-cleansing": "data_cleansing",
            "tech-debt": "tech_debt",
            "tech_debt_analysis": "tech_debt",
            "asset_inventory": "inventory"
        }
        
        normalized = phase.lower().replace("-", "_")
        return phase_mapping.get(normalized, normalized)