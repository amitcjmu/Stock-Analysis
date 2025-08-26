"""
Input validation for application deduplication operations.

This module provides comprehensive input validation for the deduplication service,
ensuring data integrity and proper error handling.
"""

import uuid
from app.core.exceptions import ValidationError


def validate_deduplication_inputs(
    application_name: str,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
):
    """Validate inputs for deduplication process"""

    if not application_name or not application_name.strip():
        raise ValidationError("Application name cannot be empty")

    if len(application_name.strip()) > 255:
        raise ValidationError("Application name cannot exceed 255 characters")

    if not client_account_id:
        raise ValidationError("Client account ID is required")

    if not engagement_id:
        raise ValidationError("Engagement ID is required")
