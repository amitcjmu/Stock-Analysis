"""
API endpoints package.
"""

# WebSocket module removed - using HTTP polling for Vercel+Railway compatibility
from . import (
    agent_learning_endpoints,
    analysis,
    asset_workflow,
    assessment_events,
    assessment_flow_router,
    asset_inventory,
    chat,
    context,
    data_import,
    feedback,
    field_mapping,
    flow_processing,
)
from .agents import router as agents_router

# Import monitoring_main.py to avoid conflict with monitoring directory
from .monitoring_main import router as monitoring_router

# Expose the routers for the main api.py to collect
# sixr_router removed - replaced by Assessment Flow with MFO integration (Phase 4, Issue #840)
# discovery_router removed - functionality moved to unified_discovery
asset_inventory_router = asset_inventory.router
monitoring_router = monitoring_router  # Use the imported monitoring_router
chat_router = chat.router
feedback_router = feedback.router
# websocket_router removed - using HTTP polling for Vercel+Railway compatibility
agent_learning_router = agent_learning_endpoints.router
data_import_router = data_import.router
context_router = context.router
# test_discovery_router removed - was dead code with auth bypass
flow_processing_router = flow_processing.router
assessment_flow_router = assessment_flow_router.router
assessment_events_router = assessment_events.router
agents_router = agents_router  # Use the imported agents_router
analysis_router = analysis.router
asset_workflow_router = asset_workflow.router
field_mapping_router = field_mapping.router
