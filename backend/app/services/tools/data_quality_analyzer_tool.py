"""
Data Quality Analyzer Tool for comprehensive data quality assessment
"""

import json
import logging
import re
from typing import Any, Dict, List

from sqlalchemy import select

from app.core.database_context import get_context_db
from app.models import RawImportRecord
from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata

logger = logging.getLogger(__name__)


class DataQualityAnalyzerTool(AsyncBaseDiscoveryTool):
    """Comprehensive data quality analysis tool"""

    name: str = "data_quality_analyzer"
    description: str = (
        "Analyze data quality metrics including completeness, accuracy, consistency"
    )

    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="data_quality_analyzer",
            description="Comprehensive data quality assessment and reporting",
            tool_class=cls,
            categories=["data_quality", "validation", "analysis"],
            required_params=["data"],
            optional_params=["quality_rules", "sample_size"],
            context_aware=True,
            async_tool=True,
        )

    async def arun(
        self,
        data: List[Dict[str, Any]] = None,
        import_id: str = None,
        quality_rules: Dict[str, Any] = None,
        sample_size: int = 1000,
    ) -> str:
        """
        Analyze data quality across multiple dimensions.

        Args:
            data: Direct data to analyze (alternative to import_id)
            import_id: ID of imported data to analyze
            quality_rules: Custom quality rules to apply
            sample_size: Number of records to sample for analysis

        Returns:
            JSON string with comprehensive quality analysis
        """
        try:
            # Get data for analysis
            analysis_data = data
            if not analysis_data and import_id:
                analysis_data = await self._load_data_from_import(
                    import_id, sample_size
                )

            if not analysis_data:
                return json.dumps({"error": "No data provided for analysis"})

            # Initialize quality analysis
            quality_analysis = {
                "overall_score": 0.0,
                "record_count": len(analysis_data),
                "field_count": len(analysis_data[0]) if analysis_data else 0,
                "dimensions": {},
                "field_analysis": {},
                "issues": [],
                "recommendations": [],
                "summary": {},
            }

            # Analyze each quality dimension
            quality_analysis["dimensions"]["completeness"] = self._analyze_completeness(
                analysis_data
            )
            quality_analysis["dimensions"]["consistency"] = self._analyze_consistency(
                analysis_data
            )
            quality_analysis["dimensions"]["accuracy"] = self._analyze_accuracy(
                analysis_data
            )
            quality_analysis["dimensions"]["validity"] = self._analyze_validity(
                analysis_data
            )
            quality_analysis["dimensions"]["uniqueness"] = self._analyze_uniqueness(
                analysis_data
            )
            quality_analysis["dimensions"]["conformity"] = self._analyze_conformity(
                analysis_data
            )

            # Field-level analysis
            quality_analysis["field_analysis"] = self._analyze_fields(analysis_data)

            # Apply custom quality rules if provided
            if quality_rules:
                custom_results = self._apply_custom_rules(analysis_data, quality_rules)
                quality_analysis["custom_rules"] = custom_results

            # Calculate overall quality score
            quality_analysis["overall_score"] = self._calculate_overall_score(
                quality_analysis["dimensions"]
            )

            # Generate issues and recommendations
            quality_analysis["issues"] = self._identify_issues(quality_analysis)
            quality_analysis["recommendations"] = self._generate_recommendations(
                quality_analysis
            )

            # Create summary
            quality_analysis["summary"] = self._create_summary(quality_analysis)

            return json.dumps(quality_analysis, indent=2)

        except Exception as e:
            logger.error(f"Data quality analysis failed: {e}")
            return json.dumps({"error": str(e), "overall_score": 0.0})

    async def _load_data_from_import(
        self, import_id: str, sample_size: int
    ) -> List[Dict[str, Any]]:
        """Load data from import records"""
        async with get_context_db() as db:
            result = await db.execute(
                select(RawImportRecord)
                .where(RawImportRecord.data_import_id == import_id)
                .limit(sample_size)
            )
            records = result.scalars().all()

            return [
                (
                    json.loads(record.raw_data)
                    if isinstance(record.raw_data, str)
                    else record.raw_data
                )
                for record in records
            ]

    def _analyze_completeness(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze data completeness"""
        if not data:
            return {"score": 0.0, "issues": ["No data available"]}

        total_cells = 0
        missing_cells = 0
        field_completeness = {}

        # Get all unique fields across all records
        all_fields = set()
        for record in data:
            all_fields.update(record.keys())

        # Analyze completeness per field
        for field in all_fields:
            field_missing = 0
            field_total = len(data)

            for record in data:
                if field not in record or record[field] is None or record[field] == "":
                    field_missing += 1
                    missing_cells += 1
                total_cells += 1

            field_completeness[field] = {
                "completeness_rate": (field_total - field_missing) / field_total,
                "missing_count": field_missing,
                "total_count": field_total,
            }

        overall_completeness = (
            (total_cells - missing_cells) / total_cells if total_cells > 0 else 0
        )

        # Identify problematic fields
        issues = []
        for field, stats in field_completeness.items():
            if stats["completeness_rate"] < 0.5:
                issues.append(
                    f"Field '{field}' has high missing rate: {(1 - stats['completeness_rate']) * 100:.1f}%"
                )

        return {
            "score": overall_completeness * 100,
            "overall_completeness_rate": overall_completeness,
            "field_completeness": field_completeness,
            "missing_cells": missing_cells,
            "total_cells": total_cells,
            "issues": issues,
        }

    def _analyze_consistency(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze data consistency"""
        if not data:
            return {"score": 0.0, "issues": ["No data available"]}

        consistency_issues = []
        field_consistency = {}

        # Analyze each field for consistency
        for field in data[0].keys():
            values = [
                record.get(field) for record in data if record.get(field) is not None
            ]

            if not values:
                continue

            # Data type consistency
            data_types = set(type(v).__name__ for v in values)
            type_consistency = len(data_types) == 1

            # Format consistency for strings
            format_consistency = True
            format_patterns = set()

            string_values = [str(v) for v in values if isinstance(v, str)]
            if string_values:
                for value in string_values[:50]:  # Sample first 50
                    pattern = self._extract_format_pattern(value)
                    format_patterns.add(pattern)

                format_consistency = len(format_patterns) <= 3  # Allow up to 3 patterns

            # Case consistency for strings
            case_consistency = True
            if string_values:
                has_upper = any(v.isupper() for v in string_values if v.isalpha())
                has_lower = any(v.islower() for v in string_values if v.isalpha())
                has_title = any(v.istitle() for v in string_values if v.isalpha())

                case_variations = sum([has_upper, has_lower, has_title])
                case_consistency = case_variations <= 1

            field_consistency[field] = {
                "type_consistency": type_consistency,
                "format_consistency": format_consistency,
                "case_consistency": case_consistency,
                "data_types": list(data_types),
                "format_patterns": list(format_patterns),
            }

            # Record issues
            if not type_consistency:
                consistency_issues.append(
                    f"Field '{field}' has mixed data types: {data_types}"
                )
            if not format_consistency:
                consistency_issues.append(f"Field '{field}' has inconsistent formats")
            if not case_consistency:
                consistency_issues.append(f"Field '{field}' has inconsistent casing")

        # Calculate overall consistency score
        total_checks = len(field_consistency) * 3  # 3 checks per field
        passed_checks = sum(
            sum(
                [
                    stats["type_consistency"],
                    stats["format_consistency"],
                    stats["case_consistency"],
                ]
            )
            for stats in field_consistency.values()
        )

        consistency_score = (
            (passed_checks / total_checks * 100) if total_checks > 0 else 0
        )

        return {
            "score": consistency_score,
            "field_consistency": field_consistency,
            "issues": consistency_issues,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
        }

    def _analyze_accuracy(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze data accuracy using pattern recognition"""
        if not data:
            return {"score": 0.0, "issues": ["No data available"]}

        accuracy_issues = []
        field_accuracy = {}

        # Define accuracy patterns
        patterns = {
            "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "phone": r"^[\+]?[\d\s\-\(\)]{7,15}$",
            "ip_address": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
            "date": r"^\d{4}-\d{2}-\d{2}$",
            "url": r"^https?://[^\s/$.?#].[^\s]*$",
            "mac_address": r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",
        }

        for field in data[0].keys():
            values = [
                str(record.get(field))
                for record in data
                if record.get(field) is not None
            ]

            if not values:
                continue

            # Detect field type based on name
            field_lower = field.lower()
            expected_pattern = None

            for pattern_name, pattern in patterns.items():
                if pattern_name in field_lower:
                    expected_pattern = pattern
                    break

            # If pattern detected, validate values
            if expected_pattern:
                valid_count = sum(1 for v in values if re.match(expected_pattern, v))
                accuracy_rate = valid_count / len(values)

                field_accuracy[field] = {
                    "expected_pattern": pattern_name,
                    "accuracy_rate": accuracy_rate,
                    "valid_count": valid_count,
                    "total_count": len(values),
                }

                if accuracy_rate < 0.8:
                    accuracy_issues.append(
                        f"Field '{field}' has low accuracy rate: {accuracy_rate * 100:.1f}%"
                    )
            else:
                # General accuracy checks
                accuracy_checks = self._general_accuracy_checks(field, values)
                field_accuracy[field] = accuracy_checks

                if accuracy_checks.get("issues"):
                    accuracy_issues.extend(accuracy_checks["issues"])

        # Calculate overall accuracy score
        if field_accuracy:
            accuracy_rates = [
                stats.get("accuracy_rate", 1.0) for stats in field_accuracy.values()
            ]
            overall_accuracy = sum(accuracy_rates) / len(accuracy_rates) * 100
        else:
            overall_accuracy = 100.0  # No specific patterns to validate

        return {
            "score": overall_accuracy,
            "field_accuracy": field_accuracy,
            "issues": accuracy_issues,
        }

    def _analyze_validity(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze data validity against business rules"""
        if not data:
            return {"score": 0.0, "issues": ["No data available"]}

        validity_issues = []
        field_validity = {}

        for field in data[0].keys():
            values = [
                record.get(field) for record in data if record.get(field) is not None
            ]

            if not values:
                continue

            validity_checks = {
                "has_values": len(values) > 0,
                "no_extreme_outliers": True,
                "reasonable_range": True,
                "issues": [],
            }

            # Numeric validity checks
            numeric_values = []
            for v in values:
                try:
                    numeric_values.append(float(v))
                except Exception:
                    pass

            if (
                numeric_values and len(numeric_values) > len(values) * 0.5
            ):  # Mostly numeric
                # Check for extreme outliers
                sorted_vals = sorted(numeric_values)
                if len(sorted_vals) > 4:
                    q1 = sorted_vals[len(sorted_vals) // 4]
                    q3 = sorted_vals[3 * len(sorted_vals) // 4]
                    iqr = q3 - q1

                    outliers = [
                        v
                        for v in numeric_values
                        if v < q1 - 3 * iqr or v > q3 + 3 * iqr
                    ]

                    if (
                        len(outliers) > len(numeric_values) * 0.1
                    ):  # More than 10% outliers
                        validity_checks["no_extreme_outliers"] = False
                        validity_checks["issues"].append(
                            f"High number of extreme outliers: {len(outliers)}"
                        )

            # String validity checks
            string_values = [str(v) for v in values if isinstance(v, str)]
            if string_values:
                # Check for extremely long values
                avg_length = sum(len(s) for s in string_values) / len(string_values)
                long_values = [s for s in string_values if len(s) > avg_length * 5]

                if len(long_values) > len(string_values) * 0.1:
                    validity_checks["issues"].append(
                        f"Unusually long values detected: {len(long_values)} values"
                    )

            field_validity[field] = validity_checks
            validity_issues.extend(validity_checks["issues"])

        # Calculate overall validity score
        total_fields = len(field_validity)
        valid_fields = sum(
            1
            for stats in field_validity.values()
            if stats["has_values"]
            and stats["no_extreme_outliers"]
            and stats["reasonable_range"]
        )

        validity_score = (valid_fields / total_fields * 100) if total_fields > 0 else 0

        return {
            "score": validity_score,
            "field_validity": field_validity,
            "issues": validity_issues,
        }

    def _analyze_uniqueness(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze data uniqueness and duplicate detection"""
        if not data:
            return {"score": 0.0, "issues": ["No data available"]}

        uniqueness_issues = []
        field_uniqueness = {}

        # Overall record uniqueness
        record_hashes = set()
        duplicate_records = 0

        for record in data:
            record_str = json.dumps(record, sort_keys=True)
            record_hash = hash(record_str)

            if record_hash in record_hashes:
                duplicate_records += 1
            else:
                record_hashes.add(record_hash)

        overall_uniqueness_rate = (len(data) - duplicate_records) / len(data)

        # Field-level uniqueness
        for field in data[0].keys():
            values = [
                record.get(field) for record in data if record.get(field) is not None
            ]

            if not values:
                continue

            unique_values = len(set(str(v) for v in values))
            uniqueness_rate = unique_values / len(values)

            field_uniqueness[field] = {
                "uniqueness_rate": uniqueness_rate,
                "unique_count": unique_values,
                "total_count": len(values),
                "duplicate_count": len(values) - unique_values,
            }

            # Identify potential key fields with low uniqueness
            if uniqueness_rate < 0.1 and "id" in field.lower():
                uniqueness_issues.append(
                    f"Potential key field '{field}' has low uniqueness: {uniqueness_rate * 100:.1f}%"
                )

        if duplicate_records > 0:
            uniqueness_issues.append(f"Found {duplicate_records} duplicate records")

        # Calculate overall uniqueness score
        field_scores = [stats["uniqueness_rate"] for stats in field_uniqueness.values()]
        field_average = sum(field_scores) / len(field_scores) if field_scores else 1.0

        overall_score = (overall_uniqueness_rate + field_average) / 2 * 100

        return {
            "score": overall_score,
            "overall_uniqueness_rate": overall_uniqueness_rate,
            "duplicate_records": duplicate_records,
            "field_uniqueness": field_uniqueness,
            "issues": uniqueness_issues,
        }

    def _analyze_conformity(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze conformity to expected data standards"""
        if not data:
            return {"score": 0.0, "issues": ["No data available"]}

        conformity_issues = []
        field_conformity = {}

        # Standard field naming conventions
        naming_standards = {
            "snake_case": r"^[a-z]+(_[a-z]+)*$",
            "camelCase": r"^[a-z]+([A-Z][a-z]*)*$",
            "kebab_case": r"^[a-z]+(-[a-z]+)*$",
        }

        field_names = list(data[0].keys())

        # Check naming convention consistency
        naming_patterns = {}
        for pattern_name, pattern in naming_standards.items():
            matching_fields = [f for f in field_names if re.match(pattern, f)]
            if matching_fields:
                naming_patterns[pattern_name] = len(matching_fields)

        # Dominant naming pattern
        dominant_pattern = (
            max(naming_patterns.items(), key=lambda x: x[1])[0]
            if naming_patterns
            else None
        )

        # Check conformity for each field
        for field in field_names:
            conformity_checks = {
                "naming_standard": dominant_pattern
                and re.match(naming_standards[dominant_pattern], field),
                "no_special_chars": not re.search(r"[^a-zA-Z0-9_-]", field),
                "reasonable_length": 3 <= len(field) <= 50,
                "not_reserved_word": field.lower()
                not in ["select", "from", "where", "table", "index"],
            }

            field_conformity[field] = conformity_checks

            # Record issues
            if not conformity_checks["naming_standard"]:
                conformity_issues.append(
                    f"Field '{field}' doesn't follow standard naming convention"
                )
            if not conformity_checks["no_special_chars"]:
                conformity_issues.append(f"Field '{field}' contains special characters")
            if not conformity_checks["reasonable_length"]:
                conformity_issues.append(f"Field '{field}' has unreasonable length")
            if not conformity_checks["not_reserved_word"]:
                conformity_issues.append(f"Field '{field}' is a reserved word")

        # Calculate conformity score
        total_checks = len(field_conformity) * 4  # 4 checks per field
        passed_checks = sum(
            sum(checks.values()) for checks in field_conformity.values()
        )

        conformity_score = (
            (passed_checks / total_checks * 100) if total_checks > 0 else 0
        )

        return {
            "score": conformity_score,
            "field_conformity": field_conformity,
            "naming_patterns": naming_patterns,
            "dominant_pattern": dominant_pattern,
            "issues": conformity_issues,
        }

    def _analyze_fields(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detailed field-level analysis"""
        field_analysis = {}

        for field in data[0].keys():
            values = [
                record.get(field) for record in data if record.get(field) is not None
            ]

            analysis = {
                "field_name": field,
                "value_count": len(values),
                "null_count": len(data) - len(values),
                "unique_count": len(set(str(v) for v in values)),
                "data_types": list(set(type(v).__name__ for v in values)),
                "sample_values": values[:5],
                "statistics": {},
            }

            # Numeric statistics
            numeric_values = []
            for v in values:
                try:
                    numeric_values.append(float(v))
                except Exception:
                    pass

            if numeric_values:
                analysis["statistics"]["numeric"] = {
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "mean": sum(numeric_values) / len(numeric_values),
                    "count": len(numeric_values),
                }

            # String statistics
            string_values = [str(v) for v in values if isinstance(v, str)]
            if string_values:
                analysis["statistics"]["string"] = {
                    "min_length": min(len(s) for s in string_values),
                    "max_length": max(len(s) for s in string_values),
                    "avg_length": sum(len(s) for s in string_values)
                    / len(string_values),
                    "count": len(string_values),
                }

            field_analysis[field] = analysis

        return field_analysis

    def _calculate_overall_score(self, dimensions: Dict[str, Dict[str, Any]]) -> float:
        """Calculate overall quality score from dimension scores"""
        weights = {
            "completeness": 0.25,
            "consistency": 0.20,
            "accuracy": 0.20,
            "validity": 0.15,
            "uniqueness": 0.10,
            "conformity": 0.10,
        }

        weighted_sum = 0
        total_weight = 0

        for dimension, weight in weights.items():
            if dimension in dimensions and "score" in dimensions[dimension]:
                weighted_sum += dimensions[dimension]["score"] * weight
                total_weight += weight

        return round(weighted_sum / total_weight, 1) if total_weight > 0 else 0.0

    def _identify_issues(self, analysis: Dict[str, Any]) -> List[str]:
        """Identify and consolidate all issues"""
        all_issues = []

        # Collect issues from all dimensions
        for dimension_data in analysis["dimensions"].values():
            if "issues" in dimension_data:
                all_issues.extend(dimension_data["issues"])

        # Add critical issues based on overall score
        overall_score = analysis["overall_score"]
        if overall_score < 50:
            all_issues.append("CRITICAL: Overall data quality is poor")
        elif overall_score < 70:
            all_issues.append("WARNING: Data quality needs improvement")

        return list(set(all_issues))  # Remove duplicates

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        overall_score = analysis["overall_score"]
        dimensions = analysis["dimensions"]

        # Prioritize recommendations based on worst-performing dimensions
        dimension_scores = {
            name: data.get("score", 0) for name, data in dimensions.items()
        }

        worst_dimensions = sorted(dimension_scores.items(), key=lambda x: x[1])[:3]

        for dimension, score in worst_dimensions:
            if score < 70:
                if dimension == "completeness":
                    recommendations.append(
                        "Address missing data issues before proceeding"
                    )
                elif dimension == "consistency":
                    recommendations.append(
                        "Standardize data formats and naming conventions"
                    )
                elif dimension == "accuracy":
                    recommendations.append("Validate and correct data accuracy issues")
                elif dimension == "validity":
                    recommendations.append("Review data for business rule violations")
                elif dimension == "uniqueness":
                    recommendations.append("Identify and resolve duplicate records")
                elif dimension == "conformity":
                    recommendations.append("Align data with organizational standards")

        # Overall recommendations
        if overall_score < 60:
            recommendations.insert(0, "Consider data cleansing before migration")

        return recommendations

    def _create_summary(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create executive summary"""
        dimensions = analysis["dimensions"]

        return {
            "overall_quality": (
                "Excellent"
                if analysis["overall_score"] >= 90
                else (
                    "Good"
                    if analysis["overall_score"] >= 75
                    else "Fair"
                    if analysis["overall_score"] >= 60
                    else "Poor"
                )
            ),
            "records_analyzed": analysis["record_count"],
            "fields_analyzed": analysis["field_count"],
            "critical_issues": len([i for i in analysis["issues"] if "CRITICAL" in i]),
            "total_issues": len(analysis["issues"]),
            "best_dimension": max(
                dimensions.items(), key=lambda x: x[1].get("score", 0)
            )[0],
            "worst_dimension": min(
                dimensions.items(), key=lambda x: x[1].get("score", 0)
            )[0],
            "ready_for_migration": analysis["overall_score"] >= 70,
        }

    # Helper methods
    def _extract_format_pattern(self, value: str) -> str:
        """Extract format pattern from string value"""
        if re.match(r"^\d+$", value):
            return "numeric"
        elif re.match(r"^\d{4}-\d{2}-\d{2}$", value):
            return "date_iso"
        elif re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", value):
            return "email"
        elif re.match(r"^https?://", value):
            return "url"
        elif re.match(r"^\d+\.\d+$", value):
            return "decimal"
        elif value.isupper():
            return "uppercase"
        elif value.islower():
            return "lowercase"
        elif value.istitle():
            return "title_case"
        else:
            return "mixed"

    def _general_accuracy_checks(self, field: str, values: List[str]) -> Dict[str, Any]:
        """General accuracy checks for non-pattern fields"""
        issues = []

        # Check for obviously wrong values
        suspicious_patterns = [
            r"^test",
            r"^dummy",
            r"^xxx+",
            r"^000+",
            r"^n/a$",
            r"^null$",
            r"^undefined$",
        ]

        suspicious_count = 0
        for value in values:
            for pattern in suspicious_patterns:
                if re.match(pattern, value.lower()):
                    suspicious_count += 1
                    break

        if suspicious_count > len(values) * 0.1:  # More than 10% suspicious
            issues.append(f"High number of suspicious values: {suspicious_count}")

        accuracy_rate = 1.0 - (suspicious_count / len(values))

        return {
            "accuracy_rate": accuracy_rate,
            "suspicious_count": suspicious_count,
            "total_count": len(values),
            "issues": issues,
        }

    def _apply_custom_rules(
        self, data: List[Dict[str, Any]], rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply custom quality rules"""
        results = {"passed": 0, "failed": 0, "rule_results": {}}

        for rule_name, rule_config in rules.items():
            rule_type = rule_config.get("type")
            field = rule_config.get("field")

            if rule_type == "required_field":
                # Check if field exists and has values
                passed = all(record.get(field) is not None for record in data)
                results["rule_results"][rule_name] = {
                    "passed": passed,
                    "type": rule_type,
                    "field": field,
                }

            elif rule_type == "value_range":
                # Check if values are within specified range
                min_val = rule_config.get("min")
                max_val = rule_config.get("max")

                values = [
                    record.get(field)
                    for record in data
                    if record.get(field) is not None
                ]
                numeric_values = []

                for v in values:
                    try:
                        numeric_values.append(float(v))
                    except Exception:
                        pass

                if numeric_values:
                    in_range = all(min_val <= v <= max_val for v in numeric_values)
                    results["rule_results"][rule_name] = {
                        "passed": in_range,
                        "type": rule_type,
                        "field": field,
                        "out_of_range_count": sum(
                            1 for v in numeric_values if not (min_val <= v <= max_val)
                        ),
                    }

            # Update counters
            if results["rule_results"][rule_name]["passed"]:
                results["passed"] += 1
            else:
                results["failed"] += 1

        return results
