"""
Collection Applications Enhanced API Module
"""

from .enhanced import (
    process_canonical_applications,
    bulk_deduplicate_applications,
)

__all__ = [
    "process_canonical_applications",
    "bulk_deduplicate_applications",
]
