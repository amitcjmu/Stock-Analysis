"""
API endpoints package.
"""

from . import sixr_analysis
from . import discovery
from . import asset_inventory
# Import monitoring_main.py to avoid conflict with monitoring directory
from .monitoring_main import router as monitoring_router
from . import chat
# WebSocket module removed - using HTTP polling for Vercel+Railway compatibility
from . import agent_learning_endpoints
from . import data_import
from . import context
from . import test_discovery
from . import flow_processing
from . import assessment_flow
from . import assessment_events
from .agents import router as agents_router

# Expose the routers for the main api.py to collect
sixr_router = sixr_analysis.router
discovery_router = discovery.router
asset_inventory_router = asset_inventory.router
# monitoring_router is already imported above
chat_router = chat.router
# websocket_router removed - using HTTP polling for Vercel+Railway compatibility
agent_learning_router = agent_learning_endpoints.router
data_import_router = data_import.router
context_router = context.router
test_discovery_router = test_discovery.router
flow_processing_router = flow_processing.router
assessment_flow_router = assessment_flow.router
assessment_events_router = assessment_events.router
# agents_router is already imported above 