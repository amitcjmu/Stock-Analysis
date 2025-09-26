"""
Flow Processing Module
Modularized flow processing endpoints with backward compatibility

This module provides the same public API as the original monolithic flow_processing.py
file while organizing the code into logical components following the 7-layer enterprise
architecture pattern.

Directory Structure:
- base.py: Core classes and shared utilities (FlowProcessingMetrics, agent imports)
- commands.py: Write operations and state modifications
- queries.py: Read operations and status queries
- utils.py: Helper functions and validation utilities

PUBLIC API (preserved for backward compatibility):
- router: FastAPI router with all endpoints
- FlowProcessingMetrics: Metrics tracking class
- continue_flow_processing: Main endpoint handler
- get_flow_processing_metrics: Metrics endpoint handler
- use_intelligent_agent: Agent utility function
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_request_context
from app.core.database import get_db

# Import all components from modular structure
from .base import (
    FlowProcessingMetrics,
    TENANT_AGENT_POOL_AVAILABLE,
    INTELLIGENT_AGENT_AVAILABLE,
    FlowIntelligenceResult,
    IntelligentFlowAgent,
)

from .commands import (
    use_intelligent_agent,
    _execute_data_cleansing_if_needed,
    _handle_fast_path_processing,
    _handle_simple_logic_processing,
    _handle_ai_processing,
    _update_phase_if_needed,
    _validate_flow_phase,
)

from .queries import (
    process_flow_continuation,
    get_flow_processing_metrics as _get_flow_processing_metrics,
)

from .utils import (
    extract_flow_metadata,
    is_phase_completed,
    get_next_required_phase,
    calculate_flow_progress,
    format_execution_time,
    create_agent_insight,
    validate_flow_continuation_request,
    sanitize_flow_data_for_logging,
    determine_routing_path,
    extract_error_context,
)

# Import models from the existing modular files (they were already extracted)
from ..flow_processing_models import (
    FlowContinuationRequest,
    FlowContinuationResponse,
)

# Import legacy functions for backward compatibility
from ..flow_processing_legacy import (
    validate_flow_phases,
    validate_phase_data,
)

logger = logging.getLogger(__name__)

# Create the FastAPI router
router = APIRouter()

# Global metrics instance (preserved from original)
flow_metrics = FlowProcessingMetrics()

# ===== MAIN ENDPOINTS (preserved from original) =====


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

    This endpoint handler delegates to the modular query processor while
    maintaining the exact same API contract as the original monolithic version.
    """
    return await process_flow_continuation(
        flow_id=flow_id,
        request=request,
        context=context,
        db=db,
        flow_metrics=flow_metrics,
    )


@router.get("/metrics")
async def get_flow_processing_metrics():
    """
    Get flow processing performance metrics (FIX for Issue #9)

    Returns statistics on fast-path vs AI-path usage and latencies

    This endpoint maintains the same response format as the original
    while delegating to the modular metrics query processor.
    """
    return await _get_flow_processing_metrics(flow_metrics)


# ===== BACKWARD COMPATIBILITY EXPORTS =====

# Export all classes and functions that were available in the original module
# This ensures that any existing imports will continue to work unchanged

__all__ = [
    # Main components
    "router",
    "flow_metrics",
    "FlowProcessingMetrics",
    # Endpoint handlers
    "continue_flow_processing",
    "get_flow_processing_metrics",
    # Agent utilities
    "use_intelligent_agent",
    "TENANT_AGENT_POOL_AVAILABLE",
    "INTELLIGENT_AGENT_AVAILABLE",
    "FlowIntelligenceResult",
    "IntelligentFlowAgent",
    # Data models
    "FlowContinuationRequest",
    "FlowContinuationResponse",
    # Internal functions (for other modules that might import them)
    "_execute_data_cleansing_if_needed",
    "_handle_fast_path_processing",
    "_handle_simple_logic_processing",
    "_handle_ai_processing",
    "_update_phase_if_needed",
    "_validate_flow_phase",
    # Legacy functions (preserved for backward compatibility)
    "validate_flow_phases",
    "validate_phase_data",
    # Utility functions
    "extract_flow_metadata",
    "is_phase_completed",
    "get_next_required_phase",
    "calculate_flow_progress",
    "format_execution_time",
    "create_agent_insight",
    "validate_flow_continuation_request",
    "sanitize_flow_data_for_logging",
    "determine_routing_path",
    "extract_error_context",
]

# Log successful modularization
logger.info(
    "✅ Flow processing module successfully modularized with backward compatibility"
)
