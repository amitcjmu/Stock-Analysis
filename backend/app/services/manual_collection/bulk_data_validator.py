"""
Bulk Data Validator

Handles validation of bulk data entries and templates.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .bulk_data_models import BulkDataValidationIssue, ValidationSeverity

logger = logging.getLogger(__name__)


class BulkDataValidator:
    """Validates bulk data entries and applies business rules."""

    def __init__(self):
        """Initialize validator."""
        pass

    async def validate_bulk_data(
        self,
        data: List[Dict[str, Any]],
        template: Optional[Dict[str, Any]] = None,
        validation_rules: Optional[Dict[str, Any]] = None,
    ) -> List[BulkDataValidationIssue]:
        """Validate bulk data against template and rules"""
        validation_issues = []

        for row_index, row_data in enumerate(data):
            # Validate required fields
            if template and "attributes" in template:
                for attr in template["attributes"]:
                    if attr.get("required", False):
                        attr_name = attr["name"]
                        if attr_name not in row_data or not row_data[attr_name]:
                            validation_issues.append(
                                BulkDataValidationIssue(
                                    row_index=row_index,
                                    column=attr_name,
                                    message=f"Required field '{attr_name}' is missing",
                                    severity=ValidationSeverity.ERROR,
                                    error_code="REQUIRED_FIELD_MISSING",
                                )
                            )

            # Validate individual attribute values
            for column, value in row_data.items():
                if value is not None:
                    issue = self._validate_attribute_value(
                        column, value, row_index, validation_rules
                    )
                    if issue:
                        validation_issues.append(issue)

        return validation_issues

    def _validate_attribute_value(
        self,
        attribute_name: str,
        value: Any,
        row_index: int,
        validation_rules: Optional[Dict[str, Any]] = None,
    ) -> Optional[BulkDataValidationIssue]:
        """Validate a single attribute value"""
        # Get validation rules for this attribute
        rules = self._get_attribute_validation_rules(attribute_name)
        if validation_rules and attribute_name in validation_rules:
            rules.update(validation_rules[attribute_name])

        # String validation
        if isinstance(value, str):
            if "max_length" in rules and len(value) > rules["max_length"]:
                return BulkDataValidationIssue(
                    row_index=row_index,
                    column=attribute_name,
                    message=f"Value exceeds maximum length of {rules['max_length']}",
                    severity=ValidationSeverity.ERROR,
                    error_code="MAX_LENGTH_EXCEEDED",
                )

            if "pattern" in rules and not re.match(rules["pattern"], value):
                return BulkDataValidationIssue(
                    row_index=row_index,
                    column=attribute_name,
                    message="Value does not match required pattern",
                    severity=ValidationSeverity.ERROR,
                    error_code="PATTERN_MISMATCH",
                )

        # Numeric validation
        if isinstance(value, (int, float)):
            if "min_value" in rules and value < rules["min_value"]:
                return BulkDataValidationIssue(
                    row_index=row_index,
                    column=attribute_name,
                    message=f"Value is below minimum of {rules['min_value']}",
                    severity=ValidationSeverity.ERROR,
                    error_code="MIN_VALUE_VIOLATION",
                )

            if "max_value" in rules and value > rules["max_value"]:
                return BulkDataValidationIssue(
                    row_index=row_index,
                    column=attribute_name,
                    message=f"Value exceeds maximum of {rules['max_value']}",
                    severity=ValidationSeverity.ERROR,
                    error_code="MAX_VALUE_VIOLATION",
                )

        # Enum validation
        if "allowed_values" in rules:
            if value not in rules["allowed_values"]:
                return BulkDataValidationIssue(
                    row_index=row_index,
                    column=attribute_name,
                    message=f"Value must be one of: {', '.join(rules['allowed_values'])}",
                    severity=ValidationSeverity.ERROR,
                    error_code="INVALID_ENUM_VALUE",
                    suggested_value=(
                        rules["allowed_values"][0] if rules["allowed_values"] else None
                    ),
                )

        # Date validation
        if "data_type" in rules and rules["data_type"] == "date":
            try:
                if isinstance(value, str):
                    datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return BulkDataValidationIssue(
                    row_index=row_index,
                    column=attribute_name,
                    message="Invalid date format. Use ISO format (YYYY-MM-DD)",
                    severity=ValidationSeverity.ERROR,
                    error_code="INVALID_DATE_FORMAT",
                )

        # Business-specific validations
        return self._validate_business_rules(attribute_name, value, row_index)

    def _get_attribute_validation_rules(self, attribute_name: str) -> Dict[str, Any]:
        """Get validation rules for a specific attribute"""
        # Default validation rules by attribute name
        rules_map = {
            "name": {"max_length": 255, "pattern": r"^[a-zA-Z0-9\s\-_\.]+$"},
            "email": {"pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"},
            "phone": {"pattern": r"^[\+]?[1-9][\d]{0,15}$"},
            "url": {"pattern": r"^https?://[^\s/$.?#].[^\s]*$"},
            "ip_address": {
                "pattern": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
                r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
            },
            "port": {"min_value": 1, "max_value": 65535},
            "cpu_cores": {"min_value": 1, "max_value": 256},
            "memory_gb": {"min_value": 0.1, "max_value": 4096},
            "storage_gb": {"min_value": 0.1, "max_value": 100000},
        }

        # Check for exact match or partial match
        for key, rules in rules_map.items():
            if key in attribute_name.lower():
                return rules

        return {}

    def _validate_business_rules(
        self, attribute_name: str, value: Any, row_index: int
    ) -> Optional[BulkDataValidationIssue]:
        """Apply business-specific validation rules"""
        # Example: Validate server naming conventions
        if "server" in attribute_name.lower() and "name" in attribute_name.lower():
            if isinstance(value, str) and not re.match(r"^[a-zA-Z0-9\-]+$", value):
                return BulkDataValidationIssue(
                    row_index=row_index,
                    column=attribute_name,
                    message="Server names should only contain alphanumeric characters and hyphens",
                    severity=ValidationSeverity.WARNING,
                    error_code="NAMING_CONVENTION_VIOLATION",
                )

        # Example: Validate environment values
        if "environment" in attribute_name.lower():
            valid_envs = ["development", "staging", "production", "test"]
            if isinstance(value, str) and value.lower() not in valid_envs:
                return BulkDataValidationIssue(
                    row_index=row_index,
                    column=attribute_name,
                    message=f"Environment should be one of: {', '.join(valid_envs)}",
                    severity=ValidationSeverity.WARNING,
                    error_code="INVALID_ENVIRONMENT",
                    suggested_value="production",
                )

        return None
