"""
Type definitions for application deduplication service
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from app.models.canonical_applications import (
    CanonicalApplication,
    ApplicationNameVariant,
    MatchMethod,
)


@dataclass
class DeduplicationResult:
    """Result of application deduplication process"""

    canonical_application: CanonicalApplication
    name_variant: Optional[ApplicationNameVariant]
    is_new_canonical: bool
    is_new_variant: bool
    match_method: MatchMethod
    similarity_score: float
    confidence_score: float
    requires_verification: bool
    potential_duplicates: List[Dict[str, Any]]
