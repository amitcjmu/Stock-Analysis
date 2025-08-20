"""
Collection Flow CRUD Operations - Main Module
Facade module that re-exports all collection flow operations from modularized components.
Provides backward compatibility while maintaining clean separation of concerns.
"""

# Import all functions from modularized components
from app.api.v1.endpoints.collection_crud_queries import (
    get_collection_status,
    get_collection_flow,
    get_collection_gaps,
    get_adaptive_questionnaires,
    get_collection_readiness,
    get_incomplete_flows,
)

from app.api.v1.endpoints.collection_crud_commands import (
    create_collection_from_discovery,
    create_collection_flow,
    update_collection_flow,
    submit_questionnaire_response,
    delete_flow,
    cleanup_flows,
    batch_delete_flows,
)

from app.api.v1.endpoints.collection_crud_execution import (
    ensure_collection_flow,
    execute_collection_flow,
    continue_flow,
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
    "delete_flow",
    "cleanup_flows",
    "batch_delete_flows",
    # Execution operations
    "ensure_collection_flow",
    "execute_collection_flow",
    "continue_flow",
]
