"""
Decommission Agent Pool Package

Modularized agent pool implementation for decommission workflow.

This package provides backward-compatible imports for the DecommissionAgentPool
while organizing code into logical modules.

Package Structure:
- agent_configs.py: Agent configuration definitions (173 lines)
- crew_factory.py: Crew creation methods (398 lines)
- pool.py: Main agent pool class (264 lines)

Total: ~835 lines split across 3 modules (all under 400 line limit)

Per ADR-024: All agents and crews use memory=False. Use TenantMemoryManager for learning.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

# Preserve backward compatibility by exporting all public symbols
from .agent_configs import DECOMMISSION_AGENT_CONFIGS
from .pool import DecommissionAgentPool

__all__ = ["DecommissionAgentPool", "DECOMMISSION_AGENT_CONFIGS"]
