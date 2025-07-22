"""
Learning Optimizer Core
Main LearningOptimizer class implementation.

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .analyzers import (
    analyze_business_context_pattern,
    analyze_completion_rates_pattern,
    analyze_complexity_adaptation_pattern,
    analyze_gap_resolution_pattern,
    analyze_question_effectiveness_pattern,
    analyze_response_quality_pattern,
    analyze_stakeholder_engagement_pattern,
    analyze_temporal_optimization_pattern,
)
from .enums import LearningPattern, OptimizationStrategy
from .insights import (
    calculate_pattern_correlation,
    generate_adaptation_insights,
    generate_completion_insights,
    generate_context_insights,
    generate_correlation_insights,
    generate_correlation_recommendations,
    generate_effectiveness_insights,
    generate_engagement_insights,
    generate_quality_insights,
    generate_resolution_insights,
    generate_temporal_insights,
    identify_next_actions,
    identify_pattern_interactions,
    optimize_recommendation_set,
    prioritize_recommendations,
)
from .models import LearningEvent, LearningInsight, OptimizationRecommendation

logger = logging.getLogger(__name__)


class LearningOptimizer:
    """
    Advanced learning system for questionnaire optimization using pattern recognition
    and continuous improvement based on historical data and feedback.
    """
    
    def __init__(self):
        """Initialize learning optimizer"""
        self.learning_events: List[LearningEvent] = []
        self.pattern_analyzers = self._initialize_pattern_analyzers()
        self.optimization_thresholds = self._initialize_optimization_thresholds()
        self.success_benchmarks = self._initialize_success_benchmarks()
        
    def _initialize_pattern_analyzers(self) -> Dict[LearningPattern, Dict[str, Any]]:
        """Initialize pattern analyzer configurations"""
        return {
            LearningPattern.RESPONSE_QUALITY: {
                "min_events": 5,
                "analysis_window_days": 30,
                "quality_threshold": 0.75,
                "improvement_target": 0.85,
                "key_metrics": ["completeness", "accuracy", "relevance"]
            },
            LearningPattern.STAKEHOLDER_ENGAGEMENT: {
                "min_events": 10,
                "analysis_window_days": 60,
                "engagement_threshold": 0.65,
                "improvement_target": 0.80,
                "key_metrics": ["response_rate", "completion_time", "follow_up_needed"]
            },
            LearningPattern.QUESTION_EFFECTIVENESS: {
                "min_events": 15,
                "analysis_window_days": 90,
                "effectiveness_threshold": 0.70,
                "improvement_target": 0.85,
                "key_metrics": ["clarity_score", "answer_quality", "confusion_rate"]
            },
            LearningPattern.COMPLETION_RATES: {
                "min_events": 8,
                "analysis_window_days": 45,
                "completion_threshold": 0.75,
                "improvement_target": 0.90,
                "key_metrics": ["completion_rate", "abandonment_point", "time_to_complete"]
            },
            LearningPattern.GAP_RESOLUTION_SUCCESS: {
                "min_events": 12,
                "analysis_window_days": 120,
                "resolution_threshold": 0.80,
                "improvement_target": 0.92,
                "key_metrics": ["gap_filled", "confidence_improvement", "validation_success"]
            },
            LearningPattern.BUSINESS_CONTEXT_CORRELATION: {
                "min_events": 20,
                "analysis_window_days": 180,
                "correlation_threshold": 0.6,
                "improvement_target": 0.8,
                "key_metrics": ["context_relevance", "stakeholder_alignment", "business_value"]
            },
            LearningPattern.TEMPORAL_OPTIMIZATION: {
                "min_events": 25,
                "analysis_window_days": 90,
                "timing_threshold": 0.65,
                "improvement_target": 0.85,
                "key_metrics": ["optimal_timing", "response_speed", "completion_quality"]
            },
            LearningPattern.COMPLEXITY_ADAPTATION: {
                "min_events": 18,
                "analysis_window_days": 120,
                "adaptation_threshold": 0.70,
                "improvement_target": 0.88,
                "key_metrics": ["complexity_match", "user_satisfaction", "accuracy_maintenance"]
            }
        }
    
    def _initialize_optimization_thresholds(self) -> Dict[str, float]:
        """Initialize optimization decision thresholds"""
        return {
            "minimum_confidence": 0.7,      # Minimum confidence to apply optimization
            "significant_improvement": 0.1,  # Minimum improvement to warrant change
            "pattern_stability": 0.8,       # Pattern consistency threshold
            "implementation_urgency": 0.75, # Urgency threshold for immediate action
            "business_impact": 0.6,         # Business impact threshold
            "risk_tolerance": 0.3           # Maximum risk acceptable for optimization
        }
    
    def _initialize_success_benchmarks(self) -> Dict[str, Dict[str, float]]:
        """Initialize success benchmarks for different contexts"""
        return {
            "enterprise": {
                "response_rate": 0.85,
                "completion_rate": 0.90,
                "quality_score": 0.88,
                "engagement_score": 0.82,
                "time_efficiency": 0.75
            },
            "large": {
                "response_rate": 0.80,
                "completion_rate": 0.85,
                "quality_score": 0.85,
                "engagement_score": 0.78,
                "time_efficiency": 0.70
            },
            "medium": {
                "response_rate": 0.75,
                "completion_rate": 0.80,
                "quality_score": 0.80,
                "engagement_score": 0.75,
                "time_efficiency": 0.65
            },
            "small": {
                "response_rate": 0.70,
                "completion_rate": 0.75,
                "quality_score": 0.75,
                "engagement_score": 0.70,
                "time_efficiency": 0.60
            }
        }
    
    def add_learning_event(
        self,
        event_type: LearningPattern,
        collection_flow_id: str,
        questionnaire_id: str,
        stakeholder_role: str,
        business_context: Dict[str, Any],
        event_data: Dict[str, Any],
        success_metrics: Dict[str, float],
        feedback_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a learning event to the optimization system.
        
        Args:
            event_type: Type of learning pattern
            collection_flow_id: Collection flow identifier
            questionnaire_id: Questionnaire identifier
            stakeholder_role: Role of the stakeholder
            business_context: Business context information
            event_data: Event-specific data
            success_metrics: Success metrics for the event
            feedback_data: Optional feedback data
            
        Returns:
            Event ID for tracking
        """
        try:
            event_id = f"{event_type.value}_{collection_flow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            learning_event = LearningEvent(
                event_id=event_id,
                event_type=event_type,
                timestamp=datetime.now(timezone.utc),
                collection_flow_id=collection_flow_id,
                questionnaire_id=questionnaire_id,
                stakeholder_role=stakeholder_role,
                business_context=business_context,
                event_data=event_data,
                success_metrics=success_metrics,
                feedback_data=feedback_data
            )
            
            self.learning_events.append(learning_event)
            logger.info(f"Added learning event: {event_id}")
            
            return event_id
            
        except Exception as e:
            logger.error(f"Error adding learning event: {e}")
            return ""
    
    def analyze_learning_patterns(
        self,
        pattern_types: Optional[List[LearningPattern]] = None,
        analysis_window_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze learning patterns to identify optimization opportunities.
        
        Args:
            pattern_types: Specific pattern types to analyze (all if None)
            analysis_window_days: Analysis window in days (default varies by pattern)
            
        Returns:
            Comprehensive learning pattern analysis
        """
        try:
            if pattern_types is None:
                pattern_types = list(LearningPattern)
            
            analysis_results = {}
            learning_insights = []
            
            for pattern_type in pattern_types:
                logger.info(f"Analyzing pattern: {pattern_type.value}")
                
                # Get events for this pattern
                pattern_events = self._get_pattern_events(pattern_type, analysis_window_days)
                
                if len(pattern_events) < self.pattern_analyzers[pattern_type]["min_events"]:
                    logger.warning(f"Insufficient events for {pattern_type.value}: {len(pattern_events)}")
                    continue
                
                # Analyze specific pattern
                pattern_analysis = self._analyze_specific_pattern(pattern_type, pattern_events)
                analysis_results[pattern_type.value] = pattern_analysis
                
                # Generate insights
                insights = self._generate_pattern_insights(pattern_type, pattern_analysis, pattern_events)
                learning_insights.extend(insights)
            
            # Cross-pattern correlation analysis
            correlation_analysis = self._analyze_cross_pattern_correlations(analysis_results)
            
            # Generate optimization recommendations
            optimization_recommendations = self._generate_optimization_recommendations(
                analysis_results, learning_insights, correlation_analysis
            )
            
            return {
                "learning_analysis": {
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                    "patterns_analyzed": len(analysis_results),
                    "total_events": len(self.learning_events),
                    "analysis_window": analysis_window_days or "pattern_specific",
                    "pattern_results": analysis_results
                },
                "learning_insights": [self._insight_to_dict(insight) for insight in learning_insights],
                "correlation_analysis": correlation_analysis,
                "optimization_recommendations": [
                    self._recommendation_to_dict(rec) for rec in optimization_recommendations
                ],
                "performance_metrics": {
                    "learning_effectiveness": self._calculate_learning_effectiveness(),
                    "optimization_success_rate": self._calculate_optimization_success_rate(),
                    "pattern_prediction_accuracy": self._calculate_prediction_accuracy(),
                    "continuous_improvement_score": self._calculate_improvement_score()
                },
                "next_actions": identify_next_actions(optimization_recommendations)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing learning patterns: {e}")
            return self._create_error_analysis_result(str(e))
    
    def _get_pattern_events(
        self, 
        pattern_type: LearningPattern, 
        analysis_window_days: Optional[int]
    ) -> List[LearningEvent]:
        """Get events for a specific pattern within the analysis window"""
        if analysis_window_days is None:
            analysis_window_days = self.pattern_analyzers[pattern_type]["analysis_window_days"]
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=analysis_window_days)
        
        return [
            event for event in self.learning_events
            if event.event_type == pattern_type and event.timestamp >= cutoff_date
        ]
    
    def _analyze_specific_pattern(
        self, 
        pattern_type: LearningPattern, 
        events: List[LearningEvent]
    ) -> Dict[str, Any]:
        """Analyze a specific learning pattern"""
        try:
            analyzers = {
                LearningPattern.RESPONSE_QUALITY: analyze_response_quality_pattern,
                LearningPattern.STAKEHOLDER_ENGAGEMENT: analyze_stakeholder_engagement_pattern,
                LearningPattern.QUESTION_EFFECTIVENESS: analyze_question_effectiveness_pattern,
                LearningPattern.COMPLETION_RATES: analyze_completion_rates_pattern,
                LearningPattern.GAP_RESOLUTION_SUCCESS: analyze_gap_resolution_pattern,
                LearningPattern.BUSINESS_CONTEXT_CORRELATION: analyze_business_context_pattern,
                LearningPattern.TEMPORAL_OPTIMIZATION: analyze_temporal_optimization_pattern,
                LearningPattern.COMPLEXITY_ADAPTATION: analyze_complexity_adaptation_pattern
            }
            
            analyzer = analyzers.get(pattern_type)
            if analyzer:
                return analyzer(events)
            else:
                return {"error": f"Unknown pattern type: {pattern_type}"}
                
        except Exception as e:
            logger.error(f"Error analyzing {pattern_type.value} pattern: {e}")
            return {"error": str(e), "events_count": len(events)}
    
    def _generate_pattern_insights(
        self, 
        pattern_type: LearningPattern, 
        pattern_analysis: Dict[str, Any],
        events: List[LearningEvent]
    ) -> List[LearningInsight]:
        """Generate insights from pattern analysis"""
        insights = []
        
        try:
            insight_generators = {
                LearningPattern.RESPONSE_QUALITY: generate_quality_insights,
                LearningPattern.STAKEHOLDER_ENGAGEMENT: generate_engagement_insights,
                LearningPattern.QUESTION_EFFECTIVENESS: generate_effectiveness_insights,
                LearningPattern.COMPLETION_RATES: generate_completion_insights,
                LearningPattern.GAP_RESOLUTION_SUCCESS: generate_resolution_insights,
                LearningPattern.BUSINESS_CONTEXT_CORRELATION: generate_context_insights,
                LearningPattern.TEMPORAL_OPTIMIZATION: generate_temporal_insights,
                LearningPattern.COMPLEXITY_ADAPTATION: generate_adaptation_insights
            }
            
            generator = insight_generators.get(pattern_type)
            if generator:
                insights.extend(generator(pattern_analysis, events))
                
        except Exception as e:
            logger.error(f"Error generating insights for {pattern_type.value}: {e}")
        
        return insights
    
    def _analyze_cross_pattern_correlations(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze correlations between different learning patterns"""
        correlations = {}
        
        try:
            patterns = list(analysis_results.keys())
            
            for i, pattern1 in enumerate(patterns):
                for j, pattern2 in enumerate(patterns[i+1:], i+1):
                    correlation = calculate_pattern_correlation(
                        analysis_results[pattern1],
                        analysis_results[pattern2]
                    )
                    correlations[f"{pattern1}_vs_{pattern2}"] = correlation
            
            # Identify strong correlations
            strong_correlations = {
                k: v for k, v in correlations.items()
                if abs(v.get("correlation_coefficient", 0)) > 0.6
            }
            
            return {
                "correlation_matrix": correlations,
                "strong_correlations": strong_correlations,
                "correlation_insights": generate_correlation_insights(strong_correlations),
                "pattern_interactions": identify_pattern_interactions(correlations)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing cross-pattern correlations: {e}")
            return {"error": str(e)}
    
    def _generate_optimization_recommendations(
        self,
        analysis_results: Dict[str, Any],
        learning_insights: List[LearningInsight],
        correlation_analysis: Dict[str, Any]
    ) -> List[OptimizationRecommendation]:
        """Generate comprehensive optimization recommendations"""
        recommendations = []
        
        try:
            # Extract recommendations from insights
            for insight in learning_insights:
                recommendations.extend(insight.recommendations)
            
            # Add correlation-based recommendations
            correlation_recommendations = generate_correlation_recommendations(correlation_analysis)
            recommendations.extend(correlation_recommendations)
            
            # Prioritize recommendations
            prioritized_recommendations = prioritize_recommendations(recommendations)
            
            # Remove duplicates and conflicts
            optimized_recommendations = optimize_recommendation_set(prioritized_recommendations)
            
            return optimized_recommendations[:10]  # Top 10 recommendations
            
        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")
            return []
    
    def _calculate_learning_effectiveness(self) -> float:
        """Calculate overall learning effectiveness"""
        if not self.learning_events:
            return 0.0
        
        # Simple calculation based on event diversity and frequency
        pattern_types = set(event.event_type for event in self.learning_events)
        pattern_diversity = len(pattern_types) / len(LearningPattern)
        
        recent_events = [
            event for event in self.learning_events
            if event.timestamp > datetime.now(timezone.utc) - timedelta(days=30)
        ]
        
        learning_velocity = len(recent_events) / 30  # Events per day
        
        return min(1.0, (pattern_diversity * 0.6 + min(learning_velocity / 2, 1.0) * 0.4))
    
    def _calculate_optimization_success_rate(self) -> float:
        """Calculate optimization success rate"""
        # This would be calculated based on actual optimization implementations
        # For now, return a placeholder
        return 0.75
    
    def _calculate_prediction_accuracy(self) -> float:
        """Calculate pattern prediction accuracy"""
        # This would be calculated based on prediction vs actual outcomes
        # For now, return a placeholder
        return 0.82
    
    def _calculate_improvement_score(self) -> float:
        """Calculate continuous improvement score"""
        if not self.learning_events:
            return 0.0
        
        # Calculate improvement trends across all patterns
        improvement_trends = []
        
        for pattern_type in LearningPattern:
            pattern_events = [e for e in self.learning_events if e.event_type == pattern_type]
            if len(pattern_events) >= 3:
                # Get quality metrics trend
                quality_trend = []
                for event in pattern_events[-10:]:  # Last 10 events
                    quality = event.success_metrics.get("overall_quality", 0)
                    quality_trend.append(quality)
                
                if len(quality_trend) >= 2:
                    # Calculate improvement
                    improvement = (quality_trend[-1] - quality_trend[0]) / (quality_trend[0] if quality_trend[0] > 0 else 1)
                    improvement_trends.append(improvement)
        
        if not improvement_trends:
            return 0.0
        
        avg_improvement = sum(improvement_trends) / len(improvement_trends)
        return min(1.0, max(0.0, (avg_improvement + 1) / 2))  # Normalize to 0-1
    
    def _insight_to_dict(self, insight: LearningInsight) -> Dict[str, Any]:
        """Convert LearningInsight to dictionary"""
        return {
            "insight_id": insight.insight_id,
            "pattern_type": insight.pattern_type.value,
            "description": insight.description,
            "supporting_evidence": insight.supporting_evidence,
            "business_impact": insight.business_impact,
            "actionability": insight.actionability,
            "recommendations": [self._recommendation_to_dict(rec) for rec in insight.recommendations]
        }
    
    def _recommendation_to_dict(self, recommendation: OptimizationRecommendation) -> Dict[str, Any]:
        """Convert OptimizationRecommendation to dictionary"""
        return {
            "strategy": recommendation.strategy.value,
            "confidence": recommendation.confidence,
            "expected_improvement": recommendation.expected_improvement,
            "implementation_complexity": recommendation.implementation_complexity,
            "evidence": recommendation.evidence,
            "specific_actions": recommendation.specific_actions,
            "success_metrics": recommendation.success_metrics
        }
    
    def _create_error_analysis_result(self, error_msg: str) -> Dict[str, Any]:
        """Create error analysis result"""
        return {
            "learning_analysis": {
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "error": True,
                "error_message": error_msg,
                "patterns_analyzed": 0,
                "total_events": len(self.learning_events)
            },
            "learning_insights": [],
            "correlation_analysis": {"error": error_msg},
            "optimization_recommendations": [],
            "performance_metrics": {
                "learning_effectiveness": 0,
                "optimization_success_rate": 0,
                "pattern_prediction_accuracy": 0,
                "continuous_improvement_score": 0
            },
            "next_actions": ["Review error and retry analysis"]
        }


# Convenience function for easy integration
def optimize_questionnaire_learning(
    learning_events_data: List[Dict[str, Any]],
    analysis_window_days: Optional[int] = None,
    pattern_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    High-level function to perform learning optimization analysis.
    
    Args:
        learning_events_data: List of learning event data
        analysis_window_days: Analysis window in days
        pattern_types: Specific pattern types to analyze
        
    Returns:
        Comprehensive learning optimization analysis
    """
    try:
        optimizer = LearningOptimizer()
        
        # Add learning events
        for event_data in learning_events_data:
            try:
                pattern_type = LearningPattern(event_data.get("event_type", "response_quality"))
                optimizer.add_learning_event(
                    event_type=pattern_type,
                    collection_flow_id=event_data.get("collection_flow_id", ""),
                    questionnaire_id=event_data.get("questionnaire_id", ""),
                    stakeholder_role=event_data.get("stakeholder_role", ""),
                    business_context=event_data.get("business_context", {}),
                    event_data=event_data.get("event_data", {}),
                    success_metrics=event_data.get("success_metrics", {}),
                    feedback_data=event_data.get("feedback_data")
                )
            except Exception as e:
                logger.error(f"Error adding learning event: {e}")
                continue
        
        # Convert pattern types from strings if provided
        pattern_type_enums = None
        if pattern_types:
            pattern_type_enums = []
            for pt in pattern_types:
                try:
                    pattern_type_enums.append(LearningPattern(pt))
                except ValueError:
                    logger.warning(f"Invalid pattern type: {pt}")
        
        # Perform analysis
        analysis_results = optimizer.analyze_learning_patterns(
            pattern_types=pattern_type_enums,
            analysis_window_days=analysis_window_days
        )
        
        return analysis_results
        
    except Exception as e:
        logger.error(f"Error in questionnaire learning optimization: {e}")
        return {
            "error": str(e),
            "learning_analysis": {
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "error": True
            },
            "learning_insights": [],
            "optimization_recommendations": [],
            "next_actions": ["Review error and retry optimization"]
        }