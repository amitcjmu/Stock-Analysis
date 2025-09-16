"""
Base Flow Module - Modularized Version

The main UnifiedDiscoveryFlow class that orchestrates all phases.
This modularized version extracts large methods into separate utility classes
for better maintainability and code organization.

This __init__.py preserves backward compatibility by exposing the same public API
as the original base_flow.py file.
"""

# Import the main class and factory function
from .base import UnifiedDiscoveryFlow
from .utils import create_unified_discovery_flow

# Export all public symbols to maintain backward compatibility
__all__ = [
    "UnifiedDiscoveryFlow",
    "create_unified_discovery_flow",
]
