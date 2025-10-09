"""
Data Cleansing Utilities - Helper functions for data cleansing operations
Extracted to maintain file length limits and improve code organization.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DataCleansingUtils:
    """Utility class for data cleansing helper methods"""

    @staticmethod
    def generate_cleansing_summary(
        cleaned_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate summary of data cleansing results"""

        total_records = len(cleaned_data)
        if total_records == 0:
            return {
                "total_records_processed": 0,
                "cleansing_summary": "No records to process",
                "quality_indicators": {},
            }

        # Count records with various quality indicators
        valid_records = sum(
            1 for record in cleaned_data if record.get("is_valid", True)
        )
        records_with_errors = sum(
            1 for record in cleaned_data if record.get("validation_errors")
        )

        # Calculate data completeness
        field_completeness = {}
        common_fields = ["name", "asset_type", "environment", "business_criticality"]

        for field in common_fields:
            complete_count = sum(
                1
                for record in cleaned_data
                if record.get(field) and str(record.get(field)).strip()
            )
            field_completeness[field] = round((complete_count / total_records) * 100, 1)

        summary = {
            "total_records_processed": total_records,
            "valid_records": valid_records,
            "invalid_records": total_records - valid_records,
            "records_with_validation_errors": records_with_errors,
            "validation_success_rate": round((valid_records / total_records) * 100, 1),
            "field_completeness_percentage": field_completeness,
            "cleansing_method": "persistent_agent",
            "data_quality_improved": True,
        }

        return summary

    @staticmethod
    def calculate_cleansing_quality_metrics(
        cleaned_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate quality metrics for cleansed data"""

        total_records = len(cleaned_data)
        if total_records == 0:
            return {
                "overall_quality_score": 0,
                "data_completeness": 0,
                "validation_pass_rate": 0,
            }

        # Calculate validation pass rate
        valid_records = sum(
            1 for record in cleaned_data if record.get("is_valid", True)
        )
        validation_pass_rate = (valid_records / total_records) * 100

        # Calculate data completeness across key fields
        critical_fields = [
            "name",
            "asset_type",
            "environment",
            "business_criticality",
            "technology_stack",
            "network_exposure",
            "data_sensitivity",
        ]

        total_completeness = 0
        for record in cleaned_data:
            record_completeness = 0
            for field in critical_fields:
                if record.get(field) and str(record.get(field)).strip():
                    record_completeness += 1
            total_completeness += record_completeness / len(critical_fields)

        data_completeness = (total_completeness / total_records) * 100

        # Calculate enrichment quality (if agentic enrichment was applied)
        enrichment_quality = 0
        enriched_records = sum(
            1
            for record in cleaned_data
            if record.get("enrichment_status") == "agentic_complete"
        )
        if enriched_records > 0:
            enrichment_quality = (enriched_records / total_records) * 100

        # Overall quality score combines multiple factors
        overall_quality_score = (
            validation_pass_rate * 0.4
            + data_completeness * 0.4
            + enrichment_quality * 0.2
        )

        metrics = {
            "overall_quality_score": round(overall_quality_score, 1),
            "data_completeness": round(data_completeness, 1),
            "validation_pass_rate": round(validation_pass_rate, 1),
            "enrichment_quality": round(enrichment_quality, 1),
            "total_records_analyzed": total_records,
            "valid_records_count": valid_records,
            "enriched_records_count": enriched_records,
            "quality_assessment": (
                "high"
                if overall_quality_score >= 80
                else "medium" if overall_quality_score >= 60 else "low"
            ),
        }

        return metrics

    @staticmethod
    def generate_enrichment_summary(
        enriched_assets: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate summary of agentic enrichment results"""

        total_assets = len(enriched_assets)
        successful_enrichments = sum(
            1
            for asset in enriched_assets
            if asset.get("enrichment_status") == "agentic_complete"
        )

        # Business Value Distribution
        business_value_distribution = {"high": 0, "medium": 0, "low": 0}
        for asset in enriched_assets:
            score = asset.get("business_value_score", 5)
            if score >= 8:
                business_value_distribution["high"] += 1
            elif score >= 6:
                business_value_distribution["medium"] += 1
            else:
                business_value_distribution["low"] += 1

        # Risk Assessment Distribution
        risk_distribution = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for asset in enriched_assets:
            risk_level = asset.get("risk_assessment", "medium")
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1

        # Cloud Readiness Distribution
        cloud_ready_count = sum(
            1
            for asset in enriched_assets
            if asset.get("cloud_readiness_score", 50) >= 70
        )
        modernization_ready_count = sum(
            1
            for asset in enriched_assets
            if asset.get("modernization_potential") == "high"
        )

        summary = {
            "total_assets_analyzed": total_assets,
            "successful_enrichments": successful_enrichments,
            "enrichment_success_rate": (
                round((successful_enrichments / total_assets * 100), 1)
                if total_assets > 0
                else 0
            ),
            "business_value_distribution": business_value_distribution,
            "risk_assessment_distribution": risk_distribution,
            "cloud_readiness_metrics": {
                "cloud_ready_assets": cloud_ready_count,
                "modernization_ready_assets": modernization_ready_count,
                "cloud_readiness_percentage": (
                    round((cloud_ready_count / total_assets * 100), 1)
                    if total_assets > 0
                    else 0
                ),
            },
            "agentic_intelligence_metrics": {
                "patterns_discovered": sum(
                    asset.get("memory_patterns_discovered", 0)
                    for asset in enriched_assets
                ),
                "average_confidence": (
                    round(
                        sum(
                            asset.get("agentic_confidence_score", 0.5)
                            for asset in enriched_assets
                        )
                        / total_assets,
                        2,
                    )
                    if total_assets > 0
                    else 0.0
                ),
            },
        }

        return summary

    @staticmethod
    def calculate_agentic_quality_metrics(
        enriched_assets: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculate quality metrics based on agentic enrichment completeness"""

        total_assets = len(enriched_assets)
        if total_assets == 0:
            return {
                "overall_agentic_quality": 0,
                "enrichment_completeness": 0,
                "data_intelligence_score": 0,
            }

        # Enrichment Completeness: How many assets were fully enriched
        fully_enriched = sum(
            1
            for asset in enriched_assets
            if asset.get("enrichment_status") == "agentic_complete"
        )
        enrichment_completeness = (fully_enriched / total_assets) * 100

        # Data Intelligence Score: Quality of insights generated
        intelligence_scores = []
        for asset in enriched_assets:
            score = 0
            # Business context completeness
            if asset.get("business_criticality"):
                score += 20
            if asset.get("business_value_score", 0) > 0:
                score += 20
            if asset.get("risk_assessment"):
                score += 20
            if asset.get("cloud_readiness_score", 0) > 0:
                score += 20
            if asset.get("modernization_potential"):
                score += 20

            intelligence_scores.append(score)

        avg_intelligence_score = (
            sum(intelligence_scores) / len(intelligence_scores)
            if intelligence_scores
            else 0
        )

        # Confidence Scoring
        confidence_scores = [
            asset.get("agentic_confidence_score", 0.5) for asset in enriched_assets
        ]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) * 100

        # Overall Quality combines all factors
        overall_quality = (
            enrichment_completeness * 0.4
            + avg_intelligence_score * 0.4
            + avg_confidence * 0.2
        )

        metrics = {
            "overall_agentic_quality": round(overall_quality, 1),
            "enrichment_completeness": round(enrichment_completeness, 1),
            "data_intelligence_score": round(avg_intelligence_score, 1),
            "average_confidence": round(avg_confidence, 1),
            "total_assets_analyzed": total_assets,
            "fully_enriched_assets": fully_enriched,
            "quality_grade": (
                "A"
                if overall_quality >= 90
                else (
                    "B"
                    if overall_quality >= 80
                    else (
                        "C"
                        if overall_quality >= 70
                        else "D" if overall_quality >= 60 else "F"
                    )
                )
            ),
        }

        return metrics

    @staticmethod
    def safe_float_convert(value) -> float:
        """Safely convert a value to float, with fallback for None/empty"""
        if value is None or value == "":
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def normalize_field_name(field_name: str) -> str:
        """
        Normalize field names to snake_case.

        Handles conversions:
        - PascalCase -> snake_case (Asset_Name -> asset_name)
        - Pascal Case with spaces -> snake_case (Asset Name -> asset_name)
        - Mixed Case -> snake_case (AssetName -> asset_name)
        - Acronyms -> snake_case (CPU_Cores -> cpu_cores)

        Args:
            field_name: Original field name

        Returns:
            Normalized snake_case field name
        """
        import re

        if not field_name:
            return field_name

        # Replace spaces and existing underscores with temporary marker
        normalized = field_name.replace(" ", "_").replace("_", "_")

        # Handle acronyms: Insert underscore before uppercase letter that follows lowercase
        # This handles: AssetName -> Asset_Name, but keeps CPU -> CPU
        normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized)

        # Convert to lowercase
        normalized = normalized.lower()

        # Replace multiple underscores with single
        normalized = re.sub(r"_+", "_", normalized)

        # Remove leading/trailing underscores
        normalized = normalized.strip("_")

        return normalized

    @staticmethod
    def normalize_record_fields(record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize all field names in a record to snake_case.

        Args:
            record: Original record with mixed-case field names

        Returns:
            Record with normalized snake_case field names
        """
        if not isinstance(record, dict):
            return record

        normalized_record = {}
        for key, value in record.items():
            normalized_key = DataCleansingUtils.normalize_field_name(key)
            normalized_record[normalized_key] = value

        logger.debug(
            f"🔄 Normalized fields: {list(record.keys())[:3]}... -> {list(normalized_record.keys())[:3]}..."
        )
        return normalized_record
