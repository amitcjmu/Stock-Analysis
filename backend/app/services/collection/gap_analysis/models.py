"""
Data models for Intelligent Gap Scanner.

This module defines data structures used by IntelligentGapScanner
to track where data exists across multiple sources and determine true gaps.

CC Generated for Issue #1111 - IntelligentGapScanner with 6-Source Data Awareness
Per ADR-037: Intelligent Gap Detection and Questionnaire Generation Architecture
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class DataSource:
    """
    Represents where data was found for a specific field.

    Attributes:
        source_type: Type of data source (standard_column, custom_attributes,
                     enrichment_tech_debt, enrichment_performance, enrichment_cost,
                     environment, canonical_applications, related_assets)
        field_path: Full path to the field (e.g., "assets.cpu_count",
                    "custom_attributes.hardware.cpu")
        value: The actual value found at this location
        confidence: Confidence score for this data source (0.0-1.0)
                    Higher values indicate more reliable sources:
                    - 1.0: Standard column (authoritative)
                    - 0.95: Custom attributes (structured data)
                    - 0.90: Enrichment tables (assessed data)
                    - 0.85: Environment field (metadata)
                    - 0.80: Canonical applications (derived)
                    - 0.70: Related assets (propagated)
    """

    source_type: str
    field_path: str
    value: Any
    confidence: float

    def __post_init__(self):
        """Validate confidence score is in valid range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")


@dataclass
class IntelligentGap:
    """
    Represents a detected gap with awareness of all data sources.

    This is an "intelligent" gap because it knows:
    - Where data WAS found (even if it's a gap for the primary location)
    - Whether this is a TRUE gap (no data in ANY source)
    - Confidence score for gap certainty

    Attributes:
        field_id: Internal field identifier (e.g., "cpu_count")
        field_name: Human-readable field name (e.g., "CPU Count")
        priority: Gap priority level: "critical", "high", "medium", "low"
        data_found: List of all data sources where this field has data
                    (empty list = TRUE gap, no data anywhere)
        is_true_gap: True if NO data found in ANY source
        confidence_score: How confident we are this is a true gap (0.0-1.0)
                          1.0 = No data anywhere (high confidence it's a gap)
                          0.0 = High-confidence data exists (NOT a gap)
        section: Which questionnaire section this gap belongs to
        suggested_question: Optional AI-generated question for this gap
        metadata: Additional context about the gap

    Example - TRUE Gap:
        IntelligentGap(
            field_id="cpu_count",
            field_name="CPU Count",
            priority="critical",
            data_found=[],  # No data in any source
            is_true_gap=True,
            confidence_score=1.0,
            section="infrastructure"
        )

    Example - Data Exists Elsewhere (NOT a gap):
        IntelligentGap(
            field_id="cpu_count",
            field_name="CPU Count",
            priority="critical",
            data_found=[
                DataSource(
                    source_type="custom_attributes",
                    field_path="custom_attributes.hardware.cpu",
                    value=8,
                    confidence=0.95
                )
            ],
            is_true_gap=False,
            confidence_score=0.05,  # Low confidence it's a gap (data exists)
            section="infrastructure"
        )
    """

    field_id: str
    field_name: str
    priority: str  # "critical", "high", "medium", "low"
    data_found: List[DataSource]
    is_true_gap: bool
    confidence_score: float
    section: str
    suggested_question: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate field values after initialization."""
        # Validate priority
        valid_priorities = {"critical", "high", "medium", "low"}
        if self.priority not in valid_priorities:
            raise ValueError(
                f"Priority must be one of {valid_priorities}, got '{self.priority}'"
            )

        # Validate confidence score
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError(
                f"Confidence score must be 0.0-1.0, got {self.confidence_score}"
            )

        # Validate logical consistency
        if self.is_true_gap and len(self.data_found) > 0:
            raise ValueError(
                f"Logical error: is_true_gap=True but data_found has "
                f"{len(self.data_found)} sources"
            )

        if not self.is_true_gap and len(self.data_found) == 0:
            raise ValueError("Logical error: is_true_gap=False but data_found is empty")

    def get_best_data_source(self) -> Optional[DataSource]:
        """
        Get the data source with highest confidence.

        Returns:
            The DataSource with highest confidence, or None if no data found
        """
        if not self.data_found:
            return None

        return max(self.data_found, key=lambda ds: ds.confidence)

    def has_data_in_primary_column(self) -> bool:
        """
        Check if data exists in the primary standard column.

        Returns:
            True if any data source is of type "standard_column"
        """
        return any(ds.source_type == "standard_column" for ds in self.data_found)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "field_id": self.field_id,
            "field_name": self.field_name,
            "priority": self.priority,
            "data_found": [
                {
                    "source_type": ds.source_type,
                    "field_path": ds.field_path,
                    "value": ds.value,
                    "confidence": ds.confidence,
                }
                for ds in self.data_found
            ],
            "is_true_gap": self.is_true_gap,
            "confidence_score": self.confidence_score,
            "section": self.section,
            "suggested_question": self.suggested_question,
            "metadata": self.metadata,
        }
