"""
Static help content for contextual chat assistant.

Modularized for maintainability - split from static_content.py (481 lines) into:
- discovery_content.py: Discovery workflow help articles
- collection_content.py: Collection workflow help articles
- assessment_content.py: Assessment workflow help articles
- general_content.py: Planning, decommission, finops, and troubleshooting content

This __init__.py preserves backward compatibility by combining all content.

Issue: #1218 - [Feature] Contextual AI Chat Assistant
Milestone: Contextual AI Chat Assistant
"""

from typing import Any, Dict, List

from .discovery_content import DISCOVERY_CONTENT
from .collection_content import COLLECTION_CONTENT
from .assessment_content import ASSESSMENT_CONTENT
from .general_content import GENERAL_CONTENT

# Combine all content into single list for backward compatibility
STATIC_HELP_CONTENT: List[Dict[str, Any]] = (
    DISCOVERY_CONTENT + ASSESSMENT_CONTENT + COLLECTION_CONTENT + GENERAL_CONTENT
)

__all__ = [
    "STATIC_HELP_CONTENT",
    "DISCOVERY_CONTENT",
    "COLLECTION_CONTENT",
    "ASSESSMENT_CONTENT",
    "GENERAL_CONTENT",
]
