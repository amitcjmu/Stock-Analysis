"""
Tier Detection and Routing Service
Team C1 - Task C1.3

This file maintains backward compatibility by re-exporting all interfaces from the modularized components.
The actual implementation has been moved to the tier_routing_service/ subdirectory.

For new imports, consider importing directly from the submodules:
- from app.services.workflow_orchestration.tier_routing_service.enums import AutomationTier
- from app.services.workflow_orchestration.tier_routing_service.models import TierAnalysis
- from app.services.workflow_orchestration.tier_routing_service.service import TierRoutingService
"""

# Re-export all public interfaces for backward compatibility
from .tier_routing_service import (
    # Enums
    AutomationTier,
    EnvironmentComplexity,
    RoutingDecision,
    RoutingStrategy,
    # Models
    TierAnalysis,
    # Main Service
    TierRoutingService,
)

__all__ = [
    'AutomationTier',
    'RoutingStrategy',
    'EnvironmentComplexity',
    'TierAnalysis',
    'RoutingDecision',
    'TierRoutingService'
]