"""
Flow Query Endpoints

This module handles all GET operations for discovery flows:
- Flow status queries
- Active flow listings
- Agent insights retrieval
- Processing status monitoring
"""

import hashlib
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.services.user_context_service import UserContextService

from .response_mappers import (
    AttributeMappingResponse,
    DiscoveryFlowResponse,
    DiscoveryFlowStatusResponse,
    ResponseMappers,
)
from .status_calculator import StatusCalculator

logger = logging.getLogger(__name__)

query_router = APIRouter(tags=["discovery-query"])


def generate_etag(data: str) -> str:
    """Generate an ETag hash with Python version compatibility.

    Note: MD5 is used here only for ETag generation (cache validation),
    not for security purposes.
    """
    if sys.version_info >= (3, 9):
        return f'"{hashlib.md5(data.encode(), usedforsecurity=False).hexdigest()}"'
    else:
        return f'"{hashlib.md5(data.encode()).hexdigest()}"'  # nosec B324


@query_router.get("/flows/active", response_model=List[DiscoveryFlowResponse])
async def get_active_flows(
    response: Response,
    if_none_match: Optional[str] = Header(None),
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Get active discovery flows for the current tenant context with ETag support.

    This endpoint retrieves all active discovery flows excluding deleted and cancelled flows.
    Supports efficient polling via ETags.
    """
    try:
        # Validate context - check for None first
        if not context:
            logger.error("No request context available")
            raise HTTPException(status_code=403, detail="Request context is required")

        if not context.client_account_id:
            logger.error("No client account ID in context")
            raise HTTPException(
                status_code=403, detail="Client account context is required"
            )

        # Initialize user context service
        user_service = UserContextService(db)

        # Handle cases where engagement_id might be None
        engagement_id = context.engagement_id

        # If we have a user_id but no engagement_id, try to resolve it
        if context.user_id and not engagement_id:
            validation_result = await user_service.validate_user_context(
                user_id=context.user_id,
                client_account_id=context.client_account_id,
                engagement_id=None,
            )

            if (
                validation_result["valid"]
                and validation_result["resolved_engagement_id"]
            ):
                engagement_id = validation_result["resolved_engagement_id"]
                logger.info(
                    f"Resolved engagement_id from user context: {engagement_id}"
                )

        logger.info(
            f"Getting active flows for client {context.client_account_id}, engagement {engagement_id}"
        )

        # Query actual discovery flows from database
        # Return all active flows, including those just initialized
        from app.models.discovery_flow import DiscoveryFlow

        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.status != "deleted",  # Exclude soft-deleted flows
                DiscoveryFlow.status != "cancelled",  # Exclude cancelled flows
                # Removed data_import_id filter to allow newly created flows to appear
                or_(
                    DiscoveryFlow.status == "active",
                    DiscoveryFlow.status == "running",
                    DiscoveryFlow.status == "paused",
                    DiscoveryFlow.status == "processing",
                    DiscoveryFlow.status == "ready",
                    DiscoveryFlow.status == "waiting_for_approval",
                    DiscoveryFlow.status
                    == "initialized",  # Include all initialized flows
                    DiscoveryFlow.status
                    == "orphaned",  # Include orphaned flows for testing
                    DiscoveryFlow.status == "in_progress",  # Include in_progress flows
                    DiscoveryFlow.status
                    == "complete",  # Include completed flows to show history
                ),
            )
        )

        # Add engagement filter only if we have a valid engagement_id
        if engagement_id:
            stmt = stmt.where(DiscoveryFlow.engagement_id == engagement_id)

        stmt = stmt.order_by(DiscoveryFlow.created_at.desc())

        result = await db.execute(stmt)
        flows = result.scalars().all()

        # Convert to response format using ResponseMappers
        active_flows = []
        for flow in flows:
            flow_response = ResponseMappers.map_flow_to_response(flow, context)
            active_flows.append(flow_response)

        logger.info(f"Found {len(active_flows)} active flows with imported data")

        # Generate ETag from active flows data
        # Convert response objects to dicts for serialization
        flows_data = [
            flow.dict() if hasattr(flow, "dict") else flow for flow in active_flows
        ]
        state_json = json.dumps(flows_data, sort_keys=True, default=str)
        etag = generate_etag(state_json)

        # Check if content has changed
        if if_none_match == etag:
            return Response(status_code=304, headers={"ETag": etag})

        # Set response headers
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
        response.headers["X-Flow-Count"] = str(len(active_flows))

        return active_flows

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active flows: {e}", exc_info=True)
        # Provide more detailed error message
        if "engagement_id" in str(e):
            raise HTTPException(
                status_code=500,
                detail="Failed to get active flows: User context error. Please ensure proper headers are sent.",
            )
        raise HTTPException(
            status_code=500, detail=f"Failed to get active flows: {str(e)}"
        )


@query_router.get("/flows/{flow_id}/status", response_model=DiscoveryFlowStatusResponse)
async def get_flow_status(
    flow_id: str,
    response: Response,
    if_none_match: Optional[str] = Header(None),
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed status of a specific discovery flow with ETag support.

    This endpoint provides comprehensive flow status including phase completion,
    agent insights, and field mappings. Supports efficient polling via ETags.

    Returns:
        Flow status data or 304 Not Modified if unchanged
    """
    try:
        logger.info(f"Getting status for flow {flow_id}")

        # Import required models
        import uuid as uuid_lib

        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        from app.models.discovery_flow import DiscoveryFlow

        # Convert flow_id to UUID if needed
        try:
            flow_uuid = uuid_lib.UUID(flow_id)
        except ValueError:
            logger.warning(f"Invalid UUID format for flow_id: {flow_id}")
            flow_uuid = flow_id

        # Get flow from DiscoveryFlow table
        stmt = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_uuid)
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if flow:
            logger.info(
                f"Found flow in DiscoveryFlow table: status={flow.status}, progress={flow.progress_percentage}"
            )

            # Get CrewAI state extensions for additional state
            ext_stmt = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_id == flow_uuid
            )
            ext_result = await db.execute(ext_stmt)
            extensions = ext_result.scalar_one_or_none()

            # Use ResponseMappers to create standardized response
            status_response = await ResponseMappers.map_flow_to_status_response(
                flow, extensions, context, db
            )

            # Generate ETag from response data
            response_dict = (
                status_response.dict()
                if hasattr(status_response, "dict")
                else status_response
            )
            state_json = json.dumps(response_dict, sort_keys=True, default=str)
            etag = generate_etag(state_json)

            # Check if content has changed
            if if_none_match == etag:
                return Response(status_code=304, headers={"ETag": etag})

            # Set response headers
            response.headers["ETag"] = etag
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
            response.headers["X-Flow-Updated-At"] = (
                flow.updated_at.isoformat() if flow.updated_at else ""
            )

            return status_response

        # Fallback to flow state persistence data
        from app.services.crewai_flows.persistence.postgres_store import (
            PostgresFlowStateStore,
        )

        try:
            store = PostgresFlowStateStore(db, context)
            state_dict = await store.load_state(flow_id)

            if state_dict:
                # Use ResponseMappers to create standardized response
                status_response = ResponseMappers.map_state_dict_to_status_response(
                    flow_id, state_dict, context
                )

                # Generate ETag from response data
                response_dict = (
                    status_response.dict()
                    if hasattr(status_response, "dict")
                    else status_response
                )
                state_json = json.dumps(response_dict, sort_keys=True, default=str)
                etag = generate_etag(state_json)

                # Check if content has changed
                if if_none_match == etag:
                    return Response(status_code=304, headers={"ETag": etag})

                # Set response headers
                response.headers["ETag"] = etag
                response.headers["Cache-Control"] = "no-cache, must-revalidate"

                return status_response
        except Exception as store_error:
            logger.warning(f"Failed to get flow state from store: {store_error}")

        # Final fallback to orchestrator
        from app.services.master_flow_orchestrator import MasterFlowOrchestrator

        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.get_flow_status(flow_id)

        # Use ResponseMappers to create standardized response
        status_response = ResponseMappers.map_orchestrator_result_to_status_response(
            flow_id, result, context
        )

        # Generate ETag from response data
        response_dict = (
            status_response.dict()
            if hasattr(status_response, "dict")
            else status_response
        )
        state_json = json.dumps(response_dict, sort_keys=True, default=str)
        etag = generate_etag(state_json)

        # Check if content has changed
        if if_none_match == etag:
            return Response(status_code=304, headers={"ETag": etag})

        # Set response headers
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "no-cache, must-revalidate"

        return status_response

    except Exception as e:
        logger.error(f"Error getting flow status: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get flow status: {str(e)}"
        )


