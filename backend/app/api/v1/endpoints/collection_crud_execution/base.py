"""
Collection Flow Execution - Base Module
Common imports, utilities, and shared components for collection flow execution operations.
"""

import logging
from typing import Any, Dict

from app.utils.security_utils import InputSanitizer

logger = logging.getLogger(__name__)


def sanitize_mfo_result(mfo_result: Any) -> Dict[str, Any]:
    """
    Sanitize MFO result to prevent sensitive data leaks.

    Only returns whitelisted fields from the MFO result to prevent
    exposure of internal system details, credentials, or other sensitive data.

    Args:
        mfo_result: Raw MFO result that may contain sensitive data

    Returns:
        Sanitized dictionary with only whitelisted fields
    """
    # Define whitelisted fields that are safe to expose
    WHITELISTED_FIELDS = {
        "status",
        "message",
        "flow_id",
        "phase",
        "progress",
        "error",  # Allow error messages but sanitize them
        "success",
        "completed",
        "timestamp",
        "next_phase",
        "summary",
    }

    if not mfo_result:
        return {"status": "no_result"}

    if isinstance(mfo_result, dict):
        sanitized = {}
        for key, value in mfo_result.items():
            if key in WHITELISTED_FIELDS:
                # Sanitize the value based on type
                if isinstance(value, str):
                    sanitized[key] = InputSanitizer.sanitize_string(
                        value, max_length=1000
                    )
                elif isinstance(value, dict):
                    # For nested dicts, only allow basic status information
                    if key == "error" and isinstance(value, dict):
                        sanitized[key] = {
                            "message": InputSanitizer.sanitize_string(
                                str(value.get("message", "")), max_length=500
                            ),
                            "type": InputSanitizer.sanitize_string(
                                str(value.get("type", "unknown")), max_length=100
                            ),
                        }
                    else:
                        # For other nested objects, convert to safe string representation
                        sanitized[key] = InputSanitizer.sanitize_string(
                            str(value), max_length=500
                        )
                elif isinstance(value, (int, float, bool)) or value is None:
                    sanitized[key] = value
                else:
                    # Convert other types to sanitized string
                    sanitized[key] = InputSanitizer.sanitize_string(
                        str(value), max_length=500
                    )
        return sanitized
    else:
        # If mfo_result is not a dict, return a safe string representation
        return {
            "status": "processed",
            "message": InputSanitizer.sanitize_string(str(mfo_result), max_length=500),
        }
