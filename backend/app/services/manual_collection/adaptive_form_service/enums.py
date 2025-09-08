"""
Adaptive Form Service Enums
"""

from enum import Enum


class FieldType(str, Enum):
    """Form field types supported by the adaptive form system"""

    TEXT = "text"
    TEXTAREA = "textarea"
    SELECT = "select"
    MULTISELECT = "multiselect"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    NUMBER = "number"
    DATE = "date"
    EMAIL = "email"
    URL = "url"
    FILE = "file"


class ValidationRule(str, Enum):
    """Validation rules for form fields"""

    REQUIRED = "required"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    PATTERN = "pattern"
    EMAIL_FORMAT = "email"
    URL_FORMAT = "url"
    CONDITIONAL_REQUIRED = "conditional_required"