@query_router.get("/flow/{flow_id}/agent-insights", response_model=List[Dict[str, Any]])
async def get_flow_agent_insights(
    flow_id: str,
    response: Response,
    page_context: str = "data_import",
    if_none_match: Optional[str] = Header(None),
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Get agent insights for a specific flow with ETag support.

    This endpoint retrieves AI agent insights and recommendations for the flow.
    Supports efficient polling via ETags.
    """
    try:
        logger.info(
            f"Getting agent insights for flow {flow_id}, page context: {page_context}"
        )

        # Import required models
        import uuid as uuid_lib

        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        from app.models.discovery_flow import DiscoveryFlow

        # Convert flow_id to UUID if needed
        try:
            flow_uuid = uuid_lib.UUID(flow_id)
        except ValueError:
            flow_uuid = flow_id

        # Get flow from DiscoveryFlow table
        stmt = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_uuid)
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if flow:
            # Extract agent insights from flow state
            agent_insights = []
            if flow.crewai_state_data and "agent_insights" in flow.crewai_state_data:
                agent_insights = flow.crewai_state_data["agent_insights"]

            # Also check extensions for additional insights
            ext_stmt = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_id == flow_uuid
            )
            ext_result = await db.execute(ext_stmt)
            extensions = ext_result.scalar_one_or_none()

            if extensions and extensions.flow_persistence_data:
                persistence_data = extensions.flow_persistence_data
                if "agent_insights" in persistence_data:
                    # Merge insights from extensions if different
                    extension_insights = persistence_data.get("agent_insights", [])
                    for insight in extension_insights:
                        if insight not in agent_insights:
                            agent_insights.append(insight)

            # Filter insights by page context if specified
            if page_context != "all":
                agent_insights = [
                    insight
                    for insight in agent_insights
                    if insight.get("context", "").lower() == page_context.lower()
                ]

            # Generate ETag from agent insights
            state_json = json.dumps(agent_insights, sort_keys=True, default=str)
            etag = generate_etag(state_json)

            # Check if content has changed
            if if_none_match == etag:
                return Response(status_code=304, headers={"ETag": etag})

            # Set response headers
            response.headers["ETag"] = etag
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
            response.headers["X-Insights-Count"] = str(len(agent_insights))
            response.headers["X-Flow-Updated-At"] = (
                flow.updated_at.isoformat() if flow.updated_at else ""
            )

            return agent_insights

        # Return empty list if flow not found
        empty_insights = []

        # Generate ETag even for empty response
        etag = generate_etag("[]")

        # Check if content has changed
        if if_none_match == etag:
            return Response(status_code=304, headers={"ETag": etag})

        # Set response headers
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
        response.headers["X-Insights-Count"] = "0"

        return empty_insights

    except Exception as e:
        logger.error(f"Error getting agent insights: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent insights: {str(e)}"
        )


@query_router.get("/flows/{flow_id}/field-mappings", response_model=Dict[str, Any])
async def get_flow_field_mappings(
    flow_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Get field mappings for a specific discovery flow.

    This endpoint retrieves the field mapping configuration for the flow.
    """
    try:
        # Validate context - engagement context is required
        if not context:
            logger.error("No request context available")
            raise HTTPException(status_code=403, detail="Request context is required")

        if not context.engagement_id:
            logger.error("No engagement ID in context")
            raise HTTPException(
                status_code=403, detail="Engagement context is required"
            )

        logger.info(
            f"Getting field mappings for flow {flow_id}, engagement {context.engagement_id}"
        )

        # Import required models
        import uuid as uuid_lib

        from app.models.discovery_flow import DiscoveryFlow

        # Convert flow_id to UUID if needed
        try:
            flow_uuid = uuid_lib.UUID(flow_id)
        except ValueError:
            logger.warning(f"Invalid UUID format for flow_id: {flow_id}")
            flow_uuid = flow_id

        # Get flow from DiscoveryFlow table
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_uuid,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(
                status_code=404,
                detail=f"Flow {flow_id} not found for engagement {context.engagement_id}",
            )

        # Extract field mappings from flow
        field_mappings = flow.field_mappings or {}

        # Also check crewai_state_data for field mappings
        if flow.crewai_state_data and "field_mappings" in flow.crewai_state_data:
            crewai_mappings = flow.crewai_state_data.get("field_mappings", {})
            # Merge with existing mappings
            field_mappings.update(crewai_mappings)

        return {
            "flow_id": str(flow_id),
            "field_mappings": field_mappings,
            "mapping_status": flow.field_mapping_status or "pending",
            "mapping_completed": flow.field_mapping_completed or False,
            "confidence_scores": (
                flow.crewai_state_data.get("confidence_scores", {})
                if flow.crewai_state_data
                else {}
            ),
            "last_updated": flow.updated_at.isoformat() if flow.updated_at else "",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting field mappings: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get field mappings: {str(e)}"
        )


@query_router.get(
    "/agents/discovery/agent-questions", response_model=List[Dict[str, Any]]
)
async def get_agent_questions(
    TypeErr: str = Query(None, description="TypeErr parameter from frontend"),
    field_mappings: bool = Query(True),
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Get agent questions and clarifications for the discovery process.

    This endpoint retrieves questions that agents need answered to proceed
    with the discovery process.
    """
    try:
        # Validate context - engagement context is required
        if not context:
            logger.error("No request context available")
            raise HTTPException(status_code=403, detail="Request context is required")

        if not context.engagement_id:
            logger.error("No engagement ID in context")
            raise HTTPException(
                status_code=403, detail="Engagement context is required"
            )

        logger.info(
            f"Getting agent questions - TypeErr: {TypeErr}, "
            f"field_mappings: {field_mappings}, engagement: {context.engagement_id}"
        )

        # TODO: Implement real agent questions retrieval
        # For now, return empty list to avoid 404 errors
        return []

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent questions: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get agent questions: {str(e)}"
        )


@query_router.get("/attribute-mapping", response_model=AttributeMappingResponse)
async def get_attribute_mapping(
    response: Response,
    if_none_match: Optional[str] = Header(None),
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Get attribute mapping data for active discovery flows.
    
    This endpoint retrieves attribute mapping information for all active flows
    in the current user context. The frontend navigation expects this endpoint
    to be available without requiring a specific flow_id.
    
    Returns:
        Attribute mapping data including field mappings, confidence scores, 
        and mapping status for active flows, or 304 Not Modified if unchanged.
    """
    try:
        # Validate context - check for None first
        if not context:
            logger.error("No request context available")
            raise HTTPException(status_code=403, detail="Request context is required")

        if not context.client_account_id:
            logger.error("No client account ID in context")
            raise HTTPException(
                status_code=403, detail="Client account context is required"
            )

        # Initialize user context service
        user_service = UserContextService(db)

        # Handle cases where engagement_id might be None
        engagement_id = context.engagement_id

        # If we have a user_id but no engagement_id, try to resolve it
        if context.user_id and not engagement_id:
            validation_result = await user_service.validate_user_context(
                user_id=context.user_id,
                client_account_id=context.client_account_id,
                engagement_id=None,
            )

            if (
                validation_result["valid"]
                and validation_result["resolved_engagement_id"]
            ):
                engagement_id = validation_result["resolved_engagement_id"]
                logger.info(
                    f"Resolved engagement_id from user context: {engagement_id}"
                )

        logger.info(
            f"Getting attribute mapping for client {context.client_account_id}, engagement {engagement_id}"
        )

        # Import required models
        from app.models.discovery_flow import DiscoveryFlow

        # Query active discovery flows from database
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.status != "deleted",  # Exclude soft-deleted flows
                DiscoveryFlow.status != "cancelled",  # Exclude cancelled flows
                or_(
                    DiscoveryFlow.status == "active",
                    DiscoveryFlow.status == "running", 
                    DiscoveryFlow.status == "paused",
                    DiscoveryFlow.status == "processing",
                    DiscoveryFlow.status == "ready",
                    DiscoveryFlow.status == "waiting_for_approval",
                    DiscoveryFlow.status == "initialized",
                    DiscoveryFlow.status == "in_progress",
                    DiscoveryFlow.status == "complete",  # Include completed flows for reference
                ),
            )
        )

        # Add engagement filter only if we have a valid engagement_id
        if engagement_id:
            stmt = stmt.where(DiscoveryFlow.engagement_id == engagement_id)

        stmt = stmt.order_by(DiscoveryFlow.updated_at.desc())

        result = await db.execute(stmt)
        flows = result.scalars().all()

        if not flows:
            # Return empty attribute mapping structure when no flows exist
            attribute_mapping_data = {
                "flows": [],
                "aggregate_mappings": {},
                "mapping_statistics": {
                    "total_flows": 0,
                    "flows_with_mappings": 0,
                    "total_mapped_fields": 0,
                    "average_confidence": 0.0,
                },
                "client_account_id": str(context.client_account_id),
                "engagement_id": str(engagement_id) if engagement_id else None,
                "last_updated": datetime.utcnow().isoformat(),
            }
        else:
            # Process active flows to extract attribute mapping data
            flows_data = []
            aggregate_mappings = {}
            total_mapped_fields = 0
            total_confidence = 0.0
            flows_with_mappings = 0

            for flow in flows:
                # Extract field mappings from flow
                field_mappings = flow.field_mappings or {}

                # Also check crewai_state_data for field mappings
                if flow.crewai_state_data and "field_mappings" in flow.crewai_state_data:
                    crewai_mappings = flow.crewai_state_data.get("field_mappings", {})
                    # Merge with existing mappings
                    field_mappings.update(crewai_mappings)

                # Get confidence scores
                confidence_scores = {}
                if flow.crewai_state_data and "confidence_scores" in flow.crewai_state_data:
                    confidence_scores = flow.crewai_state_data.get("confidence_scores", {})

                if field_mappings:
                    flows_with_mappings += 1
                    
                    # Count mapped fields and calculate confidence
                    for source_field, mapping_info in field_mappings.items():
                        total_mapped_fields += 1
                        
                        # Extract confidence score
                        confidence = 0.0
                        if isinstance(mapping_info, dict):
                            confidence = mapping_info.get("confidence", 0.0)
                        elif source_field in confidence_scores:
                            confidence = confidence_scores[source_field]
                        
                        total_confidence += confidence
                        
                        # Add to aggregate mappings (using most recent flow's mapping if duplicates)
                        if source_field not in aggregate_mappings:
                            aggregate_mappings[source_field] = {
                                "target_field": mapping_info.get("target_field", "") if isinstance(mapping_info, dict) else str(mapping_info),
                                "confidence": confidence,
                                "source_flow_id": str(flow.flow_id),
                                "is_approved": mapping_info.get("is_approved", False) if isinstance(mapping_info, dict) else False,
                                "match_type": mapping_info.get("match_type", "automatic") if isinstance(mapping_info, dict) else "automatic",
                            }

                flow_data = {
                    "flow_id": str(flow.flow_id),
                    "flow_name": flow.flow_name,
                    "status": flow.status,
                    "current_phase": flow.current_phase or "field_mapping",
                    "field_mappings": field_mappings,
                    "mapping_status": flow.field_mapping_status or "pending",
                    "mapping_completed": flow.field_mapping_completed or False,
                    "confidence_scores": confidence_scores,
                    "last_updated": flow.updated_at.isoformat() if flow.updated_at else "",
                }
                flows_data.append(flow_data)

            # Calculate average confidence
            average_confidence = (
                total_confidence / total_mapped_fields if total_mapped_fields > 0 else 0.0
            )

            attribute_mapping_data = {
                "flows": flows_data,
                "aggregate_mappings": aggregate_mappings,
                "mapping_statistics": {
                    "total_flows": len(flows),
                    "flows_with_mappings": flows_with_mappings,
                    "total_mapped_fields": total_mapped_fields,
                    "average_confidence": average_confidence,
                },
                "client_account_id": str(context.client_account_id),
                "engagement_id": str(engagement_id) if engagement_id else None,
                "last_updated": datetime.utcnow().isoformat(),
            }

        logger.info(f"Found {len(flows)} flows for attribute mapping")

        # Generate ETag from attribute mapping data
        state_json = json.dumps(attribute_mapping_data, sort_keys=True, default=str)
        etag = generate_etag(state_json)

        # Check if content has changed
        if if_none_match == etag:
            return Response(status_code=304, headers={"ETag": etag})

        # Set response headers
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
        response.headers["X-Flows-Count"] = str(len(flows))
        response.headers["X-Mapping-Fields-Count"] = str(attribute_mapping_data["mapping_statistics"]["total_mapped_fields"])

        return attribute_mapping_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting attribute mapping: {e}", exc_info=True)
        # Provide detailed error message for debugging
        if "engagement_id" in str(e):
            raise HTTPException(
                status_code=500,
                detail="Failed to get attribute mapping: User context error. Please ensure proper headers are sent.",
            )
        raise HTTPException(
            status_code=500, detail=f"Failed to get attribute mapping: {str(e)}"
        )


