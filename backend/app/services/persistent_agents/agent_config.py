"""
Agent Configuration Module - Backward Compatibility Facade

This file maintains backward compatibility while the implementation
has been modularized for better code organization.
"""

# Import from the modular implementation
from .config import AgentWrapper, AgentHealth, AgentConfigManager

# Maintain backward compatibility
__all__ = ["AgentWrapper", "AgentHealth", "AgentConfigManager"]
