"""
API endpoints package.
"""

from . import sixr_analysis
from . import discovery
from . import asset_inventory
from . import monitoring
from . import chat
from . import websocket
from . import agent_learning_endpoints
from . import data_import
from . import sessions
from . import context
from . import test_discovery
from .agents import router as agents_router

# Expose the routers for the main api.py to collect
sixr_router = sixr_analysis.router
discovery_router = discovery.router
asset_inventory_router = asset_inventory.router
monitoring_router = monitoring.router
chat_router = chat.router
websocket_router = websocket.router
agent_learning_router = agent_learning_endpoints.router
data_import_router = data_import.router
sessions_router = sessions.router
context_router = context.router
test_discovery_router = test_discovery.router
# agents_router is already imported above 