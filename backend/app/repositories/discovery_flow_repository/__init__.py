"""
Discovery Flow Repository Package

Modularized repository split into:
- base_repository.py: Base repository class with context awareness
- queries/: Read operations for fetching flows and assets
- commands/: Write operations for creating and updating flows
- specifications/: Query specifications and filters
"""

# Re-export main repository for backward compatibility
from .base_repository import DiscoveryFlowRepository

__all__ = ['DiscoveryFlowRepository']