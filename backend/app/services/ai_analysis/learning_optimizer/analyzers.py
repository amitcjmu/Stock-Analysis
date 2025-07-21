"""
Learning Optimizer Analyzers
Contains pattern-specific analysis methods.

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

import logging
from collections import defaultdict
from typing import Dict, List, Any

from .models import LearningEvent
from .calculations import (
    calculate_variance, classify_performance, get_time_bucket, 
    get_length_bucket, calculate_effectiveness_score,
    calculate_resolution_effectiveness, calculate_context_effectiveness,
    calculate_temporal_effectiveness, calculate_adaptation_effectiveness,
    classify_engagement_level, classify_effectiveness, classify_clarity,
    classify_completion_tier, classify_success_tier, assess_priority_performance,
    assess_domain_optimization, assess_size_effectiveness, assess_adaptation_success,
    assess_context_fit, calculate_trend_direction, calculate_improvement_rate
)

logger = logging.getLogger(__name__)


def analyze_response_quality_pattern(events: List[LearningEvent]) -> Dict[str, Any]:
    """Analyze response quality patterns"""
    quality_scores = []
    completeness_scores = []
    accuracy_scores = []
    relevance_scores = []
    
    quality_by_role = defaultdict(list)
    quality_by_complexity = defaultdict(list)
    quality_trends = []
    
    for event in events:
        metrics = event.success_metrics
        
        # Overall quality score
        quality = metrics.get("overall_quality", 0)
        quality_scores.append(quality)
        
        # Component scores
        completeness_scores.append(metrics.get("completeness", 0))
        accuracy_scores.append(metrics.get("accuracy", 0))
        relevance_scores.append(metrics.get("relevance", 0))
        
        # Segmented analysis
        quality_by_role[event.stakeholder_role].append(quality)
        complexity = event.event_data.get("question_complexity", "medium")
        quality_by_complexity[complexity].append(quality)
        
        # Temporal trends
        quality_trends.append({
            "timestamp": event.timestamp.isoformat(),
            "quality": quality,
            "questionnaire_id": event.questionnaire_id
        })
    
    return {
        "overall_metrics": {
            "average_quality": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            "average_completeness": sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0,
            "average_accuracy": sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0,
            "average_relevance": sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0,
            "quality_variance": calculate_variance(quality_scores),
            "events_analyzed": len(events)
        },
        "role_performance": {
            role: {
                "average_quality": sum(scores) / len(scores),
                "score_count": len(scores),
                "performance_tier": classify_performance(sum(scores) / len(scores))
            }
            for role, scores in quality_by_role.items()
        },
        "complexity_impact": {
            complexity: {
                "average_quality": sum(scores) / len(scores),
                "score_count": len(scores),
                "quality_drop": max(0, 100 - (sum(scores) / len(scores) * 100))
            }
            for complexity, scores in quality_by_complexity.items()
        },
        "quality_trends": {
            "trend_direction": calculate_trend_direction(quality_trends),
            "improvement_rate": calculate_improvement_rate(quality_trends),
            "data_points": quality_trends[-10:]  # Last 10 data points
        },
        "improvement_opportunities": identify_quality_improvements(
            quality_by_role, quality_by_complexity, events
        )
    }


def analyze_stakeholder_engagement_pattern(events: List[LearningEvent]) -> Dict[str, Any]:
    """Analyze stakeholder engagement patterns"""
    response_rates = []
    completion_times = []
    follow_up_rates = []
    
    engagement_by_role = defaultdict(list)
    engagement_by_time = defaultdict(list)
    engagement_trends = []
    
    for event in events:
        metrics = event.success_metrics
        event_data = event.event_data
        
        # Core engagement metrics
        response_rate = metrics.get("response_rate", 0)
        completion_time = event_data.get("completion_time_minutes", 0)
        follow_up_needed = metrics.get("follow_up_needed", 0)
        
        response_rates.append(response_rate)
        completion_times.append(completion_time)
        follow_up_rates.append(follow_up_needed)
        
        # Segmented analysis
        engagement_by_role[event.stakeholder_role].append(response_rate)
        
        # Time-based analysis
        hour_of_day = event.timestamp.hour
        time_bucket = get_time_bucket(hour_of_day)
        engagement_by_time[time_bucket].append(response_rate)
        
        # Trends
        engagement_trends.append({
            "timestamp": event.timestamp.isoformat(),
            "response_rate": response_rate,
            "completion_time": completion_time,
            "stakeholder_role": event.stakeholder_role
        })
    
    return {
        "overall_metrics": {
            "average_response_rate": sum(response_rates) / len(response_rates) if response_rates else 0,
            "average_completion_time": sum(completion_times) / len(completion_times) if completion_times else 0,
            "average_follow_up_rate": sum(follow_up_rates) / len(follow_up_rates) if follow_up_rates else 0,
            "engagement_consistency": 1 - calculate_variance(response_rates),
            "events_analyzed": len(events)
        },
        "role_engagement": {
            role: {
                "average_response_rate": sum(rates) / len(rates),
                "engagement_count": len(rates),
                "engagement_level": classify_engagement_level(sum(rates) / len(rates))
            }
            for role, rates in engagement_by_role.items()
        },
        "temporal_patterns": {
            time_bucket: {
                "average_response_rate": sum(rates) / len(rates),
                "response_count": len(rates),
                "optimal_timing": sum(rates) / len(rates) > 0.8
            }
            for time_bucket, rates in engagement_by_time.items()
        },
        "engagement_trends": {
            "trend_direction": calculate_trend_direction(engagement_trends, "response_rate"),
            "improvement_rate": calculate_improvement_rate(engagement_trends, "response_rate"),
            "data_points": engagement_trends[-15:]  # Last 15 data points
        },
        "optimization_insights": identify_engagement_optimizations(
            engagement_by_role, engagement_by_time, events
        )
    }


def analyze_question_effectiveness_pattern(events: List[LearningEvent]) -> Dict[str, Any]:
    """Analyze question effectiveness patterns"""
    clarity_scores = []
    answer_quality_scores = []
    confusion_rates = []
    
    effectiveness_by_type = defaultdict(list)
    effectiveness_by_complexity = defaultdict(list)
    
    for event in events:
        metrics = event.success_metrics
        event_data = event.event_data
        
        clarity = metrics.get("clarity_score", 0)
        answer_quality = metrics.get("answer_quality", 0)
        confusion_rate = metrics.get("confusion_rate", 0)
        
        clarity_scores.append(clarity)
        answer_quality_scores.append(answer_quality)
        confusion_rates.append(confusion_rate)
        
        # Segmented analysis
        question_type = event_data.get("question_type", "text_input")
        effectiveness_by_type[question_type].append(answer_quality)
        
        complexity = event_data.get("question_complexity", "medium")
        effectiveness_by_complexity[complexity].append(clarity)
    
    return {
        "overall_metrics": {
            "average_clarity": sum(clarity_scores) / len(clarity_scores) if clarity_scores else 0,
            "average_answer_quality": sum(answer_quality_scores) / len(answer_quality_scores) if answer_quality_scores else 0,
            "average_confusion_rate": sum(confusion_rates) / len(confusion_rates) if confusion_rates else 0,
            "effectiveness_score": calculate_effectiveness_score(clarity_scores, answer_quality_scores, confusion_rates),
            "events_analyzed": len(events)
        },
        "question_type_performance": {
            q_type: {
                "average_effectiveness": sum(scores) / len(scores),
                "question_count": len(scores),
                "effectiveness_tier": classify_effectiveness(sum(scores) / len(scores))
            }
            for q_type, scores in effectiveness_by_type.items()
        },
        "complexity_effectiveness": {
            complexity: {
                "average_clarity": sum(scores) / len(scores),
                "clarity_count": len(scores),
                "clarity_rating": classify_clarity(sum(scores) / len(scores))
            }
            for complexity, scores in effectiveness_by_complexity.items()
        },
        "question_optimization": identify_question_optimizations(
            effectiveness_by_type, effectiveness_by_complexity, events
        )
    }


def analyze_completion_rates_pattern(events: List[LearningEvent]) -> Dict[str, Any]:
    """Analyze completion rate patterns"""
    completion_rates = []
    abandonment_points = []
    completion_times = []
    
    completion_by_length = defaultdict(list)
    completion_by_complexity = defaultdict(list)
    
    for event in events:
        metrics = event.success_metrics
        event_data = event.event_data
        
        completion_rate = metrics.get("completion_rate", 0)
        abandonment_point = event_data.get("abandonment_point", 100)
        completion_time = event_data.get("time_to_complete", 0)
        
        completion_rates.append(completion_rate)
        abandonment_points.append(abandonment_point)
        completion_times.append(completion_time)
        
        # Segmented analysis
        questionnaire_length = event_data.get("total_questions", 0)
        length_bucket = get_length_bucket(questionnaire_length)
        completion_by_length[length_bucket].append(completion_rate)
        
        complexity = event_data.get("overall_complexity", "medium")
        completion_by_complexity[complexity].append(completion_rate)
    
    return {
        "overall_metrics": {
            "average_completion_rate": sum(completion_rates) / len(completion_rates) if completion_rates else 0,
            "average_abandonment_point": sum(abandonment_points) / len(abandonment_points) if abandonment_points else 0,
            "average_completion_time": sum(completion_times) / len(completion_times) if completion_times else 0,
            "completion_consistency": 1 - calculate_variance(completion_rates),
            "events_analyzed": len(events)
        },
        "length_impact": {
            length: {
                "average_completion_rate": sum(rates) / len(rates),
                "questionnaire_count": len(rates),
                "completion_tier": classify_completion_tier(sum(rates) / len(rates))
            }
            for length, rates in completion_by_length.items()
        },
        "complexity_impact": {
            complexity: {
                "average_completion_rate": sum(rates) / len(rates),
                "questionnaire_count": len(rates),
                "complexity_penalty": max(0, 100 - (sum(rates) / len(rates) * 100))
            }
            for complexity, rates in completion_by_complexity.items()
        },
        "completion_optimization": identify_completion_optimizations(
            completion_by_length, completion_by_complexity, events
        )
    }


def analyze_gap_resolution_pattern(events: List[LearningEvent]) -> Dict[str, Any]:
    """Analyze gap resolution success patterns"""
    resolution_rates = []
    confidence_improvements = []
    validation_success_rates = []
    
    resolution_by_gap_type = defaultdict(list)
    resolution_by_priority = defaultdict(list)
    
    for event in events:
        metrics = event.success_metrics
        event_data = event.event_data
        
        gap_filled = metrics.get("gap_filled", 0)
        confidence_improvement = metrics.get("confidence_improvement", 0)
        validation_success = metrics.get("validation_success", 0)
        
        resolution_rates.append(gap_filled)
        confidence_improvements.append(confidence_improvement)
        validation_success_rates.append(validation_success)
        
        # Segmented analysis
        gap_type = event_data.get("gap_type", "unknown")
        resolution_by_gap_type[gap_type].append(gap_filled)
        
        gap_priority = event_data.get("gap_priority", 3)
        resolution_by_priority[str(gap_priority)].append(gap_filled)
    
    return {
        "overall_metrics": {
            "average_resolution_rate": sum(resolution_rates) / len(resolution_rates) if resolution_rates else 0,
            "average_confidence_improvement": sum(confidence_improvements) / len(confidence_improvements) if confidence_improvements else 0,
            "average_validation_success": sum(validation_success_rates) / len(validation_success_rates) if validation_success_rates else 0,
            "resolution_effectiveness": calculate_resolution_effectiveness(resolution_rates, confidence_improvements),
            "events_analyzed": len(events)
        },
        "gap_type_success": {
            gap_type: {
                "average_resolution_rate": sum(rates) / len(rates),
                "gap_count": len(rates),
                "success_tier": classify_success_tier(sum(rates) / len(rates))
            }
            for gap_type, rates in resolution_by_gap_type.items()
        },
        "priority_effectiveness": {
            priority: {
                "average_resolution_rate": sum(rates) / len(rates),
                "gap_count": len(rates),
                "priority_performance": assess_priority_performance(priority, sum(rates) / len(rates))
            }
            for priority, rates in resolution_by_priority.items()
        },
        "resolution_optimization": identify_resolution_optimizations(
            resolution_by_gap_type, resolution_by_priority, events
        )
    }


def analyze_business_context_pattern(events: List[LearningEvent]) -> Dict[str, Any]:
    """Analyze business context correlation patterns"""
    context_relevance_scores = []
    stakeholder_alignment_scores = []
    business_value_scores = []
    
    context_by_domain = defaultdict(list)
    context_by_size = defaultdict(list)
    
    for event in events:
        metrics = event.success_metrics
        business_context = event.business_context
        
        context_relevance = metrics.get("context_relevance", 0)
        stakeholder_alignment = metrics.get("stakeholder_alignment", 0)
        business_value = metrics.get("business_value", 0)
        
        context_relevance_scores.append(context_relevance)
        stakeholder_alignment_scores.append(stakeholder_alignment)
        business_value_scores.append(business_value)
        
        # Segmented analysis
        domain = business_context.get("domain", "general")
        context_by_domain[domain].append(context_relevance)
        
        org_size = business_context.get("organization_size", "medium")
        context_by_size[org_size].append(stakeholder_alignment)
    
    return {
        "overall_metrics": {
            "average_context_relevance": sum(context_relevance_scores) / len(context_relevance_scores) if context_relevance_scores else 0,
            "average_stakeholder_alignment": sum(stakeholder_alignment_scores) / len(stakeholder_alignment_scores) if stakeholder_alignment_scores else 0,
            "average_business_value": sum(business_value_scores) / len(business_value_scores) if business_value_scores else 0,
            "context_effectiveness": calculate_context_effectiveness(context_relevance_scores, stakeholder_alignment_scores),
            "events_analyzed": len(events)
        },
        "domain_performance": {
            domain: {
                "average_relevance": sum(scores) / len(scores),
                "context_count": len(scores),
                "domain_optimization": assess_domain_optimization(domain, sum(scores) / len(scores))
            }
            for domain, scores in context_by_domain.items()
        },
        "size_alignment": {
            size: {
                "average_alignment": sum(scores) / len(scores),
                "alignment_count": len(scores),
                "size_effectiveness": assess_size_effectiveness(size, sum(scores) / len(scores))
            }
            for size, scores in context_by_size.items()
        },
        "context_optimization": identify_context_optimizations(
            context_by_domain, context_by_size, events
        )
    }


def analyze_temporal_optimization_pattern(events: List[LearningEvent]) -> Dict[str, Any]:
    """Analyze temporal optimization patterns"""
    timing_scores = []
    response_speeds = []
    completion_qualities = []
    
    timing_by_hour = defaultdict(list)
    timing_by_day = defaultdict(list)
    
    for event in events:
        metrics = event.success_metrics
        
        optimal_timing = metrics.get("optimal_timing", 0)
        response_speed = metrics.get("response_speed", 0)
        completion_quality = metrics.get("completion_quality", 0)
        
        timing_scores.append(optimal_timing)
        response_speeds.append(response_speed)
        completion_qualities.append(completion_quality)
        
        # Temporal analysis
        hour = event.timestamp.hour
        timing_by_hour[hour].append(optimal_timing)
        
        day_of_week = event.timestamp.weekday()
        timing_by_day[day_of_week].append(response_speed)
    
    from .calculations import get_day_name
    
    return {
        "overall_metrics": {
            "average_timing_score": sum(timing_scores) / len(timing_scores) if timing_scores else 0,
            "average_response_speed": sum(response_speeds) / len(response_speeds) if response_speeds else 0,
            "average_completion_quality": sum(completion_qualities) / len(completion_qualities) if completion_qualities else 0,
            "temporal_effectiveness": calculate_temporal_effectiveness(timing_scores, response_speeds),
            "events_analyzed": len(events)
        },
        "hourly_optimization": {
            str(hour): {
                "average_timing_score": sum(scores) / len(scores),
                "event_count": len(scores),
                "optimal_hour": sum(scores) / len(scores) > 0.8
            }
            for hour, scores in timing_by_hour.items()
        },
        "daily_patterns": {
            get_day_name(day): {
                "average_response_speed": sum(speeds) / len(speeds),
                "event_count": len(speeds),
                "preferred_day": sum(speeds) / len(speeds) > 0.75
            }
            for day, speeds in timing_by_day.items()
        },
        "temporal_recommendations": identify_temporal_optimizations(
            timing_by_hour, timing_by_day, events
        )
    }


def analyze_complexity_adaptation_pattern(events: List[LearningEvent]) -> Dict[str, Any]:
    """Analyze complexity adaptation patterns"""
    complexity_matches = []
    user_satisfactions = []
    accuracy_maintenance = []
    
    adaptation_by_role = defaultdict(list)
    adaptation_by_context = defaultdict(list)
    
    for event in events:
        metrics = event.success_metrics
        event_data = event.event_data
        
        complexity_match = metrics.get("complexity_match", 0)
        user_satisfaction = metrics.get("user_satisfaction", 0)
        accuracy_maintained = metrics.get("accuracy_maintenance", 0)
        
        complexity_matches.append(complexity_match)
        user_satisfactions.append(user_satisfaction)
        accuracy_maintenance.append(accuracy_maintained)
        
        # Segmented analysis
        adaptation_by_role[event.stakeholder_role].append(complexity_match)
        
        business_context = event.business_context
        domain = business_context.get("domain", "general")
        adaptation_by_context[domain].append(user_satisfaction)
    
    return {
        "overall_metrics": {
            "average_complexity_match": sum(complexity_matches) / len(complexity_matches) if complexity_matches else 0,
            "average_user_satisfaction": sum(user_satisfactions) / len(user_satisfactions) if user_satisfactions else 0,
            "average_accuracy_maintenance": sum(accuracy_maintenance) / len(accuracy_maintenance) if accuracy_maintenance else 0,
            "adaptation_effectiveness": calculate_adaptation_effectiveness(complexity_matches, user_satisfactions),
            "events_analyzed": len(events)
        },
        "role_adaptation": {
            role: {
                "average_complexity_match": sum(matches) / len(matches),
                "adaptation_count": len(matches),
                "adaptation_success": assess_adaptation_success(sum(matches) / len(matches))
            }
            for role, matches in adaptation_by_role.items()
        },
        "context_adaptation": {
            context: {
                "average_satisfaction": sum(satisfactions) / len(satisfactions),
                "satisfaction_count": len(satisfactions),
                "context_fit": assess_context_fit(sum(satisfactions) / len(satisfactions))
            }
            for context, satisfactions in adaptation_by_context.items()
        },
        "adaptation_optimization": identify_adaptation_optimizations(
            adaptation_by_role, adaptation_by_context, events
        )
    }


# Identification methods for optimizations
def identify_quality_improvements(by_role: Dict, by_complexity: Dict, events: List) -> List[str]:
    """Identify quality improvement opportunities"""
    improvements = []
    
    # Check for underperforming roles
    for role, scores in by_role.items():
        avg_score = sum(scores) / len(scores) if scores else 0
        if avg_score < 0.7:
            improvements.append(f"Improve question clarity for {role} role")
    
    # Check for complexity issues
    for complexity, scores in by_complexity.items():
        avg_score = sum(scores) / len(scores) if scores else 0
        if avg_score < 0.75 and complexity in ["high", "very_high"]:
            improvements.append(f"Simplify {complexity} complexity questions")
    
    if not improvements:
        improvements.append("Maintain current quality standards")
    
    return improvements


def identify_engagement_optimizations(by_role: Dict, by_time: Dict, events: List) -> List[str]:
    """Identify engagement optimization opportunities"""
    optimizations = []
    
    # Check for low engagement roles
    for role, rates in by_role.items():
        avg_rate = sum(rates) / len(rates) if rates else 0
        if avg_rate < 0.7:
            optimizations.append(f"Improve communication strategy for {role} role")
    
    # Check for optimal timing patterns
    best_time = None
    best_rate = 0
    for time_bucket, rates in by_time.items():
        avg_rate = sum(rates) / len(rates) if rates else 0
        if avg_rate > best_rate:
            best_rate = avg_rate
            best_time = time_bucket
    
    if best_time:
        optimizations.append(f"Schedule questionnaires during {best_time} for best engagement")
    
    return optimizations if optimizations else ["Current engagement strategy is effective"]


def identify_question_optimizations(by_type: Dict, by_complexity: Dict, events: List) -> List[str]:
    """Identify question optimization opportunities"""
    optimizations = []
    
    # Check for underperforming question types
    for q_type, scores in by_type.items():
        avg_score = sum(scores) / len(scores) if scores else 0
        if avg_score < 0.7:
            optimizations.append(f"Redesign {q_type} questions for better effectiveness")
    
    # Check for complexity issues
    for complexity, scores in by_complexity.items():
        avg_score = sum(scores) / len(scores) if scores else 0
        if avg_score < 0.75:
            optimizations.append(f"Improve clarity for {complexity} complexity questions")
    
    return optimizations if optimizations else ["Question design is effective"]


def identify_completion_optimizations(by_length: Dict, by_complexity: Dict, events: List) -> List[str]:
    """Identify completion optimization opportunities"""
    optimizations = []
    
    # Check for length impact
    for length, rates in by_length.items():
        avg_rate = sum(rates) / len(rates) if rates else 0
        if avg_rate < 0.75 and length in ["long", "very_long"]:
            optimizations.append(f"Consider breaking up {length} questionnaires")
    
    # Check for complexity impact
    for complexity, rates in by_complexity.items():
        avg_rate = sum(rates) / len(rates) if rates else 0
        if avg_rate < 0.8 and complexity == "high":
            optimizations.append("Provide better guidance for complex questionnaires")
    
    return optimizations if optimizations else ["Completion rates are satisfactory"]


def identify_resolution_optimizations(by_type: Dict, by_priority: Dict, events: List) -> List[str]:
    """Identify gap resolution optimization opportunities"""
    optimizations = []
    
    # Check for gap type performance
    for gap_type, rates in by_type.items():
        avg_rate = sum(rates) / len(rates) if rates else 0
        if avg_rate < 0.75:
            optimizations.append(f"Improve resolution strategy for {gap_type} gaps")
    
    # Check priority alignment
    for priority, rates in by_priority.items():
        avg_rate = sum(rates) / len(rates) if rates else 0
        if priority in ["1", "2"] and avg_rate < 0.85:
            optimizations.append(f"Focus on improving high-priority (P{priority}) gap resolution")
    
    return optimizations if optimizations else ["Gap resolution is effective"]


def identify_context_optimizations(by_domain: Dict, by_size: Dict, events: List) -> List[str]:
    """Identify context optimization opportunities"""
    optimizations = []
    
    # Check domain performance
    for domain, scores in by_domain.items():
        avg_score = sum(scores) / len(scores) if scores else 0
        if avg_score < 0.7:
            optimizations.append(f"Customize questionnaires for {domain} domain")
    
    # Check organization size alignment
    for size, scores in by_size.items():
        avg_score = sum(scores) / len(scores) if scores else 0
        if avg_score < 0.75:
            optimizations.append(f"Adapt approach for {size} organizations")
    
    return optimizations if optimizations else ["Context alignment is effective"]


def identify_temporal_optimizations(by_hour: Dict, by_day: Dict, events: List) -> List[str]:
    """Identify temporal optimization opportunities"""
    optimizations = []
    
    # Find optimal hours
    optimal_hours = []
    for hour, scores in by_hour.items():
        avg_score = sum(scores) / len(scores) if scores else 0
        if avg_score > 0.8:
            optimal_hours.append(f"{hour}:00")
    
    if optimal_hours:
        optimizations.append(f"Schedule questionnaires at: {', '.join(optimal_hours)}")
    
    # Find optimal days
    from .calculations import get_day_name
    optimal_days = []
    for day, speeds in by_day.items():
        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        if avg_speed > 0.75:
            optimal_days.append(get_day_name(day))
    
    if optimal_days:
        optimizations.append(f"Prefer these days: {', '.join(optimal_days)}")
    
    return optimizations if optimizations else ["Current timing is acceptable"]


def identify_adaptation_optimizations(by_role: Dict, by_context: Dict, events: List) -> List[str]:
    """Identify adaptation optimization opportunities"""
    optimizations = []
    
    # Check role adaptation
    for role, matches in by_role.items():
        avg_match = sum(matches) / len(matches) if matches else 0
        if avg_match < 0.7:
            optimizations.append(f"Improve complexity adaptation for {role} role")
    
    # Check context adaptation
    for context, satisfactions in by_context.items():
        avg_satisfaction = sum(satisfactions) / len(satisfactions) if satisfactions else 0
        if avg_satisfaction < 0.75:
            optimizations.append(f"Better adapt complexity for {context} context")
    
    return optimizations if optimizations else ["Complexity adaptation is effective"]