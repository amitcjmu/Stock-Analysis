"""
Compliance validation POST endpoints

Mutation endpoints for refreshing/updating compliance validation.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.core.seed_data.assessment_standards import validate_technology_compliance
from app.models.assessment_flow import AssessmentFlow
from app.utils.json_sanitization import sanitize_for_json

from .schemas import (
    ApplicationComplianceResult,
    ComplianceIssue,
    ComplianceValidationResponse,
)
from .utils import _get_default_standards

# Router will be imported from parent package
from .. import router as router_local

logger = logging.getLogger(__name__)


@router_local.post(
    "/{flow_id}/compliance/refresh", response_model=ComplianceValidationResponse
)
async def refresh_compliance_validation(  # noqa: C901
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> Dict[str, Any]:
    """
    Manually refresh compliance validation for assessment flow.

    ADR-039: This endpoint allows triggering compliance validation for flows
    that were created before the architecture_minimums phase was added, or
    to re-run validation after technology stack data has been updated.

    Process:
    1. Load assessment flow and selected applications
    2. Fetch engagement standards (or use defaults)
    3. Validate each application's technology stack
    4. Persist results to phase_results["architecture_minimums"]
    5. Return updated compliance data
    """
    try:
        client_account_id = context.client_account_id
        engagement_id = context.engagement_id

        if not client_account_id or not engagement_id:
            raise HTTPException(
                status_code=400, detail="Client account ID and Engagement ID required"
            )

        # Query assessment flow
        stmt = select(AssessmentFlow).where(
            AssessmentFlow.id == flow_id,
            AssessmentFlow.client_account_id == client_account_id,
            AssessmentFlow.engagement_id == engagement_id,
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Get selected applications from flow - use direct column or runtime_state
        selected_app_ids = flow.selected_application_ids or []

        if not selected_app_ids:
            # Try selected_asset_ids (new semantic field)
            selected_app_ids = flow.selected_asset_ids or []

        if not selected_app_ids:
            # Try runtime_state as fallback
            runtime_state = flow.runtime_state or {}
            selected_app_ids = runtime_state.get("selected_application_ids", [])

        # Deduplicate IDs to handle data quality issues (same ID repeated)
        # Use dict.fromkeys to preserve order while deduplicating
        original_count = len(selected_app_ids)
        selected_app_ids = list(dict.fromkeys(str(aid) for aid in selected_app_ids))
        if len(selected_app_ids) != original_count:
            logger.warning(
                f"Deduplicated selected_app_ids: {original_count} -> {len(selected_app_ids)} unique IDs"
            )

        logger.info(
            f"Refreshing compliance for flow {flow_id} with {len(selected_app_ids)} unique applications"
        )

        # Get engagement standards (use defaults if not configured)
        engagement_standards = _get_default_standards()

        # Get application/asset data directly from the Asset table
        from app.models.asset import Asset

        applications = []

        if selected_app_ids:
            # Query assets directly using their IDs
            for app_id in selected_app_ids:
                try:
                    asset_stmt = select(Asset).where(
                        Asset.id == app_id,
                        Asset.client_account_id == client_account_id,
                        Asset.engagement_id == engagement_id,
                    )
                    asset_result = await db.execute(asset_stmt)
                    asset = asset_result.scalar_one_or_none()

                    if asset:
                        # Parse technology_stack - it can be a string or JSON
                        tech_stack = {}
                        if asset.technology_stack:
                            if isinstance(asset.technology_stack, str):
                                # Try to parse as JSON, otherwise use as-is
                                try:
                                    import json

                                    tech_stack = json.loads(asset.technology_stack)
                                except (json.JSONDecodeError, TypeError):
                                    # Use as simple string mapping
                                    tech_stack = {"primary": asset.technology_stack}
                            elif isinstance(asset.technology_stack, dict):
                                tech_stack = asset.technology_stack

                        applications.append(
                            {
                                "id": str(app_id),
                                "application_name": asset.application_name
                                or asset.name
                                or f"Asset {str(app_id)[:8]}",
                                "technology_stack": tech_stack,
                            }
                        )
                    else:
                        # Asset not found, use placeholder
                        applications.append(
                            {
                                "id": str(app_id),
                                "application_name": f"Application {str(app_id)[:8]}",
                                "technology_stack": {},
                            }
                        )
                except Exception as asset_err:
                    logger.warning(f"Failed to fetch asset {app_id}: {asset_err}")
                    applications.append(
                        {
                            "id": str(app_id),
                            "application_name": f"Application {str(app_id)[:8]}",
                            "technology_stack": {},
                        }
                    )

        # If no selected apps, still return empty results gracefully
        if not applications and not selected_app_ids:
            logger.info("No applications selected for compliance validation")

        # Validate each application's technology stack
        app_compliance_results = {}
        overall_compliant = True

        for app in applications:
            app_id = str(app.get("id") or app.get("application_id", "unknown"))
            app_name = app.get("application_name") or app.get("name", "Unknown")
            tech_stack = app.get("technology_stack", {})

            # Convert list to dict if needed
            if isinstance(tech_stack, list):
                tech_stack = {t: "unknown" for t in tech_stack}

            # Validate technology compliance
            compliance_result = validate_technology_compliance(
                technology_stack=tech_stack,
                engagement_standards=engagement_standards,
            )

            app_compliance_results[app_id] = {
                "application_name": app_name,
                "is_compliant": compliance_result.get("compliant", True),
                "issues": compliance_result.get("issues", []),
                "checked_fields": compliance_result.get("checked_fields", 0),
                "passed_fields": compliance_result.get("passed_fields", 0),
            }

            if not compliance_result.get("compliant", True):
                overall_compliant = False

        # Build compliance validation structure - calculate from actual results
        # Use len(app_compliance_results) as total to ensure consistency with detail data
        total_apps = len(app_compliance_results)
        compliant_count = sum(
            1 for r in app_compliance_results.values() if r.get("is_compliant", True)
        )
        non_compliant_count = sum(
            1
            for r in app_compliance_results.values()
            if not r.get("is_compliant", True)
        )

        # Normalize engagement_standards to dict format for response
        # Input can be either a list (from TECH_VERSION_STANDARDS) or dict (from DB)
        if isinstance(engagement_standards, dict):
            # Already a dict - use as-is
            standards_dict = engagement_standards
        elif isinstance(engagement_standards, list):
            # Convert list to dict - each standard has requirement_type as key
            standards_dict = {
                std.get("requirement_type", f"standard_{i}"): std
                for i, std in enumerate(engagement_standards)
                if isinstance(std, dict)
            }
        else:
            # Fallback for unexpected types
            standards_dict = {}

        compliance_validation = {
            "overall_compliant": overall_compliant,
            "standards_applied": standards_dict,
            "summary": {
                "total_applications": total_apps,
                "compliant_count": compliant_count,
                "non_compliant_count": non_compliant_count,
            },
            "applications": app_compliance_results,
            "eol_status": [],  # TODO: Populate from EOL data service
            "validated_at": datetime.utcnow().isoformat(),
        }

        # Update phase_results with compliance data
        phase_results = flow.phase_results or {}
        phase_results["architecture_minimums"] = {
            "engagement_standards": engagement_standards,
            "compliance_validation": compliance_validation,
            "validated_at": datetime.utcnow().isoformat(),
        }

        # Persist to database
        # For SQLAlchemy to detect JSONB changes, we must flag the field as modified
        flow.phase_results = phase_results
        flag_modified(flow, "phase_results")
        await db.commit()
        await db.refresh(flow)

        logger.info(
            f"Compliance refresh completed for flow {flow_id}: "
            f"{compliant_count}/{total_apps} compliant"
        )

        # Build response
        response = ComplianceValidationResponse(
            flow_id=flow_id,
            standards_applied=compliance_validation.get("standards_applied", {}),
            summary=compliance_validation.get("summary", {}),
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
                for app_id, app_data in app_compliance_results.items()
            },
            eol_status=[],
            validated_at=compliance_validation.get("validated_at"),
        )

        return sanitize_for_json(response.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to refresh compliance validation for flow {flow_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh compliance validation: {str(e)}",
        )
