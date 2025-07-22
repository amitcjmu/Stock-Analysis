"""
Learning Optimizer Calculations
Contains helper methods for statistical calculations and classifications.

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

from typing import Any, Dict, List


def calculate_variance(values: List[float]) -> float:
    """Calculate variance of values"""
    if not values or len(values) < 2:
        return 0.0
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance


def calculate_trend_direction(trend_data: List[Dict[str, Any]], metric_key: str = "quality") -> str:
    """Calculate trend direction"""
    if len(trend_data) < 2:
        return "insufficient_data"
    
    values = [point.get(metric_key, 0) for point in trend_data]
    
    # Simple linear trend
    x = list(range(len(values)))
    n = len(values)
    
    sum_x = sum(x)
    sum_y = sum(values)
    sum_xy = sum(x[i] * values[i] for i in range(n))
    sum_x2 = sum(x[i] ** 2 for i in range(n))
    
    if n * sum_x2 - sum_x ** 2 == 0:
        return "stable"
    
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
    
    if slope > 0.01:
        return "improving"
    elif slope < -0.01:
        return "declining"
    else:
        return "stable"


def calculate_improvement_rate(trend_data: List[Dict[str, Any]], metric_key: str = "quality") -> float:
    """Calculate rate of improvement"""
    if len(trend_data) < 2:
        return 0.0
    
    values = [point.get(metric_key, 0) for point in trend_data]
    
    if values[0] == 0:
        return 0.0
    
    return ((values[-1] - values[0]) / values[0]) * 100


def classify_performance(score: float) -> str:
    """Classify performance level"""
    if score >= 0.9:
        return "excellent"
    elif score >= 0.8:
        return "good"
    elif score >= 0.7:
        return "acceptable"
    elif score >= 0.6:
        return "needs_improvement"
    else:
        return "poor"


def get_time_bucket(hour: int) -> str:
    """Get time bucket for hour"""
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 22:
        return "evening"
    else:
        return "night"


def get_length_bucket(question_count: int) -> str:
    """Get length bucket for question count"""
    if question_count <= 10:
        return "short"
    elif question_count <= 25:
        return "medium"
    elif question_count <= 50:
        return "long"
    else:
        return "very_long"


def get_day_name(day_number: int) -> str:
    """Get day name from day number"""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[day_number] if 0 <= day_number < 7 else "Unknown"


def calculate_effectiveness_score(clarity: List[float], quality: List[float], confusion: List[float]) -> float:
    """Calculate effectiveness score from multiple metrics"""
    if not clarity or not quality:
        return 0.0
    
    avg_clarity = sum(clarity) / len(clarity)
    avg_quality = sum(quality) / len(quality)
    avg_confusion = sum(confusion) / len(confusion) if confusion else 0
    
    # Effectiveness = high clarity + high quality - confusion
    return max(0.0, min(1.0, (avg_clarity + avg_quality) / 2 - avg_confusion))


def calculate_resolution_effectiveness(resolution: List[float], confidence: List[float]) -> float:
    """Calculate resolution effectiveness"""
    if not resolution or not confidence:
        return 0.0
    
    avg_resolution = sum(resolution) / len(resolution)
    avg_confidence = sum(confidence) / len(confidence)
    
    return (avg_resolution * 0.7 + avg_confidence * 0.3)


def calculate_context_effectiveness(relevance: List[float], alignment: List[float]) -> float:
    """Calculate context effectiveness"""
    if not relevance or not alignment:
        return 0.0
    
    avg_relevance = sum(relevance) / len(relevance)
    avg_alignment = sum(alignment) / len(alignment)
    
    return (avg_relevance + avg_alignment) / 2


def calculate_temporal_effectiveness(timing: List[float], speed: List[float]) -> float:
    """Calculate temporal effectiveness"""
    if not timing or not speed:
        return 0.0
    
    avg_timing = sum(timing) / len(timing)
    avg_speed = sum(speed) / len(speed)
    
    return (avg_timing * 0.6 + avg_speed * 0.4)


def calculate_adaptation_effectiveness(complexity: List[float], satisfaction: List[float]) -> float:
    """Calculate adaptation effectiveness"""
    if not complexity or not satisfaction:
        return 0.0
    
    avg_complexity = sum(complexity) / len(complexity)
    avg_satisfaction = sum(satisfaction) / len(satisfaction)
    
    return (avg_complexity * 0.5 + avg_satisfaction * 0.5)


# Classification helper functions
def classify_engagement_level(rate: float) -> str:
    """Classify engagement level"""
    return classify_performance(rate)


def classify_effectiveness(score: float) -> str:
    """Classify effectiveness"""
    return classify_performance(score)


def classify_clarity(score: float) -> str:
    """Classify clarity"""
    return classify_performance(score)


def classify_completion_tier(rate: float) -> str:
    """Classify completion tier"""
    return classify_performance(rate)


def classify_success_tier(rate: float) -> str:
    """Classify success tier"""
    return classify_performance(rate)


# Assessment helper functions
def assess_priority_performance(priority: str, rate: float) -> str:
    """Assess priority performance"""
    return f"Priority {priority}: {classify_performance(rate)}"


def assess_domain_optimization(domain: str, score: float) -> str:
    """Assess domain optimization"""
    return f"{domain}: {classify_performance(score)}"


def assess_size_effectiveness(size: str, score: float) -> str:
    """Assess size effectiveness"""
    return f"{size}: {classify_performance(score)}"


def assess_adaptation_success(score: float) -> str:
    """Assess adaptation success"""
    return classify_performance(score)


def assess_context_fit(score: float) -> str:
    """Assess context fit"""
    return classify_performance(score)