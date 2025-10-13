"""
Field Mapping Handlers for Unified Discovery.

Modularized structure for better maintainability:
- helpers.py: Shared helper functions
- queries.py: GET operations (read-only)
- commands.py: POST/PUT/DELETE operations (write operations)

CC: Modularized from single file to comply with 400-line limit.
"""

from fastapi import APIRouter

# Import routers from submodules
from .queries import router as queries_router
from .commands import router as commands_router

# Re-export helper functions for backward compatibility
from .helpers import (
    get_discovery_flow,
    check_and_mark_field_mapping_complete,
    ensure_field_mappings_exist,
    generate_field_mappings,
    get_field_mappings_from_db,
    convert_mapping_type,
    create_field_mapping_item,
)

# Create main router that combines all subrouters
router = APIRouter()
router.include_router(queries_router)
router.include_router(commands_router)

__all__ = [
    "router",
    "get_discovery_flow",
    "check_and_mark_field_mapping_complete",
    "ensure_field_mappings_exist",
    "generate_field_mappings",
    "get_field_mappings_from_db",
    "convert_mapping_type",
    "create_field_mapping_item",
]
