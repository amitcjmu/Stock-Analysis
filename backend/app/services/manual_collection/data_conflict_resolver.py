"""
Data Conflict Resolver

Handles detection and resolution of conflicts between data sources.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from .data_integration_models import (
    DataConflict,
    DataPoint,
    DataSource,
    ConflictResolutionStrategy,
)

logger = logging.getLogger(__name__)


class DataConflictResolver:
    """Resolves conflicts between data points from different sources."""

    def __init__(self):
        """Initialize conflict resolver."""
        self.source_priority = {
            DataSource.MANUAL_COLLECTION: 5,
            DataSource.USER_INPUT: 4,
            DataSource.BULK_UPLOAD: 3,
            DataSource.API_INTEGRATION: 2,
            DataSource.AUTOMATED_DISCOVERY: 1,
        }

    async def detect_conflicts(
        self, grouped_data: Dict[str, List[DataPoint]]
    ) -> List[DataConflict]:
        """Detect conflicts in grouped data points"""
        conflicts = []

        for attribute_name, data_points in grouped_data.items():
            if len(data_points) > 1:
                # Check for value differences
                unique_values = set()
                for dp in data_points:
                    if dp.value is not None:
                        unique_values.add(str(dp.value))

                if len(unique_values) > 1:
                    # Conflict detected
                    strategy = self._determine_resolution_strategy(
                        attribute_name, data_points
                    )

                    conflict = DataConflict(
                        attribute_name=attribute_name,
                        conflicting_values=data_points,
                        resolution_strategy=strategy,
                        requires_review=self._requires_user_review(
                            data_points, strategy
                        ),
                    )
                    conflicts.append(conflict)

        return conflicts

    async def resolve_conflicts(
        self, conflicts: List[DataConflict]
    ) -> List[DataConflict]:
        """Resolve conflicts based on strategies"""
        resolved_conflicts = []

        for conflict in conflicts:
            if conflict.requires_review:
                # Skip conflicts that require user review
                resolved_conflicts.append(conflict)
                continue

            resolved_value = None
            strategy = conflict.resolution_strategy

            if strategy == ConflictResolutionStrategy.PREFER_MANUAL:
                resolved_value = self._prefer_manual_data(conflict.conflicting_values)
            elif strategy == ConflictResolutionStrategy.PREFER_AUTOMATED:
                resolved_value = self._prefer_automated_data(
                    conflict.conflicting_values
                )
            elif strategy == ConflictResolutionStrategy.PREFER_NEWEST:
                resolved_value = self._prefer_newest_data(conflict.conflicting_values)
            elif strategy == ConflictResolutionStrategy.PREFER_HIGHEST_CONFIDENCE:
                resolved_value = self._prefer_highest_confidence(
                    conflict.conflicting_values
                )

            conflict.resolved_value = resolved_value
            resolved_conflicts.append(conflict)

        return resolved_conflicts

    def _determine_resolution_strategy(
        self, attribute_name: str, data_points: List[DataPoint]
    ) -> ConflictResolutionStrategy:
        """Determine the best resolution strategy for a conflict"""
        # Critical attributes require user review
        critical_attributes = [
            "name",
            "ip_address",
            "hostname",
            "environment",
            "application_name",
            "database_name",
            "service_name",
        ]

        if any(attr in attribute_name.lower() for attr in critical_attributes):
            return ConflictResolutionStrategy.REQUIRE_USER_REVIEW

        # Check confidence levels
        avg_confidence = sum(dp.confidence_score for dp in data_points) / len(
            data_points
        )
        if avg_confidence < 0.6:
            return ConflictResolutionStrategy.REQUIRE_USER_REVIEW

        # Check for manual data presence
        has_manual = any(
            dp.source in [DataSource.MANUAL_COLLECTION, DataSource.USER_INPUT]
            for dp in data_points
        )

        if has_manual:
            return ConflictResolutionStrategy.PREFER_MANUAL

        # Default to highest confidence
        return ConflictResolutionStrategy.PREFER_HIGHEST_CONFIDENCE

    def _requires_user_review(
        self, data_points: List[DataPoint], strategy: ConflictResolutionStrategy
    ) -> bool:
        """Determine if conflict requires user review"""
        if strategy == ConflictResolutionStrategy.REQUIRE_USER_REVIEW:
            return True

        # Check for significantly different confidence scores
        confidence_scores = [dp.confidence_score for dp in data_points]
        if max(confidence_scores) - min(confidence_scores) > 0.4:
            return True

        # Check for value type mismatches
        value_types = set(
            type(dp.value).__name__ for dp in data_points if dp.value is not None
        )
        if len(value_types) > 1:
            return True

        return False

    def _prefer_manual_data(self, data_points: List[DataPoint]) -> Optional[DataPoint]:
        """Prefer manual collection data"""
        manual_points = [
            dp
            for dp in data_points
            if dp.source in [DataSource.MANUAL_COLLECTION, DataSource.USER_INPUT]
        ]

        if manual_points:
            # Return the one with highest confidence
            return max(manual_points, key=lambda dp: dp.confidence_score)

        # Fallback to highest confidence overall
        return max(data_points, key=lambda dp: dp.confidence_score)

    def _prefer_automated_data(
        self, data_points: List[DataPoint]
    ) -> Optional[DataPoint]:
        """Prefer automated discovery data"""
        automated_points = [
            dp
            for dp in data_points
            if dp.source in [DataSource.AUTOMATED_DISCOVERY, DataSource.API_INTEGRATION]
        ]

        if automated_points:
            return max(automated_points, key=lambda dp: dp.confidence_score)

        return max(data_points, key=lambda dp: dp.confidence_score)

    def _prefer_newest_data(self, data_points: List[DataPoint]) -> Optional[DataPoint]:
        """Prefer most recent data"""
        return max(data_points, key=lambda dp: dp.timestamp)

    def _prefer_highest_confidence(
        self, data_points: List[DataPoint]
    ) -> Optional[DataPoint]:
        """Prefer data with highest confidence score"""
        return max(data_points, key=lambda dp: dp.confidence_score)

    def calculate_data_point_confidence(self, data_point: DataPoint) -> float:
        """Calculate confidence score for a data point"""
        base_confidence = 0.5

        # Source-based confidence
        source_multiplier = {
            DataSource.MANUAL_COLLECTION: 1.0,
            DataSource.USER_INPUT: 0.95,
            DataSource.BULK_UPLOAD: 0.85,
            DataSource.API_INTEGRATION: 0.8,
            DataSource.AUTOMATED_DISCOVERY: 0.7,
        }

        confidence = base_confidence * source_multiplier.get(data_point.source, 0.5)

        # Collection method confidence
        if "validated" in data_point.collection_method.lower():
            confidence *= 1.1
        elif "inferred" in data_point.collection_method.lower():
            confidence *= 0.8

        # Validation status
        if data_point.validation_status == "passed":
            confidence *= 1.1
        elif data_point.validation_status == "failed":
            confidence *= 0.6

        # Recency factor (prefer newer data)
        age_hours = (datetime.utcnow() - data_point.timestamp).total_seconds() / 3600
        if age_hours < 24:
            confidence *= 1.05
        elif age_hours > 168:  # > 1 week
            confidence *= 0.9

        return min(confidence, 1.0)
