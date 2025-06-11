"""
State validation for the discovery workflow.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, validator
from app.schemas.flow_schemas import DiscoveryFlowState

class WorkflowStateValidator:
    """Validates workflow state transitions and content."""
    
    @classmethod
    def validate_state_transition(
        cls, 
        current_state: DiscoveryFlowState, 
        new_state: DiscoveryFlowState
    ) -> bool:
        """
        Validate if the state transition is allowed.
        
        Args:
            current_state: The current workflow state
            new_state: The proposed new workflow state
            
        Returns:
            bool: True if the transition is valid, False otherwise
            
        Raises:
            ValueError: If the transition is invalid
        """
        # Define valid state transitions
        valid_transitions = {
            'pending': ['data_source_analysis', 'failed'],
            'data_source_analysis': ['data_validation', 'failed'],
            'data_validation': ['field_mapping', 'failed'],
            'field_mapping': ['asset_classification', 'failed'],
            'asset_classification': ['dependency_analysis', 'failed'],
            'dependency_analysis': ['database_integration', 'failed'],
            'database_integration': ['completed', 'failed'],
            'failed': ['retrying'],
            'retrying': [
                'data_source_analysis', 
                'data_validation', 
                'field_mapping', 
                'asset_classification', 
                'dependency_analysis', 
                'database_integration', 
                'failed'
            ],
            'completed': []  # Terminal state
        }
        
        current_phase = current_state.current_phase or 'pending'
        new_phase = new_state.current_phase or 'pending'
        
        if current_phase not in valid_transitions:
            raise ValueError(f"Unknown current phase: {current_phase}")
            
        if new_phase not in valid_transitions:
            raise ValueError(f"Unknown target phase: {new_phase}")
            
        if new_phase not in valid_transitions[current_phase]:
            raise ValueError(
                f"Invalid transition from '{current_phase}' to '{new_phase}'. "
                f"Allowed: {valid_transitions[current_phase]}"
            )
            
        return True
    
    @classmethod
    def validate_required_fields(
        cls,
        state: DiscoveryFlowState,
        phase: str
    ) -> None:
        """
        Validate that required fields are present for the current phase.
        
        Args:
            state: The workflow state to validate
            phase: The current workflow phase
            
        Raises:
            ValueError: If required fields are missing
        """
        # Define required fields for each phase
        required_fields = {
            'data_source_analysis': ['cmdb_data', 'source_analysis'],
            'data_validation': ['validation_results'],
            'field_mapping': ['field_mappings'],
            'asset_classification': ['asset_classes'],
            'dependency_analysis': ['dependencies'],
            'database_integration': ['database_operations']
        }
        
        if phase not in required_fields:
            return
            
        missing = []
        for field in required_fields[phase]:
            if not hasattr(state, field) or getattr(state, field) is None:
                missing.append(field)
                
        if missing:
            raise ValueError(
                f"Missing required fields for phase '{phase}': {', '.join(missing)}"
            )

    @classmethod
    def validate_state_completion(
        cls,
        state: DiscoveryFlowState,
        phase: str
    ) -> bool:
        """
        Validate if the current phase is complete.
        
        Args:
            state: The workflow state to validate
            phase: The current workflow phase
            
        Returns:
            bool: True if the phase is complete, False otherwise
        """
        completion_flags = {
            'data_source_analysis': 'data_source_analysis_complete',
            'data_validation': 'data_validation_complete',
            'field_mapping': 'field_mapping_complete',
            'asset_classification': 'asset_classification_complete',
            'dependency_analysis': 'dependency_analysis_complete',
            'database_integration': 'database_integration_complete'
        }
        
        if phase not in completion_flags:
            return True
            
        return getattr(state, completion_flags[phase], False)
