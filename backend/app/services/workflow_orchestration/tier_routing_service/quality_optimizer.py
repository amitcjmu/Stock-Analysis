"""
Quality Optimization Module
Team C1 - Task C1.3

Quality-based routing optimization and adaptive insights.
"""

import logging
from typing import Dict, Any, List, Optional

from app.core.logging import get_logger

from .enums import AutomationTier, RoutingStrategy
from .models import TierAnalysis

logger = get_logger(__name__)


class QualityOptimizer:
    """Handles quality optimization and adaptive routing insights"""
    
    async def optimize_routing_for_quality(
        self,
        tier_analyzer,
        routing_engine,
        target_quality: float,
        environment_config: Dict[str, Any],
        time_constraints: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Optimize routing to meet specific quality targets
        
        Args:
            tier_analyzer: TierAnalyzer instance
            routing_engine: RoutingEngine instance
            target_quality: Target overall quality score (0.0 to 1.0)
            environment_config: Environment configuration
            time_constraints: Maximum execution time constraints
            
        Returns:
            Optimized routing configuration
        """
        try:
            logger.info(f"Optimizing routing for quality target: {target_quality}")
            
            # Analyze all tier options
            tier_options = []
            
            for tier in AutomationTier:
                try:
                    # Perform analysis for each tier
                    analysis = await tier_analyzer.perform_comprehensive_tier_analysis(
                        environment_config=environment_config,
                        client_requirements={},
                        base_analysis={},
                        complexity=await self._get_environment_complexity(environment_config),
                        platform_analysis={},
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
                        "analysis": analysis
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze tier {tier.value}: {e}")
            
            # Filter options that meet quality target
            viable_options = [opt for opt in tier_options if opt["meets_quality"]]
            
            if not viable_options:
                # No tier meets target - find closest
                best_option = max(tier_options, key=lambda x: x["predicted_quality"])
                logger.warning(f"No tier meets quality target {target_quality}. "
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
                    logger.warning("No tier meets both quality and time constraints")
            
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
                "tier_analysis": best_option["analysis"],
                "all_tier_options": tier_options,
                "optimization_recommendations": recommendations,
                "quality_gap": max(0, target_quality - best_option["predicted_quality"])
            }
            
        except Exception as e:
            logger.error(f"Quality optimization failed: {e}")
            raise
    
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
            logger.info("Generating adaptive routing insights")
            
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
            
            # Calculate adaptive adjustments
            adaptive_recommendations = await self._calculate_adaptive_adjustments(
                tier_performance=tier_performance,
                patterns=patterns
            )
            
            return {
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
            logger.error(f"Adaptive routing insights failed: {e}")
            raise
    
    async def _get_environment_complexity(self, environment_config: Dict[str, Any]):
        """Get environment complexity based on configuration"""
        # Simplified complexity assessment
        platform_count = len(environment_config.get("platforms", []))
        if platform_count > 5:
            from .enums import EnvironmentComplexity
            return EnvironmentComplexity.ENTERPRISE
        elif platform_count > 2:
            from .enums import EnvironmentComplexity
            return EnvironmentComplexity.COMPLEX
        else:
            from .enums import EnvironmentComplexity
            return EnvironmentComplexity.MODERATE
    
    async def _generate_quality_optimization_recommendations(
        self, 
        best_option: Dict[str, Any], 
        target_quality: float, 
        all_options: List[Dict[str, Any]], 
        time_constraints: Optional[Dict[str, int]]
    ) -> List[str]:
        """Generate quality optimization recommendations"""
        recommendations = []
        
        if best_option["predicted_quality"] < target_quality:
            quality_gap = target_quality - best_option["predicted_quality"]
            recommendations.append(f"Quality gap of {quality_gap:.2f} detected. Consider:")
            
            # Find options that meet quality
            better_options = [opt for opt in all_options if opt["predicted_quality"] >= target_quality]
            if better_options:
                recommendations.append(f"- Upgrading to {better_options[0]['tier']} for better quality")
            
            recommendations.append("- Implementing additional validation steps")
            recommendations.append("- Increasing manual collection depth")
        
        if time_constraints and best_option["predicted_time_ms"] > time_constraints.get("max_execution_time_ms", float('inf')):
            recommendations.append("- Consider relaxing time constraints or quality targets")
            recommendations.append("- Enable parallel execution where possible")
        
        return recommendations
    
    async def _identify_execution_patterns(
        self, 
        historical_executions: List[Dict[str, Any]], 
        tier_performance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify execution patterns"""
        patterns = {
            "quality_trends": {},
            "performance_trends": {},
            "failure_patterns": []
        }
        
        # Analyze quality trends
        for tier, perf in tier_performance.items():
            if perf["execution_count"] > 5:
                if perf["quality_variance"] < 0.05:
                    patterns["quality_trends"][tier] = "stable"
                elif perf["quality_variance"] > 0.15:
                    patterns["quality_trends"][tier] = "volatile"
                else:
                    patterns["quality_trends"][tier] = "moderate"
        
        # Analyze failure patterns
        failed_executions = [exec for exec in historical_executions if exec.get("overall_status") != "completed"]
        if failed_executions:
            common_failures = {}
            for exec in failed_executions:
                failure_reason = exec.get("failure_reason", "unknown")
                common_failures[failure_reason] = common_failures.get(failure_reason, 0) + 1
            
            patterns["failure_patterns"] = [
                {"reason": reason, "count": count}
                for reason, count in sorted(common_failures.items(), key=lambda x: x[1], reverse=True)[:5]
            ]
        
        return patterns
    
    async def _calculate_adaptive_adjustments(
        self, 
        tier_performance: Dict[str, Any], 
        patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate adaptive adjustments"""
        adjustments = {
            "tier_confidence_adjustments": {},
            "recommended_changes": []
        }
        
        for tier, perf in tier_performance.items():
            if perf["execution_count"] > 10:
                # Adjust confidence based on historical performance
                if perf["success_rate"] > 0.95:
                    adjustments["tier_confidence_adjustments"][tier] = 1.1
                elif perf["success_rate"] < 0.8:
                    adjustments["tier_confidence_adjustments"][tier] = 0.9
                else:
                    adjustments["tier_confidence_adjustments"][tier] = 1.0
                
                # Recommend changes based on patterns
                if patterns["quality_trends"].get(tier) == "volatile":
                    adjustments["recommended_changes"].append(
                        f"Consider stabilizing {tier} execution through additional validation"
                    )
        
        return adjustments
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)
    
    def _calculate_confidence_adjustment(self, performance: Dict[str, Any], patterns: Dict[str, Any]) -> float:
        """Calculate confidence adjustment based on performance"""
        base_adjustment = 1.0
        
        if performance["success_rate"] > 0.95:
            base_adjustment *= 1.1
        elif performance["success_rate"] < 0.8:
            base_adjustment *= 0.9
        
        if performance["quality_variance"] < 0.05:
            base_adjustment *= 1.05
        elif performance["quality_variance"] > 0.15:
            base_adjustment *= 0.95
        
        return base_adjustment