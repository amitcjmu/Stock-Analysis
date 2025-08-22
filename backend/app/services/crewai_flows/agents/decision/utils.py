"""
Decision Agent Utilities

Shared utilities for decision-making agents.
"""

import logging
from typing import Any, Dict, List

from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

logger = logging.getLogger(__name__)


class ConfidenceCalculator:
    """Utility class for calculating confidence scores"""

    @staticmethod
    def weighted_average(
        factors: Dict[str, float], weights: Dict[str, float] = None
    ) -> float:
        """
        Calculate weighted average confidence from multiple factors.

        Args:
            factors: Dictionary of factor_name -> confidence (0-1)
            weights: Optional weights for factors

        Returns:
            Weighted average confidence score
        """
        if not factors:
            return 0.0

        if weights is None:
            weights = {k: 1.0 for k in factors.keys()}

        total_weighted_score = 0.0
        total_weight = 0.0

        for factor, confidence in factors.items():
            weight = weights.get(factor, 1.0)
            total_weighted_score += confidence * weight
            total_weight += weight

        return (
            min(1.0, total_weighted_score / total_weight) if total_weight > 0 else 0.0
        )

    @staticmethod
    def calculate_threshold(
        base_threshold: float,
        risk_factors: List[str],
        data_quality: float,
        complexity: float,
    ) -> float:
        """
        Calculate dynamic threshold based on various factors.

        Args:
            base_threshold: Base confidence threshold
            risk_factors: List of identified risk factors
            data_quality: Data quality score (0-1)
            complexity: Complexity score (0-1)

        Returns:
            Adjusted threshold
        """
        threshold = base_threshold

        # Adjust for risk factors
        risk_adjustment = len(risk_factors) * 0.05

        # Adjust for data quality
        quality_adjustment = (1 - data_quality) * 0.1

        # Adjust for complexity
        complexity_adjustment = complexity * 0.05

        # Calculate final threshold
        adjusted = (
            threshold + risk_adjustment + quality_adjustment + complexity_adjustment
        )

        # Cap at reasonable maximum
        return min(0.95, adjusted)


