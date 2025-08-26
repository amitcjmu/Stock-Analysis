"""
Canonical Applications Models - Legacy Compatibility Module

This module provides backward compatibility for the refactored canonical applications models.
The actual implementation has been moved to app.models.canonical_applications for better
modularity and maintainability.
"""

# Re-export the main components for backward compatibility
from app.models.canonical_applications.canonical_application import (
    CanonicalApplication,
)  # noqa: F401
from app.models.canonical_applications.application_variant import (
    ApplicationNameVariant,
)  # noqa: F401
from app.models.canonical_applications.collection_flow_app import (
    CollectionFlowApplication,  # noqa: F401
)
from app.models.canonical_applications.enums import (
    MatchMethod,
    VerificationSource,
)  # noqa: F401
