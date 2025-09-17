"""
Base classes, constants, and imports for dependency analysis tools.

This module contains the core infrastructure and constants used across
all dependency analysis functionality.
"""

import logging

logger = logging.getLogger(__name__)

# Import CrewAI tools
try:
    from crewai.tools import BaseTool

    CREWAI_TOOLS_AVAILABLE = True
except ImportError:
    CREWAI_TOOLS_AVAILABLE = False

    class BaseTool:
        def __init__(self, *args, **kwargs):
            pass


# Constants for dependency analysis
BOTTLENECK_THRESHOLD = 3
HIGH_CONNECTIVITY_THRESHOLD = 5
MAX_CRITICAL_PATHS = 5
LOW_COUPLING_THRESHOLD = 0.1
HIGH_COUPLING_THRESHOLD = 0.5

# Asset type constants
ASSET_TYPE_DATABASE = "database"
ASSET_TYPE_APPLICATION = "application"
ASSET_TYPE_LOAD_BALANCER = "load_balancer"
ASSET_TYPE_SECURITY_GROUP = "security_group"

# Environment constants
PRODUCTION_ENVIRONMENTS = ["production", "prod"]

# Dependency types
DEPENDENCY_TYPE_NETWORK = "network"
DEPENDENCY_TYPE_DATA_FLOW = "data_flow"
DEPENDENCY_TYPE_CONFIG = "configuration"
DEPENDENCY_TYPE_SERVICE = "service"

# Risk levels
RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"
RISK_CRITICAL = "critical"

# Flow types
FLOW_TYPE_READ_WRITE = "read_write"
FLOW_TYPE_NETWORK_CONNECTION = "network_connection"

# Analysis types
ANALYSIS_TYPE_BOTTLENECK = "bottleneck"
ANALYSIS_TYPE_CIRCULAR_DEPENDENCY = "circular_dependency"
ANALYSIS_TYPE_LOW_COUPLING = "low_coupling"
ANALYSIS_TYPE_HIGH_COUPLING = "high_coupling"
ANALYSIS_TYPE_CRITICAL_PATH = "critical_path"
