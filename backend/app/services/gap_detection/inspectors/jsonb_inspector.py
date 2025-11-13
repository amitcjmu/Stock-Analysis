"""
JSONBInspector - Inspects Asset JSONB fields for missing/empty keys.

Performance: <10ms per asset (in-memory traversal, no database queries)
Part of Issue #980: Intelligent Multi-Layer Gap Detection System
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.gap_detection.schemas import DataRequirements, JSONBGapReport

from .base import BaseInspector

logger = logging.getLogger(__name__)


class JSONBInspector(BaseInspector):
    """
    Inspects Asset JSONB fields for missing/empty keys.

    JSONB Fields Checked:
    - custom_attributes: Dict[str, Any] - Custom metadata
    - technical_details: Dict[str, Any] - Technical specifications
    - metadata: Dict[str, Any] - Additional metadata

    Supports nested key checking with dot notation (e.g., "deployment.strategy").

    Performance: <10ms per asset (in-memory traversal only)

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
    ) -> JSONBGapReport:
        """
        Traverse JSONB fields for missing/empty keys.

        Checks requirements.required_jsonb_keys which is a dict like:
        {
            "custom_attributes": ["environment", "vm_type"],
            "technical_details": ["api_endpoints", "dependencies"],
            "metadata": ["documentation_url"]
        }

        Args:
            asset: Asset SQLAlchemy model
            application: Not used by JSONB inspector
            requirements: DataRequirements with required_jsonb_keys dict
            client_account_id: Tenant client account UUID (not used for in-memory checks)
            engagement_id: Engagement UUID (not used for in-memory checks)
            db: Not used by JSONB inspector

        Returns:
            JSONBGapReport with missing keys, empty values, and completeness score

        Raises:
            ValueError: If asset or requirements are None
        """
        if asset is None:
            raise ValueError("Asset cannot be None")
        if requirements is None:
            raise ValueError("DataRequirements cannot be None")

        missing_keys: Dict[str, List[str]] = {}
        empty_values: Dict[str, List[str]] = {}
        total_expected = 0
        total_found = 0

        # Check each JSONB field defined in requirements
        for jsonb_field, expected_keys in requirements.required_jsonb_keys.items():
            # Get JSONB field from asset
            jsonb_data = getattr(asset, jsonb_field, None)

            if jsonb_data is None:
                # Entire JSONB field missing
                missing_keys[jsonb_field] = expected_keys
                total_expected += len(expected_keys)
                logger.debug(
                    f"JSONB field '{jsonb_field}' is missing entirely",
                    extra={
                        "asset_id": str(asset.id) if hasattr(asset, "id") else None,
                        "jsonb_field": jsonb_field,
                        "expected_keys": expected_keys,
                    },
                )
                continue

            if not isinstance(jsonb_data, dict):
                logger.warning(
                    f"JSONB field '{jsonb_field}' is not a dict: {type(jsonb_data)}",
                    extra={
                        "asset_id": str(asset.id) if hasattr(asset, "id") else None,
                        "jsonb_field": jsonb_field,
                        "actual_type": str(type(jsonb_data)),
                    },
                )
                missing_keys[jsonb_field] = expected_keys
                total_expected += len(expected_keys)
                continue

            # Check each expected key
            field_missing = []
            field_empty = []

            for key in expected_keys:
                total_expected += 1

                # Support nested keys with dot notation (e.g., "deployment.strategy")
                value = self._get_nested_value(jsonb_data, key)

                if value is None:
                    field_missing.append(key)
                elif self._is_empty(value):
                    field_empty.append(key)
                else:
                    total_found += 1

            if field_missing:
                missing_keys[jsonb_field] = field_missing
            if field_empty:
                empty_values[jsonb_field] = field_empty

        # Calculate completeness score (GPT-5 Rec #8: Clamp to [0.0, 1.0])
        if total_expected == 0:
            score = 1.0
        else:
            score = total_found / total_expected

        # JSON safety: Clamp and sanitize (GPT-5 Rec #8)
        score = max(0.0, min(1.0, float(score)))

        logger.debug(
            "jsonb_inspector_completed",
            extra={
                "asset_id": str(asset.id) if hasattr(asset, "id") else None,
                "asset_name": getattr(asset, "asset_name", None),
                "total_expected": total_expected,
                "total_found": total_found,
                "completeness_score": score,
                "missing_keys_count": sum(len(v) for v in missing_keys.values()),
                "empty_values_count": sum(len(v) for v in empty_values.values()),
            },
        )

        return JSONBGapReport(
            missing_keys=missing_keys,
            empty_values=empty_values,
            completeness_score=score,
        )

    def _get_nested_value(self, data: dict, key_path: str) -> Any:
        """
        Get value from nested dict using dot notation.

        Example:
            data = {"deployment": {"strategy": "rolling"}}
            _get_nested_value(data, "deployment.strategy") -> "rolling"

        Args:
            data: Dictionary to traverse
            key_path: Dot-separated key path (e.g., "deployment.strategy")

        Returns:
            Value at key path, or None if not found
        """
        keys = key_path.split(".")
        value = data

        for key in keys:
            if not isinstance(value, dict):
                return None
            value = value.get(key)
            if value is None:
                return None

        return value

    def _is_empty(self, value: Any) -> bool:
        """
        Check if value is considered empty.

        Empty conditions:
        - String with only whitespace
        - Empty list
        - Empty dict

        Args:
            value: Value to check

        Returns:
            True if value is empty, False otherwise
        """
        if isinstance(value, str):
            return not value.strip()
        elif isinstance(value, (list, dict)):
            return len(value) == 0
        return False
