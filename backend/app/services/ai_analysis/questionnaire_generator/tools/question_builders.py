"""
Question Builder Functions - Facade Module
Provides backward compatibility by re-exporting functions from modularized builders.

Modularization (Issue #980 - Fix 0.4):
- attribute_question_builders.py: Missing field and unmapped attribute questions
- assessment_question_builders.py: Quality, dependency, technical assessment questions
"""

# Import all question builder functions for backward compatibility
from .attribute_question_builders import (
    generate_missing_field_question,
    generate_unmapped_attribute_question,
)
from .assessment_question_builders import (
    generate_data_quality_question,
    generate_dependency_question,
    generate_generic_technical_question,
    generate_generic_question,
    generate_fallback_question,
)

__all__ = [
    "generate_missing_field_question",
    "generate_unmapped_attribute_question",
    "generate_data_quality_question",
    "generate_dependency_question",
    "generate_generic_technical_question",
    "generate_generic_question",
    "generate_fallback_question",
]
