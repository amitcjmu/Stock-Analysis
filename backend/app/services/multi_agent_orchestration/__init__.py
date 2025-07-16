"""
Multi-Agent Orchestration System

This module provides a comprehensive multi-agent orchestration system that:
- Spawns and manages multiple agents as separate processes or threads
- Implements workflow state machines with proper state transitions
- Provides inter-agent communication and coordination
- Executes actual agent tasks, not just documentation
- Follows the defined issue resolution workflow
"""

from .orchestrator import MultiAgentOrchestrator
from .workflow_engine import WorkflowEngine
from .agent_manager import AgentManager
from .communication import InterAgentCommunicator
from .state_machine import WorkflowStateMachine
from .agents import BaseAgent, UITestingAgent, BackendMonitoringAgent, SecurityAuditAgent

__all__ = [
    'MultiAgentOrchestrator',
    'WorkflowEngine', 
    'AgentManager',
    'InterAgentCommunicator',
    'WorkflowStateMachine',
    'BaseAgent',
    'UITestingAgent',
    'BackendMonitoringAgent',
    'SecurityAuditAgent'
]