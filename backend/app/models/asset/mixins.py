"""
Asset model mixins for computed properties and business logic.

This module contains mixins that extend the Asset model with
computed properties and business logic methods.
"""

from typing import TYPE_CHECKING

from .base import (
    COMPLEXITY_PENALTIES,
    MAX_SCORE,
    MIN_SCORE,
)
from .enums import AssetStatus, AssetType

if TYPE_CHECKING:
    pass


class AssetPropertiesMixin:
    """Mixin providing computed properties for Asset model."""

    @property
    def is_migrated(self) -> bool:
        """Check if asset has been successfully migrated."""
        return self.migration_status == AssetStatus.MIGRATED.value

    @property
    def has_dependencies(self) -> bool:
        """Check if asset has dependencies."""
        return bool(self.dependencies and len(self.dependencies) > 0)

    @property
    def is_deleted(self) -> bool:
        """Check if asset has been soft deleted (Issue #912)."""
        return self.deleted_at is not None

    @property
    def is_active(self) -> bool:
        """Check if asset is active (not soft deleted) (Issue #912)."""
        return self.deleted_at is None


class AssetBusinessLogicMixin:
    """Mixin providing business logic methods for Asset model."""

    def get_migration_readiness_score(self) -> float:
        """Calculate migration readiness score based on various factors."""
        score = MAX_SCORE

        # Reduce score based on complexity
        if (
            self.migration_complexity
            and self.migration_complexity.lower() in COMPLEXITY_PENALTIES
        ):
            score -= COMPLEXITY_PENALTIES[self.migration_complexity.lower()]

        # Reduce score based on dependencies
        if self.has_dependencies:
            score -= 10

        # Reduce score if no 6R strategy assigned
        if not self.six_r_strategy:
            score -= 20

        # Reduce score for unknown asset types
        if self.asset_type == AssetType.OTHER.value:
            score -= 25

        return max(MIN_SCORE, min(MAX_SCORE, score))
