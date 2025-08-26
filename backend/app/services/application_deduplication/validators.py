"""
Input validation for application deduplication operations.

This module provides comprehensive input validation for the deduplication service,
ensuring data integrity and proper error handling with security-first approach.
"""

import re
import uuid
from typing import Any, Dict, Optional

from app.core.exceptions import ValidationError

# Security patterns for input sanitization
DANGEROUS_PATTERNS = [
    r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",  # Script tags
    r"javascript:",  # JavaScript URLs
    r"on\w+\s*=",  # Event handlers
    r"<\s*\/?\s*(?:script|iframe|object|embed|link|meta)",  # Dangerous HTML tags
    r"(?:union|select|insert|update|delete|drop|create|alter)\s+",  # SQL keywords
    r"[';].*--",  # SQL comment injection
]

# Compile patterns for performance
DANGER_REGEX = re.compile("|".join(DANGEROUS_PATTERNS), re.IGNORECASE | re.MULTILINE)


def sanitize_application_name(application_name: str) -> str:
    """
    Sanitize application name to prevent injection attacks.

    Args:
        application_name: Raw application name input

    Returns:
        Sanitized application name

    Raises:
        ValidationError: If input contains dangerous patterns
    """
    if not application_name:
        return application_name

    # Check for dangerous patterns
    if DANGER_REGEX.search(application_name):
        raise ValidationError("Application name contains potentially dangerous content")

    # Remove control characters except tabs and newlines
    sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", application_name)

    # Normalize whitespace
    sanitized = re.sub(r"\s+", " ", sanitized).strip()

    return sanitized


def validate_uuid_parameter(value: Any, parameter_name: str) -> uuid.UUID:
    """
    Validate and convert UUID parameter with proper error handling.

    Args:
        value: Value to validate as UUID
        parameter_name: Name of parameter for error messages

    Returns:
        Validated UUID object

    Raises:
        ValidationError: If UUID is invalid
    """
    if value is None:
        raise ValidationError(f"{parameter_name} is required")

    if isinstance(value, uuid.UUID):
        return value

    if isinstance(value, str):
        try:
            return uuid.UUID(value)
        except ValueError:
            raise ValidationError(f"Invalid {parameter_name} format")

    raise ValidationError(f"{parameter_name} must be a valid UUID")


def validate_deduplication_inputs(
    application_name: str,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
):
    """
    Validate inputs for deduplication process with enhanced security.

    Args:
        application_name: Application name to validate and sanitize
        client_account_id: Client account UUID
        engagement_id: Engagement UUID

    Raises:
        ValidationError: If any input is invalid or potentially dangerous
    """

    # Validate application name
    if not application_name or not application_name.strip():
        raise ValidationError("Application name cannot be empty")

    # Sanitize application name for security
    try:
        sanitized_name = sanitize_application_name(application_name)
        if not sanitized_name:
            raise ValidationError("Application name contains only invalid characters")
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Application name validation failed: {str(e)}")

    # Validate length after sanitization
    if len(sanitized_name) > 255:
        raise ValidationError("Application name cannot exceed 255 characters")

    if len(sanitized_name) < 1:
        raise ValidationError("Application name too short after sanitization")

    # Validate UUIDs with proper error handling
    validate_uuid_parameter(client_account_id, "Client account ID")
    validate_uuid_parameter(engagement_id, "Engagement ID")


def validate_bulk_application_list(applications: list) -> list:
    """
    Validate and sanitize a list of application names for bulk operations.

    Args:
        applications: List of application names

    Returns:
        List of validated and sanitized application names

    Raises:
        ValidationError: If list is invalid or contains dangerous content
    """
    if not isinstance(applications, list):
        raise ValidationError("Applications must be provided as a list")

    if len(applications) == 0:
        raise ValidationError("Applications list cannot be empty")

    if len(applications) > 1000:  # Prevent DoS attacks
        raise ValidationError("Too many applications in batch (max 1000)")

    validated_apps = []

    for i, app_name in enumerate(applications):
        if not isinstance(app_name, str):
            raise ValidationError(f"Application at index {i} must be a string")

        try:
            sanitized = sanitize_application_name(app_name)
            if sanitized:  # Only add non-empty names after sanitization
                validated_apps.append(sanitized)
        except ValidationError as e:
            raise ValidationError(f"Application at index {i}: {str(e)}")

    if not validated_apps:
        raise ValidationError("No valid applications after sanitization")

    return validated_apps


def validate_deduplication_metadata(
    metadata: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Validate and sanitize additional metadata for deduplication.

    Args:
        metadata: Optional metadata dictionary

    Returns:
        Validated metadata dictionary

    Raises:
        ValidationError: If metadata contains invalid content
    """
    if metadata is None:
        return {}

    if not isinstance(metadata, dict):
        raise ValidationError("Metadata must be a dictionary")

    # Limit metadata size to prevent DoS
    if len(str(metadata)) > 10000:  # 10KB limit
        raise ValidationError("Metadata too large (max 10KB)")

    validated_metadata = {}

    for key, value in metadata.items():
        if not isinstance(key, str):
            raise ValidationError("Metadata keys must be strings")

        # Sanitize keys
        try:
            sanitized_key = sanitize_application_name(key)
            if not sanitized_key:
                continue  # Skip empty keys after sanitization
        except ValidationError:
            continue  # Skip dangerous keys

        # Validate values
        if isinstance(value, str):
            try:
                sanitized_value = sanitize_application_name(value)
                validated_metadata[sanitized_key] = sanitized_value
            except ValidationError:
                continue  # Skip dangerous values
        elif isinstance(value, (int, float, bool, type(None))):
            validated_metadata[sanitized_key] = value
        # Skip complex types for security

    return validated_metadata
