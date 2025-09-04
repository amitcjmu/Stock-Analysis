"""
Data Import Validation Executor - Facade for Backward Compatibility
Handles data import validation phase for the Unified Discovery Flow.
Performs PII detection, malicious payload scanning, and data type validation.

This file now serves as a facade, re-exporting the modularized implementation for backward compatibility.
"""

# Re-export everything from the modularized package
from .data_import_validation import DataImportValidationExecutor

__all__ = ["DataImportValidationExecutor"]
