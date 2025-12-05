"""
Help Content Service - Modularized for maintainability.

This module preserves backward compatibility by exporting the service
instance that was previously in help_content_service.py.

Original file: help_content_service.py (615 lines) -> split into:
- static_content.py: STATIC_HELP_CONTENT data
- service.py: HelpContentService class
- __init__.py: Backward compatibility exports

Issue: #1218 - [Feature] Contextual AI Chat Assistant
Milestone: Contextual AI Chat Assistant
"""

# Import static content from modularized subdirectory (backward compatibility)
from .content import STATIC_HELP_CONTENT

# Import service and singleton instance
from .service import HelpContentService, help_content_service

# Export all for backward compatibility
__all__ = [
    "STATIC_HELP_CONTENT",
    "HelpContentService",
    "help_content_service",
]
