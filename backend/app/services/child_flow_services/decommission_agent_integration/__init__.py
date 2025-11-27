"""
Decommission Flow - Agent Integration Package

Modularized from decommission_agent_integration.py (668 lines → 6 modules).
Maintains backward compatibility - all imports work as before.

ADR Compliance:
- ADR-015: TenantScopedAgentPool for persistent agents
- ADR-024: memory=False in crew, use TenantMemoryManager
- ADR-029: sanitize_for_json on agent output
- ADR-031: CallbackHandlerIntegration for observability tracking

Public API (exported for backward compatibility):
- execute_decommission_planning_with_agents
- execute_data_migration_with_agents
- execute_system_shutdown_with_agents
"""

from .planning import execute_decommission_planning_with_agents
from .migration import execute_data_migration_with_agents
from .shutdown import execute_system_shutdown_with_agents

# Private functions (used internally by the package)
from .base import _create_decommission_task, _get_agents_for_phase
from .fallbacks import (
    _generate_fallback_migration_result,
    _generate_fallback_planning_result,
    _generate_fallback_shutdown_result,
)
from .learning import _store_decommission_learnings

__all__ = [
    # Public API - main phase execution functions
    "execute_decommission_planning_with_agents",
    "execute_data_migration_with_agents",
    "execute_system_shutdown_with_agents",
    # Private helpers (kept for potential internal use)
    "_get_agents_for_phase",
    "_create_decommission_task",
    "_store_decommission_learnings",
    "_generate_fallback_planning_result",
    "_generate_fallback_migration_result",
    "_generate_fallback_shutdown_result",
]
