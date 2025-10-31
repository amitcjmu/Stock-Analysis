"""
EOL (End-of-Life) technology assessment intelligent options.
Handles EOL status-aware option ordering.
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def get_eol_technology_assessment_options(
    asset_context: Dict,
) -> Optional[Tuple[str, List[Dict[str, str]]]]:
    """Provide intelligent EOL assessment options based on detected EOL status.

    Args:
        asset_context: Dict with asset data including 'eol_technology', 'operating_system', etc.

    Returns:
        Tuple of (field_type, options) or None if not applicable
    """
    eol_technology = asset_context.get("eol_technology", "")
    eol_status = (eol_technology or "").upper()  # Handle None gracefully

    # EOL expired → Critical EOL assessment options first
    if "EOL_EXPIRED" in eol_status or "UNSUPPORTED" in eol_status:
        options = [
            {
                "value": "eol_expired_critical",
                "label": "EOL Expired (Critical) - Vendor support ended, security risk",
            },
            {
                "value": "eol_expired_moderate",
                "label": "EOL Expired (Moderate) - Extended support available",
            },
            {
                "value": "eol_soon",
                "label": "EOL Soon (6-12 months) - Planning required",
            },
            {
                "value": "deprecated",
                "label": "Deprecated - Replacement recommended",
            },
            {"value": "current", "label": "Current - Fully supported version"},
            {"value": "not_assessed", "label": "Not Assessed - EOL analysis needed"},
        ]
        logger.info(
            f"Providing EOL-expired assessment options for eol_technology: {eol_status}"
        )
        return "select", options

    # EOL soon → Warning options first
    elif "EOL_SOON" in eol_status or "DEPRECATED" in eol_status:
        options = [
            {
                "value": "eol_soon",
                "label": "EOL Soon (6-12 months) - Planning required",
            },
            {
                "value": "deprecated",
                "label": "Deprecated - Replacement recommended",
            },
            {
                "value": "eol_expired_moderate",
                "label": "EOL Expired (Moderate) - Extended support available",
            },
            {
                "value": "current",
                "label": "Current - Fully supported version",
            },
            {
                "value": "eol_expired_critical",
                "label": "EOL Expired (Critical) - Vendor support ended, security risk",
            },
            {"value": "not_assessed", "label": "Not Assessed - EOL analysis needed"},
        ]
        logger.info(
            f"Providing EOL-soon assessment options for eol_technology: {eol_status}"
        )
        return "select", options

    # Current/Supported → "Current" option first
    elif "CURRENT" in eol_status or "SUPPORTED" in eol_status:
        options = [
            {"value": "current", "label": "Current - Fully supported version"},
            {
                "value": "eol_soon",
                "label": "EOL Soon (6-12 months) - Planning required",
            },
            {
                "value": "deprecated",
                "label": "Deprecated - Replacement recommended",
            },
            {
                "value": "eol_expired_moderate",
                "label": "EOL Expired (Moderate) - Extended support available",
            },
            {
                "value": "eol_expired_critical",
                "label": "EOL Expired (Critical) - Vendor support ended, security risk",
            },
            {"value": "not_assessed", "label": "Not Assessed - EOL analysis needed"},
        ]
        logger.info(
            f"Providing current-version EOL assessment options for eol_technology: {eol_status}"
        )
        return "select", options

    # If eol_technology field doesn't match patterns, return None
    return None
