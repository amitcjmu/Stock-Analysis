"""
Master Flow Orchestrator - Backward Compatibility Module

This module maintains backward compatibility by re-exporting all public interfaces
from the modularized master_flow_orchestrator package.

The actual implementation has been moved to:
- master_flow_orchestrator/core.py - Main orchestrator class
- master_flow_orchestrator/enums.py - Enumerations
- master_flow_orchestrator/flow_operations.py - Flow lifecycle operations
- master_flow_orchestrator/status_operations.py - Status management
- master_flow_orchestrator/status_sync_operations.py - ADR-012 sync operations
- master_flow_orchestrator/monitoring_operations.py - Performance and audit operations
- master_flow_orchestrator/mock_monitor.py - Mock performance monitor
"""

# Re-export all public interfaces for backward compatibility
from app.services.master_flow_orchestrator.core import MasterFlowOrchestrator
from app.services.master_flow_orchestrator.enums import FlowOperationType
from app.services.master_flow_orchestrator.mock_monitor import MockFlowPerformanceMonitor

__all__ = [
    'MasterFlowOrchestrator',
    'FlowOperationType',
    'MockFlowPerformanceMonitor'
]