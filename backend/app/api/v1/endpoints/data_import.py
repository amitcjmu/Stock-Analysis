"""
Data Import API endpoints - Modular router aggregation.
Enhanced with multi-tenant context awareness and automatic session management.
"""

from fastapi import APIRouter

# Import all modularized routers from the data_import directory __init__.py
from .data_import import router as data_import_directory_router

# Also include the handler routers that contain the missing endpoints
from .data_import.handlers.import_storage_handler import router as import_storage_router

# Create main router that aggregates all modules
router = APIRouter()

# Include the modularized data import router
router.include_router(data_import_directory_router)

# Include the import storage handler that contains store-import and latest-import endpoints
router.include_router(import_storage_router, tags=["Import Storage"])
