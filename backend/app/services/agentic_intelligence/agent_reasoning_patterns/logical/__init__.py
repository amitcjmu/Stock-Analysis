"""
Logical Reasoning Patterns Module

This module contains logical reasoning patterns that agents use to analyze assets
and discover business value, risk factors, and modernization opportunities.
These patterns represent structured business logic and technical analysis rules.
"""

# Import all classes from the submodules
from .asset_patterns import AssetReasoningPatterns
from .business_value import BusinessValueReasoningPattern
from .modernization import ModernizationReasoningPattern
from .risk_assessment import RiskAssessmentReasoningPattern

# Re-export all classes for convenience
__all__ = [
    "AssetReasoningPatterns",
    "BusinessValueReasoningPattern",
    "RiskAssessmentReasoningPattern",
    "ModernizationReasoningPattern",
]
