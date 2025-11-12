"""
Data Cleansing API - Operations Module
Core data cleansing operations including analysis, stats, and triggering.
"""

import logging
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.client_account import User
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.data_cleansing import (
    DataCleansingRecommendation as DBRecommendation,
)
from app.models.data_import.core import DataImport, RawImportRecord
from app.models.data_import.mapping import ImportFieldMapping
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

from .base import (
    DataCleansingAnalysis,
    DataCleansingStats,
    ResolveQualityIssueRequest,
    ResolveQualityIssueResponse,
    ApplyRecommendationRequest,
    ApplyRecommendationResponse,
)
from .validation import _validate_and_get_flow, _get_data_import_for_flow
from .analysis import _perform_data_cleansing_analysis
from .resolution_operations import router as resolution_router
from .suggestion_operations import router as suggestion_router
from app.api.v1.api_tags import APITags

# Create operations router
router = APIRouter()

# Include sub-routers
router.include_router(resolution_router, tags=[APITags.DATA_CLEANSING_RESOLUTION])
router.include_router(suggestion_router, tags=[APITags.DATA_CLEANSING_SUGGESTIONS])

logger = logging.getLogger(__name__)


@router.get(
    "/flows/{flow_id}/data-cleansing",
    response_model=DataCleansingAnalysis,
    summary="Get data cleansing analysis for a flow",
)
async def get_data_cleansing_analysis(
    flow_id: str,
    include_details: bool = Query(
        True, description="Include detailed issues and recommendations"
    ),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
) -> DataCleansingAnalysis:
    """
    Get comprehensive data cleansing analysis for a discovery flow.

    Returns quality issues, recommendations, and field-level analysis.
    This is a READ-ONLY operation that should NOT trigger any agent execution
    or modify flow status.
    """
    try:
        logger.info(
            f"Getting data cleansing analysis for flow {flow_id} (include_details={include_details})"
        )

        # Get flow repository with proper context
        # Per ADR-012: Use child flow (DiscoveryFlow) for operational decisions
        flow_repo = DiscoveryFlowRepository(
            db, context.client_account_id, context.engagement_id
        )

        # Verify flow exists and user has access (READ-ONLY check)
        # Returns DiscoveryFlow (child flow) - per ADR-012 for operational state
        try:
            flow = await flow_repo.get_by_flow_id(flow_id)
            if not flow:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Flow {flow_id} not found",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Failed to retrieve flow")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to access flow: {str(e)}",
            ) from e

        # Log current flow status for debugging
        # Per ADR-012: flow.status is child flow operational status (not master flow)
        logger.info(
            f"🔍 Flow {flow_id} current status: {flow.status} (before data lookup)"
        )

        # Important: We are only READING data, not executing any agents
        # This endpoint should never modify flow status or trigger execution

        # Get data import for this flow using the same logic as import storage handler
        # First try to get data import via discovery flow's data_import_id
        data_import = None
        if flow.data_import_id:
            data_import_query = select(DataImport).where(
                DataImport.id == flow.data_import_id
            )
            data_import_result = await db.execute(data_import_query)
            data_import = data_import_result.scalar_one_or_none()

        # If not found, try master flow ID lookup (same as import storage handler)
        if not data_import:
            logger.info(
                f"Flow {flow_id} has no data_import_id, trying master flow ID lookup"
            )

            # Get the database ID for this flow_id (FK references id, not flow_id)
            db_id_query = select(CrewAIFlowStateExtensions.id).where(
                CrewAIFlowStateExtensions.flow_id == flow_id
            )
            db_id_result = await db.execute(db_id_query)
            flow_db_id = db_id_result.scalar_one_or_none()

            if flow_db_id:
                # Look for data imports with this master_flow_id
                import_query = (
                    select(
                        DataImport
                    )  # SKIP_TENANT_CHECK - master_flow_id FK enforces isolation
                    .where(DataImport.master_flow_id == flow_db_id)
                    .order_by(DataImport.created_at.desc())
                    .limit(1)
                )

                import_result = await db.execute(import_query)
                data_import = import_result.scalar_one_or_none()

                if data_import:
                    logger.info(
                        f"✅ Found data import via master flow ID lookup: {data_import.id}"
                    )

        if not data_import:
            # Return empty analysis when no data import exists
            logger.warning(
                f"No data import found for flow {flow_id}, returning empty analysis"
            )
            return DataCleansingAnalysis(
                flow_id=flow_id,
                analysis_timestamp="",
                total_records=0,
                total_fields=0,
                quality_score=0.0,
                issues_count=0,
                recommendations_count=0,
                quality_issues=[],
                recommendations=[],
                field_quality_scores={},
                processing_status="no_data",
                source="empty",
            )

        data_imports = [
            data_import
        ]  # Convert to list for compatibility with existing code

        # Get field mappings
        field_mapping_query = select(ImportFieldMapping).where(
            ImportFieldMapping.data_import_id == data_imports[0].id
        )
        field_mapping_result = await db.execute(field_mapping_query)
        field_mappings = field_mapping_result.scalars().all()

        # Perform data cleansing analysis
        logger.info(f"Starting data cleansing analysis for flow {flow_id}")
        analysis_result = await _perform_data_cleansing_analysis(
            flow_id=flow_id,
            data_imports=data_imports,
            field_mappings=field_mappings,
            include_details=include_details,
            db_session=db,
        )

        logger.info(f"Data cleansing analysis completed for flow {flow_id}")
        logger.info(
            f"Analysis result: {len(analysis_result.quality_issues)} quality issues returned"
        )

        return analysis_result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get data cleansing analysis")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data cleansing analysis: {str(e)}",
        ) from e


