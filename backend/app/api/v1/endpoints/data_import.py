"""
Data Import API endpoints - Modular router aggregation.
Enhanced with multi-tenant context awareness and automatic session management.
"""

from fastapi import APIRouter

# Import all modularized routers from the data_import directory
from .data_import import router as data_import_directory_router

# Create main router that aggregates all modules
router = APIRouter()

# Include the modularized data import router
router.include_router(data_import_directory_router)
