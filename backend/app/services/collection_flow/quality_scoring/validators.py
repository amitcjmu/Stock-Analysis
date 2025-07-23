"""
Quality Scoring Validators

This module contains validation functions used for data quality assessment.
"""

import re
from typing import Any


def validate_ip_address(ip: Any) -> bool:
    """Validate IP address format."""
    if not isinstance(ip, str):
        return False

    try:
        parts = ip.split(".")
        return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
    except (ValueError, AttributeError):
        return False


def validate_hostname(hostname: Any) -> bool:
    """Validate hostname format."""
    if not isinstance(hostname, str):
        return False

    pattern = r"^[a-zA-Z0-9\-\.]+$"
    return bool(re.match(pattern, hostname)) and len(hostname) <= 255


def validate_type(value: Any, expected_type: str) -> bool:
    """Validate value type."""
    type_validators = {
        "integer": lambda v: isinstance(v, int) or (isinstance(v, str) and v.isdigit()),
        "numeric": lambda v: isinstance(v, (int, float))
        or (isinstance(v, str) and is_numeric(v)),
        "string": lambda v: isinstance(v, str),
        "boolean": lambda v: isinstance(v, bool)
        or v in ["true", "false", "True", "False"],
    }

    validator = type_validators.get(expected_type)
    return validator(value) if validator else True


def is_numeric(value: str) -> bool:
    """Check if string value is numeric."""
    try:
        float(value)
        return True
    except ValueError:
        return False
