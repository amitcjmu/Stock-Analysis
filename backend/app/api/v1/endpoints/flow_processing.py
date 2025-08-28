"""
Flow Processing API Endpoints
Handles flow continuation and routing decisions using intelligent agents
"""

import logging
from typing import Any, Dict
from collections import defaultdict

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


# Observability Metrics (FIX for Issue #9)
class FlowProcessingMetrics:
    """Track performance metrics for flow processing"""

    def __init__(self):
        self.fast_path_count = 0
        self.ai_path_count = 0
        self.simple_logic_count = 0
        self.error_count = 0
        self.execution_times: Dict[str, list] = defaultdict(list)

    def record_fast_path(self, execution_time: float):
        self.fast_path_count += 1
        self.execution_times["fast_path"].append(execution_time)

    def record_ai_path(self, execution_time: float):
        self.ai_path_count += 1
        self.execution_times["ai_path"].append(execution_time)

    def record_simple_logic(self, execution_time: float):
        self.simple_logic_count += 1
        self.execution_times["simple_logic"].append(execution_time)

    def record_error(self, execution_time: float):
        self.error_count += 1
        self.execution_times["errors"].append(execution_time)

    def get_p95(self, path_type: str) -> float:
        """Get P95 latency for a given path type"""
        times = sorted(self.execution_times.get(path_type, []))
        if not times:
            return 0.0
        idx = int(len(times) * 0.95)
        return times[min(idx, len(times) - 1)]

    def get_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        total = self.fast_path_count + self.ai_path_count + self.simple_logic_count
        return {
            "total_requests": total,
            "fast_path": {
                "count": self.fast_path_count,
                "percentage": (self.fast_path_count / total * 100) if total > 0 else 0,
                "p95_latency": self.get_p95("fast_path"),
                "avg_latency": (
                    sum(self.execution_times["fast_path"])
                    / len(self.execution_times["fast_path"])
                    if self.execution_times["fast_path"]
                    else 0
                ),
            },
            "simple_logic": {
                "count": self.simple_logic_count,
                "percentage": (
                    (self.simple_logic_count / total * 100) if total > 0 else 0
                ),
                "p95_latency": self.get_p95("simple_logic"),
                "avg_latency": (
                    sum(self.execution_times["simple_logic"])
                    / len(self.execution_times["simple_logic"])
                    if self.execution_times["simple_logic"]
                    else 0
                ),
            },
            "ai_path": {
                "count": self.ai_path_count,
                "percentage": (self.ai_path_count / total * 100) if total > 0 else 0,
                "p95_latency": self.get_p95("ai_path"),
                "avg_latency": (
                    sum(self.execution_times["ai_path"])
                    / len(self.execution_times["ai_path"])
                    if self.execution_times["ai_path"]
                    else 0
                ),
            },
            "errors": self.error_count,
        }


# Global metrics instance
flow_metrics = FlowProcessingMetrics()


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

        # Step 2: Derive validation from actual flow completion data (FIX for Issue #1)
        # ADR-012: Use child flow truth for phase completion status
        phases_completed = flow_data.get("phases_completed", {})
        current_phase = flow_data.get("current_phase", "data_import")
        flow_type = flow_data.get("flow_type", "discovery")

        # Determine if current phase is actually complete based on flow type
        phase_valid = False
        if flow_type == "discovery" and isinstance(phases_completed, dict):
            # For discovery flows, check the phases_completed dictionary
            phase_valid = phases_completed.get(current_phase, False)
        elif flow_type == "collection":
            # For collection flows, check if questionnaires phase is complete
            # TODO: Map to actual collection phase completion once repository is ready
            phase_valid = (
                current_phase == "questionnaires"
                and flow_data.get("status") == "completed"
            )

        validation_data = {
            "phase_valid": phase_valid,  # Derived from actual flow data per ADR-012
            "issues": [],
            "error": None,
            "completion_status": "phase_complete" if phase_valid else "in_progress",
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

                # Record metrics for observability
                flow_metrics.record_fast_path(execution_time)

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

            # Record metrics for observability
            flow_metrics.record_simple_logic(execution_time)

            return convert_fast_path_to_api_response(
                simple_response, flow_data, execution_time
            )

        # Step 5: AI analysis is needed - use TenantScopedAgentPool (ADR-015)
        logger.info(f"🧠 AI ANALYSIS NEEDED: {ai_reason} for {flow_id}")

        if TENANT_AGENT_POOL_AVAILABLE:
            # Use persistent tenant-scoped agent for better performance
            try:
                # Get the actual agent from the pool (FIX for Issue #3 per ADR-015)
                agent = await TenantScopedAgentPool.get_agent(
                    context=context,
                    agent_type="IntelligentFlowAgent",
                    force_recreate=False,
                )

                logger.info(f"🧠 TENANT AGENT: Using persistent agent for {flow_id}")

                # Use the pooled agent's analyze_flow_continuation method
                if hasattr(agent, "analyze_flow_continuation"):
                    result = await agent.analyze_flow_continuation(
                        flow_id=flow_id,
                        client_account_id=context.client_account_id,
                        engagement_id=context.engagement_id,
                        user_id=context.user_id,
                    )
                else:
                    # Fallback if agent doesn't have expected method
                    logger.warning(
                        "Pooled agent lacks analyze_flow_continuation, using new instance"
                    )
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

        # Record metrics for AI path
        flow_metrics.record_ai_path(execution_time)

        return convert_to_api_response(result, execution_time)

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(
            f"❌ FLOW PROCESSING ERROR: {flow_id} failed after "
            f"{execution_time:.3f}s - {str(e)}"
        )

        # Record error metrics
        flow_metrics.record_error(execution_time)

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


@router.get("/metrics")
async def get_flow_processing_metrics():
    """
    Get flow processing performance metrics (FIX for Issue #9)

    Returns statistics on fast-path vs AI-path usage and latencies
    """
    stats = flow_metrics.get_stats()

    # Log current performance stats
    if stats["total_requests"] > 0:
        logger.info(
            f"📊 PERFORMANCE METRICS: "
            f"Total: {stats['total_requests']}, "
            f"Fast Path: {stats['fast_path']['percentage']:.1f}%, "
            f"Simple Logic: {stats['simple_logic']['percentage']:.1f}%, "
            f"AI Path: {stats['ai_path']['percentage']:.1f}%, "
            f"Fast P95: {stats['fast_path']['p95_latency']:.3f}s, "
            f"AI P95: {stats['ai_path']['p95_latency']:.3f}s"
        )

    return stats


# Response conversion functions moved to flow_processing_converters.py

# Legacy validation functions moved to flow_processing_legacy.py