@router.get(
    "/flows/{flow_id}/data-cleansing/stats",
    response_model=DataCleansingStats,
    summary="Get data cleansing statistics",
)
async def get_data_cleansing_stats(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
) -> DataCleansingStats:
    """Get basic data cleansing statistics for a flow."""
    try:
        logger.info(f"Getting data cleansing stats for flow {flow_id}")

        # Get flow repository with proper context
        flow_repo = DiscoveryFlowRepository(
            db, context.client_account_id, context.engagement_id
        )

        # Verify flow exists
        flow = await _validate_and_get_flow(flow_id, flow_repo)

        # Get data import for this flow
        data_import = await _get_data_import_for_flow(flow_id, flow, db)

        if not data_import:
            # Return empty stats if no data
            return DataCleansingStats(
                total_records=0,
                clean_records=0,
                records_with_issues=0,
                issues_by_severity={"low": 0, "medium": 0, "high": 0, "critical": 0},
                completion_percentage=0.0,
            )

        data_imports = [
            data_import
        ]  # Convert to list for compatibility with existing code

        # Calculate stats from first data import
        data_import = data_imports[0]

        # Get actual count of raw import records from the database
        total_records = 0
        try:
            count_query = select(func.count(RawImportRecord.id)).where(
                RawImportRecord.data_import_id == data_import.id
            )
            count_result = await db.execute(count_query)
            actual_count = count_result.scalar() or 0

            # Use the actual count if available, otherwise fall back to total_records field
            total_records = (
                actual_count if actual_count > 0 else (data_import.total_records or 0)
            )

            logger.info(
                f"📊 Stats - Data import {data_import.id}: actual_count={actual_count}, "
                f"total_records field={data_import.total_records}, using={total_records}"
            )
        except Exception:
            logger.exception(
                "Failed to get actual record count, using total_records field"
            )
            total_records = (
                data_import.total_records if data_import.total_records else 0
            )

        # For now, return basic calculated stats
        # TODO: Integrate with actual data cleansing crew results
        clean_records = int(total_records * 0.85)  # Estimate 85% clean
        records_with_issues = total_records - clean_records

        return DataCleansingStats(
            total_records=total_records,
            clean_records=clean_records,
            records_with_issues=records_with_issues,
            issues_by_severity={
                "low": int(records_with_issues * 0.4),
                "medium": int(records_with_issues * 0.3),
                "high": int(records_with_issues * 0.2),
                "critical": int(records_with_issues * 0.1),
            },
            completion_percentage=85.0,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get data cleansing stats")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data cleansing stats: {str(e)}",
        ) from e


