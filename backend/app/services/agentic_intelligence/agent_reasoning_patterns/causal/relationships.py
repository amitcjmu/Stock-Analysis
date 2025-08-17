"""
Causal Relationships Core Module

This module contains the fundamental CausalRelationship class that represents
cause-and-effect relationships between conditions and outcomes.
"""

import logging
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)


class CausalRelationship:
    """
    Represents a causal relationship between conditions and outcomes.
    """

    def __init__(
        self,
        cause_conditions: Dict[str, Any],
        effect_outcomes: Dict[str, Any],
        relationship_strength: float,
        confidence_level: float,
        description: str,
    ):
        self.cause_conditions = cause_conditions
        self.effect_outcomes = effect_outcomes
        self.relationship_strength = relationship_strength  # 0.0 - 1.0
        self.confidence_level = confidence_level  # 0.0 - 1.0
        self.description = description

    def evaluate_causality(self, asset_data: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Evaluate if causal conditions are met and predict effect strength.

        Args:
            asset_data: Asset data to evaluate

        Returns:
            Tuple of (conditions_met, predicted_effect_strength)
        """
        conditions_met = self._check_cause_conditions(asset_data)
        if conditions_met:
            return True, self.relationship_strength
        return False, 0.0

    def _check_cause_conditions(self, asset_data: Dict[str, Any]) -> bool:
        """Check if all causal conditions are present in the asset data"""
        for condition_field, condition_value in self.cause_conditions.items():
            asset_value = asset_data.get(condition_field)
            if not self._condition_matches(asset_value, condition_value):
                return False
        return True

    def _condition_matches(self, asset_value: Any, condition_value: Any) -> bool:
        """Check if a specific condition is met"""
        if asset_value is None:
            return False

        if isinstance(condition_value, dict):
            operator = condition_value.get("operator")
            value = condition_value.get("value")

            if operator == ">=":
                return isinstance(asset_value, (int, float)) and asset_value >= value
            elif operator == "contains":
                return (
                    isinstance(asset_value, str)
                    and value.lower() in asset_value.lower()
                )
            elif operator == "in":
                return asset_value in value if isinstance(value, list) else False
        elif isinstance(condition_value, list):
            return any(
                str(item).lower() in str(asset_value).lower()
                for item in condition_value
            )
        else:
            return str(condition_value).lower() == str(asset_value).lower()
