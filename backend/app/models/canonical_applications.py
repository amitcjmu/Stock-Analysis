"""
Canonical Applications Models - Legacy Compatibility Module

This module provides backward compatibility for the refactored canonical applications models.
The actual implementation has been moved to app.models.canonical_applications for better
modularity and maintainability.
"""

# Re-export the main components for backward compatibility
from app.models.canonical_applications.canonical_application import (  # noqa: F401
    CanonicalApplication,
)
from app.models.canonical_applications.application_variant import (  # noqa: F401
    ApplicationNameVariant,
)

# from app.models.canonical_applications.collection_flow_app import (  # REMOVED - CollectionFlow was removed
#     CollectionFlowApplication,
# )
from app.models.canonical_applications.enums import (  # noqa: F401
    MatchMethod,
    VerificationSource,
)
