"""
Intelligent Options Module
Extracted from intelligent_options.py for modularization.
Contains context-aware pattern detection logic for questionnaire field options.
"""

from .application_options import get_dependencies_options
from .business_options import (
    get_business_logic_complexity_options,
    get_change_tolerance_options,
)
from .eol_options import get_eol_technology_assessment_options
from .infrastructure_options import get_availability_requirements_options
from .security_options import (
    get_security_compliance_requirements_options,
    get_security_vulnerabilities_options,
)
from .utils import (
    get_fallback_field_type_and_options,
    infer_field_type_from_config,
)

__all__ = [
    # Security options
    "get_security_vulnerabilities_options",
    "get_security_compliance_requirements_options",
    # Business options
    "get_business_logic_complexity_options",
    "get_change_tolerance_options",
    # Infrastructure options
    "get_availability_requirements_options",
    # Application options
    "get_dependencies_options",
    # EOL options
    "get_eol_technology_assessment_options",
    # Utilities
    "infer_field_type_from_config",
    "get_fallback_field_type_and_options",
]
