"""
Adaptive Form Service Package - Modularized

This package provides adaptive form generation based on gap analysis results,
application context, and the 22 critical attributes framework.
All imports are maintained for backward compatibility.
"""

# Import enums
from .enums import FieldType, ValidationRule

# Import models
from .models import (
    AdaptiveForm,
    ApplicationContext,
    ConditionalDisplayRule,
    FieldValidation,
    FormField,
    FormSection,
    GapAnalysisResult,
)

# Import configuration
from .config import CRITICAL_ATTRIBUTES_CONFIG, FIELD_OPTIONS

# Import service and mixins
from .service import AdaptiveFormService
from .form_creation import FormCreationMixin

# Import utilities
from .utils import _get_json_schema_type, to_dict, to_json_schema

# Export all public interfaces for backward compatibility
__all__ = [
    # Enums
    "FieldType",
    "ValidationRule",
    # Models
    "ConditionalDisplayRule",
    "FieldValidation",
    "FormField",
    "FormSection",
    "AdaptiveForm",
    "GapAnalysisResult",
    "ApplicationContext",
    # Service
    "AdaptiveFormService",
    "FormCreationMixin",
    # Configuration
    "CRITICAL_ATTRIBUTES_CONFIG",
    "FIELD_OPTIONS",
    # Utilities
    "to_dict",
    "to_json_schema",
    "_get_json_schema_type",
]
