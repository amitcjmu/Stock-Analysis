"""
ADR-039: Compliance validation query endpoints.

GET endpoints for retrieving technology compliance validation results:
- Engagement standards compliance check results
- Version compliance issues per application
- EOL status for operating systems and runtimes

POST endpoint for refreshing compliance data:
- Manually trigger compliance validation for existing flows
- Useful for flows created before architecture_minimums phase was added

Data is sourced from phase_results["architecture_minimums"]["compliance_validation"]
which is populated during the ARCHITECTURE_MINIMUMS phase.
"""

# Import endpoints to register them with the router
from . import mutations, queries  # noqa: F401
from .schemas import (
    ApplicationComplianceResult,
    CheckedItem,
    ComplianceIssue,
    ComplianceValidationResponse,
    EOLStatusInfo,
    LevelComplianceResult,
    ThreeLevelComplianceResult,
)
from .utils import _get_default_standards, _parse_by_level

__all__ = [
    "ComplianceIssue",
    "CheckedItem",
    "LevelComplianceResult",
    "ThreeLevelComplianceResult",
    "ApplicationComplianceResult",
    "EOLStatusInfo",
    "ComplianceValidationResponse",
    "_get_default_standards",
    "_parse_by_level",
]
