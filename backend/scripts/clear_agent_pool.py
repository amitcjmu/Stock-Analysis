#!/usr/bin/env python3
"""Clear persistent agent pool to force recreation with new tool configuration."""

import asyncio
import sys
from pathlib import Path

# Add backend to path - must be done before local imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Import from app after path is set (flake8: noqa: E402)
from app.services.persistent_agents.tenant_scoped_agent_pool import (  # noqa: E402
    TenantScopedAgentPool,
)


async def clear_pool():
    """Clear all persistent agents."""
    print("Clearing persistent agent pool...")
    # Access the class variable directly
    TenantScopedAgentPool._agent_pools.clear()
    print(
        "✅ Agent pool cleared. Agents will be recreated with new tool configuration on next use."
    )


if __name__ == "__main__":
    asyncio.run(clear_pool())
