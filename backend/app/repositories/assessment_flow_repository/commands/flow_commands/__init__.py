"""
Flow commands for assessment flow operations.

This module provides backward-compatible exports for the modularized FlowCommands class.
"""

from .base import FlowCommands
from .creation import create_assessment_flow
from .updates import update_flow_phase, save_user_input, save_agent_insights
from .resumption import resume_flow
from .phase_results import PhaseResultsPersistence

# Attach methods to FlowCommands class for backward compatibility
FlowCommands.create_assessment_flow = create_assessment_flow
FlowCommands.update_flow_phase = update_flow_phase
FlowCommands.save_user_input = save_user_input
FlowCommands.save_agent_insights = save_agent_insights
FlowCommands.resume_flow = resume_flow

__all__ = ["FlowCommands", "PhaseResultsPersistence"]
