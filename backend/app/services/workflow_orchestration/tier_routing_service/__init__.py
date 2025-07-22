"""
Tier Detection and Routing Service Module
Team C1 - Task C1.3

Modularized components for intelligent tier detection and routing logic.
"""

# Re-export all public interfaces for backward compatibility
from .enums import AutomationTier, EnvironmentComplexity, RoutingStrategy
from .models import RoutingDecision, TierAnalysis
from .service import TierRoutingService

__all__ = [
    'AutomationTier',
    'RoutingStrategy', 
    'EnvironmentComplexity',
    'TierAnalysis',
    'RoutingDecision',
    'TierRoutingService'
]