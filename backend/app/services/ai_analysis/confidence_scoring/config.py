"""
Configuration and initialization for confidence scoring system.

Provides default weights, thresholds, and strategy requirements.
"""

from typing import Any, Dict

from .models import ConfidenceFactorType, SixRStrategy


class ConfidenceScoringConfig:
    """Configuration class for confidence scoring system"""

    @staticmethod
    def get_factor_weights() -> Dict[ConfidenceFactorType, float]:
        """Get default weights for confidence factors"""
        return {
            ConfidenceFactorType.DATA_COMPLETENESS: 0.25,  # 25% - How complete is the data
            ConfidenceFactorType.DATA_QUALITY: 0.20,  # 20% - Quality of the data
            ConfidenceFactorType.SOURCE_RELIABILITY: 0.15,  # 15% - How reliable is the source
            ConfidenceFactorType.VALIDATION_STATUS: 0.15,  # 15% - Has data been validated
            ConfidenceFactorType.BUSINESS_CONTEXT: 0.10,  # 10% - Business context completeness
            ConfidenceFactorType.TEMPORAL_FRESHNESS: 0.08,  # 8% - How recent is the data
            ConfidenceFactorType.CROSS_VALIDATION: 0.04,  # 4% - Cross-validation with other sources
            ConfidenceFactorType.EXPERT_VALIDATION: 0.03,  # 3% - Expert review and validation
        }

    @staticmethod
    def get_strategy_requirements() -> Dict[SixRStrategy, Dict[str, Any]]:
        """Get data requirements for each 6R strategy"""
        return {
            SixRStrategy.REHOST: {
                "critical_attributes": [
                    "hostname",
                    "os_type",
                    "os_version",
                    "cpu_cores",
                    "memory_gb",
                    "storage_gb",
                    "network_zone",
                    "environment",
                    "dependencies",
                ],
                "importance_weights": {
                    "infrastructure": 0.6,
                    "operational": 0.25,
                    "application": 0.1,
                    "dependencies": 0.05,
                },
                "minimum_confidence_threshold": 75.0,
            },
            SixRStrategy.REPLATFORM: {
                "critical_attributes": [
                    "application_type",
                    "technology_stack",
                    "os_type",
                    "database_type",
                    "integration_points",
                    "data_flows",
                    "performance_requirements",
                ],
                "importance_weights": {
                    "application": 0.4,
                    "infrastructure": 0.3,
                    "dependencies": 0.2,
                    "operational": 0.1,
                },
                "minimum_confidence_threshold": 80.0,
            },
            SixRStrategy.REFACTOR: {
                "critical_attributes": [
                    "application_name",
                    "technology_stack",
                    "code_complexity",
                    "application_dependencies",
                    "data_classification",
                    "integration_points",
                    "business_logic_complexity",
                    "technical_debt_score",
                ],
                "importance_weights": {
                    "application": 0.5,
                    "dependencies": 0.3,
                    "infrastructure": 0.1,
                    "operational": 0.1,
                },
                "minimum_confidence_threshold": 85.0,
            },
            SixRStrategy.REARCHITECT: {
                "critical_attributes": [
                    "application_name",
                    "technology_stack",
                    "architecture_complexity",
                    "microservices_suitability",
                    "cloud_native_requirements",
                    "integration_points",
                    "data_flows",
                    "scalability_requirements",
                ],
                "importance_weights": {
                    "application": 0.5,
                    "dependencies": 0.3,
                    "infrastructure": 0.1,
                    "operational": 0.1,
                },
                "minimum_confidence_threshold": 85.0,
            },
            SixRStrategy.REPLACE: {
                "critical_attributes": [
                    "business_function",
                    "user_count",
                    "business_criticality",
                    "compliance_scope",
                    "cost_center",
                    "vendor_relationship",
                    "licensing_model",
                    "integration_complexity",
                ],
                "importance_weights": {
                    "application": 0.3,
                    "operational": 0.4,
                    "dependencies": 0.2,
                    "infrastructure": 0.1,
                },
                "minimum_confidence_threshold": 70.0,
            },
            SixRStrategy.REWRITE: {
                "critical_attributes": [
                    "application_name",
                    "business_logic_complexity",
                    "technology_stack",
                    "cloud_native_requirements",
                    "development_resources",
                    "time_to_market",
                    "legacy_constraints",
                    "modernization_goals",
                ],
                "importance_weights": {
                    "application": 0.6,
                    "operational": 0.2,
                    "dependencies": 0.1,
                    "infrastructure": 0.1,
                },
                "minimum_confidence_threshold": 80.0,
            },
        }

    @staticmethod
    def get_quality_thresholds() -> Dict[str, float]:
        """Get quality assessment thresholds"""
        return {
            "excellent": 90.0,
            "good": 75.0,
            "acceptable": 60.0,
            "poor": 40.0,
            "critical": 25.0,
        }
