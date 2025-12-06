"""
Compliance validation response schemas

Pydantic models for compliance validation responses (ADR-039).
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ComplianceIssue(BaseModel):
    """Single compliance violation."""

    field: str = Field(..., description="Technology field with compliance issue")
    current: str = Field(..., description="Current version/value")
    required: str = Field(..., description="Required minimum version/value")
    severity: str = Field(
        default="medium", description="Severity: critical, high, medium, low"
    )
    recommendation: str = Field(default="", description="Remediation recommendation")


class CheckedItem(BaseModel):
    """Single item checked during compliance validation (Issue #1243)."""

    technology: str = Field(..., description="Technology name")
    version: str = Field(..., description="Version string")
    eol_status: str = Field(
        default="unknown",
        description="EOL status: active, eol_soon, eol_expired, unknown",
    )
    eol_date: Optional[str] = Field(None, description="End of life date if known")
    source: str = Field(
        default="unknown",
        description="Data source: catalog, rag, heuristics, unknown",
    )
    is_compliant: bool = Field(True, description="Whether item meets requirements")
    issue: Optional[str] = Field(None, description="Issue description if non-compliant")


class LevelComplianceResult(BaseModel):
    """Compliance result for a single level (OS, Application, Component)."""

    level_name: str = Field(..., description="Level name: os, application, component")
    is_compliant: bool = Field(True, description="Whether level is compliant")
    checked_count: int = Field(0, description="Number of items checked")
    passed_count: int = Field(0, description="Number of items passing")
    failed_count: int = Field(0, description="Number of items failing")
    checked_items: List[CheckedItem] = Field(
        default_factory=list, description="Items checked at this level"
    )
    issues: List[ComplianceIssue] = Field(
        default_factory=list, description="Issues found at this level"
    )


class ThreeLevelComplianceResult(BaseModel):
    """Three-level compliance validation result (Issue #1243)."""

    os_compliance: LevelComplianceResult = Field(
        default_factory=lambda: LevelComplianceResult(level_name="os"),
        description="Level 1: OS Compliance (operating systems)",
    )
    application_compliance: LevelComplianceResult = Field(
        default_factory=lambda: LevelComplianceResult(level_name="application"),
        description="Level 2: Application Compliance (COTS apps)",
    )
    component_compliance: LevelComplianceResult = Field(
        default_factory=lambda: LevelComplianceResult(level_name="component"),
        description="Level 3: Component Compliance (DBs, runtimes, frameworks)",
    )


class ApplicationComplianceResult(BaseModel):
    """Compliance validation result for a single application."""

    application_id: str
    application_name: Optional[str] = None
    is_compliant: bool = Field(
        default=True, description="True if all technology versions meet minimums"
    )
    issues: List[ComplianceIssue] = Field(
        default_factory=list, description="List of compliance violations"
    )
    checked_fields: int = Field(
        default=0, description="Number of technology fields validated"
    )
    passed_fields: int = Field(
        default=0, description="Number of fields meeting requirements"
    )


class EOLStatusInfo(BaseModel):
    """End-of-Life status for a technology."""

    product: str
    version: str
    status: str = Field(
        description="EOL status: active, eol_soon, eol_expired, unknown"
    )
    eol_date: Optional[str] = None
    support_type: str = Field(
        default="none", description="Support type: mainstream, extended, none"
    )
    source: str = Field(
        default="fallback_heuristics",
        description="Data source: endoflife.date, vendor_catalog, fallback_heuristics",
    )
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Confidence score"
    )


class ComplianceValidationResponse(BaseModel):
    """Complete compliance validation results for assessment flow."""

    flow_id: str
    standards_applied: Dict[str, Any] = Field(
        default_factory=dict, description="Engagement standards used for validation"
    )
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary: total_apps, compliant_count, non_compliant_count",
    )
    applications: Dict[str, ApplicationComplianceResult] = Field(
        default_factory=dict, description="Per-application compliance results"
    )
    eol_status: List[EOLStatusInfo] = Field(
        default_factory=list, description="EOL status for detected technologies"
    )
    # Issue #1243: Three-level compliance validation
    by_level: Optional[ThreeLevelComplianceResult] = Field(
        default=None,
        description="Three-level compliance breakdown (OS, Application, Component)",
    )
    checked_items: List[CheckedItem] = Field(
        default_factory=list,
        description="All items checked during validation (aggregated from by_level)",
    )
    validated_at: Optional[str] = None
