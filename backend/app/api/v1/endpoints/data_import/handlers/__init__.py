"""
Modular API Handlers for Data Import
"""

# Import all modularized routers from the handlers directory
from .clean_api_handler import router as clean_api_router
from .field_handler import router as field_handler
from .import_retrieval_handler import router as import_retrieval_router
from .upload_handler import router as upload_router

__all__ = [
    "clean_api_router",
    "field_handler",
    "import_retrieval_router",
    "upload_router",
]
