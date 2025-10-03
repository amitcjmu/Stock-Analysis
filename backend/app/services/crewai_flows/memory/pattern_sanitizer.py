"""
Pattern Data Sanitizer - Security Module
Removes PII and sensitive information from pattern data before storage.

This module addresses Qodo Bot security finding: "Sensitive Information Exposure"
by implementing comprehensive sanitization of pattern data.
"""

import logging
import re
from typing import Any, Dict, Union
import uuid

logger = logging.getLogger(__name__)


def safe_int_conversion(value: Union[int, str, uuid.UUID]) -> int:
    """
    Safely convert UUID, string, or int to int.

    This addresses Qodo Bot finding: "UUID Conversion Error"
    where int(uuid.UUID) fails at runtime.

    Args:
        value: Can be int, string representation of int, or UUID

    Returns:
        Integer value

    Raises:
        ValueError: If value cannot be converted to int
    """
    if isinstance(value, int):
        return value
    elif isinstance(value, uuid.UUID):
        # Use UUID.int property to get integer representation
        return value.int
    elif isinstance(value, str):
        # Try to parse as UUID first
        try:
            parsed_uuid = uuid.UUID(value)
            return parsed_uuid.int
        except (ValueError, AttributeError):
            # Fall back to direct int conversion
            return int(value)
    else:
        raise ValueError(f"Cannot convert {type(value)} to int: {value}")


