"""
Collection Applications Enhanced API - Legacy Compatibility Module

This module provides backward compatibility for the refactored collection applications API.
The actual implementation has been moved to app.api.v1.endpoints.collection_applications
for better modularity and maintainability.
"""

# Re-export the main components for backward compatibility
from app.api.v1.endpoints.collection_applications.enhanced import (
    process_canonical_applications,
    bulk_deduplicate_applications,
)
