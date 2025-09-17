"""
Data Cleansing API - Triggers Module
Trigger functionality for data cleansing analysis execution.
"""

import logging

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.client_account import User
from app.models.data_import.mapping import ImportFieldMapping
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

from .base import router, TriggerDataCleansingRequest, DataCleansingAnalysis
from .validation import _validate_and_get_flow, _get_data_import_for_flow
from .analysis import _perform_data_cleansing_analysis

logger = logging.getLogger(__name__)


@router.post(
    "/flows/{flow_id}/data-cleansing/trigger",
    response_model=DataCleansingAnalysis,
    summary="Trigger data cleansing analysis for a flow",
)
async def trigger_data_cleansing_analysis(
    flow_id: str,
    request: TriggerDataCleansingRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
) -> DataCleansingAnalysis:
    """
    Trigger data cleansing analysis for a discovery flow.

    This endpoint actually executes the data cleansing phase using CrewAI agents
    to analyze data quality and provide recommendations.
    """
    try:
        logger.info(f"🚀 TRIGGERING data cleansing analysis for flow {flow_id}")

        # Get flow repository with proper context
        flow_repo = DiscoveryFlowRepository(
            db, context.client_account_id, context.engagement_id
        )

        # Verify flow exists and user has access
        flow = await _validate_and_get_flow(flow_id, flow_repo)

        logger.info(f"🔍 Flow {flow_id} current status: {flow.status}")

        # Import the MasterFlowOrchestrator to execute the data cleansing phase
        try:
            from app.services.master_flow_orchestrator import MasterFlowOrchestrator

            flow_orchestrator = MasterFlowOrchestrator(db, context)

            # Execute the data cleansing phase using the orchestrator
            logger.info(f"🤖 Executing data cleansing phase for flow {flow_id}")

            # Get data_import_id from the flow
            phase_input = {
                "force_refresh": request.force_refresh,
                "include_agent_analysis": request.include_agent_analysis,
            }

            # Add data_import_id if available
            if flow.data_import_id:
                phase_input["data_import_id"] = str(flow.data_import_id)
                logger.info(
                    f"📋 Adding data_import_id to phase_input: {flow.data_import_id}"
                )

            execution_result = await flow_orchestrator.execute_phase(
                flow_id=flow_id,
                phase_name="data_cleansing",
                phase_input=phase_input,
            )

            logger.info(
                f"✅ Data cleansing phase execution completed: {execution_result.get('status', 'unknown')}"
            )

            # If execution was successful, get the updated analysis
            if execution_result.get("status") in ("success", "completed"):
                data_import = await _get_data_import_for_flow(flow_id, flow, db)

                if not data_import:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"No data import found for flow {flow_id}",
                    )

                data_imports = [data_import]

                # Get field mappings
                field_mapping_query = select(ImportFieldMapping).where(
                    ImportFieldMapping.data_import_id == data_imports[0].id
                )
                field_mapping_result = await db.execute(field_mapping_query)
                field_mappings = field_mapping_result.scalars().all()

                # Perform data cleansing analysis with agent results
                analysis_result = await _perform_data_cleansing_analysis(
                    flow_id=flow_id,
                    data_imports=data_imports,
                    field_mappings=field_mappings,
                )

                logger.info(f"✅ Data cleansing analysis completed for flow {flow_id}")

                return analysis_result
            else:
                # Execution failed, but still return analysis with error status
                logger.warning(
                    f"⚠️ Data cleansing execution failed: {execution_result.get('error', 'Unknown error')}"
                )

                # Return a basic analysis indicating the execution failed
                from datetime import datetime

                return DataCleansingAnalysis(
                    flow_id=flow_id,
                    analysis_timestamp=datetime.utcnow().isoformat(),
                    total_records=0,
                    total_fields=0,
                    quality_score=0.0,
                    issues_count=0,
                    recommendations_count=0,
                    quality_issues=[],
                    recommendations=[],
                    field_quality_scores={},
                    processing_status=f"failed: {execution_result.get('error', 'Unknown error')}",
                    source="agent_failed",
                )

        except ImportError as e:
            logger.error(f"❌ CrewAI service not available: {e}")

            # Return analysis without agent execution instead of HTTP 503
            from datetime import datetime

            # Get data import for basic analysis
            data_import = await _get_data_import_for_flow(flow_id, flow, db)

            if data_import:
                data_imports = [data_import]
                field_mapping_query = select(ImportFieldMapping).where(
                    ImportFieldMapping.data_import_id == data_imports[0].id
                )
                field_mapping_result = await db.execute(field_mapping_query)
                field_mappings = field_mapping_result.scalars().all()

                # Perform basic analysis without agent execution
                analysis_result = await _perform_data_cleansing_analysis(
                    flow_id=flow_id,
                    data_imports=data_imports,
                    field_mappings=field_mappings,
                    include_details=True,
                    db_session=db,
                )
                analysis_result.processing_status = "completed_without_agents"
                analysis_result.source = "fallback"
                return analysis_result
            else:
                # Return basic analysis indicating service unavailable
                return DataCleansingAnalysis(
                    flow_id=flow_id,
                    analysis_timestamp=datetime.utcnow().isoformat(),
                    total_records=0,
                    total_fields=0,
                    quality_score=0.0,
                    issues_count=0,
                    recommendations_count=0,
                    quality_issues=[],
                    recommendations=[],
                    field_quality_scores={},
                    processing_status="service_unavailable: CrewAI orchestrator not available",
                    source="service_unavailable",
                )
        except Exception as e:
            logger.error(f"❌ Failed to execute data cleansing phase: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to execute data cleansing analysis: {str(e)}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"❌ Failed to trigger data cleansing analysis for flow {flow_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger data cleansing analysis: {str(e)}",
        )
