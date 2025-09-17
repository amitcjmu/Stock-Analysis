"""
Critical Attributes Assessment Logic

Implements the core assessment functionality for evaluating data coverage
against the 22 critical attributes needed for 6R migration decisions.
"""

import logging
from typing import Any, Dict, List

from .base import CriticalAttributesDefinition

logger = logging.getLogger(__name__)


class CriticalAttributesAssessor:
    """Implementation of critical attributes assessment logic"""

    @staticmethod
    def assess_data_coverage(
        raw_data: List[Dict[str, Any]], field_mappings: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Assess how well the raw data covers the 22 critical attributes

        Args:
            raw_data: List of raw import records
            field_mappings: Optional field mappings already defined

        Returns:
            Assessment results with coverage metrics and recommendations
        """
        try:
            logger.info(
                f"🔍 Assessing critical attributes coverage for {len(raw_data)} records"
            )

            if not raw_data:
                return CriticalAttributesAssessor._create_empty_assessment_result()

            # Get attribute definitions
            attribute_mapping = CriticalAttributesDefinition.get_attribute_mapping()
            all_fields = CriticalAttributesAssessor._extract_fields_from_data(raw_data)

            # Analyze attribute coverage
            (
                covered_attributes,
                missing_critical,
                partial_coverage,
                attribute_details,
            ) = CriticalAttributesAssessor._analyze_attribute_coverage(
                attribute_mapping, all_fields, field_mappings
            )

            # Calculate scores and metrics
            scores = CriticalAttributesAssessor._calculate_coverage_scores(
                attribute_mapping, covered_attributes, missing_critical
            )

            # Generate recommendations
            recommendations = CriticalAttributesAssessor._generate_recommendations(
                missing_critical, partial_coverage, scores["migration_readiness_score"]
            )

            # Build category coverage
            category_coverage = CriticalAttributesAssessor._build_category_coverage(
                covered_attributes, attribute_details
            )

            return {
                "total_attributes": scores["total_attributes"],
                "covered_attributes": scores["covered_count"],
                "partial_coverage": len(partial_coverage),
                "coverage_percentage": scores["coverage_percentage"],
                "migration_readiness_score": scores["migration_readiness_score"],
                "missing_critical": missing_critical,
                "attribute_details": attribute_details,
                "recommendations": recommendations,
                "category_coverage": category_coverage,
            }

        except Exception as e:
            logger.error(f"❌ Critical attributes assessment failed: {e}")
            return {
                "error": str(e),
                "total_attributes": 22,
                "covered_attributes": 0,
                "migration_readiness_score": 0,
            }

    @staticmethod
    def _create_empty_assessment_result() -> Dict[str, Any]:
        """Create empty assessment result for when no data is available"""
        return {
            "total_attributes": 22,
            "covered_attributes": 0,
            "coverage_percentage": 0,
            "migration_readiness_score": 0,
            "missing_critical": CriticalAttributesDefinition.get_all_attributes(),
            "recommendations": ["No data available for assessment"],
        }

    @staticmethod
    def _extract_fields_from_data(raw_data: List[Dict[str, Any]]) -> set:
        """Extract unique field names from raw data records"""
        all_fields = set()
        for record in raw_data[:100]:  # Sample first 100 records
            if isinstance(record, dict):
                all_fields.update(record.keys())
        return all_fields

    @staticmethod
    def _analyze_attribute_coverage(
        attribute_mapping: Dict[str, Dict[str, Any]],
        all_fields: set,
        field_mappings: Dict[str, str] = None,
    ) -> tuple:
        """Analyze coverage for each critical attribute"""
        covered_attributes = []
        missing_critical = []
        partial_coverage = []
        attribute_details = {}

        for attr_name, attr_config in attribute_mapping.items():
            found, confidence, matched_fields = (
                CriticalAttributesAssessor._check_attribute_coverage(
                    attr_config, all_fields, field_mappings
                )
            )

            attribute_details[attr_name] = {
                "covered": found,
                "required": attr_config["required"],
                "category": attr_config["category"],
                "confidence": confidence,
                "matched_fields": matched_fields,
            }

            if found:
                if confidence >= 0.8:
                    covered_attributes.append(attr_name)
                else:
                    partial_coverage.append(attr_name)
            elif attr_config["required"]:
                missing_critical.append(attr_name)

        return covered_attributes, missing_critical, partial_coverage, attribute_details

    @staticmethod
    def _check_attribute_coverage(
        attr_config: Dict[str, Any],
        all_fields: set,
        field_mappings: Dict[str, str] = None,
    ) -> tuple:
        """Check if a single attribute is covered by available data"""
        patterns = attr_config["patterns"]
        found = False
        confidence = 0.0
        matched_fields = []

        # Check for pattern matches in raw data fields
        for field in all_fields:
            field_lower = field.lower()
            for pattern in patterns:
                if pattern in field_lower or field_lower in pattern:
                    found = True
                    matched_fields.append(field)
                    confidence = max(confidence, 0.8)
                    break

        # Check if field mappings cover this attribute
        if field_mappings:
            for source_field, target_field in field_mappings.items():
                for asset_field in attr_config["asset_fields"]:
                    if target_field == asset_field or asset_field in target_field:
                        found = True
                        matched_fields.append(f"{source_field} -> {target_field}")
                        confidence = 1.0

        return found, confidence, matched_fields

    @staticmethod
    def _calculate_coverage_scores(
        attribute_mapping: Dict[str, Dict[str, Any]],
        covered_attributes: List[str],
        missing_critical: List[str],
    ) -> Dict[str, Any]:
        """Calculate coverage scores and metrics"""
        total_attributes = len(attribute_mapping)
        covered_count = len(covered_attributes)
        coverage_percentage = (covered_count / total_attributes) * 100

        # Calculate migration readiness score (weighted by requirement)
        required_attributes = [k for k, v in attribute_mapping.items() if v["required"]]
        required_covered = len(
            [a for a in covered_attributes if a in required_attributes]
        )
        migration_readiness_score = (required_covered / len(required_attributes)) * 100

        return {
            "total_attributes": total_attributes,
            "covered_count": covered_count,
            "coverage_percentage": round(coverage_percentage, 2),
            "migration_readiness_score": round(migration_readiness_score, 2),
        }

    @staticmethod
    def _generate_recommendations(
        missing_critical: List[str],
        partial_coverage: List[str],
        migration_readiness_score: float,
    ) -> List[str]:
        """Generate recommendations based on assessment results"""
        recommendations = []

        if missing_critical:
            recommendations.append(
                f"Missing {len(missing_critical)} critical required attributes"
            )
            for attr in missing_critical[:3]:  # Show top 3
                recommendations.append(f"  - Add mapping for: {attr}")

        if partial_coverage:
            recommendations.append(
                f"{len(partial_coverage)} attributes have partial coverage"
            )

        if migration_readiness_score < 50:
            recommendations.append(
                "Migration readiness is LOW - need more critical attributes"
            )
        elif migration_readiness_score < 75:
            recommendations.append(
                "Migration readiness is MODERATE - consider enriching data"
            )
        else:
            recommendations.append(
                "Migration readiness is GOOD - sufficient attributes for 6R analysis"
            )

        return recommendations

    @staticmethod
    def _build_category_coverage(
        covered_attributes: List[str], attribute_details: Dict[str, Dict[str, Any]]
    ) -> Dict[str, int]:
        """Build category coverage metrics"""
        return {
            "infrastructure": len(
                [
                    a
                    for a in covered_attributes
                    if attribute_details[a]["category"] == "infrastructure"
                ]
            ),
            "application": len(
                [
                    a
                    for a in covered_attributes
                    if attribute_details[a]["category"] == "application"
                ]
            ),
            "business": len(
                [
                    a
                    for a in covered_attributes
                    if attribute_details[a]["category"] == "business"
                ]
            ),
            "technical_debt": len(
                [
                    a
                    for a in covered_attributes
                    if attribute_details[a]["category"] == "technical_debt"
                ]
            ),
        }
