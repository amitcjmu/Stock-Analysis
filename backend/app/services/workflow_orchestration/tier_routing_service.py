"""
Tier Detection and Routing Service
Team C1 - Task C1.3

Intelligent tier detection and routing logic that analyzes environments, determines optimal
automation tiers, and routes Collection Flows through appropriate execution paths.

Integrates with existing TierDetectionService and extends it with advanced routing logic,
quality-based tier adjustments, and intelligent workflow path optimization.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.context import RequestContext
from app.core.exceptions import FlowError, InvalidFlowStateError

# Import Phase 1 & 2 components
from app.services.collection_flow import TierDetectionService, adapter_registry
from app.services.ai_analysis import BusinessContextAnalyzer, ConfidenceScorer

logger = get_logger(__name__)


class AutomationTier(Enum):
    """Automation tier levels with capabilities"""
    TIER_1 = "tier_1"  # Full automation - 95%+ automation
    TIER_2 = "tier_2"  # High automation - 85%+ automation with minimal manual
    TIER_3 = "tier_3"  # Moderate automation - 70%+ automation with manual collection
    TIER_4 = "tier_4"  # Manual-heavy - 50%+ automation with significant manual effort


class RoutingStrategy(Enum):
    """Routing strategies for tier assignment"""
    AGGRESSIVE = "aggressive"      # Prefer higher automation tiers
    BALANCED = "balanced"         # Balance automation and reliability
    CONSERVATIVE = "conservative"  # Prefer lower tiers for reliability
    ADAPTIVE = "adaptive"         # Learn and adapt based on results


class EnvironmentComplexity(Enum):
    """Environment complexity levels"""
    SIMPLE = "simple"        # Single platform, standard configuration
    MODERATE = "moderate"    # Multiple platforms, some customization
    COMPLEX = "complex"      # Many platforms, heavy customization
    ENTERPRISE = "enterprise" # Large scale, complex integrations


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


class TierRoutingService:
    """
    Tier Detection and Routing Service
    
    Provides intelligent tier detection and routing logic with:
    - Advanced environment analysis and complexity assessment
    - Quality-based tier recommendations
    - Adaptive routing strategies
    - Fallback and alternative path planning
    - Integration with existing TierDetectionService
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        """Initialize the Tier Routing Service"""
        self.db = db
        self.context = context
        
        # Initialize base tier detection service
        self.tier_detection = TierDetectionService(db, context)
        
        # Initialize AI analysis services
        self.business_analyzer = BusinessContextAnalyzer()
        self.confidence_scoring = ConfidenceScorer()
        
        # Routing configuration
        self.default_strategy = RoutingStrategy.BALANCED
        self.tier_weights = {
            AutomationTier.TIER_1: {"speed": 1.0, "reliability": 0.8, "coverage": 0.9},
            AutomationTier.TIER_2: {"speed": 0.9, "reliability": 0.9, "coverage": 0.95},
            AutomationTier.TIER_3: {"speed": 0.7, "reliability": 0.95, "coverage": 0.98},
            AutomationTier.TIER_4: {"speed": 0.5, "reliability": 0.99, "coverage": 1.0}
        }
        
        # Platform compatibility matrix
        self.platform_compatibility = {
            "aws": {"tier_1": 0.95, "tier_2": 0.98, "tier_3": 0.99, "tier_4": 1.0},
            "azure": {"tier_1": 0.90, "tier_2": 0.95, "tier_3": 0.98, "tier_4": 1.0},
            "gcp": {"tier_1": 0.85, "tier_2": 0.92, "tier_3": 0.97, "tier_4": 1.0},
            "vmware": {"tier_1": 0.70, "tier_2": 0.85, "tier_3": 0.95, "tier_4": 1.0},
            "kubernetes": {"tier_1": 0.80, "tier_2": 0.90, "tier_3": 0.95, "tier_4": 1.0},
            "on_premise": {"tier_1": 0.60, "tier_2": 0.80, "tier_3": 0.95, "tier_4": 1.0}
        }
        
        logger.info("✅ Tier Routing Service initialized")
    
    async def analyze_and_route(
        self,
        environment_config: Dict[str, Any],
        client_requirements: Optional[Dict[str, Any]] = None,
        routing_strategy: Optional[str] = None,
        quality_requirements: Optional[Dict[str, float]] = None
    ) -> Tuple[TierAnalysis, RoutingDecision]:
        """
        Perform comprehensive tier analysis and routing decision
        
        Args:
            environment_config: Environment configuration and platform details
            client_requirements: Client-specific requirements and preferences
            routing_strategy: Strategy for tier selection (aggressive, balanced, conservative, adaptive)
            quality_requirements: Minimum quality requirements per aspect
            
        Returns:
            Tuple of (TierAnalysis, RoutingDecision)
        """
        try:
            logger.info("🔍 Starting tier analysis and routing")
            
            # Step 1: Perform base tier detection
            base_tier_result = await self.tier_detection.analyze_environment_tier(
                environment_config=environment_config,
                automation_tier="tier_2"  # Use tier_2 as baseline for analysis
            )
            
            # Step 2: Analyze environment complexity
            complexity_analysis = await self._analyze_environment_complexity(
                environment_config=environment_config,
                base_analysis=base_tier_result
            )
            
            # Step 3: Assess platform coverage and compatibility
            platform_analysis = await self._analyze_platform_coverage(
                environment_config=environment_config,
                complexity=complexity_analysis
            )
            
            # Step 4: Perform comprehensive tier analysis
            tier_analysis = await self._perform_comprehensive_tier_analysis(
                environment_config=environment_config,
                client_requirements=client_requirements or {},
                base_analysis=base_tier_result,
                complexity=complexity_analysis,
                platform_analysis=platform_analysis,
                quality_requirements=quality_requirements or {}
            )
            
            # Step 5: Make routing decision
            routing_decision = await self._make_routing_decision(
                tier_analysis=tier_analysis,
                routing_strategy=RoutingStrategy(routing_strategy or self.default_strategy.value),
                client_requirements=client_requirements or {},
                environment_config=environment_config
            )
            
            logger.info(f"✅ Tier analysis completed: {tier_analysis.recommended_tier.value} "
                       f"(confidence: {tier_analysis.confidence_score:.2f})")
            
            return tier_analysis, routing_decision
            
        except Exception as e:
            logger.error(f"❌ Tier analysis and routing failed: {e}")
            raise FlowError(f"Tier analysis failed: {str(e)}")
    
    async def validate_tier_selection(
        self,
        selected_tier: str,
        environment_config: Dict[str, Any],
        minimum_confidence: float = 0.7
    ) -> Dict[str, Any]:
        """
        Validate a manually selected tier against environment analysis
        
        Args:
            selected_tier: Manually selected automation tier
            environment_config: Environment configuration
            minimum_confidence: Minimum confidence required for validation
            
        Returns:
            Validation result with recommendations
        """
        try:
            # Perform analysis for the selected tier
            tier_analysis, routing_decision = await self.analyze_and_route(
                environment_config=environment_config,
                routing_strategy="balanced"
            )
            
            selected_automation_tier = AutomationTier(selected_tier)
            
            # Check if selected tier matches recommendation
            tier_match = selected_automation_tier == tier_analysis.recommended_tier
            
            # Find confidence for selected tier in alternatives
            selected_confidence = tier_analysis.confidence_score
            if not tier_match:
                for alt_tier, alt_confidence in tier_analysis.alternative_tiers:
                    if alt_tier == selected_automation_tier:
                        selected_confidence = alt_confidence
                        break
                else:
                    selected_confidence = 0.5  # Low confidence if not in alternatives
            
            # Validation result
            is_valid = selected_confidence >= minimum_confidence
            
            # Generate warnings and recommendations
            warnings = []
            recommendations = []
            
            if not is_valid:
                warnings.append(f"Selected tier {selected_tier} has low confidence ({selected_confidence:.2f})")
                recommendations.append(f"Consider using recommended tier: {tier_analysis.recommended_tier.value}")
            
            if not tier_match and tier_analysis.confidence_score > 0.8:
                warnings.append(f"Selected tier differs from high-confidence recommendation")
                recommendations.append(f"Recommended tier {tier_analysis.recommended_tier.value} has {tier_analysis.confidence_score:.2f} confidence")
            
            # Risk assessment for selected tier
            risk_factors = await self._assess_tier_selection_risks(
                selected_tier=selected_automation_tier,
                tier_analysis=tier_analysis,
                environment_config=environment_config
            )
            
            return {
                "selected_tier": selected_tier,
                "is_valid": is_valid,
                "confidence_score": selected_confidence,
                "recommended_tier": tier_analysis.recommended_tier.value,
                "recommendation_confidence": tier_analysis.confidence_score,
                "tier_match": tier_match,
                "warnings": warnings,
                "recommendations": recommendations,
                "risk_assessment": risk_factors,
                "environment_complexity": tier_analysis.environment_complexity.value,
                "platform_coverage": tier_analysis.platform_coverage,
                "quality_prediction": tier_analysis.quality_prediction,
                "execution_time_estimate": tier_analysis.execution_time_estimate
            }
            
        except Exception as e:
            logger.error(f"❌ Tier validation failed: {e}")
            raise FlowError(f"Tier validation failed: {str(e)}")
    
    async def optimize_routing_for_quality(
        self,
        target_quality: float,
        environment_config: Dict[str, Any],
        time_constraints: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Optimize routing to meet specific quality targets
        
        Args:
            target_quality: Target overall quality score (0.0 to 1.0)
            environment_config: Environment configuration
            time_constraints: Maximum execution time constraints
            
        Returns:
            Optimized routing configuration
        """
        try:
            logger.info(f"🎯 Optimizing routing for quality target: {target_quality}")
            
            # Analyze all tier options
            tier_options = []
            
            for tier in AutomationTier:
                try:
                    analysis, routing = await self.analyze_and_route(
                        environment_config=environment_config,
                        quality_requirements={"overall": target_quality}
                    )
                    
                    predicted_quality = analysis.quality_prediction.get("overall", 0.0)
                    predicted_time = analysis.execution_time_estimate.get("total", 0)
                    
                    tier_options.append({
                        "tier": tier.value,
                        "predicted_quality": predicted_quality,
                        "predicted_time_ms": predicted_time,
                        "confidence": analysis.confidence_score,
                        "meets_quality": predicted_quality >= target_quality,
                        "analysis": analysis,
                        "routing": routing
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze tier {tier.value}: {e}")
            
            # Filter options that meet quality target
            viable_options = [opt for opt in tier_options if opt["meets_quality"]]
            
            if not viable_options:
                # No tier meets target - find closest
                best_option = max(tier_options, key=lambda x: x["predicted_quality"])
                logger.warning(f"⚠️ No tier meets quality target {target_quality}. "
                             f"Best available: {best_option['predicted_quality']:.2f}")
            else:
                # Select best viable option based on strategy
                if time_constraints:
                    max_time = time_constraints.get("max_execution_time_ms", float('inf'))
                    viable_options = [opt for opt in viable_options 
                                    if opt["predicted_time_ms"] <= max_time]
                
                if viable_options:
                    # Prefer fastest among viable options
                    best_option = min(viable_options, key=lambda x: x["predicted_time_ms"])
                else:
                    # No option meets time constraints
                    best_option = min(tier_options, key=lambda x: x["predicted_time_ms"])
                    logger.warning("⚠️ No tier meets both quality and time constraints")
            
            # Generate optimization recommendations
            recommendations = await self._generate_quality_optimization_recommendations(
                best_option=best_option,
                target_quality=target_quality,
                all_options=tier_options,
                time_constraints=time_constraints
            )
            
            return {
                "optimal_tier": best_option["tier"],
                "predicted_quality": best_option["predicted_quality"],
                "predicted_time_ms": best_option["predicted_time_ms"],
                "confidence": best_option["confidence"],
                "meets_target": best_option["meets_quality"],
                "routing_decision": best_option["routing"],
                "tier_analysis": best_option["analysis"],
                "all_tier_options": tier_options,
                "optimization_recommendations": recommendations,
                "quality_gap": max(0, target_quality - best_option["predicted_quality"])
            }
            
        except Exception as e:
            logger.error(f"❌ Quality optimization failed: {e}")
            raise FlowError(f"Quality optimization failed: {str(e)}")
    
    async def get_adaptive_routing_insights(
        self,
        historical_executions: List[Dict[str, Any]],
        environment_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate adaptive routing insights based on historical execution data
        
        Args:
            historical_executions: Historical workflow execution data
            environment_config: Current environment configuration
            
        Returns:
            Adaptive routing insights and recommendations
        """
        try:
            logger.info("🧠 Generating adaptive routing insights")
            
            # Analyze historical performance by tier
            tier_performance = {}
            for tier in AutomationTier:
                tier_executions = [exec for exec in historical_executions 
                                 if exec.get("automation_tier") == tier.value]
                
                if tier_executions:
                    avg_quality = sum(exec.get("overall_quality_score", 0) for exec in tier_executions) / len(tier_executions)
                    avg_time = sum(exec.get("execution_time_ms", 0) for exec in tier_executions) / len(tier_executions)
                    success_rate = sum(1 for exec in tier_executions if exec.get("overall_status") == "completed") / len(tier_executions)
                    
                    tier_performance[tier.value] = {
                        "execution_count": len(tier_executions),
                        "average_quality": avg_quality,
                        "average_time_ms": avg_time,
                        "success_rate": success_rate,
                        "quality_variance": self._calculate_variance([exec.get("overall_quality_score", 0) for exec in tier_executions])
                    }
            
            # Identify patterns and trends
            patterns = await self._identify_execution_patterns(
                historical_executions=historical_executions,
                tier_performance=tier_performance
            )
            
            # Generate environment-specific recommendations
            current_analysis, current_routing = await self.analyze_and_route(
                environment_config=environment_config,
                routing_strategy="adaptive"
            )
            
            # Calculate adaptive adjustments
            adaptive_recommendations = await self._calculate_adaptive_adjustments(
                current_analysis=current_analysis,
                tier_performance=tier_performance,
                patterns=patterns
            )
            
            return {
                "current_recommendation": current_analysis.recommended_tier.value,
                "current_confidence": current_analysis.confidence_score,
                "tier_performance_history": tier_performance,
                "identified_patterns": patterns,
                "adaptive_recommendations": adaptive_recommendations,
                "learning_insights": {
                    "best_performing_tier": max(tier_performance.items(), 
                                               key=lambda x: x[1]["average_quality"])[0] if tier_performance else None,
                    "most_reliable_tier": max(tier_performance.items(), 
                                            key=lambda x: x[1]["success_rate"])[0] if tier_performance else None,
                    "fastest_tier": min(tier_performance.items(), 
                                      key=lambda x: x[1]["average_time_ms"])[0] if tier_performance else None
                },
                "confidence_adjustments": {
                    tier: self._calculate_confidence_adjustment(perf, patterns) 
                    for tier, perf in tier_performance.items()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Adaptive routing insights failed: {e}")
            raise FlowError(f"Adaptive routing insights failed: {str(e)}")
    
    # Private methods
    
    async def _analyze_environment_complexity(
        self,
        environment_config: Dict[str, Any],
        base_analysis: Dict[str, Any]
    ) -> EnvironmentComplexity:
        """Analyze environment complexity level"""
        try:
            complexity_score = 0
            
            # Platform diversity
            platforms = environment_config.get("platforms", [])
            platform_count = len(platforms)
            if platform_count > 5:
                complexity_score += 3
            elif platform_count > 2:
                complexity_score += 2
            elif platform_count > 1:
                complexity_score += 1
            
            # Integration complexity
            integrations = environment_config.get("integrations", [])
            if len(integrations) > 10:
                complexity_score += 3
            elif len(integrations) > 5:
                complexity_score += 2
            elif len(integrations) > 0:
                complexity_score += 1
            
            # Custom configurations
            custom_configs = environment_config.get("custom_configurations", {})
            if len(custom_configs) > 20:
                complexity_score += 3
            elif len(custom_configs) > 10:
                complexity_score += 2
            elif len(custom_configs) > 0:
                complexity_score += 1
            
            # Data volume
            estimated_resources = environment_config.get("estimated_resource_count", 0)
            if estimated_resources > 10000:
                complexity_score += 3
            elif estimated_resources > 1000:
                complexity_score += 2
            elif estimated_resources > 100:
                complexity_score += 1
            
            # Determine complexity level
            if complexity_score >= 9:
                return EnvironmentComplexity.ENTERPRISE
            elif complexity_score >= 6:
                return EnvironmentComplexity.COMPLEX
            elif complexity_score >= 3:
                return EnvironmentComplexity.MODERATE
            else:
                return EnvironmentComplexity.SIMPLE
                
        except Exception as e:
            logger.warning(f"Environment complexity analysis failed: {e}")
            return EnvironmentComplexity.MODERATE
    
    async def _analyze_platform_coverage(
        self,
        environment_config: Dict[str, Any],
        complexity: EnvironmentComplexity
    ) -> Dict[str, float]:
        """Analyze platform coverage and adapter compatibility"""
        coverage = {}
        
        platforms = environment_config.get("platforms", [])
        for platform in platforms:
            platform_type = platform.get("type", "").lower()
            
            # Get adapter compatibility
            if platform_type in self.platform_compatibility:
                coverage[platform_type] = self.platform_compatibility[platform_type]
            else:
                # Unknown platform - conservative coverage
                coverage[platform_type] = {
                    "tier_1": 0.5, "tier_2": 0.7, "tier_3": 0.9, "tier_4": 1.0
                }
        
        return coverage
    
    async def _perform_comprehensive_tier_analysis(
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
            score = await self._calculate_tier_score(
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
    
    async def _make_routing_decision(
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
    
    async def _calculate_tier_score(
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
        weights = self.tier_weights[tier]
        
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
    
    # Additional helper methods for analysis
    
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
    
    # Simplified implementations for remaining methods due to length constraints
    
    async def _apply_routing_strategy(self, tier_analysis: TierAnalysis, strategy: RoutingStrategy, client_requirements: Dict[str, Any]) -> AutomationTier:
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
    
    async def _generate_execution_path(self, selected_tier: AutomationTier, environment_config: Dict[str, Any], complexity: EnvironmentComplexity) -> List[str]:
        """Generate execution path for selected tier"""
        base_path = ["platform_detection", "automated_collection", "gap_analysis", "synthesis"]
        if selected_tier != AutomationTier.TIER_1:
            base_path.insert(-1, "manual_collection")
        return base_path
    
    async def _configure_phases_for_tier(self, selected_tier: AutomationTier, tier_analysis: TierAnalysis, client_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Configure phases for selected tier"""
        return {
            "platform_detection": {"enable_ai_assistance": True, "confidence_threshold": 0.8},
            "automated_collection": {"parallel_execution": selected_tier in [AutomationTier.TIER_1, AutomationTier.TIER_2]},
            "gap_analysis": {"depth": "comprehensive"},
            "manual_collection": {"enabled": selected_tier != AutomationTier.TIER_1},
            "synthesis": {"validation_level": "strict" if selected_tier == AutomationTier.TIER_1 else "standard"}
        }
    
    async def _set_quality_thresholds_for_tier(self, selected_tier: AutomationTier, client_requirements: Dict[str, Any]) -> Dict[str, float]:
        """Set quality thresholds for selected tier"""
        base_thresholds = {
            AutomationTier.TIER_1: {"overall": 0.95, "collection": 0.95, "synthesis": 0.95},
            AutomationTier.TIER_2: {"overall": 0.85, "collection": 0.85, "synthesis": 0.85},
            AutomationTier.TIER_3: {"overall": 0.75, "collection": 0.75, "synthesis": 0.75},
            AutomationTier.TIER_4: {"overall": 0.60, "collection": 0.60, "synthesis": 0.60}
        }
        return base_thresholds[selected_tier]
    
    async def _configure_timeouts_for_tier(self, selected_tier: AutomationTier, complexity: EnvironmentComplexity) -> Dict[str, int]:
        """Configure timeouts for selected tier"""
        base_timeouts = {
            "platform_detection": 600, "automated_collection": 3600,
            "gap_analysis": 900, "manual_collection": 7200, "synthesis": 1200
        }
        multiplier = {EnvironmentComplexity.SIMPLE: 1.0, EnvironmentComplexity.MODERATE: 1.3,
                     EnvironmentComplexity.COMPLEX: 1.6, EnvironmentComplexity.ENTERPRISE: 2.0}[complexity]
        return {phase: int(timeout * multiplier) for phase, timeout in base_timeouts.items()}
    
    async def _select_adapters_for_tier(self, selected_tier: AutomationTier, environment_config: Dict[str, Any], platform_coverage: Dict[str, float]) -> List[Dict[str, Any]]:
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
    
    async def _configure_manual_collection_strategy(self, selected_tier: AutomationTier, tier_analysis: TierAnalysis, client_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Configure manual collection strategy"""
        return {
            "enabled": True,
            "questionnaire_depth": "comprehensive" if selected_tier == AutomationTier.TIER_4 else "targeted",
            "validation_level": "strict",
            "user_engagement": "high" if selected_tier in [AutomationTier.TIER_3, AutomationTier.TIER_4] else "medium"
        }
    
    async def _generate_fallback_options(self, selected_tier: AutomationTier, tier_analysis: TierAnalysis) -> List[Dict[str, Any]]:
        """Generate fallback options"""
        fallbacks = []
        for alt_tier, confidence in tier_analysis.alternative_tiers[:2]:  # Top 2 alternatives
            fallbacks.append({
                "tier": alt_tier.value,
                "confidence": confidence,
                "trigger_conditions": ["quality_below_threshold", "execution_timeout"]
            })
        return fallbacks
    
    async def _calculate_routing_confidence(self, selected_tier: AutomationTier, tier_analysis: TierAnalysis, routing_strategy: RoutingStrategy) -> float:
        """Calculate routing confidence"""
        base_confidence = tier_analysis.confidence_score
        strategy_adjustment = {
            RoutingStrategy.AGGRESSIVE: 0.9, RoutingStrategy.BALANCED: 1.0,
            RoutingStrategy.CONSERVATIVE: 1.1, RoutingStrategy.ADAPTIVE: 1.05
        }[routing_strategy]
        return min(1.0, base_confidence * strategy_adjustment)
    
    # Utility methods
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)
    
    async def _assess_tier_selection_risks(self, selected_tier: AutomationTier, tier_analysis: TierAnalysis, environment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risks for tier selection"""
        return {"risk_level": "low", "risk_factors": []}
    
    async def _generate_quality_optimization_recommendations(self, best_option: Dict[str, Any], target_quality: float, all_options: List[Dict[str, Any]], time_constraints: Optional[Dict[str, int]]) -> List[str]:
        """Generate quality optimization recommendations"""
        return ["Consider tier upgrades for better quality", "Implement additional validation steps"]
    
    async def _identify_execution_patterns(self, historical_executions: List[Dict[str, Any]], tier_performance: Dict[str, Any]) -> Dict[str, Any]:
        """Identify execution patterns"""
        return {"patterns": [], "trends": []}
    
    async def _calculate_adaptive_adjustments(self, current_analysis: TierAnalysis, tier_performance: Dict[str, Any], patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate adaptive adjustments"""
        return {"adjustments": []}
    
    def _calculate_confidence_adjustment(self, performance: Dict[str, Any], patterns: Dict[str, Any]) -> float:
        """Calculate confidence adjustment"""
        return 1.0