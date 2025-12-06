"""
ADR-039: Compliance validation query endpoints.

GET endpoints for retrieving technology compliance validation results:
- Engagement standards compliance check results
- Version compliance issues per application
- EOL status for operating systems and runtimes

Data is sourced from phase_results["architecture_minimums"]["compliance_validation"]
which is populated during the ARCHITECTURE_MINIMUMS phase.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models.assessment_flow import AssessmentFlow
from app.utils.json_sanitization import sanitize_for_json

from . import router

logger = logging.getLogger(__name__)


# =============================================================================
# Response Schemas
# =============================================================================


class ComplianceIssue(BaseModel):
    """Single compliance violation."""

    field: str = Field(..., description="Technology field with compliance issue")
    current: str = Field(..., description="Current version/value")
    required: str = Field(..., description="Required minimum version/value")
    severity: str = Field(
        default="medium", description="Severity: critical, high, medium, low"
    )
    recommendation: str = Field(default="", description="Remediation recommendation")


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
    validated_at: Optional[str] = None


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/{flow_id}/compliance", response_model=ComplianceValidationResponse)
async def get_compliance_validation(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Get technology compliance validation results for assessment flow.

    ADR-039: Retrieves compliance validation from phase_results populated during
    the ARCHITECTURE_MINIMUMS phase. Includes:
    - Per-application version compliance issues
    - Summary statistics (compliant vs non-compliant)
    - EOL status for detected technologies (OS, runtimes, databases)

    The compliance validation checks technology versions against engagement-specific
    minimum standards (or defaults) to identify migration blockers early.
    """
    try:
        client_account_id = context.client_account_id
        engagement_id = context.engagement_id

        if not client_account_id or not engagement_id:
            raise HTTPException(
                status_code=400, detail="Client account ID and Engagement ID required"
            )

        # Query assessment flow with phase_results
        stmt = select(AssessmentFlow).where(
            AssessmentFlow.id == flow_id,
            AssessmentFlow.client_account_id == client_account_id,
            AssessmentFlow.engagement_id == engagement_id,
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Extract compliance data from phase_results
        phase_results = flow.phase_results or {}
        arch_minimums = phase_results.get("architecture_minimums", {})
        compliance_validation = arch_minimums.get("compliance_validation", {})

        # Build response
        response = ComplianceValidationResponse(
            flow_id=flow_id,
            standards_applied=compliance_validation.get("standards_applied", {}),
            summary=compliance_validation.get(
                "summary",
                {
                    "total_applications": 0,
                    "compliant_count": 0,
                    "non_compliant_count": 0,
                },
            ),
            applications={
                app_id: ApplicationComplianceResult(
                    application_id=app_id,
                    application_name=app_data.get("application_name"),
                    is_compliant=app_data.get("is_compliant", True),
                    issues=[
                        ComplianceIssue(**issue) for issue in app_data.get("issues", [])
                    ],
                    checked_fields=app_data.get("checked_fields", 0),
                    passed_fields=app_data.get("passed_fields", 0),
                )
                for app_id, app_data in compliance_validation.get(
                    "applications", {}
                ).items()
            },
            eol_status=[
                EOLStatusInfo(**eol)
                for eol in compliance_validation.get("eol_status", [])
            ],
            validated_at=compliance_validation.get("validated_at"),
        )

        return sanitize_for_json(response.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get compliance validation for flow {flow_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get compliance validation: {str(e)}",
        )


@router.get("/{flow_id}/eol-risks")
async def get_eol_risks(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Get End-of-Life risk summary for assessment flow.

    ADR-039: Provides a focused view of EOL risks across all applications
    in the assessment. Groups technologies by EOL status (expired, soon, active)
    and calculates risk metrics.

    Returns:
    - eol_expired: Technologies past EOL date (high risk)
    - eol_soon: Technologies within 12 months of EOL (medium risk)
    - active: Technologies with current support (low risk)
    - risk_score: Overall EOL risk score (0-100)
    """
    try:
        client_account_id = context.client_account_id
        engagement_id = context.engagement_id

        if not client_account_id or not engagement_id:
            raise HTTPException(
                status_code=400, detail="Client account ID and Engagement ID required"
            )

        # Query assessment flow with phase_results
        stmt = select(AssessmentFlow).where(
            AssessmentFlow.id == flow_id,
            AssessmentFlow.client_account_id == client_account_id,
            AssessmentFlow.engagement_id == engagement_id,
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Extract compliance data for EOL risks
        phase_results = flow.phase_results or {}
        arch_minimums = phase_results.get("architecture_minimums", {})
        compliance_validation = arch_minimums.get("compliance_validation", {})

        # Collect EOL risks from compliance validation
        eol_expired = []
        eol_soon = []
        active = []

        for eol_info in compliance_validation.get("eol_status", []):
            status = eol_info.get("status", "unknown")
            eol_item = {
                "product": eol_info.get("product", "Unknown"),
                "version": eol_info.get("version", "Unknown"),
                "eol_date": eol_info.get("eol_date"),
                "support_type": eol_info.get("support_type", "none"),
                "source": eol_info.get("source", "fallback_heuristics"),
            }

            if status == "eol_expired":
                eol_expired.append(eol_item)
            elif status == "eol_soon":
                eol_soon.append(eol_item)
            elif status == "active":
                active.append(eol_item)

        # Also collect version compliance issues as EOL-related risks
        for app_id, app_data in compliance_validation.get("applications", {}).items():
            for issue in app_data.get("issues", []):
                if issue.get("severity") in ("critical", "high"):
                    # Version below minimum is effectively an EOL risk
                    eol_expired.append(
                        {
                            "product": issue.get("field", "Unknown"),
                            "version": issue.get("current", "Unknown"),
                            "required_version": issue.get("required", "Unknown"),
                            "application_id": app_id,
                            "type": "version_compliance",
                        }
                    )

        # Calculate risk score
        # Each expired = 10 points, each soon = 5 points, max 100
        risk_score = min(100, len(eol_expired) * 10 + len(eol_soon) * 5)

        return sanitize_for_json(
            {
                "flow_id": flow_id,
                "eol_expired": eol_expired,
                "eol_expired_count": len(eol_expired),
                "eol_soon": eol_soon,
                "eol_soon_count": len(eol_soon),
                "active": active,
                "active_count": len(active),
                "risk_score": risk_score,
                "risk_level": (
                    "critical"
                    if risk_score >= 50
                    else (
                        "high"
                        if risk_score >= 30
                        else "medium" if risk_score >= 10 else "low"
                    )
                ),
                "total_technologies": len(eol_expired) + len(eol_soon) + len(active),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get EOL risks for flow {flow_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get EOL risks: {str(e)}",
        )
