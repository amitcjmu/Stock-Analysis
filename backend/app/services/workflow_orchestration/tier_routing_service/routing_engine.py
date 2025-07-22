"""
Routing Decision Engine Module
Team C1 - Task C1.3

Core routing decision making and execution path generation.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

from .enums import AutomationTier, EnvironmentComplexity, RoutingStrategy
from .models import RoutingDecision, TierAnalysis

logger = get_logger(__name__)


class RoutingEngine:
    """Handles routing decisions and execution path generation"""
    
    async def make_routing_decision(
        self,
        tier_analysis: TierAnalysis,
        routing_strategy: RoutingStrategy,
        client_requirements: Dict[str, Any],
        environment_config: Dict[str, Any]
    ) -> RoutingDecision:
        """Make final routing decision based on analysis and strategy"""
        
        # Apply routing strategy adjustments
        selected_tier = await self._apply_routing_strategy(
            tier_analysis=tier_analysis,
            strategy=routing_strategy,
            client_requirements=client_requirements
        )
        
        # Generate execution path
        execution_path = await self._generate_execution_path(
            selected_tier=selected_tier,
            environment_config=environment_config,
            complexity=tier_analysis.environment_complexity
        )
        
        # Configure phases
        phase_configuration = await self._configure_phases_for_tier(
            selected_tier=selected_tier,
            tier_analysis=tier_analysis,
            client_requirements=client_requirements
        )
        
        # Set quality thresholds
        quality_thresholds = await self._set_quality_thresholds_for_tier(
            selected_tier=selected_tier,
            client_requirements=client_requirements
        )
        
        # Configure timeouts
        timeout_configuration = await self._configure_timeouts_for_tier(
            selected_tier=selected_tier,
            complexity=tier_analysis.environment_complexity
        )
        
        # Select adapters
        adapter_selection = await self._select_adapters_for_tier(
            selected_tier=selected_tier,
            environment_config=environment_config,
            platform_coverage=tier_analysis.platform_coverage
        )
        
        # Configure manual collection strategy
        manual_strategy = await self._configure_manual_collection_strategy(
            selected_tier=selected_tier,
            tier_analysis=tier_analysis,
            client_requirements=client_requirements
        ) if selected_tier != AutomationTier.TIER_1 else None
        
        # Generate fallback options
        fallback_options = await self._generate_fallback_options(
            selected_tier=selected_tier,
            tier_analysis=tier_analysis
        )
        
        # Calculate routing confidence
        routing_confidence = await self._calculate_routing_confidence(
            selected_tier=selected_tier,
            tier_analysis=tier_analysis,
            routing_strategy=routing_strategy
        )
        
        return RoutingDecision(
            selected_tier=selected_tier,
            execution_path=execution_path,
            phase_configuration=phase_configuration,
            quality_thresholds=quality_thresholds,
            timeout_configuration=timeout_configuration,
            adapter_selection=adapter_selection,
            manual_collection_strategy=manual_strategy,
            fallback_options=fallback_options,
            routing_confidence=routing_confidence,
            decision_metadata={
                "routing_strategy": routing_strategy.value,
                "decision_timestamp": datetime.utcnow().isoformat(),
                "selected_from_alternatives": len(tier_analysis.alternative_tiers),
                "complexity_level": tier_analysis.environment_complexity.value
            }
        )
    
    async def _apply_routing_strategy(
        self, 
        tier_analysis: TierAnalysis, 
        strategy: RoutingStrategy, 
        client_requirements: Dict[str, Any]
    ) -> AutomationTier:
        """Apply routing strategy to select tier"""
        if strategy == RoutingStrategy.AGGRESSIVE:
            # Prefer highest automation
            return max(tier_analysis.alternative_tiers + [(tier_analysis.recommended_tier, tier_analysis.confidence_score)], 
                      key=lambda x: (x[0].value == "tier_1", x[1]))[0]
        elif strategy == RoutingStrategy.CONSERVATIVE:
            # Prefer reliability over speed
            return AutomationTier.TIER_4 if tier_analysis.confidence_score < 0.8 else tier_analysis.recommended_tier
        else:  # BALANCED or ADAPTIVE
            return tier_analysis.recommended_tier
    
    async def _generate_execution_path(
        self, 
        selected_tier: AutomationTier, 
        environment_config: Dict[str, Any], 
        complexity: EnvironmentComplexity
    ) -> List[str]:
        """Generate execution path for selected tier"""
        base_path = ["platform_detection", "automated_collection", "gap_analysis", "synthesis"]
        if selected_tier != AutomationTier.TIER_1:
            base_path.insert(-1, "manual_collection")
        return base_path
    
    async def _configure_phases_for_tier(
        self, 
        selected_tier: AutomationTier, 
        tier_analysis: TierAnalysis, 
        client_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Configure phases for selected tier"""
        return {
            "platform_detection": {"enable_ai_assistance": True, "confidence_threshold": 0.8},
            "automated_collection": {"parallel_execution": selected_tier in [AutomationTier.TIER_1, AutomationTier.TIER_2]},
            "gap_analysis": {"depth": "comprehensive"},
            "manual_collection": {"enabled": selected_tier != AutomationTier.TIER_1},
            "synthesis": {"validation_level": "strict" if selected_tier == AutomationTier.TIER_1 else "standard"}
        }
    
    async def _set_quality_thresholds_for_tier(
        self, 
        selected_tier: AutomationTier, 
        client_requirements: Dict[str, Any]
    ) -> Dict[str, float]:
        """Set quality thresholds for selected tier"""
        base_thresholds = {
            AutomationTier.TIER_1: {"overall": 0.95, "collection": 0.95, "synthesis": 0.95},
            AutomationTier.TIER_2: {"overall": 0.85, "collection": 0.85, "synthesis": 0.85},
            AutomationTier.TIER_3: {"overall": 0.75, "collection": 0.75, "synthesis": 0.75},
            AutomationTier.TIER_4: {"overall": 0.60, "collection": 0.60, "synthesis": 0.60}
        }
        return base_thresholds[selected_tier]
    
    async def _configure_timeouts_for_tier(
        self, 
        selected_tier: AutomationTier, 
        complexity: EnvironmentComplexity
    ) -> Dict[str, int]:
        """Configure timeouts for selected tier"""
        base_timeouts = {
            "platform_detection": 600, "automated_collection": 3600,
            "gap_analysis": 900, "manual_collection": 7200, "synthesis": 1200
        }
        multiplier = {
            EnvironmentComplexity.SIMPLE: 1.0, 
            EnvironmentComplexity.MODERATE: 1.3,
            EnvironmentComplexity.COMPLEX: 1.6, 
            EnvironmentComplexity.ENTERPRISE: 2.0
        }[complexity]
        return {phase: int(timeout * multiplier) for phase, timeout in base_timeouts.items()}
    
    async def _select_adapters_for_tier(
        self, 
        selected_tier: AutomationTier, 
        environment_config: Dict[str, Any], 
        platform_coverage: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Select adapters for selected tier"""
        adapters = []
        for platform in environment_config.get("platforms", []):
            adapter_type = platform.get("type", "").lower()
            adapters.append({
                "platform": platform,
                "adapter_type": adapter_type,
                "priority": "high" if platform_coverage.get(adapter_type, 0) > 0.8 else "medium"
            })
        return adapters
    
    async def _configure_manual_collection_strategy(
        self, 
        selected_tier: AutomationTier, 
        tier_analysis: TierAnalysis, 
        client_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Configure manual collection strategy"""
        return {
            "enabled": True,
            "questionnaire_depth": "comprehensive" if selected_tier == AutomationTier.TIER_4 else "targeted",
            "validation_level": "strict",
            "user_engagement": "high" if selected_tier in [AutomationTier.TIER_3, AutomationTier.TIER_4] else "medium"
        }
    
    async def _generate_fallback_options(
        self, 
        selected_tier: AutomationTier, 
        tier_analysis: TierAnalysis
    ) -> List[Dict[str, Any]]:
        """Generate fallback options"""
        fallbacks = []
        for alt_tier, confidence in tier_analysis.alternative_tiers[:2]:  # Top 2 alternatives
            fallbacks.append({
                "tier": alt_tier.value,
                "confidence": confidence,
                "trigger_conditions": ["quality_below_threshold", "execution_timeout"]
            })
        return fallbacks
    
    async def _calculate_routing_confidence(
        self, 
        selected_tier: AutomationTier, 
        tier_analysis: TierAnalysis, 
        routing_strategy: RoutingStrategy
    ) -> float:
        """Calculate routing confidence"""
        base_confidence = tier_analysis.confidence_score
        strategy_adjustment = {
            RoutingStrategy.AGGRESSIVE: 0.9, 
            RoutingStrategy.BALANCED: 1.0,
            RoutingStrategy.CONSERVATIVE: 1.1, 
            RoutingStrategy.ADAPTIVE: 1.05
        }[routing_strategy]
        return min(1.0, base_confidence * strategy_adjustment)