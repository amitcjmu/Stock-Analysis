"""
Data models for intelligent data profiling.

Extracted from data_profiler.py to modularize the code.

Related: ADR-038, Issue #1204
"""

import re
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


# Multi-value detection patterns (require 3+ items to be considered multi-valued)
MULTI_VALUE_PATTERNS = {
    "comma": re.compile(r"[^,]+(?:,\s*[^,]+){2,}"),
    "semicolon": re.compile(r"[^;]+(?:;\s*[^;]+){2,}"),
    "pipe": re.compile(r"[^|]+(?:\|\s*[^|]+){2,}"),
}

# Delimiter mapping for splitting
DELIMITERS = {
    "comma": ",",
    "semicolon": ";",
    "pipe": "|",
}


@dataclass
class FieldStatistics:
    """Track statistics for a single field across all records."""

    lengths: List[int] = field(default_factory=list)
    null_count: int = 0
    unique_values: set = field(default_factory=set)
    total_records: int = 0

    # Memory optimization: cap unique values tracking
    MAX_UNIQUE_VALUES = 1000

    def add_value(self, value: Any) -> None:
        """Add a value to the statistics."""
        self.total_records += 1

        if value is None or value == "":
            self.null_count += 1
        else:
            str_val = str(value)
            self.lengths.append(len(str_val))
            # Cap unique values to prevent memory issues with large datasets
            if len(self.unique_values) < self.MAX_UNIQUE_VALUES:
                self.unique_values.add(str_val)

    def summary(self) -> Dict[str, Any]:
        """Generate summary statistics."""
        return {
            "min_length": min(self.lengths) if self.lengths else 0,
            "max_length": max(self.lengths) if self.lengths else 0,
            "avg_length": (
                round(statistics.mean(self.lengths), 2) if self.lengths else 0
            ),
            "null_count": self.null_count,
            "null_percentage": round(
                (
                    (self.null_count / self.total_records * 100)
                    if self.total_records > 0
                    else 0
                ),
                2,
            ),
            "unique_count": len(self.unique_values),
            "unique_capped": len(self.unique_values) >= self.MAX_UNIQUE_VALUES,
            "total_records": self.total_records,
            "non_null_records": self.total_records - self.null_count,
        }


@dataclass
class MultiValueResult:
    """Result of multi-value detection for a field."""

    field_name: str
    is_multi_valued: bool
    affected_count: int
    delimiter: Optional[str]
    samples: List[Dict[str, Any]]
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field_name,
            "is_multi_valued": self.is_multi_valued,
            "affected_count": self.affected_count,
            "delimiter": self.delimiter,
            "samples": self.samples,
            "recommendation": self.recommendation,
        }


@dataclass
class LengthViolation:
    """Result of field length constraint violation."""

    field_name: str
    schema_limit: int
    max_found: int
    exceeds_by: int
    affected_count: int
    samples: List[Dict[str, Any]]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": "critical",
            "field": self.field_name,
            "issue": f"Value exceeds VARCHAR({self.schema_limit}) limit",
            "schema_limit": self.schema_limit,
            "max_found": self.max_found,
            "exceeds_by": self.exceeds_by,
            "affected_count": self.affected_count,
            "samples": self.samples,
            "recommendations": self.recommendations,
        }


@dataclass
class DataProfileReport:
    """Comprehensive data profile report."""

    generated_at: datetime
    total_records: int
    total_fields: int

    # Quality scores (0-100)
    completeness_score: float
    consistency_score: float
    constraint_compliance_score: float
    overall_quality_score: float

    # Issues by severity
    critical_issues: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    info: List[Dict[str, Any]]

    # Field-level details
    field_profiles: Dict[str, Dict[str, Any]]

    # User action required
    requires_user_decision: bool
    blocking_issue_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "summary": {
                "total_records": self.total_records,
                "total_fields": self.total_fields,
                "quality_scores": {
                    "completeness": self.completeness_score,
                    "consistency": self.consistency_score,
                    "constraint_compliance": self.constraint_compliance_score,
                    "overall": self.overall_quality_score,
                },
            },
            "issues": {
                "critical": self.critical_issues,
                "warnings": self.warnings,
                "info": self.info,
            },
            "field_profiles": self.field_profiles,
            "user_action_required": self.requires_user_decision,
            "blocking_issues": self.blocking_issue_count,
        }
