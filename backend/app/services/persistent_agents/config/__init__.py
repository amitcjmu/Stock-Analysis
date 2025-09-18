"""
Agent Configuration Module

Modularized agent configuration components for the persistent agents system.
Maintains backward compatibility while improving code organization.
"""

# Import main classes for backward compatibility
from .agent_wrapper import AgentWrapper
from .health import AgentHealth
from .manager import AgentConfigManager

__all__ = ["AgentWrapper", "AgentHealth", "AgentConfigManager"]
