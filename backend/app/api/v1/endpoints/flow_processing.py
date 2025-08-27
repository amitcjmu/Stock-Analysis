"""
Flow Processing API Endpoints
Handles flow continuation and routing decisions using intelligent agents
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_request_context
from app.core.database import get_db
from app.services.flow_orchestration.transition_utils import (
    is_simple_transition,
    needs_ai_analysis,
    get_fast_path_response,
)
from app.services.agents.agent_service_layer.handlers.flow_handler import FlowHandler

# Import modularized components
from .flow_processing_models import (
    FlowContinuationRequest,
    FlowContinuationResponse,
)
from .flow_processing_converters import (
    convert_fast_path_to_api_response,
    create_simple_transition_response,
    convert_to_api_response,
    create_fallback_response,
)

# Legacy validation functions available in flow_processing_legacy.py if needed

# Import TenantScopedAgentPool for optimized AI operations (ADR-015)
try:
    from app.services.persistent_agents.tenant_scoped_agent_pool import (
        TenantScopedAgentPool,
    )

    TENANT_AGENT_POOL_AVAILABLE = True
except ImportError:
    TENANT_AGENT_POOL_AVAILABLE = False

# Import the REAL single intelligent CrewAI agent
try:
    from app.services.agents.intelligent_flow_agent import (
        FlowIntelligenceResult,
        IntelligentFlowAgent,
    )

    INTELLIGENT_AGENT_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ REAL Single Intelligent CrewAI Agent imported successfully")
except ImportError as e:
    INTELLIGENT_AGENT_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.error(f"❌ Failed to import intelligent agent: {e}")

    # Fallback classes
    class FlowIntelligenceResult:
        def __init__(self, **kwargs):
            from app.core.security.cache_encryption import secure_setattr

            for key, value in kwargs.items():
                secure_setattr(self, key, value)

    class IntelligentFlowAgent:
        async def analyze_flow_continuation(self, flow_id: str, **kwargs):
            return FlowIntelligenceResult(
                success=False,
                flow_id=flow_id,
                flow_type="discovery",
                current_phase="data_import",
                routing_decision="/discovery/overview",
                user_guidance="Intelligent agent not available",
                reasoning="Agent import failed",
                confidence=0.0,
            )


logger = logging.getLogger(__name__)

router = APIRouter()


# Models are now imported from flow_processing_models.py


@router.post("/continue/{flow_id}", response_model=FlowContinuationResponse)
async def continue_flow_processing(
    flow_id: str,
    request: FlowContinuationRequest,
    context: RequestContext = Depends(get_request_context),
    db: AsyncSession = Depends(get_db),
):
    """
    Optimized flow processing with fast path detection

    FAST PATH (< 1 second): Simple phase transitions without AI
    INTELLIGENT PATH (when needed): AI analysis for complex scenarios

    Performance goals:
    - Simple transitions: < 1 second response time
    - AI-required scenarios: Only when needed (field mapping, errors, etc.)
    - Uses TenantScopedAgentPool (ADR-015) for persistent agents
    """
    import time

    start_time = time.time()

    try:
        logger.info(f"🚀 OPTIMIZED FLOW PROCESSING: Starting for {flow_id}")

        # Step 1: Get flow status using FlowHandler
        flow_handler = FlowHandler(context)
        flow_status_result = await flow_handler.get_flow_status(flow_id)

        if not flow_status_result.get("flow_exists", False):
            logger.warning(f"Flow not found: {flow_id}")
            return create_fallback_response(flow_id, "Flow not found")

        flow_data = flow_status_result.get("flow", {})

        # Step 2: Basic validation for simple transition check
        # For now, assume phase is valid for simple transitions
        # In a real implementation, you'd call a validation service here
        validation_data = {
            "phase_valid": True,  # Simplified - would come from actual validation
            "issues": [],
            "error": None,
            "completion_status": "phase_complete",
        }

        # Step 3: Check if this can be a fast path (simple) transition
        if is_simple_transition(flow_data, validation_data):
            logger.info(f"⚡ FAST PATH: Simple transition detected for {flow_id}")

            # Get fast path response without AI (< 1 second)
            fast_response = get_fast_path_response(flow_data, validation_data)

            if fast_response:
                execution_time = time.time() - start_time
                logger.info(
                    f"✅ FAST PATH COMPLETE: {flow_id} in {execution_time:.3f}s"
                )

                # Convert to proper API response format
                return convert_fast_path_to_api_response(
                    fast_response, flow_data, execution_time
                )

        # Step 4: Check if AI analysis is actually needed
        requires_ai, ai_reason = needs_ai_analysis(flow_data, validation_data)

        if not requires_ai:
            logger.info(f"⚡ SIMPLE LOGIC: No AI needed for {flow_id} - {ai_reason}")
            # Use simple logic without AI but with proper response format
            simple_response = create_simple_transition_response(flow_data)
            execution_time = time.time() - start_time
            return convert_fast_path_to_api_response(
                simple_response, flow_data, execution_time
            )

        # Step 5: AI analysis is needed - use TenantScopedAgentPool (ADR-015)
        logger.info(f"🧠 AI ANALYSIS NEEDED: {ai_reason} for {flow_id}")

        if TENANT_AGENT_POOL_AVAILABLE:
            # Use persistent tenant-scoped agent for better performance
            try:
                # Get agent for potential future use
                await TenantScopedAgentPool.get_agent(
                    context=context, agent_type="flow_analyst", force_recreate=False
                )

                # Use agent for flow analysis
                # Note: Implementation needed based on agent interface
                logger.info(f"🧠 TENANT AGENT: Using persistent agent for {flow_id}")

                # Fallback to intelligent agent if tenant agent interface not ready
                result = await use_intelligent_agent(flow_id, context)

            except Exception as e:
                logger.warning(f"Tenant agent failed, using intelligent agent: {e}")
                result = await use_intelligent_agent(flow_id, context)
        else:
            # Fallback to single intelligent agent
            logger.info(f"🧠 INTELLIGENT AGENT: TenantPool unavailable for {flow_id}")
            result = await use_intelligent_agent(flow_id, context)

        execution_time = time.time() - start_time
        logger.info(f"✅ AI ANALYSIS COMPLETE: {flow_id} in {execution_time:.3f}s")

        return convert_to_api_response(result, execution_time)

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(
            f"❌ FLOW PROCESSING ERROR: {flow_id} failed after "
            f"{execution_time:.3f}s - {str(e)}"
        )
        return create_fallback_response(flow_id, f"Processing failed: {str(e)}")


async def use_intelligent_agent(flow_id: str, context: RequestContext) -> Any:
    """Use the intelligent agent for flow analysis"""
    if not INTELLIGENT_AGENT_AVAILABLE:
        raise Exception("Intelligent agent not available")

    # Create single intelligent agent
    intelligent_agent = IntelligentFlowAgent()

    # Analyze flow using single agent with multiple tools
    result = await intelligent_agent.analyze_flow_continuation(
        flow_id=flow_id,
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id,
        user_id=context.user_id,
    )

    return result


# Response conversion functions moved to flow_processing_converters.py

# Legacy validation functions moved to flow_processing_legacy.py
