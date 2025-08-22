"""
Discovery Flow Phase Analysis Methods

Contains analysis methods specific to discovery flow phases.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class DiscoveryAnalysis:
    """Discovery-specific analysis methods for phase results"""

    @staticmethod
    def analyze_import_metrics(results: Any, state: Any) -> Dict[str, Any]:
        """Analyze data import metrics"""
        from app.services.flow_orchestration.execution_engine_phase_utils import (
            DecisionUtils,
        )

        raw_data = DecisionUtils.get_state_attribute(state, "raw_data", [])
        return {
            "total_records": len(raw_data),
            "field_count": (
                len(raw_data[0]) if raw_data and isinstance(raw_data[0], dict) else 0
            ),
            "import_duration": (
                results.get("duration", 0) if isinstance(results, dict) else 0
            ),
            "success_rate": 0.9,  # Would calculate from actual import results
        }

    @staticmethod
    def analyze_mapping_quality(state: Any) -> Dict[str, Any]:
        """Analyze field mapping quality"""
        from app.services.flow_orchestration.execution_engine_phase_utils import (
            DecisionUtils,
        )

        field_mappings = DecisionUtils.get_state_attribute(state, "field_mappings", {})

        if not field_mappings:
            return {"confidence": 0, "missing_critical_fields": []}

        # Identify which fields are actually critical based on data
        critical_fields = DecisionUtils.identify_critical_fields(state)
        mapped_fields = set(field_mappings.keys())
        missing_critical = [f for f in critical_fields if f not in mapped_fields]

        confidence = DecisionUtils.get_state_attribute(
            state, "field_mapping_confidence", 0.5
        )

        return {
            "confidence": confidence,
            "total_fields": len(field_mappings),
            "critical_fields": critical_fields,
            "missing_critical_fields": missing_critical,
            "field_coverage": (
                len(mapped_fields) / len(critical_fields) if critical_fields else 1.0
            ),
        }

    @staticmethod
    def analyze_cleansing_impact(results: Any, state: Any) -> Dict[str, Any]:
        """Analyze data cleansing impact"""
        if not isinstance(results, dict):
            return {"failure_rate": 0, "records_processed": 0}

        total_records = results.get("total_records", 0)
        failed_records = results.get("failed_records", 0)

        failure_rate = failed_records / total_records if total_records > 0 else 0

        return {
            "failure_rate": failure_rate,
            "records_processed": total_records,
            "records_cleaned": results.get("records_cleaned", 0),
            "quality_improvement": results.get("quality_improvement", 0),
            "failed_records": results.get("failed_record_details", []),
        }

    @staticmethod
    def analyze_asset_creation(results: Any, state: Any) -> Dict[str, Any]:
        """Analyze asset creation results"""
        if not isinstance(results, dict):
            return {"assets_created": 0, "success_rate": 0}

        return {
            "assets_created": results.get("assets_created", 0),
            "success_rate": results.get("success_rate", 0),
            "creation_errors": results.get("errors", []),
        }

    @staticmethod
    def analyze_discovery_phase_results(
        phase: str, results: Any, state: Any
    ) -> Dict[str, Any]:
        """Main method to analyze discovery-specific phase results"""
        if phase == "data_import":
            return DiscoveryAnalysis.analyze_import_metrics(results, state)
        elif phase == "field_mapping":
            return DiscoveryAnalysis.analyze_mapping_quality(state)
        elif phase == "data_cleansing":
            return DiscoveryAnalysis.analyze_cleansing_impact(results, state)
        elif phase == "asset_creation":
            return DiscoveryAnalysis.analyze_asset_creation(results, state)
        else:
            logger.warning(f"Unknown discovery phase for analysis: {phase}")
            return {}
