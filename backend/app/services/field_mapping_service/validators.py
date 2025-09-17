"""
Field mapping validation logic.

This module contains validation functions for field mappings,
including content validation and pattern matching.
"""

import ipaddress
import re
from typing import Any, Dict, List, Optional

from .base import (
    VALIDATION_PATTERNS,
    MAX_VALIDATION_SAMPLES,
    MAX_ISSUES_REPORTED,
    logger,
)


class FieldMappingValidator:
    """Field mapping validation utilities"""

    @staticmethod
    def validate_content(target_field: str, sample_values: List[Any]) -> List[str]:
        """
        Validate content against expected patterns for target field.

        Args:
            target_field: Target field name to validate against
            sample_values: Sample values to validate

        Returns:
            List of validation issues found
        """
        issues = []

        # Field-specific validation rules
        if target_field == "ip_address":
            for value in sample_values[:MAX_VALIDATION_SAMPLES]:  # Check first 5 values
                if not FieldMappingValidator._is_valid_ip(str(value)):
                    issues.append(f"Invalid IP address format: {value}")

        elif target_field == "email":
            for value in sample_values[:MAX_VALIDATION_SAMPLES]:
                if not FieldMappingValidator._is_valid_email(str(value)):
                    issues.append(f"Invalid email format: {value}")

        elif target_field == "hostname":
            for value in sample_values[:MAX_VALIDATION_SAMPLES]:
                if not FieldMappingValidator._is_valid_hostname(str(value)):
                    issues.append(f"Invalid hostname format: {value}")

        elif target_field in ["cpu_cores", "memory_gb", "storage_gb"]:
            for value in sample_values[:MAX_VALIDATION_SAMPLES]:
                if not FieldMappingValidator._is_numeric(value):
                    issues.append(f"Expected numeric value, got: {value}")

        elif target_field in ["criticality", "priority"]:
            for value in sample_values[:MAX_VALIDATION_SAMPLES]:
                if not FieldMappingValidator._is_valid_criticality(str(value)):
                    issues.append(f"Invalid criticality value: {value}")

        elif target_field == "status":
            for value in sample_values[:MAX_VALIDATION_SAMPLES]:
                if not FieldMappingValidator._is_valid_status(str(value)):
                    issues.append(f"Invalid status value: {value}")

        return issues[:MAX_ISSUES_REPORTED]  # Return max 3 issues

    @staticmethod
    def _is_valid_ip(value: str) -> bool:
        """Check if value is a valid IP address (IPv4 or IPv6)."""
        try:
            # This validates both IPv4 and IPv6 addresses
            ipaddress.ip_address(value.strip())
            return True
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def _is_valid_email(value: str) -> bool:
        """Check if value is a valid email address."""
        if not value or not isinstance(value, str):
            return False

        pattern = VALIDATION_PATTERNS.get(
            "email", r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )
        return bool(re.match(pattern, value.strip()))

    @staticmethod
    def _is_valid_hostname(value: str) -> bool:
        """Check if value is a valid hostname."""
        if not value or not isinstance(value, str):
            return False

        pattern = VALIDATION_PATTERNS.get(
            "hostname",
            r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$",
        )
        return bool(re.match(pattern, value.strip()))

    @staticmethod
    def _is_numeric(value: Any) -> bool:
        """Check if value is numeric."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _is_valid_criticality(value: str) -> bool:
        """Check if value is a valid criticality level."""
        if not value or not isinstance(value, str):
            return False

        valid_criticalities = {
            "low",
            "medium",
            "high",
            "critical",
            "tier1",
            "tier2",
            "tier3",
            "tier4",
            "1",
            "2",
            "3",
            "4",
            "5",
            "normal",
            "important",
            "urgent",
        }
        return value.lower().strip() in valid_criticalities

    @staticmethod
    def _is_valid_status(value: str) -> bool:
        """Check if value is a valid status."""
        if not value or not isinstance(value, str):
            return False

        valid_statuses = {
            "active",
            "inactive",
            "running",
            "stopped",
            "pending",
            "online",
            "offline",
            "operational",
            "maintenance",
            "up",
            "down",
            "healthy",
            "unhealthy",
            "available",
            "unavailable",
        }
        return value.lower().strip() in valid_statuses

    @staticmethod
    def validate_mapping_consistency(
        source_field: str, target_field: str, sample_values: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate the consistency of a field mapping.

        Args:
            source_field: Source field name
            target_field: Target field name
            sample_values: Optional sample values for validation

        Returns:
            Validation result with confidence and issues
        """
        issues = []
        confidence = 1.0

        # Check field name similarity
        source_normalized = source_field.lower().replace("_", "").replace("-", "")
        target_normalized = target_field.lower().replace("_", "").replace("-", "")

        # Simple similarity check
        if (
            source_normalized not in target_normalized
            and target_normalized not in source_normalized
        ):
            # Check for common abbreviations
            abbreviations = {
                "ip": "ipaddress",
                "addr": "address",
                "os": "operatingsystem",
                "cpu": "cpucores",
                "mem": "memory",
                "ram": "memory",
                "hdd": "storage",
                "disk": "storage",
            }

            found_match = False
            for abbr, full in abbreviations.items():
                if (abbr in source_normalized and full in target_normalized) or (
                    full in source_normalized and abbr in target_normalized
                ):
                    found_match = True
                    break

            if not found_match:
                confidence *= 0.7
                issues.append("Field names have low similarity")

        # Validate content if sample values provided
        if sample_values:
            content_issues = FieldMappingValidator.validate_content(
                target_field, sample_values
            )
            if content_issues:
                confidence *= 0.5
                issues.extend(content_issues)

        return {
            "valid": confidence > 0.3,
            "confidence": confidence,
            "issues": issues,
        }

    @staticmethod
    def get_validation_suggestions(target_field: str) -> Dict[str, Any]:
        """
        Get validation suggestions for a target field.

        Args:
            target_field: Target field name

        Returns:
            Dictionary with validation requirements and suggestions
        """
        suggestions = {
            "field": target_field,
            "data_type": "string",
            "required": True,
            "validation_rules": [],
            "examples": [],
        }

        if target_field == "ip_address":
            suggestions.update(
                {
                    "data_type": "string",
                    "validation_rules": ["Valid IPv4 or IPv6 address"],
                    "examples": ["192.168.1.1", "2001:db8::1"],
                    "pattern": VALIDATION_PATTERNS.get("ip_address"),
                }
            )
        elif target_field == "email":
            suggestions.update(
                {
                    "data_type": "string",
                    "validation_rules": ["Valid email format with @ symbol"],
                    "examples": ["user@domain.com", "admin@company.org"],
                    "pattern": VALIDATION_PATTERNS.get("email"),
                }
            )
        elif target_field == "hostname":
            suggestions.update(
                {
                    "data_type": "string",
                    "validation_rules": ["Valid hostname format"],
                    "examples": ["server01.domain.com", "web-server"],
                    "pattern": VALIDATION_PATTERNS.get("hostname"),
                }
            )
        elif target_field in ["cpu_cores", "memory_gb", "storage_gb"]:
            suggestions.update(
                {
                    "data_type": "number",
                    "validation_rules": ["Must be a positive number"],
                    "examples": ["4", "16.5", "1024"],
                }
            )
        elif target_field == "criticality":
            suggestions.update(
                {
                    "data_type": "string",
                    "validation_rules": ["One of: low, medium, high, critical"],
                    "examples": ["low", "medium", "high", "critical"],
                }
            )
        elif target_field == "status":
            suggestions.update(
                {
                    "data_type": "string",
                    "validation_rules": ["Operational status"],
                    "examples": ["active", "inactive", "running", "stopped"],
                }
            )

        return suggestions
