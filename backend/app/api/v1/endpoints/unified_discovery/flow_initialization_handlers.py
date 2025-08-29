"""
Flow Initialization Handlers for Unified Discovery

Handles flow initialization through Master Flow Orchestrator.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import mask_id, safe_log_format
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from .flow_schemas import FlowInitializationRequest, FlowInitializationResponse

logger = logging.getLogger(__name__)

# Conditional import for flow initialization
try:
    from app.services.flow_configs import initialize_all_flows
except ImportError as e:
    # CC: Flow configuration module not available (likely CrewAI dependency missing)
    logger.warning(f"Flow configuration initialization unavailable: {e}")

    # Create fallback async function that returns expected structure
    async def initialize_all_flows():
        """Fallback for when flow configs cannot be initialized due to missing dependencies"""
        logger.warning("Flow initialization skipped - CrewAI dependencies unavailable")
        return {
            "status": "skipped_missing_dependencies",
            "flows_registered": [],
            "validators_registered": [],
            "handlers_registered": [],
            "errors": ["CrewAI dependencies not available"],
        }


router = APIRouter()


@router.post("/flows/initialize", response_model=FlowInitializationResponse)
async def initialize_discovery_flow(
    request: FlowInitializationRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Initialize a discovery flow through Master Flow Orchestrator.

    This is the main entry point for starting discovery flows. It ensures proper
    architectural flow through the Master Flow Orchestrator.
    """
    try:
        # Ensure flow configs are initialized (fallback handles missing dependencies)
        flow_init_result = await initialize_all_flows()
        if "errors" in flow_init_result and flow_init_result["errors"]:
            logger.warning(
                f"Flow initialization completed with warnings: {flow_init_result['errors']}"
            )

        # Extract configuration
        configuration = request.configuration or {}

        # Handle raw_data payload
        initial_data = {}
        if request.raw_data:
            logger.info(
                f"📊 Received raw_data with {len(request.raw_data)} records in flow initialization"
            )
            initial_data["raw_data"] = request.raw_data

            # Store import metadata separately for backward compatibility
            if (
                isinstance(request.raw_data, dict)
                and "import_metadata" in request.raw_data
            ):
                initial_data["import_metadata"] = request.raw_data["import_metadata"]
                logger.info("📋 Extracted import_metadata from raw_data payload")

        # Generate flow name if not provided
        flow_name = (
            request.flow_name
            or f"Discovery Flow - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        # Initialize through Master Flow Orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)

        flow_id, flow_details = await orchestrator.create_flow(
            flow_type="discovery",
            flow_name=flow_name,
            configuration=configuration,
            initial_data=initial_data,
        )

        logger.info(
            safe_log_format(
                "✅ Discovery flow initialized successfully: {flow_id} (user: {user_id})",
                flow_id=mask_id(str(flow_id)),
                user_id=mask_id(context.user_id),
            )
        )

        return FlowInitializationResponse(
            success=True,
            flow_id=str(flow_id),
            flow_name=flow_name,
            status="initialized",
            message="Discovery flow initialized successfully through Master Flow Orchestrator",
            metadata={
                "flow_details": flow_details,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "has_raw_data": bool(request.raw_data),
                "configuration_keys": (
                    list(configuration.keys()) if configuration else []
                ),
            },
        )

    except Exception as e:
        logger.error(
            safe_log_format(
                "❌ Flow initialization failed: {error} (user: {user_id})",
                error=str(e),
                user_id=mask_id(context.user_id),
            )
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize discovery flow: {str(e)}",
        )
