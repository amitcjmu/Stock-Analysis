"""
ColumnInspector - Inspects Asset SQLAlchemy columns for missing/empty data.

Performance: <10ms per asset (in-memory checks only, no database queries)
Part of Issue #980: Intelligent Multi-Layer Gap Detection System
"""

import logging
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.gap_detection.schemas import ColumnGapReport, DataRequirements
from .base import BaseInspector

logger = logging.getLogger(__name__)

# System columns to EXCLUDE from gap analysis (GPT-5 best practice)
SYSTEM_COLUMNS = {
    "id",
    "created_at",
    "updated_at",
    "deleted_at",
    "client_account_id",
    "engagement_id",
    "master_flow_id",
    "flow_id",  # Legacy field
}


class ColumnInspector(BaseInspector):
    """
    Inspects Asset SQLAlchemy columns for missing/empty data.

    Checks:
    - Required columns from DataRequirements
    - Empty strings (after strip)
    - Null/None values
    - Empty lists/dicts

    Performance: <10ms per asset (in-memory attribute checks only)

    GPT-5 Recommendations Applied:
    - #1: Tenant scoping parameters included (not used for in-memory checks)
    - #3: Async method signature
    - #8: Completeness score clamped to [0.0, 1.0]
    """

    async def inspect(
        self,
        asset: Any,
        application: Optional[Any],
        requirements: DataRequirements,
        client_account_id: str,
        engagement_id: str,
        db: Optional[AsyncSession] = None,
    ) -> ColumnGapReport:
        """
        Scan Asset columns for gaps based on requirements.

        This is an in-memory operation - no database queries.
        System columns (id, timestamps, tenant fields) are excluded.

        Args:
            asset: Asset SQLAlchemy model
            application: Not used by column inspector
            requirements: DataRequirements with required_columns list
            client_account_id: Tenant client account UUID (not used for in-memory checks)
            engagement_id: Engagement UUID (not used for in-memory checks)
            db: Not used by column inspector

        Returns:
            ColumnGapReport with:
            - missing_attributes: Columns that don't exist on asset
            - empty_attributes: Columns with empty strings/lists/dicts
            - null_attributes: Columns with None values
            - completeness_score: [0.0-1.0] ratio of found to required

        Raises:
            ValueError: If asset or requirements are None
        """
        if asset is None:
            raise ValueError("Asset cannot be None")
        if requirements is None:
            raise ValueError("DataRequirements cannot be None")

        missing = []
        empty = []
        null = []

        # Check each required column
        for col_name in requirements.required_columns:
            # Skip system columns
            if col_name in SYSTEM_COLUMNS:
                logger.debug(
                    f"Skipping system column '{col_name}' in gap analysis",
                    extra={
                        "asset_id": str(asset.id) if hasattr(asset, "id") else None,
                        "column": col_name,
                    },
                )
                continue

            # Check if attribute exists
            if not hasattr(asset, col_name):
                missing.append(col_name)
                continue

            value = getattr(asset, col_name, None)

            # Categorize the gap
            if value is None:
                null.append(col_name)
            elif isinstance(value, str) and not value.strip():
                empty.append(col_name)
            elif isinstance(value, list) and len(value) == 0:
                empty.append(col_name)
            elif isinstance(value, dict) and len(value) == 0:
                empty.append(col_name)
            # Value exists and is not empty - no gap

        # Combine all gaps
        all_gaps = missing + empty + null

        # Calculate completeness score (GPT-5 Rec #8: Clamp to [0.0, 1.0])
        # Exclude system columns from total count
        non_system_required = [
            col for col in requirements.required_columns if col not in SYSTEM_COLUMNS
        ]
        total_required = len(non_system_required)

        if total_required == 0:
            score = 1.0
        else:
            found = total_required - len(all_gaps)
            score = found / total_required

        # JSON safety: Clamp and sanitize (GPT-5 Rec #8)
        score = max(0.0, min(1.0, float(score)))

        logger.debug(
            "column_inspector_completed",
            extra={
                "asset_id": str(asset.id) if hasattr(asset, "id") else None,
                "asset_name": getattr(asset, "asset_name", None),
                "total_required": total_required,
                "gaps_found": len(all_gaps),
                "completeness_score": score,
                "missing_count": len(missing),
                "empty_count": len(empty),
                "null_count": len(null),
            },
        )

        return ColumnGapReport(
            missing_attributes=missing,
            empty_attributes=empty,
            null_attributes=null,
            completeness_score=score,
        )
