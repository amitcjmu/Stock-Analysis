"""
Assessment Flow Processors
Business logic processing for assessment flows including background task execution,
flow initialization, and phase processing operations.

This module maintains backward compatibility by re-exporting all public functions
from the modularized submodules.
"""

# Import from initialization module
from .initialization import execute_assessment_flow_initialization

# Import from continuation module
from .continuation import (
    continue_assessment_flow,
    resume_assessment_flow_execution,
)

# Import from phase processors module
from .phase_processors import (
    process_app_on_page_generation_phase,
    process_architecture_standards_phase,
    process_component_sixr_strategies_phase,
    process_finalization_phase,
    process_tech_debt_analysis_phase,
)

# Define public API
__all__ = [
    # Initialization functions
    "execute_assessment_flow_initialization",
    # Continuation functions
    "continue_assessment_flow",
    "resume_assessment_flow_execution",
    # Phase processor functions
    "process_app_on_page_generation_phase",
    "process_architecture_standards_phase",
    "process_component_sixr_strategies_phase",
    "process_finalization_phase",
    "process_tech_debt_analysis_phase",
]