@router.patch(
    "/flows/{flow_id}/data-cleansing/quality-issues/{issue_id}",
    response_model=ResolveQualityIssueResponse,
    summary="Resolve or ignore a quality issue",
    tags=[APITags.DATA_CLEANSING_OPERATIONS],
)
async def resolve_quality_issue(
    flow_id: str,
    issue_id: str,
    resolution: ResolveQualityIssueRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
) -> ResolveQualityIssueResponse:
    """
    Resolve or ignore a data quality issue.

    This endpoint stores the resolution in the flow's data_cleansing_results field
    with audit trail information (user_id, timestamp, resolution status).
    """
    try:
        logger.info(
            f"Resolving quality issue {issue_id} for flow {flow_id} with status: {resolution.status}"
        )

        # Validate resolution status
        if resolution.status not in ["resolved", "ignored"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resolution status: {resolution.status}. Must be 'resolved' or 'ignored'",
            )

        # Get flow repository with proper context
        flow_repo = DiscoveryFlowRepository(
            db, context.client_account_id, context.engagement_id
        )

        # Verify flow exists and user has access
        # Per ADR-012: Returns DiscoveryFlow (child flow) for operational decisions
        flow = await _validate_and_get_flow(flow_id, flow_repo)

        # Per ADR-012: flow.status is child flow operational status
        logger.info(f"Flow {flow_id} found: {flow.flow_name} (status: {flow.status})")

        # Prepare resolution data with audit trail
        resolved_at = datetime.utcnow().isoformat()
        resolution_data = {
            "issue_id": issue_id,
            "status": resolution.status,
            "resolved_at": resolved_at,
            "resolved_by_user_id": str(current_user.id),
            "client_account_id": str(context.client_account_id),
            "engagement_id": str(context.engagement_id),
            "resolution_notes": resolution.resolution_notes,
        }

        # Get existing data_cleansing_results or initialize
        # Per ADR-012: Store operational state in child flow's crewai_state_data
        existing_data = flow.crewai_state_data or {}
        data_cleansing_results = existing_data.get("data_cleansing_results", {})

        # Store resolution in resolutions dict keyed by issue_id
        if "resolutions" not in data_cleansing_results:
            data_cleansing_results["resolutions"] = {}

        data_cleansing_results["resolutions"][issue_id] = resolution_data

        logger.info(f"Stored resolution for issue {issue_id}: {resolution_data}")
        logger.info(
            f"Total resolutions stored: {len(data_cleansing_results['resolutions'])}"
        )

        # Update flow with new data_cleansing_results
        existing_data["data_cleansing_results"] = data_cleansing_results
        flow.crewai_state_data = existing_data

        # Ensure SQLAlchemy detects the JSONB field change
        flag_modified(flow, "crewai_state_data")

        # Ensure the flow object is properly tracked by the session
        db.add(flow)

        logger.info(
            f"Updating flow {flow_id} with resolution data for issue {issue_id}"
        )

        # Commit changes to database
        await db.commit()
        await db.refresh(flow)

        logger.info(f"Database commit successful for flow {flow_id}")

        logger.info(
            f"Quality issue {issue_id} resolved with status '{resolution.status}' for flow {flow_id}"
        )

        return ResolveQualityIssueResponse(
            success=True,
            message=f"Quality issue {resolution.status} successfully",
            issue_id=issue_id,
            resolution_status=resolution.status,
            resolved_at=resolved_at,
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Failed to resolve quality issue")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve quality issue: {str(e)}",
        ) from e


