"""Context filtering utilities for gap analysis.

Provides tenant-configurable filtering of custom_attributes with:
- Per-tenant allowlist (cached in Redis)
- Global denylist for PII/secrets
- Payload size caps and string truncation
- Key canonicalization
"""

import json
import logging
import re
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Global defaults (fallback if tenant config not set)
DEFAULT_SAFE_KEYS = {
    "environment",
    "app_owner",
    "technology",
    "tech_stack",
    "framework",
    "language",
    "deployment_type",
    "region",
    "cost_center",
    "business_unit",
    "application_tier",
    "compliance_requirements",
    "backup_policy",
    "monitoring_enabled",
}

# Global denylist (PII and secrets) - applies to ALL tenants
DENYLIST_PATTERNS = [
    r"password",
    r"token",
    r"secret",
    r"api[_-]?key",
    r"credential",
    r"auth",
    r"private[_-]?key",
    r"ssn",
    r"social[_-]?security",
    r"credit[_-]?card",
    r"email",
    r"phone",
]

MAX_STRING_LENGTH = 500
MAX_PAYLOAD_SIZE = 8192  # 8KB total per asset


async def get_tenant_safe_keys(client_account_id: str, redis_client) -> set:
    """Get tenant-specific safe keys from Redis cache.

    Args:
        client_account_id: Tenant identifier
        redis_client: Redis client instance

    Returns:
        Set of allowed custom_attribute keys for this tenant
    """
    cache_key = f"tenant_safe_keys:{client_account_id}"

    # Try cache first
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            keys = set(json.loads(cached))
            logger.debug(f"Loaded {len(keys)} tenant safe keys from cache")
            return keys
    except Exception as e:
        logger.warning(f"Failed to load tenant safe keys from cache: {e}")

    # Fall back to default
    logger.debug(f"Using default safe keys ({len(DEFAULT_SAFE_KEYS)} keys)")
    return DEFAULT_SAFE_KEYS


def is_denied_key(key: str) -> bool:
    """Check if key matches global denylist (PII/secrets).

    Args:
        key: Key name to check (should be lowercased)

    Returns:
        True if key matches denylist pattern
    """
    key_lower = key.lower()
    return any(re.search(pattern, key_lower) for pattern in DENYLIST_PATTERNS)


def filter_custom_attributes(
    custom_attrs: Dict[str, Any],
    allowed_keys: set,
    max_payload_size: int = MAX_PAYLOAD_SIZE,
) -> Dict[str, Any]:
    """Filter custom_attributes with allowlist, denylist, and size caps.

    Args:
        custom_attrs: Raw custom_attributes from asset
        allowed_keys: Tenant-specific allowed keys (from get_tenant_safe_keys)
        max_payload_size: Maximum total payload size in bytes

    Returns:
        Filtered dict with:
        - Only allowlisted keys
        - No denylisted keys (PII/secrets)
        - Truncated strings (max 500 chars)
        - Bounded total size (max 8KB)
        - Canonicalized keys (lowercase, trimmed)
    """
    if not custom_attrs:
        return {}

    filtered = {}
    total_size = 0
    keys_dropped = 0

    for key, value in custom_attrs.items():
        # Canonicalize key (lowercase, trim)
        key_canonical = key.strip().lower()

        # Check denylist first (PII/secrets)
        if is_denied_key(key_canonical):
            logger.debug(f"Redacted denied key: {key}")
            keys_dropped += 1
            continue

        # Check allowlist
        if key_canonical not in allowed_keys:
            logger.debug(f"Skipped non-allowlisted key: {key}")
            keys_dropped += 1
            continue

        # Skip null/empty
        if value is None or value == "":
            continue

        # Cap string length
        if isinstance(value, str):
            value = value.strip()
            if len(value) > MAX_STRING_LENGTH:
                value = value[:MAX_STRING_LENGTH] + "..."
                logger.debug(f"Truncated {key} to {MAX_STRING_LENGTH} chars")

        # Check payload size
        value_size = len(json.dumps({key_canonical: value}))
        if total_size + value_size > max_payload_size:
            logger.warning(
                f"Payload size limit reached ({max_payload_size} bytes), "
                f"dropped {key} and {len(custom_attrs) - len(filtered) - keys_dropped} remaining fields"
            )
            break

        filtered[key_canonical] = value
        total_size += value_size

    logger.debug(
        f"Filtered custom_attributes: kept {len(filtered)}, dropped {keys_dropped}, "
        f"total size: {total_size} bytes"
    )

    return filtered


def build_compact_asset_context(
    asset: Any, tenant_safe_keys: set, redis_client=None
) -> Dict[str, Any]:
    """Build compact asset context with only relevant fields.

    Args:
        asset: Asset model instance
        tenant_safe_keys: Allowed custom_attribute keys for this tenant
        redis_client: Optional Redis client (not used currently)

    Returns:
        Compact dict with filtered fields and bounded size
    """
    context = {
        "id": str(asset.id),
        "name": asset.name,
        "asset_type": asset.asset_type,
    }

    # Include only non-null standard fields
    optional_fields = [
        "description",
        "environment",
        "location",
        "discovery_source",
    ]

    for field in optional_fields:
        value = getattr(asset, field, None)
        if value is not None and value != "":
            # Truncate long descriptions
            if (
                field == "description"
                and isinstance(value, str)
                and len(value) > MAX_STRING_LENGTH
            ):
                value = value[:MAX_STRING_LENGTH] + "..."
            context[field] = value

    # Filter custom_attributes
    if asset.custom_attributes:
        filtered_custom = filter_custom_attributes(
            asset.custom_attributes, tenant_safe_keys
        )
        if filtered_custom:
            context["custom_attributes"] = filtered_custom

    return context
