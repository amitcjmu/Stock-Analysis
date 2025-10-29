"""
Main endpoint for Critical Attributes Analysis - AGENTIC INTELLIGENCE
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import extract_context_from_request
from app.core.database import get_db
from app.models.data_import import DataImport
from .services import get_agentic_critical_attributes, trigger_discovery_flow_analysis

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/critical-attributes-status")
async def get_critical_attributes_status(
    request: Request,
    flow_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    AGENTIC CRITICAL ATTRIBUTES ANALYSIS

    Uses CrewAI discovery flow and field mapping crew to dynamically determine
    which attributes are critical based on:
    - Agent analysis of actual data patterns
    - Field mapping crew intelligence
    - Discovery flow insights
    - Learned patterns from AI agents

    This replaces static heuristics with intelligent agent decision-making.
    """
    try:
        # Extract context directly from request to bypass middleware issues
        context = extract_context_from_request(request)
        logger.info(f"🤖 AGENTIC Critical Attributes Analysis - Context: {context}")

        # If flow_id is provided, find the import associated with that flow
        if flow_id:
            logger.info(f"🔍 Looking for import associated with flow_id: {flow_id}")

            # First check if flow_id is actually a data_import_id (for backward compatibility)
            direct_import_query = select(DataImport).where(DataImport.id == flow_id)
            direct_result = await db.execute(direct_import_query)
            latest_import = direct_result.scalar_one_or_none()

            if latest_import:
                logger.info(f"✅ Found import directly by ID: {latest_import.id}")
            else:
                # Try to find import by master_flow_id
                flow_import_query = select(DataImport).where(
                    and_(
                        DataImport.master_flow_id == flow_id,
                        DataImport.client_account_id == context.client_account_id,
                        DataImport.engagement_id == context.engagement_id,
                    )
                )
                flow_result = await db.execute(flow_import_query)
                latest_import = flow_result.scalar_one_or_none()

                if latest_import:
                    logger.info(
                        f"✅ Found import by master_flow_id: {latest_import.id}"
                    )
                else:
                    # Try to find via discovery flow
                    from app.models.discovery_flow import DiscoveryFlow

                    discovery_query = select(DiscoveryFlow).where(
                        and_(
                            (DiscoveryFlow.flow_id == flow_id)
                            | (DiscoveryFlow.master_flow_id == flow_id),
                            DiscoveryFlow.client_account_id
                            == context.client_account_id,
                            DiscoveryFlow.engagement_id == context.engagement_id,
                        )
                    )
                    discovery_result = await db.execute(discovery_query)
                    discovery_flow = discovery_result.scalar_one_or_none()

                    if discovery_flow and discovery_flow.data_import_id:
                        logger.info(
                            f"✅ Found discovery flow: {discovery_flow.flow_id}, "
                            f"data_import_id: {discovery_flow.data_import_id}"
                        )
                        import_query = select(DataImport).where(
                            DataImport.id == discovery_flow.data_import_id
                        )
                        import_result = await db.execute(import_query)
                        latest_import = import_result.scalar_one_or_none()

                        if latest_import:
                            logger.info(
                                f"✅ Found import via discovery flow: {latest_import.id}"
                            )
                    else:
                        logger.warning(
                            f"❌ No discovery flow found or no data_import_id for flow_id: {flow_id}"
                        )
        else:
            # Get the latest data import session for the current context
            latest_import_query = (
                select(DataImport)
                .where(
                    and_(
                        DataImport.client_account_id == context.client_account_id,
                        DataImport.engagement_id == context.engagement_id,
                    )
                )
                .order_by(DataImport.created_at.desc())
                .limit(1)
            )
            latest_import_result = await db.execute(latest_import_query)
            latest_import = latest_import_result.scalar_one_or_none()

        if not flow_id:
            logger.info(
                f"🔍 Searching for imports with client_id: {context.client_account_id}, "
                f"engagement_id: {context.engagement_id}"
            )

        if not latest_import:
            logger.warning(f"🔍 No import found for context: {context}")
            # Return agentic zero-state with discovery flow recommendation
            return {
                "attributes": [],
                "statistics": {
                    "total_attributes": 0,
                    "mapped_count": 0,
                    "pending_count": 0,
                    "unmapped_count": 0,
                    "migration_critical_count": 0,
                    "migration_critical_mapped": 0,
                    "overall_completeness": 0,
                    "avg_quality_score": 0,
                    "assessment_ready": False,
                },
                "recommendations": {
                    "next_priority": "Import CMDB data to trigger agentic discovery flow",
                    "assessment_readiness": (
                        "Discovery flow agents will analyze your data to determine critical attributes"
                    ),
                    "quality_improvement": (
                        "AI agents will learn from your data patterns to identify migration-critical fields"
                    ),
                },
                "agent_status": {
                    "discovery_flow_active": False,
                    "field_mapping_crew_status": "waiting_for_data",
                    "learning_system_status": "ready",
                },
                "last_updated": datetime.utcnow().isoformat(),
            }

        logger.info(
            f"✅ Found import: {latest_import.id}, status: {latest_import.status}"
        )

        # CHECK FOR AGENTIC DISCOVERY FLOW RESULTS
        # Try to get results from the discovery flow agents first
        agentic_results = await get_agentic_critical_attributes(
            context, latest_import, db
        )

        if agentic_results:
            logger.info(
                "🤖 Using AGENTIC discovery flow results for critical attributes"
            )
            return agentic_results

        # FALLBACK: If no agentic results, trigger discovery flow
        logger.info(
            "🚀 Triggering discovery flow for agentic critical attributes analysis"
        )
        await trigger_discovery_flow_analysis(context, latest_import, db)

        # For now, return discovery flow in progress status
        return {
            "attributes": [],
            "statistics": {
                "total_attributes": 0,
                "mapped_count": 0,
                "pending_count": 0,
                "unmapped_count": 0,
                "migration_critical_count": 0,
                "migration_critical_mapped": 0,
                "overall_completeness": 0,
                "avg_quality_score": 0,
                "assessment_ready": False,
            },
            "recommendations": {
                "next_priority": "Discovery flow agents are analyzing your data to determine critical attributes",
                "assessment_readiness": "Field mapping crew is identifying migration-critical fields",
                "quality_improvement": "AI agents are learning patterns from your data",
            },
            "agent_status": {
                "discovery_flow_active": True,
                "field_mapping_crew_status": "analyzing",
                "learning_system_status": "active",
            },
            "last_updated": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(
            f"Failed to get agentic critical attributes status: {e}", exc_info=True
        )

        # Return a safe fallback response instead of HTTP 500
        try:
            return {
                "attributes": [],
                "statistics": {
                    "total_attributes": 0,
                    "mapped_count": 0,
                    "pending_count": 0,
                    "unmapped_count": 0,
                    "migration_critical_count": 0,
                    "migration_critical_mapped": 0,
                    "overall_completeness": 0,
                    "avg_quality_score": 0,
                    "assessment_ready": False,
                },
                "recommendations": {
                    "next_priority": "Service temporarily unavailable - please try again later",
                    "assessment_readiness": "Critical attributes analysis is currently unavailable",
                    "quality_improvement": "Please contact support if this issue persists",
                },
                "agent_status": {
                    "discovery_flow_active": False,
                    "field_mapping_crew_status": "error",
                    "learning_system_status": "error",
                },
                "error": {
                    "message": "Service temporarily unavailable",
                    "code": "ANALYSIS_ERROR",
                    "details": "Critical attributes analysis encountered an error",
                },
                "last_updated": datetime.utcnow().isoformat(),
            }
        except Exception as fallback_error:
            logger.error(f"Failed to create fallback response: {fallback_error}")
            raise HTTPException(
                status_code=500,
                detail="Critical attributes service is temporarily unavailable",
            )
