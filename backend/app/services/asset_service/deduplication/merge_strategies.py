"""
Asset Merge Strategies

Implements enrich and overwrite strategies for updating existing assets
with field allowlist validation and security controls.

CC: Asset merge strategies with field validation
"""

import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime

from app.models.asset import Asset
from ..helpers import convert_single_field_value
from .constants import DEFAULT_ALLOWED_MERGE_FIELDS, NEVER_MERGE_FIELDS

logger = logging.getLogger(__name__)


async def enrich_asset(
    service_instance,
    existing: Asset,
    new_data: Dict[str, Any],
    allowed_merge_fields: Optional[Set[str]] = None,
) -> Asset:
    """
    Non-destructive enrichment: add new fields, keep existing values.

    Field allowlist validation:
    - Only merge fields in allowlist that don't exist in existing asset
    - Skip fields in NEVER_MERGE_FIELDS
    - Log warnings for attempted protected field merges

    Args:
        service_instance: AssetService instance
        existing: Existing asset to enrich
        new_data: New data to merge
        allowed_merge_fields: Set of fields allowed for merge

    Returns:
        Updated asset instance
    """
    allowlist = allowed_merge_fields or DEFAULT_ALLOWED_MERGE_FIELDS

    for field, value in new_data.items():
        # Skip if field not in allowlist
        if field not in allowlist:
            continue

        # Skip if field in never-merge list
        if field in NEVER_MERGE_FIELDS:
            logger.warning(f"⚠️ Attempted to merge protected field '{field}' - skipping")
            continue

        # Only update if existing value is None
        # CC FIX: Use explicit 'is None' check to prevent overwriting existing falsy values
        # This ensures enrichment only fills missing (None) values, not overwrites 0/False/""
        if value is not None and getattr(existing, field, None) is None:
            # CC FIX: Convert value to proper type (fixes cpu_cores='8' string->int error)
            typed_value = convert_single_field_value(field, value)
            setattr(existing, field, typed_value)

    # Special handling for custom_attributes (merge dicts)
    if "custom_attributes" in new_data and "custom_attributes" in allowlist:
        existing_attrs = existing.custom_attributes or {}
        new_attrs = new_data["custom_attributes"]
        existing.custom_attributes = {**existing_attrs, **new_attrs}

    existing.updated_at = datetime.utcnow()
    await service_instance.db.flush()
    return existing


async def overwrite_asset(
    service_instance,
    existing: Asset,
    new_data: Dict[str, Any],
    allowed_merge_fields: Optional[Set[str]] = None,
) -> Asset:
    """
    Explicit overwrite: replace allowed fields with new values.

    Implements "replace_with_new" as UPDATE (not delete+create):
    - Preserves FK relationships and audit history
    - Only updates fields in allowlist
    - Respects NEVER_MERGE_FIELDS protection

    Args:
        service_instance: AssetService instance
        existing: Existing asset to overwrite
        new_data: New data to replace with
        allowed_merge_fields: Set of fields allowed for merge

    Returns:
        Updated asset instance
    """
    allowlist = allowed_merge_fields or DEFAULT_ALLOWED_MERGE_FIELDS

    for field, value in new_data.items():
        # Skip if field not in allowlist or in never-merge list
        if field not in allowlist or field in NEVER_MERGE_FIELDS:
            continue

        # Overwrite existing value with new value
        if value is not None:
            # CC FIX: Convert value to proper type (fixes cpu_cores='8' string->int error)
            typed_value = convert_single_field_value(field, value)
            setattr(existing, field, typed_value)

    existing.updated_at = datetime.utcnow()
    await service_instance.db.flush()
    return existing
