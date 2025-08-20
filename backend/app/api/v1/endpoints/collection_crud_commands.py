"""
Collection Flow Command Operations - Main Module
Facade module that re-exports all collection flow command operations from modularized components.
Provides backward compatibility while maintaining clean separation of concerns.
"""

# Import all functions from modularized components
from app.api.v1.endpoints.collection_crud_create_commands import (
    create_collection_from_discovery,
    create_collection_flow,
)

from app.api.v1.endpoints.collection_crud_update_commands import (
    update_collection_flow,
    submit_questionnaire_response,
)

from app.api.v1.endpoints.collection_crud_delete_commands import (
    delete_flow,
    cleanup_flows,
    batch_delete_flows,
)

# Re-export all functions for backward compatibility
__all__ = [
    # Create operations
    "create_collection_from_discovery",
    "create_collection_flow",
    # Update operations
    "update_collection_flow",
    "submit_questionnaire_response",
    # Delete operations
    "delete_flow",
    "cleanup_flows",
    "batch_delete_flows",
]
