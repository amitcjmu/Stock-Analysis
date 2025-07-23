"""
Tier Routing Service Enumerations
Team C1 - Task C1.3

Core enumerations for tier routing and decision making.
"""

from enum import Enum


class AutomationTier(Enum):
    """Automation tier levels with capabilities"""

    TIER_1 = "tier_1"  # Full automation - 95%+ automation
    TIER_2 = "tier_2"  # High automation - 85%+ automation with minimal manual
    TIER_3 = "tier_3"  # Moderate automation - 70%+ automation with manual collection
    TIER_4 = "tier_4"  # Manual-heavy - 50%+ automation with significant manual effort


class RoutingStrategy(Enum):
    """Routing strategies for tier assignment"""

    AGGRESSIVE = "aggressive"  # Prefer higher automation tiers
    BALANCED = "balanced"  # Balance automation and reliability
    CONSERVATIVE = "conservative"  # Prefer lower tiers for reliability
    ADAPTIVE = "adaptive"  # Learn and adapt based on results


class EnvironmentComplexity(Enum):
    """Environment complexity levels"""

    SIMPLE = "simple"  # Single platform, standard configuration
    MODERATE = "moderate"  # Multiple platforms, some customization
    COMPLEX = "complex"  # Many platforms, heavy customization
    ENTERPRISE = "enterprise"  # Large scale, complex integrations
