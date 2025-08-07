"""
Persistent Agents Package

This package implements ADR-015: Persistent Multi-Tenant Agent Architecture

Key Components:
- TenantScopedAgentPool: Maintains persistent agents per tenant context
- MemoryEnabledAgentFactory: Creates agents with full memory integration
- Agent lifecycle management and health monitoring
"""

from .tenant_scoped_agent_pool import (
    AgentHealth,
    TenantPoolStats,
    TenantScopedAgentPool,
    validate_agent_pool_health,
)

__all__ = [
    "TenantScopedAgentPool",
    "AgentHealth",
    "TenantPoolStats",
    "validate_agent_pool_health",
]
