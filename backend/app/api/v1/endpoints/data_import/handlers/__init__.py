"""
Data Import Handlers - Modular import functionality.
Exports all specialized handlers following the modular handler pattern.
"""

from .clean_api_handler import router as clean_api_router
from .field_handler import router as field_router
# from .legacy_upload_handler import router as legacy_upload_router  # File doesn't exist
from .import_retrieval_handler import router as import_retrieval_router
from .import_storage_handler import router as import_storage_router

__all__ = [
    "clean_api_router",
    # "legacy_upload_router",  # Commented out - file doesn't exist
    "import_retrieval_router",
    "import_storage_router",
    "field_router",
]