# REMOVED: Unused endpoint - no frontend references
# @query_router.get("/flow/{flow_id}/processing-status", response_model=Dict[str, Any])
# async def get_flow_processing_status(
#     flow_id: str,
#     response: Response,
#     phase: str = Query(None),
#     if_none_match: Optional[str] = Header(None),
#     context: RequestContext = Depends(get_current_context),
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     Get detailed processing status for a specific flow with ETag support.
#
#     This endpoint provides real-time processing status information
#     for monitoring UI components with efficient polling via ETags.
#     """
#     try:
#         logger.info(f"Getting processing status for flow {flow_id}, phase: {phase}")
#
#         # Import required models
#         from app.models.discovery_flow import DiscoveryFlow
#         import uuid as uuid_lib
#
#         # Convert flow_id to UUID if needed
#         try:
#             flow_uuid = uuid_lib.UUID(flow_id)
#         except ValueError:
#             flow_uuid = flow_id
#
#         # Get flow from DiscoveryFlow table
#         stmt = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_uuid)
#         result = await db.execute(stmt)
#         flow = result.scalar_one_or_none()
#
#         if flow:
#             # Use StatusCalculator to get processing status
#             processing_status = StatusCalculator.calculate_processing_status(flow, phase)
#
#             # Generate ETag from processing status
#             state_json = json.dumps(processing_status, sort_keys=True, default=str)
#             etag = generate_etag(state_json)
#
#             # Check if content has changed
#             if if_none_match == etag:
#                 response.status_code = 304  # Not Modified
#                 return None
#
#             # Set response headers
#             response.headers["ETag"] = etag
#             response.headers["Cache-Control"] = "no-cache, must-revalidate"
#             response.headers["X-Flow-Updated-At"] = flow.updated_at.isoformat() if flow.updated_at else ""
#
#             return processing_status
#
#         # Try orchestrator as fallback
#         from app.api.v1.unified_discovery.services.discovery_orchestrator import DiscoveryOrchestrator
#
#         orchestrator = DiscoveryOrchestrator(db, context)
#
#         try:
#             result = await orchestrator.get_discovery_flow_status(flow_id)
#
#             # Transform to processing status format
#             processing_status = {
#                 "flow_id": flow_id,
#                 "phase": result.get("current_phase", "data_import"),
#                 "status": result.get("status", "initializing"),
#                 "progress_percentage": float(result.get("progress_percentage", 0)),
#                 "progress": float(result.get("progress_percentage", 0)),
#                 "records_processed": int(result.get("records_processed", 0)),
#                 "records_total": int(result.get("records_total", 0)),
#                 "records_failed": int(result.get("records_failed", 0)),
#                 "validation_status": {
#                     "format_valid": True,
#                     "security_scan_passed": True,
#                     "data_quality_score": 1.0,
#                     "issues_found": []
#                 },
#                 "agent_status": result.get("agent_status", {}),
#                 "recent_updates": [],
#                 "estimated_completion": None,
#                 "last_update": result.get("updated_at", ""),
#                 "phases": result.get("phase_completion", {}),
#                 "current_phase": result.get("current_phase", "data_import")
#             }
#
#             # Generate ETag from processing status
#             state_json = json.dumps(processing_status, sort_keys=True, default=str)
#             etag = generate_etag(state_json)
#
#             # Check if content has changed
#             if if_none_match == etag:
#                 response.status_code = 304  # Not Modified
#                 return None
#
#             # Set response headers
#             response.headers["ETag"] = etag
#             response.headers["Cache-Control"] = "no-cache, must-revalidate"
#
#             return processing_status
#
#         except Exception as orch_error:
#             logger.warning(f"Failed to get flow from orchestrator: {orch_error}")
#
#             # Return default processing status
#             default_status = {
#                 "flow_id": flow_id,
#                 "phase": phase or "data_import",
#                 "status": "initializing",
#                 "progress_percentage": 0.0,
#                 "progress": 0.0,
#                 "records_processed": 0,
#                 "records_total": 0,
#                 "records_failed": 0,
#                 "validation_status": {
#                     "format_valid": True,
#                     "security_scan_passed": True,
#                     "data_quality_score": 1.0,
#                     "issues_found": []
#                 },
#                 "agent_status": {},
#                 "recent_updates": [],
#                 "estimated_completion": None,
#                 "last_update": "",
#                 "phases": {
#                     "data_import": False,
#                     "field_mapping": False,
#                     "data_cleansing": False,
#                     "asset_inventory": False,
#                     "dependency_analysis": False,
#                     "tech_debt_analysis": False
#                 },
#                 "current_phase": "data_import"
#             }
#
#             # Generate ETag even for default status
#             state_json = json.dumps(default_status, sort_keys=True, default=str)
#             etag = generate_etag(state_json)
#
#             # Check if content has changed
#             if if_none_match == etag:
#                 response.status_code = 304  # Not Modified
#                 return None
#
#             # Set response headers
#             response.headers["ETag"] = etag
#             response.headers["Cache-Control"] = "no-cache, must-revalidate"
#
#             return default_status
#
#     except Exception as e:
#         logger.error(f"Error getting processing status: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to get processing status: {str(e)}")


