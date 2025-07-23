"""
Quality Validator

Validates collection data quality throughout the process.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from app.core.context import get_current_context
from app.services.collection_flow.quality_scoring import QualityAssessmentService
from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata

from .base import BaseCollectionTool

logger = logging.getLogger(__name__)


class QualityValidator(AsyncBaseDiscoveryTool, BaseCollectionTool):
    """Validates collection quality throughout the process"""

    name: str = "QualityValidator"
    description: str = "Validate data quality during collection"

    def __init__(self):
        super().__init__()
        self.name = "QualityValidator"
        self.format_patterns = {
            "email": r"^[\w\.-]+@[\w\.-]+\.\w+$",
            "ip": r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
            "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            "date": r"^\d{4}-\d{2}-\d{2}$",
        }

    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        return ToolMetadata(
            name="QualityValidator",
            description="Validates collection data quality and completeness",
            tool_class=cls,
            categories=["collection", "validation", "quality"],
            required_params=["collected_data", "validation_type"],
            optional_params=["quality_thresholds", "validation_rules"],
            context_aware=True,
            async_tool=True,
        )

    async def arun(
        self,
        collected_data: Dict[str, Any],
        validation_type: str,
        quality_thresholds: Optional[Dict[str, float]] = None,
        validation_rules: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Validate collected data quality.

        Args:
            collected_data: Data collected from platforms
            validation_type: Type of validation (quick, standard, comprehensive)
            quality_thresholds: Quality score thresholds
            validation_rules: Custom validation rules

        Returns:
            Validation results with quality scores
        """
        get_current_context()
        QualityAssessmentService()

        validation_results = self._create_base_result("validate_quality") | {
            "validation_type": validation_type,
            "overall_quality": 0.0,
            "platform_scores": {},
            "issues": [],
            "recommendations": [],
        }

        try:
            # Set default thresholds if not provided
            thresholds = quality_thresholds or self._get_default_thresholds()

            # Validate each platform's data
            for platform, data in collected_data.items():
                platform_validation = await self._validate_platform_data(
                    platform, data, validation_type, thresholds, validation_rules
                )
                validation_results["platform_scores"][platform] = platform_validation

                # Add platform issues to overall results
                validation_results["issues"].extend(
                    [
                        {"platform": platform, **issue}
                        for issue in platform_validation["issues"]
                    ]
                )

            # Calculate overall quality
            validation_results["overall_quality"] = self._calculate_overall_quality(
                validation_results["platform_scores"]
            )

            # Generate recommendations
            validation_results["recommendations"] = self._generate_recommendations(
                validation_results
            )

            self._mark_success(validation_results)
            return validation_results

        except Exception as e:
            self._add_error(validation_results, f"Quality validation failed: {str(e)}")
            return validation_results

    async def _validate_platform_data(
        self,
        platform: str,
        data: Any,
        validation_type: str,
        thresholds: Dict[str, float],
        validation_rules: Optional[List[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """Validate data for a single platform"""

        platform_validation = {
            "completeness": 0.0,
            "accuracy": 0.0,
            "consistency": 0.0,
            "timeliness": 0.0,
            "issues": [],
        }

        # Completeness check
        if validation_type in ["standard", "comprehensive"]:
            completeness = await self._check_completeness(data, validation_rules)
            platform_validation["completeness"] = completeness

            if completeness < thresholds["completeness"]:
                platform_validation["issues"].append(
                    {
                        "type": "completeness",
                        "severity": "high" if completeness < 0.5 else "medium",
                        "message": f"Data completeness {completeness:.2%} below threshold",
                        "threshold": thresholds["completeness"],
                        "actual": completeness,
                    }
                )

        # Accuracy check
        if validation_type == "comprehensive":
            accuracy = await self._check_accuracy(data, validation_rules)
            platform_validation["accuracy"] = accuracy

            if accuracy < thresholds["accuracy"]:
                platform_validation["issues"].append(
                    {
                        "type": "accuracy",
                        "severity": "high",
                        "message": f"Data accuracy {accuracy:.2%} below threshold",
                        "threshold": thresholds["accuracy"],
                        "actual": accuracy,
                    }
                )

        # Consistency check
        consistency = await self._check_consistency(data)
        platform_validation["consistency"] = consistency

        if consistency < thresholds["consistency"]:
            platform_validation["issues"].append(
                {
                    "type": "consistency",
                    "severity": "medium",
                    "message": f"Data consistency {consistency:.2%} below threshold",
                    "threshold": thresholds["consistency"],
                    "actual": consistency,
                }
            )

        # Calculate overall platform score
        scores = [
            v
            for k, v in platform_validation.items()
            if k in thresholds and isinstance(v, (int, float)) and v > 0
        ]
        platform_validation["overall_score"] = (
            sum(scores) / len(scores) if scores else 0.0
        )

        return platform_validation

    async def _check_completeness(
        self, data: Any, rules: Optional[List[Dict[str, Any]]]
    ) -> float:
        """Check data completeness"""
        if not data:
            return 0.0

        if isinstance(data, dict):
            # Check required fields from rules
            if rules:
                required_fields = [r["field"] for r in rules if r.get("required")]
                if required_fields:
                    present_fields = sum(
                        1 for f in required_fields if f in data and data[f] is not None
                    )
                    return present_fields / len(required_fields)

            # Basic completeness - non-null values
            total_fields = len(data)
            non_null_fields = sum(1 for v in data.values() if v is not None)
            return non_null_fields / total_fields if total_fields > 0 else 0.0

        elif isinstance(data, list):
            # For lists, check completeness of each item
            if not data:
                return 0.0
            completeness_scores = [
                await self._check_completeness(item, rules) for item in data[:100]
            ]
            return sum(completeness_scores) / len(completeness_scores)

        return 1.0  # Single values are complete if present

    async def _check_accuracy(
        self, data: Any, rules: Optional[List[Dict[str, Any]]]
    ) -> float:
        """Check data accuracy using validation rules"""
        if not rules:
            return 1.0  # Assume accurate if no rules

        # Apply validation rules
        passed_rules = 0
        total_rules = 0

        if isinstance(data, dict):
            for rule in rules:
                result = self._apply_validation_rule(data, rule)
                if result is not None:
                    if result:
                        passed_rules += 1
                    total_rules += 1

        elif isinstance(data, list):
            # Check rules against each item in list
            for item in data[:50]:  # Sample for performance
                if isinstance(item, dict):
                    for rule in rules:
                        result = self._apply_validation_rule(item, rule)
                        if result is not None:
                            if result:
                                passed_rules += 1
                            total_rules += 1

        return passed_rules / total_rules if total_rules > 0 else 1.0

    async def _check_consistency(self, data: Any) -> float:
        """Check data consistency"""
        # Simple consistency check - look for conflicting or duplicate data
        if isinstance(data, list):
            if not data:
                return 1.0

            # Check for duplicates
            try:
                unique_items = len(set(str(item) for item in data))
                return unique_items / len(data)
            except (TypeError, ValueError):
                # If items can't be hashed/stringified, assume consistent
                return 1.0

        return 1.0  # Single items are consistent

    def _apply_validation_rule(
        self, data_item: Dict[str, Any], rule: Dict[str, Any]
    ) -> Optional[bool]:
        """Apply a single validation rule"""
        rule_type = rule.get("type")
        field_name = rule.get("field")

        if not field_name or field_name not in data_item:
            return None

        field_value = data_item[field_name]
        if field_value is None:
            return None

        if rule_type == "format":
            # Format validation
            format_type = rule.get("format")
            return self._validate_format(field_value, format_type)

        elif rule_type == "range":
            # Range validation
            min_val = rule.get("min")
            max_val = rule.get("max")
            try:
                numeric_value = float(field_value)
                return min_val <= numeric_value <= max_val
            except (ValueError, TypeError):
                return False

        elif rule_type == "enum":
            # Enum validation
            allowed_values = rule.get("values", [])
            return field_value in allowed_values

        return None

    def _validate_format(self, value: Any, format_type: str) -> bool:
        """Validate value format"""
        if not isinstance(value, str):
            return False

        pattern = self.format_patterns.get(format_type)
        if pattern:
            return bool(re.match(pattern, value, re.IGNORECASE))

        return True

    def _get_default_thresholds(self) -> Dict[str, float]:
        """Get default quality thresholds"""
        return {
            "completeness": 0.8,
            "accuracy": 0.9,
            "consistency": 0.85,
            "timeliness": 0.95,
        }

    def _calculate_overall_quality(
        self, platform_scores: Dict[str, Dict[str, Any]]
    ) -> float:
        """Calculate overall quality score"""
        all_scores = [p["overall_score"] for p in platform_scores.values()]
        return sum(all_scores) / len(all_scores) if all_scores else 0.0

    def _generate_recommendations(
        self, validation_results: Dict[str, Any]
    ) -> List[str]:
        """Generate quality improvement recommendations"""
        recommendations = []
        overall_quality = validation_results["overall_quality"]
        issues = validation_results["issues"]

        if overall_quality < 0.8:
            recommendations.append(
                "Consider re-collecting data from platforms with low quality scores"
            )

        critical_issues = [i for i in issues if i.get("severity") == "high"]
        if critical_issues:
            recommendations.append(
                f"Address {len(critical_issues)} critical quality issues before proceeding"
            )

        # Issue-specific recommendations
        issue_types = set(i.get("type") for i in issues)

        if "completeness" in issue_types:
            recommendations.append(
                "Investigate missing data fields and improve data collection coverage"
            )

        if "accuracy" in issue_types:
            recommendations.append(
                "Review validation rules and data format requirements"
            )

        if "consistency" in issue_types:
            recommendations.append(
                "Check for duplicate records and data normalization issues"
            )

        return recommendations