class DecisionUtils:
    """Utility functions for decision-making logic"""

    @staticmethod
    def get_state_attribute(state: Any, attr: str, default: Any = None) -> Any:
        """Get attribute from state, handling both dict and object types"""
        if isinstance(state, dict):
            return state.get(attr, default)
        return getattr(state, attr, default)

    @staticmethod
    def assess_data_quality(state: UnifiedDiscoveryFlowState) -> float:
        """Assess overall data quality (0-1)"""
        raw_data = DecisionUtils.get_state_attribute(state, "raw_data", [])

        if not raw_data:
            return 0.0

        quality_score = 1.0
        sample_size = min(100, len(raw_data))

        for record in raw_data[:sample_size]:
            # Check for missing values
            if isinstance(record, dict):
                missing_count = sum(1 for v in record.values() if v is None or v == "")
                if len(record) > 0:
                    quality_score -= (missing_count / len(record)) * 0.01

        return max(0.0, min(1.0, quality_score))

    @staticmethod
    def assess_completeness(phase: str, state: UnifiedDiscoveryFlowState) -> float:
        """Assess phase completeness"""
        phase_completion = DecisionUtils.get_state_attribute(
            state, "phase_completion", {}
        )
        return 1.0 if phase_completion.get(phase, False) else 0.0

    @staticmethod
    def assess_complexity(state: UnifiedDiscoveryFlowState) -> float:
        """Assess data/mapping complexity"""
        raw_data = DecisionUtils.get_state_attribute(state, "raw_data", [])

        if not raw_data:
            return 0.0

        complexity_score = 0.0
        if raw_data and isinstance(raw_data[0], dict):
            field_names = list(raw_data[0].keys())
            for field in field_names:
                field_lower = field.lower()
                # Complex field indicators
                if any(
                    ind in field_lower for ind in ["custom", "legacy", "temp", "_old"]
                ):
                    complexity_score += 0.1
                if len(field) > 30:
                    complexity_score += 0.05

        return min(1.0, complexity_score)

    @staticmethod
    def identify_risk_factors(state: UnifiedDiscoveryFlowState) -> List[str]:
        """Identify risk factors in current state"""
        risks = []

        # Check data volume
        raw_data = DecisionUtils.get_state_attribute(state, "raw_data", [])
        if len(raw_data) > 10000:
            risks.append("large_data_volume")

        # Check for sensitive data patterns
        if DecisionUtils._has_sensitive_data_patterns(state):
            risks.append("sensitive_data_detected")

        return risks

    @staticmethod
    def check_for_errors(state: UnifiedDiscoveryFlowState) -> bool:
        """Check if there are critical errors in the state"""
        errors = DecisionUtils.get_state_attribute(state, "errors", [])
        if errors:
            return len([e for e in errors if e.get("severity") == "critical"]) > 0
        return False

    @staticmethod
    def identify_critical_fields(state: UnifiedDiscoveryFlowState) -> List[str]:
        """
        Dynamically identify critical fields based on data analysis.
        This replaces hardcoded critical fields lists.
        """
        raw_data = DecisionUtils.get_state_attribute(state, "raw_data", [])

        if not raw_data:
            return []

        critical_fields = []
        field_names = (
            list(raw_data[0].keys())
            if raw_data and isinstance(raw_data[0], dict)
            else []
        )

        for field in field_names:
            field_lower = field.lower()

            # Identity fields are always critical
            if any(
                id_pattern in field_lower for id_pattern in ["id", "identifier", "key"]
            ):
                critical_fields.append(field)

            # Name fields are critical
            elif any(
                name_pattern in field_lower for name_pattern in ["name", "hostname"]
            ):
                critical_fields.append(field)

            # Network identifiers
            elif any(
                net_pattern in field_lower for net_pattern in ["ip", "mac", "address"]
            ):
                critical_fields.append(field)

            # Business context fields
            elif any(
                biz_pattern in field_lower
                for biz_pattern in ["owner", "department", "application"]
            ):
                critical_fields.append(field)

        return critical_fields

    @staticmethod
    def get_next_phase(current_phase: str, flow_type: str = "discovery") -> str:
        """Get the next phase in the flow with flow-type awareness"""
        # Try flow registry first for all flow types
        try:
            from app.services.flow_type_registry import FlowTypeRegistry

            flow_registry = FlowTypeRegistry()
            flow_config = flow_registry.get_flow_config(flow_type)
            next_phase = flow_config.get_next_phase(current_phase)
            if next_phase:
                return next_phase

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"⚠️ Failed to get next phase from flow registry for {flow_type}: {e}"
            )

        # Fallback to hardcoded phase orders for backward compatibility
        if flow_type == "discovery":
            discovery_order = [
                "data_import",
                "field_mapping",
                "data_cleansing",
                "asset_creation",
                "asset_inventory",
                "dependency_analysis",
                "tech_debt_assessment",
            ]

            try:
                current_index = discovery_order.index(current_phase)
                if current_index < len(discovery_order) - 1:
                    return discovery_order[current_index + 1]
            except ValueError:
                pass

        elif flow_type == "collection":
            collection_order = [
                "platform_detection",
                "automated_collection",
                "gap_analysis",
                "questionnaire_generation",
                "manual_collection",
                "synthesis",
            ]

            try:
                current_index = collection_order.index(current_phase)
                if current_index < len(collection_order) - 1:
                    return collection_order[current_index + 1]
            except ValueError:
                pass

        return "completed"

    @staticmethod
    def _has_sensitive_data_patterns(state: UnifiedDiscoveryFlowState) -> bool:
        """Check for sensitive data patterns"""
        raw_data = DecisionUtils.get_state_attribute(state, "raw_data", [])

        if not raw_data:
            return False

        sensitive_patterns = ["ssn", "social", "tax", "ein", "credit", "account"]

        if raw_data and isinstance(raw_data[0], dict):
            field_names = list(raw_data[0].keys())
            for field in field_names:
                if any(pattern in field.lower() for pattern in sensitive_patterns):
                    return True

        return False
