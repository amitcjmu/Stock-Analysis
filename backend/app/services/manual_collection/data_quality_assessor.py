"""
Data Quality Assessor

Handles quality assessment, scoring, and completeness analysis.
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from .data_integration_models import (
    DataPoint,
    DataQualityLevel,
    IntegratedDataset,
)

logger = logging.getLogger(__name__)


class DataQualityAssessor:
    """Assesses data quality and completeness."""

    def __init__(self):
        """Initialize quality assessor."""
        self.critical_attributes = [
            "name",
            "hostname",
            "ip_address",
            "operating_system",
            "application_name",
            "environment",
            "owner",
            "cost_center",
        ]

    async def calculate_overall_confidence(self, data_points: List[DataPoint]) -> float:
        """Calculate overall confidence score for dataset"""
        if not data_points:
            return 0.0

        confidence_scores = [
            dp.confidence_score for dp in data_points if dp.confidence_score
        ]
        if not confidence_scores:
            return 0.0

        # Weighted average based on attribute importance
        weighted_sum = 0.0
        total_weight = 0.0

        for dp in data_points:
            weight = self._get_attribute_weight(dp.attribute_name)
            weighted_sum += dp.confidence_score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    async def calculate_completeness_score(
        self, data_points: List[DataPoint], application_type: str = "general"
    ) -> float:
        """Calculate completeness score based on available data"""
        required_attributes = self._get_required_attributes(application_type)

        if not required_attributes:
            return 100.0

        # Count present attributes
        present_attributes = set(
            dp.attribute_name for dp in data_points if dp.value is not None
        )
        required_set = set(required_attributes)

        coverage = len(present_attributes.intersection(required_set)) / len(
            required_set
        )
        return coverage * 100

    async def calculate_critical_attributes_coverage(
        self, data_points: List[DataPoint]
    ) -> float:
        """Calculate coverage of critical attributes"""
        if not self.critical_attributes:
            return 100.0

        present_critical = set()
        for dp in data_points:
            if dp.value is not None:
                for critical_attr in self.critical_attributes:
                    if critical_attr in dp.attribute_name.lower():
                        present_critical.add(critical_attr)

        coverage = len(present_critical) / len(self.critical_attributes)
        return coverage * 100

    def determine_quality_level(
        self,
        completeness_score: float,
        confidence_score: float,
        critical_coverage: float,
    ) -> DataQualityLevel:
        """Determine overall quality level"""
        # Calculate composite score
        composite_score = (
            completeness_score * 0.4
            + confidence_score * 100 * 0.35
            + critical_coverage * 0.25
        )

        if composite_score >= 90:
            return DataQualityLevel.EXCELLENT
        elif composite_score >= 75:
            return DataQualityLevel.GOOD
        elif composite_score >= 60:
            return DataQualityLevel.ACCEPTABLE
        elif composite_score >= 40:
            return DataQualityLevel.POOR
        else:
            return DataQualityLevel.CRITICAL

    async def assess_6r_readiness(self, dataset: IntegratedDataset) -> float:
        """Assess 6R migration readiness based on data quality"""
        readiness_factors = {
            "completeness": dataset.completeness_score / 100,
            "confidence": dataset.confidence_score,
            "critical_coverage": dataset.critical_attributes_coverage / 100,
        }

        # Check for specific 6R-relevant attributes
        sixr_attributes = [
            "dependencies",
            "database_connections",
            "network_requirements",
            "performance_requirements",
            "compliance_requirements",
            "data_sensitivity",
        ]

        present_sixr = 0
        for dp in dataset.data_points:
            if dp.value is not None:
                for attr in sixr_attributes:
                    if attr in dp.attribute_name.lower():
                        present_sixr += 1
                        break

        sixr_coverage = min(present_sixr / len(sixr_attributes), 1.0)
        readiness_factors["sixr_specific"] = sixr_coverage

        # Calculate weighted readiness score
        weights = {
            "completeness": 0.3,
            "confidence": 0.25,
            "critical_coverage": 0.25,
            "sixr_specific": 0.2,
        }

        readiness_score = sum(
            readiness_factors[factor] * weight for factor, weight in weights.items()
        )

        return min(readiness_score * 100, 100.0)

    async def get_data_gaps(
        self, application_id: UUID, data_points: List[DataPoint]
    ) -> List[Dict[str, Any]]:
        """Identify data gaps for an application"""
        gaps = []

        # Get required attributes for application type
        # Note: In real implementation, this would query the application type
        required_attributes = self._get_required_attributes("web_application")

        present_attributes = set(
            dp.attribute_name for dp in data_points if dp.value is not None
        )

        for required_attr in required_attributes:
            if required_attr not in present_attributes:
                gap = {
                    "attribute_name": required_attr,
                    "gap_type": "missing_data",
                    "severity": self._get_gap_severity(required_attr),
                    "suggested_collection_methods": self._suggest_collection_methods(
                        required_attr
                    ),
                    "description": f"Missing required attribute: {required_attr}",
                }
                gaps.append(gap)

        # Check for low confidence data
        for dp in data_points:
            if dp.confidence_score < 0.6:
                gap = {
                    "attribute_name": dp.attribute_name,
                    "gap_type": "low_confidence",
                    "severity": "medium" if dp.confidence_score > 0.4 else "high",
                    "current_confidence": dp.confidence_score,
                    "suggested_collection_methods": self._suggest_collection_methods(
                        dp.attribute_name
                    ),
                    "description": f"Low confidence data for: {dp.attribute_name}",
                }
                gaps.append(gap)

        return gaps

    async def generate_recommendations(self, dataset: IntegratedDataset) -> List[str]:
        """Generate recommendations for improving data quality"""
        recommendations = []

        if dataset.completeness_score < 70:
            recommendations.append(
                f"Data completeness is {dataset.completeness_score:.1f}%. "
                "Consider conducting additional data collection activities."
            )

        if dataset.confidence_score < 0.7:
            recommendations.append(
                f"Average confidence score is {dataset.confidence_score:.1f}. "
                "Validate critical data points through manual verification."
            )

        if dataset.critical_attributes_coverage < 80:
            recommendations.append(
                f"Critical attributes coverage is {dataset.critical_attributes_coverage:.1f}%. "
                "Focus on collecting missing critical attributes first."
            )

        if len(dataset.conflicts) > 0:
            unresolved_conflicts = len(
                [c for c in dataset.conflicts if c.resolved_value is None]
            )
            if unresolved_conflicts > 0:
                recommendations.append(
                    f"{unresolved_conflicts} data conflicts require manual review and resolution."
                )

        if dataset.sixr_readiness_score < 60:
            recommendations.append(
                f"6R readiness score is {dataset.sixr_readiness_score:.1f}%. "
                "Collect additional technical and dependency information."
            )

        return recommendations

    async def generate_next_actions(self, dataset: IntegratedDataset) -> List[str]:
        """Generate specific next actions"""
        actions = []

        # Identify most critical gaps
        gaps = await self.get_data_gaps(dataset.application_id, dataset.data_points)
        high_priority_gaps = [g for g in gaps if g.get("severity") == "high"]

        if high_priority_gaps:
            actions.append(
                f"Prioritize collection of {len(high_priority_gaps)} high-priority missing attributes"
            )

        # Review conflicts
        unresolved_conflicts = [c for c in dataset.conflicts if c.requires_review]
        if unresolved_conflicts:
            actions.append(
                f"Review and resolve {len(unresolved_conflicts)} data conflicts"
            )

        # Quality improvements
        if dataset.quality_level in [DataQualityLevel.POOR, DataQualityLevel.CRITICAL]:
            actions.append("Conduct comprehensive data validation and cleanup")

        return actions

    def _get_attribute_weight(self, attribute_name: str) -> float:
        """Get importance weight for an attribute"""
        weights = {
            "name": 1.0,
            "hostname": 1.0,
            "ip_address": 0.9,
            "operating_system": 0.8,
            "environment": 0.8,
            "application_name": 0.9,
            "database_name": 0.7,
            "owner": 0.6,
            "cost_center": 0.5,
        }

        for key, weight in weights.items():
            if key in attribute_name.lower():
                return weight

        return 0.5  # Default weight

    def _get_required_attributes(self, application_type: str) -> List[str]:
        """Get required attributes for application type"""
        base_attributes = [
            "name",
            "hostname",
            "ip_address",
            "operating_system",
            "environment",
            "owner",
            "cost_center",
        ]

        type_specific = {
            "web_application": ["web_server", "application_server", "database_server"],
            "database": ["database_type", "database_version", "backup_strategy"],
            "api_service": ["api_endpoints", "authentication_method", "rate_limits"],
            "batch_job": ["schedule", "dependencies", "execution_time"],
        }

        return base_attributes + type_specific.get(application_type, [])

    def _get_gap_severity(self, attribute_name: str) -> str:
        """Determine severity of a data gap"""
        if attribute_name.lower() in self.critical_attributes:
            return "high"
        elif any(
            keyword in attribute_name.lower()
            for keyword in ["security", "compliance", "backup"]
        ):
            return "high"
        elif any(
            keyword in attribute_name.lower()
            for keyword in ["performance", "capacity", "monitor"]
        ):
            return "medium"
        else:
            return "low"

    def _suggest_collection_methods(self, attr_name: str) -> List[str]:
        """Suggest collection methods for an attribute"""
        method_map = {
            "hostname": ["Network scanning", "DNS lookup", "Manual input"],
            "ip_address": ["Network scanning", "DHCP logs", "Manual input"],
            "operating_system": [
                "Agent-based scanning",
                "SSH connection",
                "Manual input",
            ],
            "application": ["Process scanning", "Configuration review", "Manual input"],
            "database": ["Connection testing", "Configuration files", "Manual input"],
            "network": [
                "Network topology discovery",
                "Configuration review",
                "Manual input",
            ],
            "storage": ["System monitoring", "Disk usage analysis", "Manual input"],
            "performance": ["Monitoring tools", "Log analysis", "Load testing"],
        }

        for keyword, methods in method_map.items():
            if keyword in attr_name.lower():
                return methods

        return ["Manual collection", "Automated discovery", "Configuration review"]
