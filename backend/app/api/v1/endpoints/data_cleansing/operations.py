"""
Data Cleansing API - Operations Module
Core data cleansing operations including analysis, stats, and triggering.
"""

import logging

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.client_account import User
from app.models.data_import.core import DataImport
from app.models.data_import.mapping import ImportFieldMapping
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

from .base import (
    router,
    DataCleansingAnalysis,
    DataCleansingStats,
)
from .validation import _validate_and_get_flow, _get_data_import_for_flow
from .analysis import _perform_data_cleansing_analysis

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
            f"📊 READ-ONLY: Getting data cleansing analysis for flow {flow_id} (should not modify flow status)"
        )

        # Get flow repository with proper context
        flow_repo = DiscoveryFlowRepository(
            db, context.client_account_id, context.engagement_id
        )

        # Verify flow exists and user has access (READ-ONLY check)
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
            logger.error(f"❌ Failed to retrieve flow {flow_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to access flow: {str(e)}",
            )

        # Log current flow status for debugging
        logger.info(
            f"🔍 Flow {flow_id} current status: {flow.status} (before data lookup)"
        )

        # Important: We are only READING data, not executing any agents
        # This endpoint should never modify flow status or trigger execution

        # Get data import for this flow using the same logic as import storage handler
        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

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
                    select(DataImport)
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
        analysis_result = await _perform_data_cleansing_analysis(
            flow_id=flow_id,
            data_imports=data_imports,
            field_mappings=field_mappings,
            include_details=include_details,
            db_session=db,
        )

        logger.info(f"✅ Data cleansing analysis completed for flow {flow_id}")
        return analysis_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Failed to get data cleansing analysis for flow {flow_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data cleansing analysis: {str(e)}",
        )


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
        from sqlalchemy import func
        from app.models.data_import.core import RawImportRecord

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
        except Exception as e:
            logger.warning(
                f"Failed to get actual record count: {e}, using total_records field"
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
        logger.error(
            f"❌ Failed to get data cleansing stats for flow {flow_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data cleansing stats: {str(e)}",
        )
