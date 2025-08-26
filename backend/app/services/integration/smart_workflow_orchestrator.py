"""
Smart Workflow Orchestrator for ADCS End-to-End Integration - Backward Compatibility Module

This module maintains backward compatibility for existing imports while delegating
to the modularized smart_workflow_orchestrator package.

The actual implementation has been split into:
- smart_workflow_orchestrator/workflow_types.py: Core enums, types, and context classes
- smart_workflow_orchestrator/quality_analyzer.py: Quality analysis and validation functionality
- smart_workflow_orchestrator/flow_manager.py: Flow retrieval and management operations
- smart_workflow_orchestrator/base_orchestrator.py: Main orchestrator class with workflow coordination

All existing imports continue to work without modification.

Generated with CC for ADCS end-to-end integration.
"""

# Re-export all classes from the modularized package for backward compatibility
from .smart_workflow_orchestrator import (
    SmartWorkflowContext,
    SmartWorkflowOrchestrator,
    WorkflowPhase,
    WorkflowTransition,
)

__all__ = [
    "SmartWorkflowOrchestrator",
    "SmartWorkflowContext",
    "WorkflowPhase",
    "WorkflowTransition",
]