@router.patch(
    "/flows/{flow_id}/data-cleansing/recommendations/{recommendation_id}",
    response_model=ApplyRecommendationResponse,
    summary="Apply or reject a cleansing recommendation",
    tags=[APITags.DATA_CLEANSING_OPERATIONS],
)
async def apply_recommendation(
    flow_id: str,
    recommendation_id: str,
    request: ApplyRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
) -> ApplyRecommendationResponse:
    """
    Apply or reject a data cleansing recommendation.

    This endpoint stores the action in the flow's data_cleansing_results field
    with audit trail information (user_id, timestamp, action status).
    """
    try:
        logger.info(
            f"Processing recommendation {recommendation_id} for flow {flow_id} with action: {request.action}"
        )

        # Validate action
        if request.action not in ["apply", "reject"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {request.action}. Must be 'apply' or 'reject'",
            )

        # Get flow repository with proper context
        flow_repo = DiscoveryFlowRepository(
            db, context.client_account_id, context.engagement_id
        )

        # Verify flow exists and user has access
        # Per ADR-012: Returns DiscoveryFlow (child flow) for operational decisions
        flow = await _validate_and_get_flow(flow_id, flow_repo)

        # Per ADR-012: flow.status is child flow operational status
        logger.info(f"Flow {flow_id} found: {flow.flow_name} (status: {flow.status})")

        # Prepare action data with audit trail
        # Use timezone-aware datetime object for database storage, ISO string for JSONB fallback
        applied_at_datetime = datetime.now(timezone.utc)
        applied_at_iso = applied_at_datetime.isoformat()  # For JSONB fallback
        action_status = "applied" if request.action == "apply" else "rejected"

        # Update recommendation in database (with graceful fallback for legacy IDs)
        # Per ADR-012, we maintain backward compatibility for operational state
        # Legacy flows use deterministic UUID5-based IDs that may not exist in the new table
        db_rec = None
        try:
            # Try to convert recommendation_id to UUID (non-blocking for backward compatibility)
            recommendation_uuid = None
            try:
                recommendation_uuid = uuid.UUID(recommendation_id)
            except ValueError:
                # Not a valid UUID - skip database lookup and fall back to JSONB storage
                logger.info(
                    f"Recommendation ID {recommendation_id} is not a valid UUID. "
                    f"Falling back to JSONB storage for backward compatibility."
                )
                recommendation_uuid = None

            # Only try database lookup if we have a valid UUID
            if recommendation_uuid is not None:
                try:
                    # Find the recommendation in database
                    rec_query = select(DBRecommendation).where(
                        DBRecommendation.id == recommendation_uuid,
                        DBRecommendation.flow_id == flow.flow_id,
                    )
                    rec_result = await db.execute(rec_query)
                    db_rec = rec_result.scalar_one_or_none()

                    if db_rec:
                        # Found in database - update it
                        db_rec.status = action_status
                        db_rec.action_notes = request.notes
                        db_rec.applied_by_user_id = str(current_user.id)
                        db_rec.applied_at = (
                            applied_at_datetime  # Use datetime object for database
                        )

                        logger.info(
                            f"Updating recommendation {recommendation_id} "
                            f"with action '{request.action}' for flow {flow_id}"
                        )

                        # Commit changes to database
                        await db.commit()
                        await db.refresh(db_rec)
                    else:
                        # Valid UUID but not found in database - fall back to JSONB for legacy flows
                        logger.info(
                            f"Recommendation {recommendation_id} (valid UUID) not found in database. "
                            f"Falling back to JSONB storage for legacy flow compatibility."
                        )
                        db_rec = None  # Ensure we fall through to JSONB storage

                except Exception as db_error:
                    # Check if the error is due to table not existing
                    error_msg = str(db_error)
                    if (
                        "does not exist" in error_msg
                        or "UndefinedTableError" in error_msg
                    ):
                        # Table doesn't exist - fall back to legacy storage
                        logger.warning(
                            f"Recommendation table does not exist. "
                            f"Falling back to crewai_state_data storage for recommendation {recommendation_id}"
                        )
                        db_rec = None  # Ensure we fall through to JSONB storage
                    else:
                        # Re-raise if it's a different error
                        logger.exception("Database error during recommendation lookup")
                        raise RuntimeError(
                            "Database error during recommendation lookup"
                        ) from db_error

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception:
            # If database operation fails for other reasons, log and fall back to JSONB
            logger.exception(
                f"Failed to update recommendation in database. "
                f"Falling back to JSONB storage for recommendation {recommendation_id}"
            )
            db_rec = None  # Ensure we fall through to JSONB storage

        # If database lookup failed or recommendation not found, fall back to JSONB storage
        # This maintains backward compatibility for legacy flows with deterministic IDs
        if db_rec is None:
            logger.info(
                f"Storing recommendation action in JSONB (fallback) for recommendation {recommendation_id}"
            )
            # Fall back to legacy storage method
            # Per ADR-012: Store operational state in child flow's crewai_state_data
            existing_data = flow.crewai_state_data or {}
            data_cleansing_results = existing_data.get("data_cleansing_results", {})

            if "recommendation_actions" not in data_cleansing_results:
                data_cleansing_results["recommendation_actions"] = {}

            action_data = {
                "recommendation_id": recommendation_id,
                "action": request.action,
                "status": action_status,
                "applied_at": applied_at_iso,  # Use ISO string for JSONB storage
                "applied_by_user_id": str(current_user.id),
                "client_account_id": str(context.client_account_id),
                "engagement_id": str(context.engagement_id),
                "notes": request.notes,
            }

            data_cleansing_results["recommendation_actions"][
                recommendation_id
            ] = action_data

            # Update flow with new data_cleansing_results
            existing_data["data_cleansing_results"] = data_cleansing_results
            flow.crewai_state_data = existing_data

            # Ensure SQLAlchemy detects the JSONB field change
            flag_modified(flow, "crewai_state_data")
            db.add(flow)

            await db.commit()
            await db.refresh(flow)

            logger.info(
                f"Stored recommendation action in crewai_state_data (fallback) "
                f"for recommendation {recommendation_id}"
            )

        logger.info(f"Database commit successful for flow {flow_id}")

        logger.info(
            f"Recommendation {recommendation_id} {request.action}ed successfully for flow {flow_id}"
        )

        return ApplyRecommendationResponse(
            success=True,
            message=f"Recommendation {action_status} successfully",
            recommendation_id=recommendation_id,
            action=request.action,
            applied_at=applied_at_iso,  # Return ISO string for API response
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Failed to process recommendation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to {request.action} recommendation: {str(e)}",
        ) from e
