"""
Agent Monitoring API Endpoints
Provides real-time observability into CrewAI agent task execution for the frontend.
Enhanced with comprehensive agent registry and phase organization.

This module now serves as the main entry point that combines all monitoring sub-modules.
All functionality has been modularized into separate files for better organization:
- agent_monitoring.py: Agent status, tasks, and registry management
- health_metrics.py: System health and performance metrics
- crewai_flow_monitoring.py: CrewAI flow-specific monitoring
- crew_monitoring.py: Phase 2 crew system monitoring
- error_monitoring.py: Background task and error tracking
"""

from fastapi import APIRouter

# Import all sub-routers from monitoring modules
from .monitoring.agent_monitoring import router as agent_router
from .monitoring.crewai_flow_monitoring import router as crewai_flow_router
from .monitoring.error_monitoring import router as error_router
from .monitoring.health_metrics import router as health_router

# Create main monitoring router
router = APIRouter()

# Include all sub-routers
# Agent monitoring endpoints
router.include_router(agent_router, tags=["Agent Monitoring"])

# Health and metrics endpoints
router.include_router(health_router, tags=["Health & Metrics"])

# CrewAI flow monitoring endpoints
router.include_router(crewai_flow_router, tags=["CrewAI Flow Monitoring"])

# Phase 2 crew monitoring endpoints - REMOVED (legacy code cleaned up)

# Error monitoring endpoints
router.include_router(error_router, tags=["Error Monitoring"])

# For backward compatibility, we maintain all the same endpoints
# They are now just organized into separate modules for better maintainability
