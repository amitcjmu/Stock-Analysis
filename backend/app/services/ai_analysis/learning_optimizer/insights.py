"""
Learning Optimizer Insights
Contains methods for generating insights and recommendations.

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

import logging
from datetime import datetime
from typing import Dict, List, Any

from .models import LearningEvent, LearningInsight, OptimizationRecommendation
from .enums import LearningPattern, OptimizationStrategy

logger = logging.getLogger(__name__)


def generate_quality_insights(analysis: Dict[str, Any], events: List[LearningEvent]) -> List[LearningInsight]:
    """Generate quality-specific insights"""
    insights = []
    
    overall_metrics = analysis.get("overall_metrics", {})
    avg_quality = overall_metrics.get("average_quality", 0)
    
    if avg_quality < 0.75:
        insights.append(LearningInsight(
            insight_id=f"quality_low_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            pattern_type=LearningPattern.RESPONSE_QUALITY,
            description=f"Response quality is below target at {avg_quality:.2%}. Focus on question clarity and stakeholder guidance.",
            supporting_evidence={"average_quality": avg_quality, "target": 0.75},
            business_impact="high",
            actionability="immediate",
            recommendations=[
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.REFINE_QUESTIONS,
                    confidence=0.85,
                    expected_improvement=15.0,
                    implementation_complexity="medium",
                    evidence=overall_metrics,
                    specific_actions=[
                        "Review and simplify question wording",
                        "Add more detailed help text",
                        "Implement question validation"
                    ],
                    success_metrics=["Quality score > 75%", "Reduced confusion rate"]
                )
            ]
        ))
    
    # Role performance insights
    role_performance = analysis.get("role_performance", {})
    underperforming_roles = [
        role for role, data in role_performance.items()
        if data.get("average_quality", 0) < 0.7
    ]
    
    if underperforming_roles:
        insights.append(LearningInsight(
            insight_id=f"role_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            pattern_type=LearningPattern.RESPONSE_QUALITY,
            description=f"Roles {', '.join(underperforming_roles)} show lower response quality. Needs targeted support.",
            supporting_evidence={"underperforming_roles": underperforming_roles, "role_data": role_performance},
            business_impact="medium",
            actionability="short_term",
            recommendations=[
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.PERSONALIZE_APPROACH,
                    confidence=0.78,
                    expected_improvement=20.0,
                    implementation_complexity="medium",
                    evidence=role_performance,
                    specific_actions=[
                        "Create role-specific question templates",
                        "Provide role-specific training materials",
                        "Implement adaptive question complexity"
                    ],
                    success_metrics=["Role quality parity", "Improved engagement"]
                )
            ]
        ))
    
    return insights


def generate_engagement_insights(analysis: Dict[str, Any], events: List[LearningEvent]) -> List[LearningInsight]:
    """Generate engagement-specific insights"""
    insights = []
    
    overall_metrics = analysis.get("overall_metrics", {})
    avg_response_rate = overall_metrics.get("average_response_rate", 0)
    
    if avg_response_rate < 0.7:
        insights.append(LearningInsight(
            insight_id=f"engagement_low_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            pattern_type=LearningPattern.STAKEHOLDER_ENGAGEMENT,
            description=f"Stakeholder engagement is low at {avg_response_rate:.2%}. Needs improvement in targeting and communication.",
            supporting_evidence={"response_rate": avg_response_rate, "target": 0.8},
            business_impact="high",
            actionability="immediate",
            recommendations=[
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.ENHANCE_ENGAGEMENT,
                    confidence=0.82,
                    expected_improvement=25.0,
                    implementation_complexity="medium",
                    evidence=overall_metrics,
                    specific_actions=[
                        "Improve stakeholder communication strategy",
                        "Optimize questionnaire timing",
                        "Implement engagement incentives"
                    ],
                    success_metrics=["Response rate > 80%", "Reduced follow-up needed"]
                )
            ]
        ))
    
    # Temporal patterns
    temporal_patterns = analysis.get("temporal_patterns", {})
    optimal_times = [
        time for time, data in temporal_patterns.items()
        if data.get("optimal_timing", False)
    ]
    
    if optimal_times:
        insights.append(LearningInsight(
            insight_id=f"temporal_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            pattern_type=LearningPattern.STAKEHOLDER_ENGAGEMENT,
            description=f"Optimal engagement times identified: {', '.join(optimal_times)}. Schedule questionnaires accordingly.",
            supporting_evidence={"optimal_times": optimal_times, "temporal_data": temporal_patterns},
            business_impact="medium",
            actionability="immediate",
            recommendations=[
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.ADJUST_TIMING,
                    confidence=0.75,
                    expected_improvement=12.0,
                    implementation_complexity="low",
                    evidence=temporal_patterns,
                    specific_actions=[
                        "Schedule questionnaires during optimal times",
                        "Avoid low-engagement time periods",
                        "Implement time-zone aware scheduling"
                    ],
                    success_metrics=["Improved response rates", "Faster completion times"]
                )
            ]
        ))
    
    return insights


def generate_effectiveness_insights(analysis: Dict[str, Any], events: List[LearningEvent]) -> List[LearningInsight]:
    """Generate question effectiveness insights"""
    insights = []
    
    overall_metrics = analysis.get("overall_metrics", {})
    avg_clarity = overall_metrics.get("average_clarity", 0)
    avg_confusion = overall_metrics.get("average_confusion_rate", 0)
    
    if avg_clarity < 0.7 or avg_confusion > 0.3:
        insights.append(LearningInsight(
            insight_id=f"effectiveness_low_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            pattern_type=LearningPattern.QUESTION_EFFECTIVENESS,
            description=f"Questions need clarity improvement. Clarity: {avg_clarity:.2%}, Confusion: {avg_confusion:.2%}",
            supporting_evidence={"clarity": avg_clarity, "confusion": avg_confusion},
            business_impact="high",
            actionability="immediate",
            recommendations=[
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.REFINE_QUESTIONS,
                    confidence=0.88,
                    expected_improvement=20.0,
                    implementation_complexity="low",
                    evidence=overall_metrics,
                    specific_actions=[
                        "Simplify question language",
                        "Add contextual examples",
                        "Test questions with stakeholders"
                    ],
                    success_metrics=["Clarity > 85%", "Confusion < 15%"]
                )
            ]
        ))
    
    return insights


def generate_completion_insights(analysis: Dict[str, Any], events: List[LearningEvent]) -> List[LearningInsight]:
    """Generate completion rate insights"""
    insights = []
    
    overall_metrics = analysis.get("overall_metrics", {})
    avg_completion = overall_metrics.get("average_completion_rate", 0)
    
    if avg_completion < 0.75:
        insights.append(LearningInsight(
            insight_id=f"completion_low_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            pattern_type=LearningPattern.COMPLETION_RATES,
            description=f"Completion rate is below target at {avg_completion:.2%}. Focus on questionnaire length and complexity.",
            supporting_evidence={"completion_rate": avg_completion, "target": 0.75},
            business_impact="high",
            actionability="short_term",
            recommendations=[
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.REDUCE_COMPLEXITY,
                    confidence=0.80,
                    expected_improvement=18.0,
                    implementation_complexity="medium",
                    evidence=overall_metrics,
                    specific_actions=[
                        "Break long questionnaires into sections",
                        "Implement progress indicators",
                        "Allow saving and resuming"
                    ],
                    success_metrics=["Completion rate > 80%", "Reduced abandonment"]
                )
            ]
        ))
    
    # Length impact insights
    length_impact = analysis.get("length_impact", {})
    problematic_lengths = [
        length for length, data in length_impact.items()
        if data.get("average_completion_rate", 0) < 0.7 and length in ["long", "very_long"]
    ]
    
    if problematic_lengths:
        insights.append(LearningInsight(
            insight_id=f"length_impact_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            pattern_type=LearningPattern.COMPLETION_RATES,
            description=f"Long questionnaires show poor completion. Consider restructuring {', '.join(problematic_lengths)} questionnaires.",
            supporting_evidence={"problematic_lengths": problematic_lengths, "length_data": length_impact},
            business_impact="medium",
            actionability="short_term",
            recommendations=[
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.OPTIMIZE_SEQUENCING,
                    confidence=0.75,
                    expected_improvement=15.0,
                    implementation_complexity="medium",
                    evidence=length_impact,
                    specific_actions=[
                        "Prioritize critical questions first",
                        "Make optional questions clearly marked",
                        "Implement smart skip logic"
                    ],
                    success_metrics=["Improved completion for long forms", "Better data quality"]
                )
            ]
        ))
    
    return insights


def generate_resolution_insights(analysis: Dict[str, Any], events: List[LearningEvent]) -> List[LearningInsight]:
    """Generate gap resolution insights"""
    insights = []
    
    overall_metrics = analysis.get("overall_metrics", {})
    avg_resolution = overall_metrics.get("average_resolution_rate", 0)
    
    if avg_resolution < 0.8:
        insights.append(LearningInsight(
            insight_id=f"resolution_improvement_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            pattern_type=LearningPattern.GAP_RESOLUTION_SUCCESS,
            description=f"Gap resolution rate at {avg_resolution:.2%} needs improvement. Focus on targeting and validation.",
            supporting_evidence={"resolution_rate": avg_resolution, "target": 0.8},
            business_impact="high",
            actionability="immediate",
            recommendations=[
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.IMPROVE_TARGETING,
                    confidence=0.83,
                    expected_improvement=22.0,
                    implementation_complexity="medium",
                    evidence=overall_metrics,
                    specific_actions=[
                        "Better match questions to identified gaps",
                        "Implement multi-source validation",
                        "Add confidence indicators"
                    ],
                    success_metrics=["Resolution rate > 85%", "Higher confidence scores"]
                )
            ]
        ))
    
    return insights


def generate_context_insights(analysis: Dict[str, Any], events: List[LearningEvent]) -> List[LearningInsight]:
    """Generate business context insights"""
    insights = []
    
    overall_metrics = analysis.get("overall_metrics", {})
    avg_relevance = overall_metrics.get("average_context_relevance", 0)
    
    if avg_relevance < 0.75:
        insights.append(LearningInsight(
            insight_id=f"context_relevance_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            pattern_type=LearningPattern.BUSINESS_CONTEXT_CORRELATION,
            description=f"Context relevance at {avg_relevance:.2%} indicates need for better business alignment.",
            supporting_evidence={"relevance": avg_relevance, "target": 0.75},
            business_impact="medium",
            actionability="short_term",
            recommendations=[
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.PERSONALIZE_APPROACH,
                    confidence=0.77,
                    expected_improvement=16.0,
                    implementation_complexity="high",
                    evidence=overall_metrics,
                    specific_actions=[
                        "Develop industry-specific templates",
                        "Incorporate business metrics",
                        "Align with organizational goals"
                    ],
                    success_metrics=["Relevance > 80%", "Better stakeholder alignment"]
                )
            ]
        ))
    
    return insights


def generate_temporal_insights(analysis: Dict[str, Any], events: List[LearningEvent]) -> List[LearningInsight]:
    """Generate temporal optimization insights"""
    insights = []
    
    hourly_optimization = analysis.get("hourly_optimization", {})
    optimal_hours = [
        hour for hour, data in hourly_optimization.items()
        if data.get("optimal_hour", False)
    ]
    
    if optimal_hours:
        insights.append(LearningInsight(
            insight_id=f"optimal_timing_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            pattern_type=LearningPattern.TEMPORAL_OPTIMIZATION,
            description=f"Best response times identified: {', '.join(optimal_hours)}:00. Schedule accordingly for maximum engagement.",
            supporting_evidence={"optimal_hours": optimal_hours, "hourly_data": hourly_optimization},
            business_impact="medium",
            actionability="immediate",
            recommendations=[
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.ADJUST_TIMING,
                    confidence=0.85,
                    expected_improvement=20.0,
                    implementation_complexity="low",
                    evidence=hourly_optimization,
                    specific_actions=[
                        f"Schedule questionnaires at {', '.join(optimal_hours)}:00",
                        "Implement automated scheduling",
                        "Consider timezone differences"
                    ],
                    success_metrics=["20% improvement in response rates", "Faster completions"]
                )
            ]
        ))
    
    return insights


def generate_adaptation_insights(analysis: Dict[str, Any], events: List[LearningEvent]) -> List[LearningInsight]:
    """Generate complexity adaptation insights"""
    insights = []
    
    overall_metrics = analysis.get("overall_metrics", {})
    avg_match = overall_metrics.get("average_complexity_match", 0)
    
    if avg_match < 0.7:
        insights.append(LearningInsight(
            insight_id=f"adaptation_needed_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            pattern_type=LearningPattern.COMPLEXITY_ADAPTATION,
            description=f"Complexity matching at {avg_match:.2%} shows need for better adaptation to stakeholder capabilities.",
            supporting_evidence={"complexity_match": avg_match, "target": 0.7},
            business_impact="medium",
            actionability="short_term",
            recommendations=[
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.PERSONALIZE_APPROACH,
                    confidence=0.79,
                    expected_improvement=17.0,
                    implementation_complexity="high",
                    evidence=overall_metrics,
                    specific_actions=[
                        "Implement stakeholder profiling",
                        "Create adaptive question paths",
                        "Provide complexity options"
                    ],
                    success_metrics=["Match rate > 80%", "Higher satisfaction scores"]
                )
            ]
        ))
    
    return insights


def generate_correlation_insights(correlations: Dict) -> List[str]:
    """Generate insights from pattern correlations"""
    insights = []
    
    for correlation_pair, data in correlations.items():
        if isinstance(data, dict):
            coefficient = data.get("correlation_coefficient", 0)
            if abs(coefficient) > 0.7:
                patterns = correlation_pair.split("_vs_")
                if coefficient > 0:
                    insights.append(f"Strong positive correlation between {patterns[0]} and {patterns[1]} (r={coefficient:.2f})")
                else:
                    insights.append(f"Strong negative correlation between {patterns[0]} and {patterns[1]} (r={coefficient:.2f})")
    
    return insights if insights else ["No significant pattern correlations detected"]


def generate_correlation_recommendations(correlation_analysis: Dict) -> List[OptimizationRecommendation]:
    """Generate recommendations based on correlation analysis"""
    recommendations = []
    
    strong_correlations = correlation_analysis.get("strong_correlations", {})
    
    for correlation_pair, data in strong_correlations.items():
        if isinstance(data, dict) and data.get("correlation_coefficient", 0) > 0.7:
            patterns = correlation_pair.split("_vs_")
            recommendations.append(
                OptimizationRecommendation(
                    strategy=OptimizationStrategy.OPTIMIZE_SEQUENCING,
                    confidence=0.7,
                    expected_improvement=10.0,
                    implementation_complexity="low",
                    evidence=data,
                    specific_actions=[
                        f"Leverage synergy between {patterns[0]} and {patterns[1]}",
                        "Implement combined optimization strategies",
                        "Monitor both patterns together"
                    ],
                    success_metrics=["Improved overall performance", "Synergistic effects realized"]
                )
            )
    
    return recommendations


def prioritize_recommendations(recommendations: List[OptimizationRecommendation]) -> List[OptimizationRecommendation]:
    """Prioritize recommendations by impact and feasibility"""
    # Calculate priority score: confidence * expected_improvement / complexity_weight
    complexity_weights = {"low": 1.0, "medium": 1.5, "high": 2.0}
    
    for rec in recommendations:
        complexity_weight = complexity_weights.get(rec.implementation_complexity, 1.5)
        rec.priority_score = (rec.confidence * rec.expected_improvement) / complexity_weight
    
    return sorted(recommendations, key=lambda r: getattr(r, 'priority_score', 0), reverse=True)


def optimize_recommendation_set(recommendations: List[OptimizationRecommendation]) -> List[OptimizationRecommendation]:
    """Optimize recommendation set to remove conflicts and duplicates"""
    seen_strategies = set()
    optimized = []
    
    # Sort by priority first
    prioritized = prioritize_recommendations(recommendations)
    
    for rec in prioritized:
        # Check for strategy conflicts
        if rec.strategy not in seen_strategies:
            # Check if this recommendation conflicts with existing ones
            conflict = False
            for existing in optimized:
                if are_recommendations_conflicting(rec, existing):
                    conflict = True
                    break
            
            if not conflict:
                optimized.append(rec)
                seen_strategies.add(rec.strategy)
    
    return optimized


def are_recommendations_conflicting(rec1: OptimizationRecommendation, rec2: OptimizationRecommendation) -> bool:
    """Check if two recommendations conflict with each other"""
    # Define conflicting strategy pairs
    conflicts = [
        (OptimizationStrategy.REDUCE_COMPLEXITY, OptimizationStrategy.ENHANCE_ENGAGEMENT),
        (OptimizationStrategy.OPTIMIZE_SEQUENCING, OptimizationStrategy.STRENGTHEN_VALIDATION),
    ]
    
    for conflict_pair in conflicts:
        if (rec1.strategy in conflict_pair and rec2.strategy in conflict_pair and 
            rec1.strategy != rec2.strategy):
            return True
    
    return False


def calculate_pattern_correlation(pattern1_data: Dict, pattern2_data: Dict) -> Dict[str, Any]:
    """Calculate correlation between two patterns"""
    # Simplified correlation calculation
    # In a real implementation, this would use proper statistical methods
    
    # Extract comparable metrics
    metric1 = pattern1_data.get("overall_metrics", {}).get("events_analyzed", 0)
    metric2 = pattern2_data.get("overall_metrics", {}).get("events_analyzed", 0)
    
    if metric1 == 0 or metric2 == 0:
        return {"correlation_coefficient": 0, "significance": "none"}
    
    # Simple correlation estimate based on event counts
    correlation = min(metric1, metric2) / max(metric1, metric2)
    
    significance = "high" if correlation > 0.7 else "medium" if correlation > 0.4 else "low"
    
    return {
        "correlation_coefficient": correlation,
        "significance": significance,
        "sample_size": min(metric1, metric2)
    }


def identify_pattern_interactions(correlations: Dict) -> Dict[str, Any]:
    """Identify pattern interactions from correlations"""
    primary_interactions = []
    secondary_interactions = []
    
    for correlation_pair, data in correlations.items():
        if isinstance(data, dict):
            coefficient = data.get("correlation_coefficient", 0)
            if abs(coefficient) > 0.7:
                primary_interactions.append({
                    "patterns": correlation_pair.split("_vs_"),
                    "strength": coefficient,
                    "type": "positive" if coefficient > 0 else "negative"
                })
            elif abs(coefficient) > 0.4:
                secondary_interactions.append({
                    "patterns": correlation_pair.split("_vs_"),
                    "strength": coefficient,
                    "type": "positive" if coefficient > 0 else "negative"
                })
    
    return {
        "primary_interactions": primary_interactions,
        "secondary_interactions": secondary_interactions,
        "interaction_count": len(primary_interactions) + len(secondary_interactions)
    }


def identify_next_actions(recommendations: List[OptimizationRecommendation]) -> List[str]:
    """Identify immediate next actions from recommendations"""
    immediate_actions = []
    
    for rec in recommendations[:5]:  # Top 5 recommendations
        if rec.implementation_complexity == "low" and rec.confidence > 0.7:
            immediate_actions.extend(rec.specific_actions[:2])  # Top 2 actions per recommendation
    
    return immediate_actions[:8]  # Max 8 immediate actions