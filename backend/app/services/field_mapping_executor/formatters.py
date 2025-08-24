"""
Field Mapping Formatters
Output formatting and response creation for field mapping results.

This module provides a centralized interface to various formatter types.
The actual implementations are modularized into separate files for maintainability.
"""

import logging
from typing import Any, Dict, List

from .mapping_formatters import BaseFormatter, MappingResponseFormatter
from .utility_formatters import (
    ClarificationFormatter,
    LoggingFormatter,
    ValidationResultsFormatter,
)

logger = logging.getLogger(__name__)


# Placeholder formatters for backward compatibility
class PlaceholderValidationResultsFormatter(BaseFormatter):
    """Validation results formatter - placeholder implementation"""

    def format_validation_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Placeholder validation results formatting"""
        return results


class PlaceholderLoggingFormatter(BaseFormatter):
    """Logging formatter - placeholder implementation"""

    def format_log_entry(self, message: str, level: str = "INFO") -> str:
        """Placeholder log formatting"""
        return f"[{level}] {message}"


class PlaceholderClarificationFormatter(BaseFormatter):
    """Clarification formatter - placeholder implementation"""

    def format_clarifications(self, clarifications: List[str]) -> Dict[str, Any]:
        """Placeholder clarification formatting"""
        return {"clarifications": clarifications}


# Export all formatters for easy importing
__all__ = [
    "BaseFormatter",
    "MappingResponseFormatter",
    "ValidationResultsFormatter",
    "LoggingFormatter",
    "ClarificationFormatter",
    "PlaceholderValidationResultsFormatter",
    "PlaceholderLoggingFormatter",
    "PlaceholderClarificationFormatter",
]
