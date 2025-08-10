"""
Monitoring module for agent and system observability.

This module provides comprehensive monitoring capabilities organized by domain:
- Agent monitoring (agent status, tasks, registry)
- Health & metrics (system health, performance metrics)
- CrewAI flow monitoring
- Phase 2 crew system monitoring
- Error monitoring (background tasks, error tracking)
"""

from .agent_monitoring import router as agent_monitoring_router
from .crewai_flow_monitoring import router as crewai_flow_monitoring_router
from .error_monitoring import router as error_monitoring_router
from .health_metrics import router as health_metrics_router

__all__ = [
    "agent_monitoring_router",
    "health_metrics_router",
    "crewai_flow_monitoring_router",
    "error_monitoring_router",
]
