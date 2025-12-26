"""
Data Validation Handlers for Unified Discovery

Provides endpoints for intelligent data profiling during the Data Validation phase.
Implements ADR-038: Multi-value detection, field length analysis, quality scoring.

Related: ADR-038, Issue #1204, Issue #1210
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import mask_id, safe_log_format

# REMOVED: Data import models
# from app.models.data_import.core import RawImportRecord
from app.models.discovery_flow import DiscoveryFlow
from app.services.crewai_flows.handlers.phase_executors.data_import_validation.data_profiler import (
    DataProfiler,
)
from app.utils.schema_constraints import get_asset_schema_constraints

from .data_validation_schemas import (
    DataProfileDecisionsRequest,
    DataProfileDecisionsResponse,
    DataProfileWrapper,
    LengthValidationResponse,
    MultiValueDetectionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_discovery_flow(
    flow_id: str,
    db: AsyncSession,
    context: RequestContext,
) -> DiscoveryFlow:
    """Get discovery flow with tenant scoping."""
    stmt = select(DiscoveryFlow).where(
        and_(
            DiscoveryFlow.flow_id == UUID(flow_id),
            DiscoveryFlow.client_account_id == context.client_account_id,
            DiscoveryFlow.engagement_id == context.engagement_id,
        )
    )
    result = await db.execute(stmt)
    discovery_flow = result.scalar_one_or_none()

    if not discovery_flow:
        raise HTTPException(status_code=404, detail="Discovery flow not found")

    if discovery_flow.status == "archived":
        raise HTTPException(status_code=400, detail="Cannot process archived flow")

    return discovery_flow


async def _get_raw_data_for_flow(
    data_import_id: UUID,
    db: AsyncSession,
    context: RequestContext,
) -> List[Dict[str, Any]]:
    """
    Fetch raw data records for a data import.

    Data import functionality removed - RawImportRecord model was removed.
    Returns empty list.
    """
    return []


@router.get("/flows/{flow_id}/data-profile")
async def get_data_profile(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> DataProfileWrapper:
    """
    Get comprehensive data profile for a discovery flow.

    This endpoint generates intelligent data analysis including:
    - Full dataset analysis (all records, not samples)
    - Multi-value detection (comma/semicolon/pipe-separated)
    - Field length analysis against schema constraints
    - Quality scoring (completeness, consistency, compliance)

    Returns a DataProfileWrapper with the full profile or error info.

    Related: ADR-038, Issue #1204
    """
    try:
        logger.info(
            safe_log_format(
                "[ADR-038] Getting data profile for flow {flow_id}",
                flow_id=mask_id(flow_id),
            )
        )

        # Get the discovery flow
        discovery_flow = await _get_discovery_flow(flow_id, db, context)

        # Check if data import exists
        if not discovery_flow.data_import_id:
            return DataProfileWrapper(
                success=False,
                flow_id=flow_id,
                error="No data import associated with this flow",
                message="Please complete the data import phase first",
            )

        # Fetch raw data records
        raw_data = await _get_raw_data_for_flow(
            discovery_flow.data_import_id, db, context
        )

        if not raw_data:
            return DataProfileWrapper(
                success=False,
                flow_id=flow_id,
                error="No raw data records found",
                message="The data import has no records to analyze",
            )

        logger.info(
            safe_log_format(
                "[ADR-038] Found {count} records for profiling",
                count=len(raw_data),
            )
        )

        # Get schema constraints for length validation
        schema_constraints = get_asset_schema_constraints()

        # Create profiler and generate report
        profiler = DataProfiler(raw_data)
        report = profiler.generate_profile_report(schema_constraints)

        logger.info(
            safe_log_format(
                "[ADR-038] Profile complete: {records} records, "
                "{critical} critical issues, {warnings} warnings",
                records=report.total_records,
                critical=len(report.critical_issues),
                warnings=len(report.warnings),
            )
        )

        # Convert report to response format
        profile_dict = report.to_dict()

        return DataProfileWrapper(
            success=True,
            flow_id=flow_id,
            data_profile=profile_dict,
            message="Data profile generated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "[ADR-038] Data profile failed: flow_id={flow_id}, error={error}",
                flow_id=mask_id(flow_id),
                error=str(e),
            ),
            exc_info=True,
        )
        return DataProfileWrapper(
            success=False,
            flow_id=flow_id,
            error=str(e),
            message="Failed to generate data profile",
        )


@router.post("/flows/{flow_id}/data-profile/decisions")
async def submit_data_profile_decisions(
    flow_id: str,
    request: DataProfileDecisionsRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> DataProfileDecisionsResponse:
    """
    Submit user decisions for handling data profile issues.

    Accepts decisions for each field with issues (split, truncate, skip, keep).
    Stores decisions in flow state for use during data cleansing phase.

    Related: ADR-038, Issue #1204
    """
    try:
        logger.info(
            safe_log_format(
                "[ADR-038] Submitting data profile decisions for flow {flow_id}",
                flow_id=mask_id(flow_id),
            )
        )

        # Get the discovery flow
        discovery_flow = await _get_discovery_flow(flow_id, db, context)

        # Validate decisions
        if not request.decisions:
            raise HTTPException(
                status_code=400,
                detail="At least one decision is required",
            )

        # Store decisions in flow state
        decisions_data = {
            "decisions": [d.model_dump() for d in request.decisions],
            "proceed_with_warnings": request.proceed_with_warnings,
        }

        # Update phase_state with decisions
        current_phase_state = discovery_flow.phase_state or {}
        current_phase_state["data_validation_decisions"] = decisions_data
        discovery_flow.phase_state = current_phase_state

        # Mark data validation as completed
        discovery_flow.data_validation_completed = True
        discovery_flow.current_phase = "field_mapping"

        await db.commit()

        logger.info(
            safe_log_format(
                "[ADR-038] Data profile decisions saved: {count} decisions",
                count=len(request.decisions),
            )
        )

        warnings = []
        if request.proceed_with_warnings:
            warnings.append("Proceeding with unresolved warnings as requested")

        return DataProfileDecisionsResponse(
            success=True,
            flow_id=flow_id,
            decisions_applied=len(request.decisions),
            message="Data validation decisions saved successfully",
            next_phase="field_mapping",
            warnings=warnings if warnings else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "[ADR-038] Submit decisions failed: flow_id={flow_id}, error={error}",
                flow_id=mask_id(flow_id),
                error=str(e),
            ),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save decisions: {str(e)}",
        )


@router.get("/flows/{flow_id}/multi-value-check")
async def check_multi_values(
    flow_id: str,
    field_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> MultiValueDetectionResponse:
    """
    Quick check for multi-valued fields without full profiling.

    Useful for field mapping preview to detect comma/semicolon/pipe-separated values.

    Args:
        flow_id: The discovery flow ID
        field_name: Optional specific field to check (checks all if not provided)

    Related: ADR-038, Issue #1206
    """
    try:
        logger.info(
            safe_log_format(
                "[ADR-038] Multi-value check for flow {flow_id}, field={field}",
                flow_id=mask_id(flow_id),
                field=field_name or "all",
            )
        )

        # Get the discovery flow
        discovery_flow = await _get_discovery_flow(flow_id, db, context)

        if not discovery_flow.data_import_id:
            return MultiValueDetectionResponse(
                success=False,
                flow_id=flow_id,
                results=[],
            )

        # Fetch raw data
        raw_data = await _get_raw_data_for_flow(
            discovery_flow.data_import_id, db, context
        )

        if not raw_data:
            return MultiValueDetectionResponse(
                success=True,
                flow_id=flow_id,
                results=[],
            )

        # Run multi-value detection
        profiler = DataProfiler(raw_data)
        results = profiler.detect_multi_values(field_name)

        return MultiValueDetectionResponse(
            success=True,
            flow_id=flow_id,
            results=[r.to_dict() for r in results],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "[ADR-038] Multi-value check failed: flow_id={flow_id}, error={error}",
                flow_id=mask_id(flow_id),
                error=str(e),
            ),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Multi-value check failed: {str(e)}",
        )


@router.get("/flows/{flow_id}/length-check")
async def check_field_lengths(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> LengthValidationResponse:
    """
    Quick check for field length violations without full profiling.

    Validates field values against Asset model schema constraints.

    Related: ADR-038, Issue #1208
    """
    try:
        logger.info(
            safe_log_format(
                "[ADR-038] Length check for flow {flow_id}",
                flow_id=mask_id(flow_id),
            )
        )

        # Get the discovery flow
        discovery_flow = await _get_discovery_flow(flow_id, db, context)

        if not discovery_flow.data_import_id:
            return LengthValidationResponse(
                success=False,
                flow_id=flow_id,
                violations=[],
                total_violations=0,
            )

        # Fetch raw data
        raw_data = await _get_raw_data_for_flow(
            discovery_flow.data_import_id, db, context
        )

        if not raw_data:
            return LengthValidationResponse(
                success=True,
                flow_id=flow_id,
                violations=[],
                total_violations=0,
            )

        # Get schema constraints
        schema_constraints = get_asset_schema_constraints()

        # Run length validation
        profiler = DataProfiler(raw_data)
        violations = profiler.check_field_length_violations(schema_constraints)

        return LengthValidationResponse(
            success=True,
            flow_id=flow_id,
            violations=[v.to_dict() for v in violations],
            total_violations=len(violations),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "[ADR-038] Length check failed: flow_id={flow_id}, error={error}",
                flow_id=mask_id(flow_id),
                error=str(e),
            ),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Length check failed: {str(e)}",
        )


@router.post("/flows/{flow_id}/data-validation/complete")
async def mark_data_validation_complete(
    flow_id: str,
    request: dict = Body(default={}),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> dict:
    """
    Mark data validation phase as complete without decisions.

    Used when there are no critical issues and user wants to proceed.
    Optionally accepts acknowledgement of warnings.

    Related: ADR-038
    """
    try:
        logger.info(
            safe_log_format(
                "[ADR-038] Marking data validation complete for flow {flow_id}",
                flow_id=mask_id(flow_id),
            )
        )

        # Get the discovery flow
        discovery_flow = await _get_discovery_flow(flow_id, db, context)

        # CC FIX: Check for blocking issues before allowing completion (Qodo suggestion)
        # Prevents users from bypassing critical data issues
        if discovery_flow.data_import_id:
            raw_data = await _get_raw_data_for_flow(
                discovery_flow.data_import_id, db, context
            )
            if raw_data:
                profiler = DataProfiler(raw_data)
                schema_constraints = get_asset_schema_constraints()
                violations = profiler.check_field_length_violations(schema_constraints)
                if violations:
                    logger.warning(
                        safe_log_format(
                            "[ADR-038] Blocking completion due to {count} critical issues",
                            count=len(violations),
                        )
                    )
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot complete validation. Critical issues found that require user decisions.",
                    )

        # Update phase state
        acknowledge_warnings = request.get("acknowledge_warnings", False)
        current_phase_state = discovery_flow.phase_state or {}
        current_phase_state["data_validation_decisions"] = {
            "decisions": [],
            "acknowledge_warnings": acknowledge_warnings,
            "completed_without_issues": True,
        }
        discovery_flow.phase_state = current_phase_state

        # Mark as completed
        discovery_flow.data_validation_completed = True
        discovery_flow.current_phase = "field_mapping"

        await db.commit()

        return {
            "success": True,
            "flow_id": flow_id,
            "message": "Data validation phase completed",
            "next_phase": "field_mapping",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "[ADR-038] Mark complete failed: flow_id={flow_id}, error={error}",
                flow_id=mask_id(flow_id),
                error=str(e),
            ),
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to mark validation complete: {str(e)}",
        )
