"""
Tier Analysis Module
Team C1 - Task C1.3

Core tier analysis and scoring logic.
"""

from datetime import datetime
from typing import Any, Dict

from app.core.logging import get_logger

from .enums import AutomationTier, EnvironmentComplexity
from .models import TierAnalysis

logger = get_logger(__name__)


class TierAnalyzer:
    """Handles tier analysis and scoring logic"""
    
    def __init__(self):
        """Initialize the Tier Analyzer"""
        self.tier_weights = {
            AutomationTier.TIER_1: {"speed": 1.0, "reliability": 0.8, "coverage": 0.9},
            AutomationTier.TIER_2: {"speed": 0.9, "reliability": 0.9, "coverage": 0.95},
            AutomationTier.TIER_3: {"speed": 0.7, "reliability": 0.95, "coverage": 0.98},
            AutomationTier.TIER_4: {"speed": 0.5, "reliability": 0.99, "coverage": 1.0}
        }
        
        self.platform_compatibility = {
            "aws": {"tier_1": 0.95, "tier_2": 0.98, "tier_3": 0.99, "tier_4": 1.0},
            "azure": {"tier_1": 0.90, "tier_2": 0.95, "tier_3": 0.98, "tier_4": 1.0},
            "gcp": {"tier_1": 0.85, "tier_2": 0.92, "tier_3": 0.97, "tier_4": 1.0},
            "vmware": {"tier_1": 0.70, "tier_2": 0.85, "tier_3": 0.95, "tier_4": 1.0},
            "kubernetes": {"tier_1": 0.80, "tier_2": 0.90, "tier_3": 0.95, "tier_4": 1.0},
            "on_premise": {"tier_1": 0.60, "tier_2": 0.80, "tier_3": 0.95, "tier_4": 1.0}
        }
    
    async def perform_comprehensive_tier_analysis(
        self,
        environment_config: Dict[str, Any],
        client_requirements: Dict[str, Any],
        base_analysis: Dict[str, Any],
        complexity: EnvironmentComplexity,
        platform_analysis: Dict[str, float],
        quality_requirements: Dict[str, float]
    ) -> TierAnalysis:
        """Perform comprehensive tier analysis"""
        
        # Calculate scores for each tier
        tier_scores = {}
        alternative_tiers = []
        
        for tier in AutomationTier:
            score = await self.calculate_tier_score(
                tier=tier,
                environment_config=environment_config,
                client_requirements=client_requirements,
                complexity=complexity,
                platform_analysis=platform_analysis,
                quality_requirements=quality_requirements
            )
            
            tier_scores[tier] = score
            alternative_tiers.append((tier, score))
        
        # Sort alternatives by score
        alternative_tiers.sort(key=lambda x: x[1], reverse=True)
        recommended_tier = alternative_tiers[0][0]
        confidence_score = alternative_tiers[0][1]
        
        # Generate detailed analysis
        return TierAnalysis(
            recommended_tier=recommended_tier,
            confidence_score=confidence_score,
            environment_complexity=complexity,
            platform_coverage=await self._calculate_platform_coverage_scores(platform_analysis),
            automation_feasibility=await self._assess_automation_feasibility(
                environment_config, complexity
            ),
            risk_assessment=await self._perform_risk_assessment(
                recommended_tier, environment_config, complexity
            ),
            quality_prediction=await self._predict_quality_scores(
                recommended_tier, environment_config, complexity
            ),
            execution_time_estimate=await self._estimate_execution_times(
                recommended_tier, environment_config, complexity
            ),
            resource_requirements=await self._calculate_resource_requirements(
                recommended_tier, environment_config
            ),
            alternative_tiers=alternative_tiers[1:],  # Exclude the recommended one
            routing_metadata={
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "tier_scores": {tier.value: score for tier, score in tier_scores.items()},
                "complexity_factors": {
                    "platform_count": len(environment_config.get("platforms", [])),
                    "integration_count": len(environment_config.get("integrations", [])),
                    "custom_config_count": len(environment_config.get("custom_configurations", {}))
                }
            }
        )
    
    async def calculate_tier_score(
        self,
        tier: AutomationTier,
        environment_config: Dict[str, Any],
        client_requirements: Dict[str, Any],
        complexity: EnvironmentComplexity,
        platform_analysis: Dict[str, float],
        quality_requirements: Dict[str, float]
    ) -> float:
        """Calculate score for a specific tier"""
        
        score = 0.0
        self.tier_weights[tier]
        
        # Platform compatibility score
        platform_score = 0.0
        platforms = environment_config.get("platforms", [])
        for platform in platforms:
            platform_type = platform.get("type", "").lower()
            if platform_type in platform_analysis:
                tier_compat = platform_analysis[platform_type].get(tier.value, 0.0)
                platform_score += tier_compat
        
        if platforms:
            platform_score /= len(platforms)
        
        score += platform_score * 0.3  # 30% weight
        
        # Complexity compatibility
        complexity_weights = {
            EnvironmentComplexity.SIMPLE: {
                AutomationTier.TIER_1: 1.0, AutomationTier.TIER_2: 0.9,
                AutomationTier.TIER_3: 0.8, AutomationTier.TIER_4: 0.7
            },
            EnvironmentComplexity.MODERATE: {
                AutomationTier.TIER_1: 0.8, AutomationTier.TIER_2: 1.0,
                AutomationTier.TIER_3: 0.9, AutomationTier.TIER_4: 0.8
            },
            EnvironmentComplexity.COMPLEX: {
                AutomationTier.TIER_1: 0.6, AutomationTier.TIER_2: 0.9,
                AutomationTier.TIER_3: 1.0, AutomationTier.TIER_4: 0.9
            },
            EnvironmentComplexity.ENTERPRISE: {
                AutomationTier.TIER_1: 0.4, AutomationTier.TIER_2: 0.7,
                AutomationTier.TIER_3: 0.9, AutomationTier.TIER_4: 1.0
            }
        }
        
        complexity_score = complexity_weights[complexity][tier]
        score += complexity_score * 0.25  # 25% weight
        
        # Quality requirement alignment
        min_quality = quality_requirements.get("overall", 0.8)
        tier_quality_capability = {
            AutomationTier.TIER_1: 0.95, AutomationTier.TIER_2: 0.85,
            AutomationTier.TIER_3: 0.75, AutomationTier.TIER_4: 0.60
        }
        
        quality_score = min(1.0, tier_quality_capability[tier] / min_quality) if min_quality > 0 else 1.0
        score += quality_score * 0.25  # 25% weight
        
        # Client preference alignment
        preferred_tier = client_requirements.get("preferred_automation_tier")
        if preferred_tier:
            preference_score = 1.0 if tier.value == preferred_tier else 0.5
            score += preference_score * 0.2  # 20% weight
        else:
            score += 0.8 * 0.2  # Neutral score
        
        return min(1.0, score)
    
    async def _calculate_platform_coverage_scores(self, platform_analysis: Dict[str, float]) -> Dict[str, float]:
        """Calculate platform coverage scores"""
        coverage_scores = {}
        for platform, tier_coverage in platform_analysis.items():
            coverage_scores[platform] = sum(tier_coverage.values()) / len(tier_coverage)
        return coverage_scores
    
    async def _assess_automation_feasibility(self, environment_config: Dict[str, Any], complexity: EnvironmentComplexity) -> Dict[str, float]:
        """Assess automation feasibility"""
        base_feasibility = {
            EnvironmentComplexity.SIMPLE: 0.9,
            EnvironmentComplexity.MODERATE: 0.8,
            EnvironmentComplexity.COMPLEX: 0.7,
            EnvironmentComplexity.ENTERPRISE: 0.6
        }[complexity]
        
        return {
            "platform_detection": base_feasibility,
            "automated_collection": base_feasibility * 0.9,
            "gap_analysis": base_feasibility * 0.95,
            "synthesis": base_feasibility * 0.85
        }
    
    async def _perform_risk_assessment(self, tier: AutomationTier, environment_config: Dict[str, Any], complexity: EnvironmentComplexity) -> Dict[str, Any]:
        """Perform risk assessment for tier selection"""
        base_risk = {
            AutomationTier.TIER_1: 0.3,
            AutomationTier.TIER_2: 0.2,
            AutomationTier.TIER_3: 0.15,
            AutomationTier.TIER_4: 0.1
        }[tier]
        
        complexity_risk_multiplier = {
            EnvironmentComplexity.SIMPLE: 1.0,
            EnvironmentComplexity.MODERATE: 1.2,
            EnvironmentComplexity.COMPLEX: 1.5,
            EnvironmentComplexity.ENTERPRISE: 1.8
        }[complexity]
        
        overall_risk = min(1.0, base_risk * complexity_risk_multiplier)
        
        return {
            "overall_risk": overall_risk,
            "automation_risk": base_risk,
            "complexity_risk": complexity_risk_multiplier - 1.0,
            "risk_factors": [
                "High automation tier with complex environment" if tier == AutomationTier.TIER_1 and complexity in [EnvironmentComplexity.COMPLEX, EnvironmentComplexity.ENTERPRISE] else None,
                "Large number of platforms" if len(environment_config.get("platforms", [])) > 5 else None,
                "Custom configurations present" if environment_config.get("custom_configurations") else None
            ]
        }
    
    async def _predict_quality_scores(self, tier: AutomationTier, environment_config: Dict[str, Any], complexity: EnvironmentComplexity) -> Dict[str, float]:
        """Predict quality scores for tier selection"""
        base_quality = {
            AutomationTier.TIER_1: {"overall": 0.95, "speed": 0.95, "coverage": 0.85},
            AutomationTier.TIER_2: {"overall": 0.85, "speed": 0.85, "coverage": 0.95},
            AutomationTier.TIER_3: {"overall": 0.75, "speed": 0.75, "coverage": 0.98},
            AutomationTier.TIER_4: {"overall": 0.60, "speed": 0.60, "coverage": 1.0}
        }[tier]
        
        complexity_adjustment = {
            EnvironmentComplexity.SIMPLE: 1.0,
            EnvironmentComplexity.MODERATE: 0.95,
            EnvironmentComplexity.COMPLEX: 0.9,
            EnvironmentComplexity.ENTERPRISE: 0.85
        }[complexity]
        
        return {
            aspect: score * complexity_adjustment
            for aspect, score in base_quality.items()
        }
    
    async def _estimate_execution_times(self, tier: AutomationTier, environment_config: Dict[str, Any], complexity: EnvironmentComplexity) -> Dict[str, int]:
        """Estimate execution times for tier selection"""
        base_times = {
            AutomationTier.TIER_1: {"total": 3600000, "platform_detection": 600000, "collection": 1800000},  # 1 hour
            AutomationTier.TIER_2: {"total": 5400000, "platform_detection": 900000, "collection": 2700000},  # 1.5 hours  
            AutomationTier.TIER_3: {"total": 7200000, "platform_detection": 1200000, "collection": 3600000},  # 2 hours
            AutomationTier.TIER_4: {"total": 10800000, "platform_detection": 1800000, "collection": 5400000}  # 3 hours
        }[tier]
        
        complexity_multiplier = {
            EnvironmentComplexity.SIMPLE: 1.0,
            EnvironmentComplexity.MODERATE: 1.3,
            EnvironmentComplexity.COMPLEX: 1.6,
            EnvironmentComplexity.ENTERPRISE: 2.0
        }[complexity]
        
        return {
            aspect: int(time_ms * complexity_multiplier)
            for aspect, time_ms in base_times.items()
        }
    
    async def _calculate_resource_requirements(self, tier: AutomationTier, environment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate resource requirements for tier selection"""
        return {
            "cpu_intensive": tier in [AutomationTier.TIER_1, AutomationTier.TIER_2],
            "memory_requirements": "high" if tier == AutomationTier.TIER_1 else "medium",
            "network_requirements": "high" if len(environment_config.get("platforms", [])) > 3 else "medium",
            "storage_requirements": "medium",
            "concurrent_adapters": 5 if tier == AutomationTier.TIER_1 else 3
        }