class PatternSanitizer:
    """Sanitizes pattern data to remove PII and sensitive information."""

    # Patterns that may contain sensitive information
    SENSITIVE_KEYS = {
        "asset_name",
        "server_name",
        "hostname",
        "ip_address",
        "credentials",
        "password",
        "api_key",
        "token",
        "secret",
        "vulnerability_details",
        "threat_details",
        "permissions_found",
        "specific_issues",
    }

    @staticmethod
    def sanitize_pattern_data(pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize pattern data to remove PII and sensitive information.

        Redacts:
        - Asset names (replace with generic identifier)
        - Specific recommendations that may contain business secrets
        - Raw credential/permission details
        - Detailed vulnerability/threat information
        - Specific hostnames, IPs, and infrastructure details

        Args:
            pattern_data: Original pattern data dictionary

        Returns:
            Sanitized pattern data safe for storage
        """
        sanitized = pattern_data.copy()

        # 1. Redact asset-specific identifiers from name field
        sanitized = PatternSanitizer._sanitize_name_field(sanitized)

        # 2. Redact sensitive recommendation details (keep high-level categories only)
        sanitized = PatternSanitizer._sanitize_recommendations(sanitized)

        # 3. Redact specific threat/vulnerability details
        sanitized = PatternSanitizer._sanitize_threats_and_vulnerabilities(sanitized)

        # 4. Redact specific permission details (keep counts only)
        sanitized = PatternSanitizer._sanitize_permissions(sanitized)

        # 5. Redact common issues with PII (keep issue types only)
        sanitized = PatternSanitizer._sanitize_common_issues(sanitized)

        # 6. Redact any remaining sensitive keys
        sanitized = PatternSanitizer._redact_sensitive_keys(sanitized)

        # 7. Log sanitization for audit trail
        logger.debug(
            f"Sanitized pattern data: {len(pattern_data)} -> {len(sanitized)} keys"
        )

        return sanitized

    @staticmethod
    def _sanitize_name_field(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact asset-specific identifiers from name field.

        Examples:
        - "asset_classification_AWS_prod-server-1_eng123" -> "asset_classification_AWS_[REDACTED]_eng123"
        - "business_value_analysis_critical-db-prod_2025-01-01" -> "business_value_analysis_[REDACTED]_2025-01-01"
        """
        if "name" in data and "_" in data["name"]:
            parts = data["name"].split("_")

            # For patterns like: pattern_type_specific_identifier_timestamp
            # Keep pattern type and timestamp, redact specific identifier
            if len(parts) >= 3:
                # Preserve first part (pattern type) and last part (timestamp/engagement)
                # Redact middle parts that may contain asset names
                sanitized_parts = []
                sanitized_parts.append(parts[0])  # Pattern type

                # Redact middle parts (potentially sensitive asset identifiers)
                for i in range(1, len(parts) - 1):
                    # Check if this part looks like a UUID or engagement ID - preserve it
                    if PatternSanitizer._is_uuid_or_id(parts[i]):
                        sanitized_parts.append(parts[i])
                    else:
                        sanitized_parts.append("[REDACTED]")

                sanitized_parts.append(parts[-1])  # Timestamp or engagement ID
                data["name"] = "_".join(sanitized_parts)

        return data

    @staticmethod
    def _sanitize_recommendations(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact sensitive recommendation details (keep high-level categories only).

        Example:
        - "Upgrade server prod-db-01 to PostgreSQL 15" -> "Upgrade database version"
        - "Fix critical vulnerability in payment API" -> "Address security vulnerability"
        """
        if "recommendations" in data and isinstance(data["recommendations"], list):
            sanitized_recs = []
            for rec in data["recommendations"]:
                if isinstance(rec, str):
                    # Keep only category before colon, truncate details
                    if ":" in rec:
                        category = rec.split(":")[0]
                        sanitized_recs.append(f"{category}: [Details redacted]")
                    else:
                        # Truncate to 50 chars and remove specific details
                        sanitized_rec = PatternSanitizer._remove_hostnames(rec[:50])
                        sanitized_recs.append(sanitized_rec)
                else:
                    sanitized_recs.append("[Non-string recommendation redacted]")

            data["recommendations"] = sanitized_recs

        return data

    @staticmethod
    def _sanitize_threats_and_vulnerabilities(data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact specific threat/vulnerability details."""
        # Redact primary threats
        if "primary_threats" in data and isinstance(data["primary_threats"], list):
            # Keep count and categories only, not specific details
            threat_count = len(data["primary_threats"])
            data["primary_threats"] = [
                f"Threat Category {i+1}" for i in range(threat_count)
            ]

        # Redact vulnerability summary
        if "vulnerability_summary" in data:
            if isinstance(data["vulnerability_summary"], str):
                data["vulnerability_summary"] = (
                    "[Vulnerability details redacted for security]"
                )
            elif isinstance(data["vulnerability_summary"], dict):
                data["vulnerability_summary"] = {
                    "total_count": len(data["vulnerability_summary"]),
                    "details": "[REDACTED]",
                }

        # Redact security risks
        if "security_risks" in data and isinstance(data["security_risks"], list):
            data["security_risks"] = [
                f"Risk Type {i+1}" for i in range(len(data["security_risks"]))
            ]

        return data

    @staticmethod
    def _sanitize_permissions(data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact specific permission details (keep counts only)."""
        if "permissions_found" in data:
            if isinstance(data["permissions_found"], list):
                # Replace with count only
                data["permissions_count"] = len(data["permissions_found"])
                del data["permissions_found"]
            elif isinstance(data["permissions_found"], dict):
                data["permissions_count"] = len(data["permissions_found"])
                del data["permissions_found"]

        return data

    @staticmethod
    def _sanitize_common_issues(data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact common issues with PII (keep issue types only)."""
        if "common_issues" in data and isinstance(data["common_issues"], list):
            sanitized_issues = []
            for issue in data["common_issues"]:
                if isinstance(issue, str):
                    # Keep only issue type (before colon)
                    if ":" in issue:
                        issue_type = issue.split(":")[0]
                        sanitized_issues.append(f"{issue_type}: [Details redacted]")
                    else:
                        # Remove hostnames and specific identifiers
                        sanitized_issue = PatternSanitizer._remove_hostnames(issue)
                        sanitized_issues.append(sanitized_issue)
                else:
                    sanitized_issues.append("[Non-string issue redacted]")

            data["common_issues"] = sanitized_issues

        return data

    @staticmethod
    def _redact_sensitive_keys(data: Dict[str, Any]) -> Dict[str, Any]:
        """Redact any remaining sensitive keys."""
        for key in list(data.keys()):
            if key.lower() in PatternSanitizer.SENSITIVE_KEYS:
                # Replace with redacted indicator
                data[f"{key}_redacted"] = True
                del data[key]
                logger.debug(f"Redacted sensitive key: {key}")

        return data

    @staticmethod
    def _is_uuid_or_id(value: str) -> bool:
        """Check if a string looks like a UUID or numeric ID."""
        # Check for UUID pattern
        try:
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError):
            pass

        # Check for numeric ID
        if value.isdigit():
            return True

        # Check for engagement/client ID pattern (e.g., "eng123", "client456")
        if re.match(r"^(eng|client|acc)\d+$", value, re.IGNORECASE):
            return True

        return False

    @staticmethod
    def _remove_hostnames(text: str) -> str:
        """Remove hostnames, IPs, and specific server names from text."""
        # Remove IPv4 addresses (valid octets only: 0-255)
        ipv4_octet = r"(25[0-5]|2[0-4]\d|1?\d{1,2})"
        text = re.sub(
            rf"\b{ipv4_octet}\.{ipv4_octet}\.{ipv4_octet}\.{ipv4_octet}\b",
            "[IP]",
            text,
        )

        # Remove multi-level subdomains (e.g., api.internal.example.com)
        text = re.sub(
            r"\b(?:[a-z0-9-]+\.)+(com|net|org|io|local|cloud|corp|internal)\b",
            "[HOSTNAME]",
            text,
            flags=re.IGNORECASE,
        )

        # Remove server name patterns (e.g., "prod-db-01", "web-server-2")
        text = re.sub(
            r"\b(prod|dev|test|staging)-[a-z0-9-]+\b",
            "[SERVER]",
            text,
            flags=re.IGNORECASE,
        )

        return text


# Convenience function for direct import
def sanitize_pattern_data(pattern_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to sanitize pattern data.

    Usage:
        from app.services.crewai_flows.memory.pattern_sanitizer import sanitize_pattern_data

        sanitized = sanitize_pattern_data(pattern_data)
    """
    return PatternSanitizer.sanitize_pattern_data(pattern_data)
