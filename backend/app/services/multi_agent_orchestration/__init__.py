"""
Multi-Agent Orchestration System

This module provides a comprehensive multi-agent orchestration system that:
- Spawns and manages multiple agents as separate processes or threads
- Implements workflow state machines with proper state transitions
- Provides inter-agent communication and coordination
- Executes actual agent tasks, not just documentation
- Follows the defined issue resolution workflow
"""

from .agent_manager import AgentManager
from .agents import (BackendMonitoringAgent, BaseAgent, SecurityAuditAgent,
                     UITestingAgent)
from .communication import InterAgentCommunicator
from .orchestrator import MultiAgentOrchestrator
from .state_machine import WorkflowStateMachine
from .workflow_engine import WorkflowEngine

__all__ = [
    "MultiAgentOrchestrator",
    "WorkflowEngine",
    "AgentManager",
    "InterAgentCommunicator",
    "WorkflowStateMachine",
    "BaseAgent",
    "UITestingAgent",
    "BackendMonitoringAgent",
    "SecurityAuditAgent",
]
