"""
Collection Applications Enhanced API Module
"""

from .enhanced import (
    process_canonical_applications,
    bulk_deduplicate_applications,
    find_potential_duplicates,
    merge_canonical_applications,
    get_canonical_applications,
    update_flow_applications_legacy,
)

__all__ = [
    "process_canonical_applications",
    "bulk_deduplicate_applications",
    "find_potential_duplicates",
    "merge_canonical_applications",
    "get_canonical_applications",
    "update_flow_applications_legacy",
]
