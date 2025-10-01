"""
Questionnaire Utilities Module

Modularized utilities for questionnaire generation phase handlers.
Maintains backward compatibility by re-exporting all functions.
"""

# Import from utils
from .utils import (
    determine_questionnaire_type,
    get_next_phase_name,
    prepare_questionnaire_config,
)

# Import from state_management
from .state_management import (
    commit_database_transaction,
    save_and_update_state,
    update_state_for_generation,
)

# Import from core
from .core import (
    check_should_generate,
    create_adaptive_forms,
    generate_questionnaires_core,
    should_skip_detailed_questionnaire,
)

# Import from orchestration
from .orchestration import (
    check_loop_prevention,
    finalize_generation,
    handle_generation_error,
    handle_no_questionnaires_generated,
    record_orchestrator_submission,
)

# Export all functions for backward compatibility
__all__ = [
    # Utils
    "determine_questionnaire_type",
    "get_next_phase_name",
    "prepare_questionnaire_config",
    # State Management
    "commit_database_transaction",
    "save_and_update_state",
    "update_state_for_generation",
    # Core
    "check_should_generate",
    "create_adaptive_forms",
    "generate_questionnaires_core",
    "should_skip_detailed_questionnaire",
    # Orchestration
    "check_loop_prevention",
    "finalize_generation",
    "handle_generation_error",
    "handle_no_questionnaires_generated",
    "record_orchestrator_submission",
]
