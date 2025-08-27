"""
Collection Flow CRUD Operations - Main Module
Facade module that re-exports all collection flow operations from modularized components.
Provides backward compatibility while maintaining clean separation of concerns.
"""

# Import all functions from modularized components
from app.api.v1.endpoints.collection_crud_commands import (
    batch_delete_flows,
    cleanup_flows,
    create_collection_flow,
    create_collection_from_discovery,
    delete_flow,
)

# Import update operations from the new modular file
from app.api.v1.endpoints.collection_crud_update_commands import (
    update_collection_flow,
    submit_questionnaire_response,
    get_questionnaire_responses,
    batch_update_questionnaire_responses,
)
from app.api.v1.endpoints.collection_crud_execution import (
    continue_flow,
    ensure_collection_flow,
    execute_collection_flow,
)
from app.api.v1.endpoints.collection_crud_queries import (
    get_adaptive_questionnaires,
    get_collection_flow,
    get_collection_gaps,
    get_collection_readiness,
    get_collection_status,
    get_incomplete_flows,
)

# Re-export all functions for backward compatibility
__all__ = [
    # Query operations
    "get_collection_status",
    "get_collection_flow",
    "get_collection_gaps",
    "get_adaptive_questionnaires",
    "get_collection_readiness",
    "get_incomplete_flows",
    # Command operations
    "create_collection_from_discovery",
    "create_collection_flow",
    "update_collection_flow",
    "submit_questionnaire_response",
    "get_questionnaire_responses",
    "batch_update_questionnaire_responses",
    "delete_flow",
    "cleanup_flows",
    "batch_delete_flows",
    # Execution operations
    "ensure_collection_flow",
    "execute_collection_flow",
    "continue_flow",
]
