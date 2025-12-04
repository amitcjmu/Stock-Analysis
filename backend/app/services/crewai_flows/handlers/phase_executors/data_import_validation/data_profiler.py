"""
Intelligent data profiling for import validation.

Provides comprehensive data analysis including:
- Multi-value detection (comma/semicolon/pipe-separated values)
- Full dataset analysis (not just samples)
- Field length analysis against schema constraints
- Data profile report generation

Related: ADR-038, Issue #1204, Issues #1206-#1209
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from .data_profiler_models import (
    DELIMITERS,
    MULTI_VALUE_PATTERNS,
    DataProfileReport,
    FieldStatistics,
    LengthViolation,
    MultiValueResult,
)

logger = logging.getLogger(__name__)


class DataProfiler:
    """
    Intelligent data profiler for discovery flow import validation.

    Performs comprehensive analysis of imported data to detect:
    - Multi-valued fields (comma/semicolon/pipe-separated)
    - Fields exceeding schema constraints
    - Data quality issues
    - Completeness and consistency metrics
    """

    def __init__(self, raw_data: List[Dict[str, Any]]):
        """
        Initialize the data profiler.

        Args:
            raw_data: List of dictionaries representing imported records
        """
        self.raw_data = raw_data or []
        self._field_stats: Dict[str, FieldStatistics] = {}
        self._multi_value_results: Dict[str, MultiValueResult] = {}
        self._length_violations: List[LengthViolation] = []

    def analyze_full_dataset(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze ALL records in the dataset (not just samples).

        Returns:
            Dict mapping field_name -> statistics summary
        """
        if not self.raw_data:
            logger.warning("No data to analyze")
            return {}

        logger.info(
            f"[ISSUE-1207] Analyzing full dataset: {len(self.raw_data)} records"
        )

        self._field_stats = defaultdict(FieldStatistics)

        for record in self.raw_data:
            if not isinstance(record, dict):
                continue
            for field_name, value in record.items():
                self._field_stats[field_name].add_value(value)

        # Convert to summary format
        result = {name: stats.summary() for name, stats in self._field_stats.items()}

        logger.info(
            f"[ISSUE-1207] Analyzed {len(result)} fields across {len(self.raw_data)} records"
        )
        return result

    def detect_multi_values(
        self, field_name: Optional[str] = None
    ) -> List[MultiValueResult]:
        """
        Detect multi-valued fields (comma/semicolon/pipe-separated).

        Args:
            field_name: Optional specific field to check. If None, checks all fields.

        Returns:
            List of MultiValueResult for fields with detected multi-values
        """
        if not self.raw_data:
            return []

        # CC FIX: Iterate all records to build complete field list (Qodo suggestion)
        if field_name:
            fields_to_check = [field_name]
        else:
            fields_to_check = []
            for rec in self.raw_data:
                if isinstance(rec, dict):
                    for k in rec.keys():
                        if k not in fields_to_check:
                            fields_to_check.append(k)

        results = []

        for fname in fields_to_check:
            multi_value_records = []
            delimiter_counts = defaultdict(int)

            for idx, record in enumerate(self.raw_data):
                if not isinstance(record, dict):
                    continue

                # CC FIX: Stringify non-string values to catch multi-values in any type (Qodo suggestion)
                raw_value = record.get(fname)
                if raw_value is None:
                    continue
                value = str(raw_value)

                # Check against all delimiter patterns
                for pattern_name, pattern in MULTI_VALUE_PATTERNS.items():
                    if pattern.match(value):
                        delimiter_counts[pattern_name] += 1
                        if len(multi_value_records) < 10:  # Limit samples
                            delimiter = DELIMITERS[pattern_name]
                            item_count = len(value.split(delimiter))
                            multi_value_records.append(
                                {
                                    "record_index": idx,
                                    "value": (
                                        value[:100] + "..."
                                        if len(value) > 100
                                        else value
                                    ),
                                    "delimiter": pattern_name,
                                    "item_count": item_count,
                                }
                            )
                        break  # Only count first matching pattern

            # Determine most common delimiter if multi-values found
            is_multi_valued = len(multi_value_records) > 0
            primary_delimiter = None
            if delimiter_counts:
                primary_delimiter = max(delimiter_counts, key=delimiter_counts.get)

            total_affected = sum(delimiter_counts.values())

            result = MultiValueResult(
                field_name=fname,
                is_multi_valued=is_multi_valued,
                affected_count=total_affected,
                delimiter=primary_delimiter,
                samples=multi_value_records[:5],  # Top 5 samples
                recommendation=(
                    "Consider splitting into separate records or using AssetDependency table"
                    if is_multi_valued
                    else "No multi-value issues detected"
                ),
            )

            if is_multi_valued:
                self._multi_value_results[fname] = result
                results.append(result)

        logger.info(
            f"[ISSUE-1206] Detected {len(results)} fields with multi-valued data"
        )
        return results

    def check_field_length_violations(
        self,
        schema_constraints: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[LengthViolation]:
        """
        Check if any field values exceed schema constraints.

        Args:
            schema_constraints: Dict mapping column_name -> {"max_length": int, ...}
                               If None, loads from schema_constraints utility

        Returns:
            List of LengthViolation for fields exceeding limits
        """
        if not self._field_stats:
            self.analyze_full_dataset()

        if schema_constraints is None:
            try:
                from app.utils.schema_constraints import get_asset_schema_constraints

                schema_constraints = get_asset_schema_constraints()
            except ImportError:
                logger.warning("Could not import schema constraints utility")
                schema_constraints = {}

        self._length_violations = []

        for field_name, stats in self._field_stats.items():
            summary = stats.summary()
            max_found = summary["max_length"]

            # Check if field exists in schema with max_length constraint
            schema_info = schema_constraints.get(field_name, {})
            max_allowed = schema_info.get("max_length")

            if max_allowed and max_found > max_allowed:
                # Find sample records that exceed limit
                exceeding_samples = self._find_exceeding_records(
                    field_name, max_allowed
                )

                violation = LengthViolation(
                    field_name=field_name,
                    schema_limit=max_allowed,
                    max_found=max_found,
                    exceeds_by=max_found - max_allowed,
                    affected_count=len(exceeding_samples),
                    samples=exceeding_samples[:5],
                    recommendations=[
                        f"Truncate values to {max_allowed} characters",
                        "Split multi-valued fields into separate records",
                        "Map to different field with larger limit",
                    ],
                )
                self._length_violations.append(violation)

        logger.info(
            f"[ISSUE-1208] Found {len(self._length_violations)} field length violations"
        )
        return self._length_violations

    def _find_exceeding_records(
        self,
        field_name: str,
        max_length: int,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Find sample records where field exceeds length limit."""
        samples: List[Dict[str, Any]] = []

        for idx, record in enumerate(self.raw_data):
            if not isinstance(record, dict):
                continue

            # CC FIX: Handle falsy values like "0" correctly (Qodo suggestion)
            raw = record.get(field_name, "")
            str_value = "" if raw is None else str(raw)
            if len(str_value) > max_length:
                # CC FIX: Mask potential sensitive data in previews (Qodo security)
                preview = str_value[:50] + "..." if len(str_value) > 50 else str_value
                # Redact if field name suggests sensitive content
                if any(
                    sensitive in field_name.lower()
                    for sensitive in [
                        "password",
                        "secret",
                        "token",
                        "key",
                        "ssn",
                        "credit",
                    ]
                ):
                    preview = "[REDACTED - sensitive field]"

                samples.append(
                    {
                        "record_index": idx,
                        "value_length": len(str_value),
                        "preview": preview,
                    }
                )
                if len(samples) >= limit:
                    break

        return samples

    def _calculate_completeness_score(self) -> float:
        """Calculate completeness score (% non-null values)."""
        if not self._field_stats:
            return 0.0

        total_values = 0
        non_null_values = 0

        for stats in self._field_stats.values():
            summary = stats.summary()
            total_values += summary["total_records"]
            non_null_values += summary["non_null_records"]

        if total_values == 0:
            return 0.0

        return round((non_null_values / total_values) * 100, 2)

    def _calculate_consistency_score(self) -> float:
        """Calculate consistency score based on data type uniformity."""
        # For now, return a high score - can be enhanced later
        return 95.0

    def _calculate_constraint_compliance_score(self) -> float:
        """Calculate constraint compliance score.

        CC FIX: Revised to be field-based rather than cell-based (Qodo suggestion).
        Score is 100 minus the percentage of fields that have violations.
        This provides a more intuitive and accurate compliance metric.
        """
        if not self._field_stats:
            return 100.0

        total_relevant_fields = len(self._field_stats)
        if total_relevant_fields == 0:
            return 100.0

        # Count unique fields with violations
        fields_with_violations = len({v.field_name for v in self._length_violations})

        # Score is 100 minus the percentage of fields that have violations
        violation_percentage = (fields_with_violations / total_relevant_fields) * 100
        score = 100 - violation_percentage

        return round(max(0, min(100, score)), 2)

    def generate_profile_report(
        self,
        schema_constraints: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> DataProfileReport:
        """
        Generate comprehensive data profile report.

        Args:
            schema_constraints: Optional schema constraints dict

        Returns:
            DataProfileReport with full analysis results
        """
        logger.info("[ISSUE-1209] Generating data profile report")

        # Run all analyses if not already done
        field_profiles = self.analyze_full_dataset()
        multi_value_results = self.detect_multi_values()
        length_violations = self.check_field_length_violations(schema_constraints)

        # Calculate quality scores
        completeness = self._calculate_completeness_score()
        consistency = self._calculate_consistency_score()
        compliance = self._calculate_constraint_compliance_score()
        overall = round((completeness + consistency + compliance) / 3, 2)

        # Categorize issues
        critical_issues = [v.to_dict() for v in length_violations]
        warnings = [
            {
                "severity": "warning",
                "field": mv.field_name,
                "issue": f"Multi-valued field detected (delimiter: {mv.delimiter})",
                "affected_count": mv.affected_count,
                "delimiter": mv.delimiter,
                "samples": mv.samples,
                "recommendation": mv.recommendation,
            }
            for mv in multi_value_results
        ]

        # Add info about high null counts
        info = []
        for field_name, profile in field_profiles.items():
            if profile["null_percentage"] > 50:
                info.append(
                    {
                        "severity": "info",
                        "field": field_name,
                        "issue": "High null percentage",
                        "null_percentage": profile["null_percentage"],
                        "recommendation": "Consider if this field is necessary",
                    }
                )

        report = DataProfileReport(
            generated_at=datetime.utcnow(),
            total_records=len(self.raw_data),
            total_fields=len(field_profiles),
            completeness_score=completeness,
            consistency_score=consistency,
            constraint_compliance_score=compliance,
            overall_quality_score=overall,
            critical_issues=critical_issues,
            warnings=warnings,
            info=info,
            field_profiles=field_profiles,
            requires_user_decision=len(critical_issues) > 0 or len(warnings) > 0,
            blocking_issue_count=len(critical_issues),
        )

        logger.info(
            f"[ISSUE-1209] Profile complete: {report.total_records} records, "
            f"{len(critical_issues)} critical, {len(warnings)} warnings"
        )

        return report
