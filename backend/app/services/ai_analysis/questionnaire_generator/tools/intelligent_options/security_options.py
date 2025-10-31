"""
Security-related intelligent options for questionnaire generation.
Handles security vulnerabilities and compliance requirements.
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def get_security_vulnerabilities_options(
    asset_context: Dict,
) -> Optional[Tuple[str, List[Dict[str, str]]]]:
    """Provide intelligent vulnerability options based on EOL technology assessment.

    Args:
        asset_context: Dict with asset data including 'eol_technology', etc.

    Returns:
        Tuple of (field_type, options) or None if not applicable
    """
    eol_technology = asset_context.get("eol_technology", "")
    eol_status = (eol_technology or "").upper()  # Handle None gracefully

    # EOL expired → High vulnerability risk
    if "EOL_EXPIRED" in eol_status or "UNSUPPORTED" in eol_status:
        options = [
            {
                "value": "high_severity",
                "label": "High Severity - Critical vulnerabilities exist",
            },
            {
                "value": "medium_severity",
                "label": "Medium Severity - Moderate risk, should be addressed",
            },
            {"value": "not_assessed", "label": "Not Assessed - Security scan needed"},
            {"value": "low_severity", "label": "Low Severity - Minor issues, low risk"},
            {
                "value": "none_known",
                "label": "None Known - No vulnerabilities identified",
            },
        ]
        logger.info(
            f"Providing high-risk vulnerability options for EOL status: {eol_status}"
        )
        return "select", options

    # EOL soon → Medium vulnerability risk
    elif "EOL_SOON" in eol_status or "DEPRECATED" in eol_status:
        options = [
            {
                "value": "medium_severity",
                "label": "Medium Severity - Moderate risk, should be addressed",
            },
            {"value": "not_assessed", "label": "Not Assessed - Security scan needed"},
            {"value": "low_severity", "label": "Low Severity - Minor issues, low risk"},
            {
                "value": "high_severity",
                "label": "High Severity - Critical vulnerabilities exist",
            },
            {
                "value": "none_known",
                "label": "None Known - No vulnerabilities identified",
            },
        ]
        logger.info(
            f"Providing medium-risk vulnerability options for EOL status: {eol_status}"
        )
        return "select", options

    # Current/Supported → Lower vulnerability risk
    elif "CURRENT" in eol_status or "SUPPORTED" in eol_status:
        options = [
            {
                "value": "none_known",
                "label": "None Known - No vulnerabilities identified",
            },
            {"value": "low_severity", "label": "Low Severity - Minor issues, low risk"},
            {"value": "not_assessed", "label": "Not Assessed - Security scan needed"},
            {
                "value": "medium_severity",
                "label": "Medium Severity - Moderate risk, should be addressed",
            },
            {
                "value": "high_severity",
                "label": "High Severity - Critical vulnerabilities exist",
            },
        ]
        logger.info(
            f"Providing low-risk vulnerability options for EOL status: {eol_status}"
        )
        return "select", options

    # If eol_technology field exists but doesn't match patterns, return None
    return None


def get_security_compliance_requirements_options(
    asset_context: Dict,
) -> Optional[Tuple[str, List[Dict[str, str]]]]:
    """Provide intelligent compliance requirement options based on business criticality.

    Args:
        asset_context: Dict with asset data including 'business_criticality', etc.

    Returns:
        Tuple of (field_type, options) or None if not applicable
    """
    business_criticality_raw = asset_context.get("business_criticality", "")
    # Normalize: strip whitespace, convert to lowercase
    business_criticality = (business_criticality_raw or "").strip().lower()

    # Mission critical → Strict compliance requirements first
    # Use exact matching with normalized enum values to avoid substring matching bugs
    if business_criticality in [
        "mission_critical",
        "mission-critical",
        "critical",
        "mission",
    ]:
        options = [
            {"value": "pci_dss", "label": "PCI-DSS - Payment Card Industry"},
            {"value": "hipaa", "label": "HIPAA - Healthcare Data Protection"},
            {"value": "sox", "label": "SOX - Sarbanes-Oxley Financial Compliance"},
            {"value": "gdpr", "label": "GDPR - EU Data Protection"},
            {"value": "iso_27001", "label": "ISO 27001 - Information Security"},
            {"value": "fedramp", "label": "FedRAMP - Federal Security Authorization"},
            {"value": "fisma", "label": "FISMA - Federal Information Security"},
            {"value": "none", "label": "None - No specific compliance requirements"},
        ]
        logger.info(
            f"Providing mission-critical compliance options (strict compliance first) "
            f"for business_criticality: {business_criticality}"
        )
        return "multi_select", options

    # Business critical → Balanced compliance options
    elif business_criticality in [
        "business_critical",
        "business-critical",
        "business",
        "high",
    ]:
        options = [
            {"value": "gdpr", "label": "GDPR - EU Data Protection"},
            {"value": "pci_dss", "label": "PCI-DSS - Payment Card Industry"},
            {"value": "hipaa", "label": "HIPAA - Healthcare Data Protection"},
            {"value": "iso_27001", "label": "ISO 27001 - Information Security"},
            {"value": "sox", "label": "SOX - Sarbanes-Oxley Financial Compliance"},
            {"value": "none", "label": "None - No specific compliance requirements"},
        ]
        logger.info(
            f"Providing business-critical compliance options "
            f"for business_criticality: {business_criticality}"
        )
        return "multi_select", options

    # Low priority/Development → "None" option first
    elif business_criticality in [
        "low",
        "low_priority",
        "development",
        "testing",
        "dev",
        "test",
        "qa",
    ]:
        options = [
            {"value": "none", "label": "None - No specific compliance requirements"},
            {"value": "iso_27001", "label": "ISO 27001 - Information Security"},
            {"value": "gdpr", "label": "GDPR - EU Data Protection"},
            {"value": "pci_dss", "label": "PCI-DSS - Payment Card Industry"},
            {"value": "hipaa", "label": "HIPAA - Healthcare Data Protection"},
            {"value": "sox", "label": "SOX - Sarbanes-Oxley Financial Compliance"},
        ]
        logger.info(
            f"Providing low-priority compliance options (None first) "
            f"for business_criticality: {business_criticality}"
        )
        return "multi_select", options

    # Default ordering (GDPR first as most common)
    options = [
        {"value": "gdpr", "label": "GDPR - EU Data Protection"},
        {"value": "pci_dss", "label": "PCI-DSS - Payment Card Industry"},
        {"value": "hipaa", "label": "HIPAA - Healthcare Data Protection"},
        {"value": "iso_27001", "label": "ISO 27001 - Information Security"},
        {"value": "sox", "label": "SOX - Sarbanes-Oxley Financial Compliance"},
        {"value": "fedramp", "label": "FedRAMP - Federal Security Authorization"},
        {"value": "none", "label": "None - No specific compliance requirements"},
    ]
    logger.info(
        f"Providing default compliance options for business_criticality: {business_criticality}"
    )
    return "multi_select", options
