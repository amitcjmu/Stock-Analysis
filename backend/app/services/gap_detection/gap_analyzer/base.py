"""
GapAnalyzer base class - Initializes all 5 inspectors.

Part of Issue #980: Intelligent Multi-Layer Gap Detection System
"""

import logging
from typing import Dict

from app.services.collection.critical_attributes import CriticalAttributesDefinition
from app.services.gap_detection.inspectors import (
    ApplicationInspector,
    ColumnInspector,
    EnrichmentInspector,
    JSONBInspector,
    StandardsInspector,
)
from app.services.gap_detection.requirements.requirements_engine import (
    RequirementsEngine,
)

logger = logging.getLogger(__name__)


class GapAnalyzerBase:
    """
    Base class for GapAnalyzer with inspector initialization.

    Provides:
    - All 5 inspector instances
    - RequirementsEngine instance
    - Critical attributes mapping for priority lookups

    Performance Target: <50ms per asset
    GPT-5 Recommendations Applied:
    - #1: Tenant scoping (client_account_id, engagement_id)
    - #3: Async consistency (all methods are async)
    - #8: JSON safety (clamp overall_completeness to [0.0, 1.0])
    """

    def __init__(self) -> None:
        """Initialize all 5 inspectors and requirements engine."""
        self.column_inspector = ColumnInspector()
        self.enrichment_inspector = EnrichmentInspector()
        self.jsonb_inspector = JSONBInspector()
        self.application_inspector = ApplicationInspector()
        self.standards_inspector = StandardsInspector()
        self.requirements_engine = RequirementsEngine()

        # Load critical attributes for priority mapping
        self._critical_attributes: Dict = (
            CriticalAttributesDefinition.get_attribute_mapping()
        )

        logger.info("GapAnalyzer initialized with 5 inspectors")
