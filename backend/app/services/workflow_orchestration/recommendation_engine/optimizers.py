"""
Recommendation Engine Optimizers
Team C1 - Task C1.5

Optimization methods for recommendation prioritization, execution ordering, and goal-based optimization.
"""

import statistics
from typing import Any, Dict, List, Optional

from app.core.exceptions import FlowError
from app.core.logging import get_logger

from .enums import RecommendationType
from .models import WorkflowRecommendation

logger = get_logger(__name__)


class RecommendationOptimizer:
    """
    Handles optimization of recommendations including prioritization,
    execution ordering, and goal-based optimization.
    """
    
    def __init__(self):
        # Business rules and weights
        self.recommendation_weights = {
            RecommendationType.AUTOMATION_TIER: {
                "quality_impact": 0.3,
                "performance_impact": 0.25,
                "cost_impact": 0.2,
                "risk_impact": 0.15,
                "effort_impact": 0.1
            },
            RecommendationType.WORKFLOW_CONFIG: {
                "quality_impact": 0.35,
                "performance_impact": 0.3,
                "cost_impact": 0.15,
                "risk_impact": 0.1,
                "effort_impact": 0.1
            },
            RecommendationType.PHASE_OPTIMIZATION: {
                "quality_impact": 0.4,
                "performance_impact": 0.35,
                "cost_impact": 0.1,
                "risk_impact": 0.1,
                "effort_impact": 0.05
            },
            RecommendationType.QUALITY_IMPROVEMENT: {
                "quality_impact": 0.5,
                "performance_impact": 0.2,
                "cost_impact": 0.1,
                "risk_impact": 0.1,
                "effort_impact": 0.1
            },
            RecommendationType.PERFORMANCE_OPTIMIZATION: {
                "quality_impact": 0.2,
                "performance_impact": 0.5,
                "cost_impact": 0.15,
                "risk_impact": 0.1,
                "effort_impact": 0.05
            }
        }
    
    async def prioritize_recommendations(
        self,
        recommendations: List[WorkflowRecommendation],
        optimization_goals: List[str],
        constraints: Dict[str, Any]
    ) -> List[WorkflowRecommendation]:
        """
        Prioritize recommendations based on goals and constraints
        
        Args:
            recommendations: List of recommendations to prioritize
            optimization_goals: Primary optimization goals
            constraints: Implementation constraints
            
        Returns:
            Prioritized list of recommendations
        """
        
        # Calculate priority scores based on optimization goals
        for recommendation in recommendations:
            priority_score = await self._calculate_priority_score(
                recommendation=recommendation,
                optimization_goals=optimization_goals,
                constraints=constraints
            )
            
            # Update priority (1-10 scale)
            recommendation.priority = max(1, min(10, int(priority_score * 10)))
        
        # Sort by priority (highest first)
        return sorted(recommendations, key=lambda r: r.priority, reverse=True)
    
    async def calculate_optimal_execution_order(
        self,
        recommendations: List[WorkflowRecommendation]
    ) -> List[str]:
        """
        Calculate optimal execution order for recommendations
        
        Args:
            recommendations: List of recommendations to order
            
        Returns:
            Ordered list of recommendation IDs
        """
        
        # Group by type and priority
        type_groups = {
            RecommendationType.AUTOMATION_TIER: [],
            RecommendationType.WORKFLOW_CONFIG: [],
            RecommendationType.PHASE_OPTIMIZATION: [],
            RecommendationType.QUALITY_IMPROVEMENT: [],
            RecommendationType.PERFORMANCE_OPTIMIZATION: []
        }
        
        for rec in recommendations:
            if rec.recommendation_type in type_groups:
                type_groups[rec.recommendation_type].append(rec)
        
        # Recommended execution order: tier -> config -> phase -> quality -> performance
        execution_order = []
        
        for rec_type in [
            RecommendationType.AUTOMATION_TIER,
            RecommendationType.WORKFLOW_CONFIG,
            RecommendationType.PHASE_OPTIMIZATION,
            RecommendationType.QUALITY_IMPROVEMENT,
            RecommendationType.PERFORMANCE_OPTIMIZATION
        ]:
            # Sort by priority within group
            sorted_group = sorted(
                type_groups.get(rec_type, []),
                key=lambda r: r.priority,
                reverse=True
            )
            execution_order.extend([r.recommendation_id for r in sorted_group])
        
        return execution_order
    
    async def estimate_overall_improvement(
        self,
        recommendations: List[WorkflowRecommendation],
        environment_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Estimate overall improvement from implementing all recommendations
        
        Args:
            recommendations: List of recommendations
            environment_analysis: Environment context
            
        Returns:
            Estimated improvement metrics
        """
        
        # Aggregate expected impacts
        total_quality_improvement = 0.0
        total_performance_improvement = 0.0
        total_cost_reduction = 0.0
        total_risk_reduction = 0.0
        
        for recommendation in recommendations:
            # Weight by confidence and priority
            weight = (recommendation.confidence_score * recommendation.priority) / 100.0
            
            total_quality_improvement += recommendation.expected_impact.get("quality", 0.0) * weight
            total_performance_improvement += recommendation.expected_impact.get("performance", 0.0) * weight
            total_cost_reduction += recommendation.expected_impact.get("cost_reduction", 0.0) * weight
            total_risk_reduction += recommendation.expected_impact.get("risk_reduction", 0.0) * weight
        
        # Apply diminishing returns and caps
        quality_improvement = self._apply_diminishing_returns(total_quality_improvement, 0.5)
        performance_improvement = self._apply_diminishing_returns(total_performance_improvement, 0.4)
        cost_reduction = self._apply_diminishing_returns(total_cost_reduction, 0.3)
        risk_reduction = self._apply_diminishing_returns(total_risk_reduction, 0.6)
        
        return {
            "quality_improvement": quality_improvement,
            "performance_improvement": performance_improvement,
            "cost_reduction": cost_reduction,
            "risk_reduction": risk_reduction,
            "overall_score": (quality_improvement + performance_improvement + 
                            cost_reduction + risk_reduction) / 4,
            "confidence": self._calculate_overall_confidence(recommendations),
            "implementation_complexity": self._calculate_implementation_complexity(recommendations)
        }
    
    async def optimize_recommendation_for_goals(
        self,
        base_environment: Dict[str, Any],
        optimization_targets: Dict[str, float],
        acceptable_tradeoffs: Optional[Dict[str, float]] = None,
        candidate_recommendations: List[WorkflowRecommendation] = None
    ) -> Dict[str, Any]:
        """
        Optimize recommendations to meet specific goals
        
        Args:
            base_environment: Base environment configuration
            optimization_targets: Target metrics (quality, performance, cost)
            acceptable_tradeoffs: Acceptable degradation in other metrics
            candidate_recommendations: Pre-generated recommendations to optimize
            
        Returns:
            Optimized recommendation configuration
        """
        try:
            logger.info("🎯 Optimizing recommendations for specific goals")
            
            if not candidate_recommendations:
                raise ValueError("Candidate recommendations required for optimization")
            
            # Simulate different recommendation combinations
            optimization_candidates = []
            
            # Generate combinations of recommendations
            combinations = await self._generate_recommendation_combinations(
                recommendations=candidate_recommendations,
                max_combinations=20
            )
            
            for combination in combinations:
                # Estimate outcomes for this combination
                estimated_outcomes = await self._estimate_combination_outcomes(
                    recommendations=combination,
                    environment=base_environment
                )
                
                # Calculate optimization score
                optimization_score = await self._calculate_optimization_score(
                    estimated_outcomes=estimated_outcomes,
                    optimization_targets=optimization_targets,
                    acceptable_tradeoffs=acceptable_tradeoffs or {}
                )
                
                optimization_candidates.append({
                    "recommendations": combination,
                    "estimated_outcomes": estimated_outcomes,
                    "optimization_score": optimization_score,
                    "meets_targets": self._check_target_achievement(
                        estimated_outcomes, optimization_targets
                    ),
                    "combination_size": len(combination)
                })
            
            # Select best optimization candidate
            best_candidate = max(
                optimization_candidates,
                key=lambda x: x["optimization_score"]
            )
            
            # Generate optimization insights
            optimization_insights = await self._generate_optimization_insights(
                best_candidate=best_candidate,
                all_candidates=optimization_candidates,
                optimization_targets=optimization_targets
            )
            
            return {
                "optimized_recommendations": best_candidate["recommendations"],
                "estimated_outcomes": best_candidate["estimated_outcomes"],
                "optimization_score": best_candidate["optimization_score"],
                "meets_all_targets": best_candidate["meets_targets"],
                "optimization_insights": optimization_insights,
                "alternatives": sorted(
                    optimization_candidates,
                    key=lambda x: x["optimization_score"],
                    reverse=True
                )[1:6],  # Top 5 alternatives (excluding best)
                "target_achievement": {
                    target: best_candidate["estimated_outcomes"].get(target, 0) / target_value
                    for target, target_value in optimization_targets.items()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to optimize recommendations: {e}")
            raise FlowError(f"Recommendation optimization failed: {str(e)}")
    
    async def _calculate_priority_score(
        self,
        recommendation: WorkflowRecommendation,
        optimization_goals: List[str],
        constraints: Dict[str, Any]
    ) -> float:
        """Calculate priority score for a recommendation"""
        
        priority_score = 0.0
        
        # Get weights for this recommendation type
        type_weights = self.recommendation_weights.get(
            recommendation.recommendation_type,
            {"quality_impact": 0.2, "performance_impact": 0.2, "cost_impact": 0.2, 
             "risk_impact": 0.2, "effort_impact": 0.2}
        )
        
        # Goal alignment score
        for goal in optimization_goals:
            if goal in recommendation.expected_impact:
                impact_value = recommendation.expected_impact[goal]
                goal_weight = type_weights.get(f"{goal}_impact", 0.2)
                priority_score += impact_value * goal_weight * 0.4
        
        # Confidence score weight
        priority_score += recommendation.confidence_score * 0.25
        
        # Implementation effort penalty
        effort_penalty = {
            "low": 0.0, "medium": 0.1, "high": 0.2
        }.get(recommendation.implementation_effort, 0.1)
        priority_score -= effort_penalty
        
        # Risk penalty
        if "overall_risk" in recommendation.risk_assessment:
            priority_score -= recommendation.risk_assessment["overall_risk"] * 0.15
        
        # Constraint alignment
        if constraints:
            constraint_score = await self._calculate_constraint_alignment(
                recommendation, constraints
            )
            priority_score += constraint_score * 0.2
        
        return max(0.0, min(1.0, priority_score))
    
    async def _calculate_constraint_alignment(
        self,
        recommendation: WorkflowRecommendation,
        constraints: Dict[str, Any]
    ) -> float:
        """Calculate how well a recommendation aligns with constraints"""
        
        alignment_score = 1.0
        
        # Time constraint
        if "time_limit_hours" in constraints:
            if recommendation.implementation_effort == "high":
                alignment_score -= 0.3
            elif recommendation.implementation_effort == "medium":
                alignment_score -= 0.1
        
        # Budget constraint
        if "budget_limit" in constraints:
            cost_impact = recommendation.expected_impact.get("cost", 0)
            if cost_impact < 0:  # Negative means cost increase
                alignment_score += cost_impact  # Subtract the cost
        
        # Resource constraint
        if "max_resources" in constraints:
            if recommendation.recommended_action.get("resource_intensive", False):
                alignment_score -= 0.2
        
        return max(0.0, alignment_score)
    
    def _apply_diminishing_returns(self, value: float, cap: float) -> float:
        """Apply diminishing returns formula with a cap"""
        if value <= 0:
            return 0.0
        
        # Use logarithmic curve for diminishing returns
        # This ensures rapid initial gains that taper off
        import math
        scaled_value = min(value, cap * 2)  # Prevent extreme values
        return cap * (1 - math.exp(-2 * scaled_value / cap))
    
    def _calculate_overall_confidence(self, recommendations: List[WorkflowRecommendation]) -> float:
        """Calculate overall confidence across all recommendations"""
        if not recommendations:
            return 0.0
        
        weighted_confidence = sum(
            rec.confidence_score * rec.priority for rec in recommendations
        )
        total_weight = sum(rec.priority for rec in recommendations)
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    def _calculate_implementation_complexity(self, recommendations: List[WorkflowRecommendation]) -> str:
        """Calculate overall implementation complexity"""
        if not recommendations:
            return "low"
        
        # Count effort levels
        effort_counts = {"low": 0, "medium": 0, "high": 0}
        for rec in recommendations:
            effort_counts[rec.implementation_effort] += 1
        
        # Determine overall complexity
        if effort_counts["high"] > len(recommendations) * 0.3:
            return "high"
        elif effort_counts["high"] > 0 or effort_counts["medium"] > len(recommendations) * 0.5:
            return "medium"
        else:
            return "low"
    
    async def _generate_recommendation_combinations(
        self,
        recommendations: List[WorkflowRecommendation],
        max_combinations: int
    ) -> List[List[WorkflowRecommendation]]:
        """Generate combinations of recommendations to test"""
        
        combinations = []
        
        # Always include the full set
        combinations.append(recommendations)
        
        # High priority only
        high_priority = [r for r in recommendations if r.priority >= 8]
        if high_priority and len(high_priority) < len(recommendations):
            combinations.append(high_priority)
        
        # By type combinations
        for rec_type in RecommendationType:
            type_recs = [r for r in recommendations if r.recommendation_type == rec_type]
            if type_recs and len(type_recs) < len(recommendations):
                combinations.append(type_recs)
        
        # Low effort only
        low_effort = [r for r in recommendations if r.implementation_effort == "low"]
        if low_effort and len(low_effort) < len(recommendations):
            combinations.append(low_effort)
        
        # High confidence only
        high_confidence = [r for r in recommendations if r.confidence_score >= 0.8]
        if high_confidence and len(high_confidence) < len(recommendations):
            combinations.append(high_confidence)
        
        # Remove duplicates and limit
        unique_combinations = []
        seen = set()
        for combo in combinations:
            combo_key = frozenset(r.recommendation_id for r in combo)
            if combo_key not in seen:
                seen.add(combo_key)
                unique_combinations.append(combo)
        
        return unique_combinations[:max_combinations]
    
    async def _estimate_combination_outcomes(
        self,
        recommendations: List[WorkflowRecommendation],
        environment: Dict[str, Any]
    ) -> Dict[str, float]:
        """Estimate outcomes for a combination of recommendations"""
        
        # Use the estimate_overall_improvement method
        improvement_estimates = await self.estimate_overall_improvement(
            recommendations=recommendations,
            environment_analysis=environment
        )
        
        return {
            "quality": improvement_estimates["quality_improvement"],
            "performance": improvement_estimates["performance_improvement"],
            "cost": improvement_estimates["cost_reduction"],
            "risk": improvement_estimates["risk_reduction"],
            "overall": improvement_estimates["overall_score"]
        }
    
    async def _calculate_optimization_score(
        self,
        estimated_outcomes: Dict[str, float],
        optimization_targets: Dict[str, float],
        acceptable_tradeoffs: Dict[str, float]
    ) -> float:
        """Calculate optimization score based on targets and tradeoffs"""
        
        score = 0.0
        total_weight = 0.0
        
        # Score for meeting targets
        for target, target_value in optimization_targets.items():
            if target in estimated_outcomes:
                achievement = min(1.0, estimated_outcomes[target] / target_value)
                weight = 1.0  # Equal weight for all targets
                score += achievement * weight
                total_weight += weight
        
        # Penalty for violating tradeoffs
        for metric, min_acceptable in acceptable_tradeoffs.items():
            if metric in estimated_outcomes and metric not in optimization_targets:
                if estimated_outcomes[metric] < min_acceptable:
                    violation = (min_acceptable - estimated_outcomes[metric]) / min_acceptable
                    score -= violation * 0.5  # Penalty for violations
        
        return max(0.0, score / total_weight if total_weight > 0 else 0.0)
    
    def _check_target_achievement(
        self,
        estimated_outcomes: Dict[str, float],
        optimization_targets: Dict[str, float]
    ) -> bool:
        """Check if all targets are achieved"""
        
        for target, target_value in optimization_targets.items():
            if target not in estimated_outcomes:
                return False
            if estimated_outcomes[target] < target_value:
                return False
        
        return True
    
    async def _generate_optimization_insights(
        self,
        best_candidate: Dict[str, Any],
        all_candidates: List[Dict[str, Any]],
        optimization_targets: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate insights about the optimization"""
        
        insights = []
        
        # Insight about target achievement
        if best_candidate["meets_targets"]:
            insights.append({
                "type": "target_achievement",
                "description": "All optimization targets successfully met",
                "confidence": 0.9,
                "impact": "positive"
            })
        else:
            unmet_targets = []
            for target, target_value in optimization_targets.items():
                if best_candidate["estimated_outcomes"].get(target, 0) < target_value:
                    unmet_targets.append(target)
            
            insights.append({
                "type": "partial_achievement",
                "description": f"Some targets not fully met: {', '.join(unmet_targets)}",
                "confidence": 0.8,
                "impact": "neutral",
                "recommendation": "Consider adjusting targets or accepting tradeoffs"
            })
        
        # Insight about recommendation composition
        rec_types = {}
        for rec in best_candidate["recommendations"]:
            rec_type = rec.recommendation_type.value
            rec_types[rec_type] = rec_types.get(rec_type, 0) + 1
        
        dominant_type = max(rec_types.items(), key=lambda x: x[1])[0] if rec_types else None
        if dominant_type:
            insights.append({
                "type": "recommendation_focus",
                "description": f"Optimization focuses on {dominant_type} recommendations",
                "confidence": 0.85,
                "impact": "informational"
            })
        
        # Insight about alternatives
        score_variance = statistics.variance([c["optimization_score"] for c in all_candidates])
        if score_variance < 0.01:
            insights.append({
                "type": "similar_alternatives",
                "description": "Multiple combinations achieve similar optimization scores",
                "confidence": 0.8,
                "impact": "positive",
                "recommendation": "Choice can be based on implementation preferences"
            })
        
        return insights