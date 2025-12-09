"""
Utility functions for asset processing.
Handles context management, asset type determination, and helper functions.
"""

import logging
from typing import Any, Dict

from app.core.context import RequestContext, get_current_context

logger = logging.getLogger(__name__)


def get_safe_context() -> RequestContext:
    """Get context safely with fallback values"""
    context = get_current_context()
    if context:
        return context

    logger.warning("⚠️ No context available, using fallback values")
    return RequestContext(
        client_account_id="11111111-1111-1111-1111-111111111111",
        engagement_id="22222222-2222-2222-2222-222222222222",
        user_id="347d1ecd-04f6-4e3a-86ca-d35703512301",
    )


def _extract_raw_type(raw_data: Dict[str, Any]) -> str:
    """Extract raw type from data, checking CITYPE variations first."""
    citype_variations = ["CITYPE", "citype", "CI_TYPE", "ci_type", "CIType"]

    # Check for CITYPE field variations
    for field_name in citype_variations:
        if field_name in raw_data and raw_data[field_name]:
            return str(raw_data[field_name]).lower()

    # If no CITYPE found, check other type fields
    return (
        raw_data.get("asset_type")
        or raw_data.get("type")
        or raw_data.get("Type")
        or raw_data.get("TYPE")
        or ""
    ).lower()


def _classify_by_type_patterns(raw_type: str) -> str:
    """Classify asset type based on type string patterns."""
    # Enhanced mapping with exact CITYPE matches first
    if "application" in raw_type:
        return "application"
    elif "server" in raw_type:
        return "server"
    elif "database" in raw_type:
        return "database"
    elif any(term in raw_type for term in ["network", "switch", "router", "firewall"]):
        return "network_device"
    elif any(term in raw_type for term in ["storage", "san", "nas", "disk"]):
        return "storage_device"
    # Pattern-based fallback for unclear types
    elif any(term in raw_type for term in ["app", "software", "portal", "service"]):
        return "application"
    elif any(term in raw_type for term in ["srv", "vm", "virtual", "host"]):
        return "server"
    elif any(term in raw_type for term in ["db", "sql", "oracle", "mysql", "postgres"]):
        return "database"
    return ""  # No match found


def _classify_by_ciid(raw_data: Dict[str, Any]) -> str:
    """Classify asset type based on CIID pattern."""
    ciid = raw_data.get("CIID", raw_data.get("ciid", raw_data.get("CI_ID", "")))
    if ciid:
        ciid_lower = str(ciid).lower()
        if ciid_lower.startswith("app"):
            return "application"
        elif ciid_lower.startswith("srv"):
            return "server"
        elif ciid_lower.startswith("db"):
            return "database"
    return ""


def determine_asset_type_agentic(
    raw_data: Dict[str, Any], asset_classification: Dict[str, Any]
) -> str:
    """Determine asset type using agentic intelligence with enhanced CITYPE field reading."""

    # First, use agentic classification if available
    if asset_classification and asset_classification.get("asset_type"):
        agentic_type = asset_classification["asset_type"].lower()
        if agentic_type in [
            "server",
            "application",
            "database",
            "network_device",
            "storage_device",
        ]:
            return agentic_type

    # Extract raw type from data
    raw_type = _extract_raw_type(raw_data)

    # Try to classify by type patterns
    if raw_type:
        asset_type = _classify_by_type_patterns(raw_type)
        if asset_type:
            return asset_type

    # Check CIID patterns as final fallback
    asset_type = _classify_by_ciid(raw_data)
    if asset_type:
        return asset_type

    return "server"  # Default fallback
