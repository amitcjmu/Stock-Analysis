"""
Comprehensive Agent Registry Service
Central registry for all agents across all phases with detailed metadata and observability support.

MODULAR STRUCTURE:
- Base types and classes: ./agent_registry/base.py
- Core registry functionality: ./agent_registry/registry_core.py
- Lifecycle management: ./agent_registry/lifecycle_manager.py
- Phase-specific agents: ./agent_registry/phase_agents.py
- Complete registry implementation: ./agent_registry/registry.py

Generated with CC for modular backend architecture.
"""

import logging

# Import modular components
from .agent_registry import (
    AgentPhase,
    AgentStatus, 
    AgentRegistration,
    AgentRegistry as ModularAgentRegistry
)

# For backward compatibility - re-export all classes
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


# Backward compatibility: Delegate to modular implementation
class AgentRegistry(ModularAgentRegistry):
    """Central registry for all platform agents - delegates to modular implementation"""
    pass


# Global registry instance - maintaining backward compatibility
agent_registry = AgentRegistry()