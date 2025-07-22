"""
Tier Routing Service Data Models
Team C1 - Task C1.3

Data models for tier analysis and routing decisions.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .enums import AutomationTier, EnvironmentComplexity


@dataclass
class TierAnalysis:
    """Result of tier detection analysis"""
    recommended_tier: AutomationTier
    confidence_score: float
    environment_complexity: EnvironmentComplexity
    platform_coverage: Dict[str, float]
    automation_feasibility: Dict[str, float]
    risk_assessment: Dict[str, Any]
    quality_prediction: Dict[str, float]
    execution_time_estimate: Dict[str, int]
    resource_requirements: Dict[str, Any]
    alternative_tiers: List[Tuple[AutomationTier, float]]
    routing_metadata: Dict[str, Any]


@dataclass
class RoutingDecision:
    """Routing decision with execution path"""
    selected_tier: AutomationTier
    execution_path: List[str]
    phase_configuration: Dict[str, Any]
    quality_thresholds: Dict[str, float]
    timeout_configuration: Dict[str, int]
    adapter_selection: List[Dict[str, Any]]
    manual_collection_strategy: Optional[Dict[str, Any]]
    fallback_options: List[Dict[str, Any]]
    routing_confidence: float
    decision_metadata: Dict[str, Any]