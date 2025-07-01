"""
Discovery Flow Repository - Modularized

This file now imports from the modularized discovery_flow_repository package.
The original 705-line file has been split into:

- base_repository.py: Main repository class
- queries/: Read operations for flows and assets
- commands/: Write operations for flows and assets
- specifications/: Reusable query specifications

For backward compatibility, the DiscoveryFlowRepository is re-exported.
"""

# Re-export the main repository from the package
from .discovery_flow_repository import DiscoveryFlowRepository

__all__ = ['DiscoveryFlowRepository']