@query_router.get("/flows/summary", response_model=Dict[str, Any])
async def get_flows_summary(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Get summary statistics for discovery flows.

    This endpoint provides aggregate statistics about all flows
    for the current tenant.
    """
    try:
        # Validate context - check for None first
        if not context:
            logger.error("No request context available")
            raise HTTPException(status_code=403, detail="Request context is required")

        if not context.client_account_id:
            logger.error("No client account ID in context")
            raise HTTPException(
                status_code=403, detail="Client account context is required"
            )

        # Initialize user context service
        user_service = UserContextService(db)

        # Handle cases where engagement_id might be None
        engagement_id = context.engagement_id

        # If we have a user_id but no engagement_id, try to resolve it
        if context.user_id and not engagement_id:
            validation_result = await user_service.validate_user_context(
                user_id=context.user_id,
                client_account_id=context.client_account_id,
                engagement_id=None,
            )

            if (
                validation_result["valid"]
                and validation_result["resolved_engagement_id"]
            ):
                engagement_id = validation_result["resolved_engagement_id"]
                logger.info(
                    f"Resolved engagement_id from user context: {engagement_id}"
                )

        logger.info(
            f"Getting flows summary for client {context.client_account_id}, engagement {engagement_id}"
        )

        from app.models.discovery_flow import DiscoveryFlow

        # Build base query
        base_conditions = [
            DiscoveryFlow.client_account_id == context.client_account_id,
            DiscoveryFlow.status != "deleted",
        ]

        # Add engagement filter only if we have a valid engagement_id
        if engagement_id:
            base_conditions.append(DiscoveryFlow.engagement_id == engagement_id)

        # Get flow counts by status
        status_counts_stmt = (
            select(
                DiscoveryFlow.status, func.count(DiscoveryFlow.flow_id).label("count")
            )
            .where(and_(*base_conditions))
            .group_by(DiscoveryFlow.status)
        )

        result = await db.execute(status_counts_stmt)
        status_counts = {row.status: row.count for row in result.fetchall()}

        # Get total flows
        total_flows = sum(status_counts.values())

        # Get active flows count
        active_statuses = [
            "active",
            "running",
            "processing",
            "paused",
            "waiting_for_approval",
        ]
        active_count = sum(status_counts.get(status, 0) for status in active_statuses)

        # Get completed flows count
        completed_count = status_counts.get("completed", 0)

        # Get failed flows count
        failed_count = status_counts.get("failed", 0)

        return {
            "total_flows": total_flows,
            "active_flows": active_count,
            "completed_flows": completed_count,
            "failed_flows": failed_count,
            "status_breakdown": status_counts,
            "success_rate": (
                (completed_count / total_flows * 100) if total_flows > 0 else 0.0
            ),
            "client_account_id": str(context.client_account_id),
            "engagement_id": str(engagement_id) if engagement_id else None,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting flows summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get flows summary: {str(e)}"
        )


@query_router.get("/flows/{flow_id}/health", response_model=Dict[str, Any])
async def get_flow_health(
    flow_id: str,
    response: Response,
    if_none_match: Optional[str] = Header(None),
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Get health status for a specific flow with ETag support.

    This endpoint provides health metrics and diagnostics for the flow
    with efficient polling via ETags.
    """
    try:
        logger.info(f"Getting health status for flow {flow_id}")

        # Import required models
        import uuid as uuid_lib

        from app.models.discovery_flow import DiscoveryFlow

        # Convert flow_id to UUID if needed
        try:
            flow_uuid = uuid_lib.UUID(flow_id)
        except ValueError:
            flow_uuid = flow_id

        # Get flow from database
        stmt = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_uuid)
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")

        # Calculate health metrics using StatusCalculator
        health_score = StatusCalculator.get_flow_health_score(flow)
        current_phase, steps_completed = StatusCalculator.calculate_current_phase(flow)
        progress_percentage = StatusCalculator.calculate_progress_percentage(flow)

        # Determine health status
        if health_score >= 0.8:
            health_status = "healthy"
        elif health_score >= 0.6:
            health_status = "warning"
        else:
            health_status = "unhealthy"

        health_data = {
            "flow_id": str(flow_id),
            "health_status": health_status,
            "health_score": health_score,
            "current_phase": current_phase,
            "progress_percentage": progress_percentage,
            "steps_completed": steps_completed,
            "total_steps": StatusCalculator.TOTAL_PHASES,
            "can_resume": StatusCalculator.is_flow_resumable(flow),
            "can_delete": StatusCalculator.can_flow_be_deleted(flow),
            "last_activity": flow.updated_at.isoformat() if flow.updated_at else "",
            "created_at": flow.created_at.isoformat() if flow.created_at else "",
            "status": flow.status,
            "diagnostics": {
                "has_errors": flow.status in ["failed", "error"],
                "is_stale": False,  # TODO: Calculate based on last activity
                "requires_attention": health_score < 0.6,
            },
        }

        # Generate ETag from health data
        state_json = json.dumps(health_data, sort_keys=True, default=str)
        etag = generate_etag(state_json)

        # Check if content has changed
        if if_none_match == etag:
            return Response(status_code=304, headers={"ETag": etag})

        # Set response headers
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
        response.headers["X-Flow-Updated-At"] = (
            flow.updated_at.isoformat() if flow.updated_at else ""
        )

        return health_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting flow health: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get flow health: {str(e)}"
        )
