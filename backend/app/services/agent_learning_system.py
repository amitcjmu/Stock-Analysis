"""
Agent Learning System - Platform-wide learning infrastructure for AI agents

This system manages learning patterns, memory, and performance improvement across all agents
while maintaining strict client-specific context isolation for enterprise deployment.
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import statistics
from collections import defaultdict, deque

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, func
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.asset import Asset

logger = logging.getLogger(__name__)

class LearningDomain(Enum):
    """Learning domains for different types of agent intelligence"""
    FIELD_MAPPING = "field_mapping"
    ASSET_CLASSIFICATION = "asset_classification"
    DATA_QUALITY = "data_quality"
    APPLICATION_DISCOVERY = "application_discovery"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    TECH_DEBT_ASSESSMENT = "tech_debt_assessment"
    USER_PREFERENCES = "user_preferences"

@dataclass
class LearningPattern:
    """Represents a learned pattern that can be applied across agents"""
    pattern_id: str
    domain: LearningDomain
    pattern_type: str
    confidence: float
    evidence_count: int
    pattern_data: Dict[str, Any]
    created_at: datetime
    last_reinforced: datetime
    success_rate: float
    organizational_context: Optional[str] = None

@dataclass
class UserFeedback:
    """User feedback that improves agent accuracy"""
    feedback_id: str
    agent_name: str
    domain: LearningDomain
    original_prediction: Any
    corrected_value: Any
    feedback_type: str  # correction, confirmation, clarification
    context: Dict[str, Any]
    timestamp: datetime
    confidence_delta: float

@dataclass
class AgentPerformanceMetric:
    """Performance tracking for individual agents"""
    agent_name: str
    domain: LearningDomain
    accuracy_score: float
    confidence_score: float
    response_time: float
    task_count: int
    success_rate: float
    learning_velocity: float
    last_updated: datetime

class AgentLearningSystem:
    """
    Comprehensive learning system for AI agents with enterprise-grade
    pattern recognition, memory management, and performance optimization.
    """
    
    def __init__(self):
        self.learning_patterns: Dict[str, LearningPattern] = {}
        self.user_feedback_history: deque = deque(maxlen=10000)
        self.agent_performance: Dict[str, AgentPerformanceMetric] = {}
        self.pattern_cache: Dict[str, Any] = {}
        self.learning_session_id = self._generate_session_id()
        
    def _generate_session_id(self) -> str:
        """Generate unique session ID for learning tracking"""
        return hashlib.md5(f"{datetime.now().isoformat()}".encode()).hexdigest()[:12]
    
    async def record_user_feedback(
        self,
        agent_name: str,
        domain: LearningDomain,
        original_prediction: Any,
        corrected_value: Any,
        feedback_type: str,
        context: Dict[str, Any],
        client_account_id: Optional[int] = None
    ) -> UserFeedback:
        """Record user feedback for agent learning improvement"""
        try:
            feedback_id = self._generate_feedback_id(agent_name, domain, context)
            
            # Calculate confidence delta based on feedback type
            confidence_delta = self._calculate_confidence_delta(
                feedback_type, original_prediction, corrected_value
            )
            
            feedback = UserFeedback(
                feedback_id=feedback_id,
                agent_name=agent_name,
                domain=domain,
                original_prediction=original_prediction,
                corrected_value=corrected_value,
                feedback_type=feedback_type,
                context=context,
                timestamp=datetime.now(),
                confidence_delta=confidence_delta
            )
            
            # Store feedback in history
            self.user_feedback_history.append(feedback)
            
            # Extract learning patterns from feedback
            await self._extract_patterns_from_feedback(feedback, client_account_id)
            
            # Update agent performance metrics
            await self._update_agent_performance(feedback)
            
            logger.info(f"Recorded user feedback for {agent_name} in {domain.value}: {feedback_type}")
            return feedback
            
        except Exception as e:
            logger.error(f"Error recording user feedback: {str(e)}")
            raise
    
    async def get_learning_patterns(
        self,
        domain: LearningDomain,
        confidence_threshold: float = 0.7,
        context_filter: Optional[str] = None,
        client_account_id: Optional[int] = None
    ) -> List[LearningPattern]:
        """Retrieve learning patterns for specific domain with confidence filtering"""
        try:
            patterns = []
            
            for pattern in self.learning_patterns.values():
                if pattern.domain != domain:
                    continue
                    
                if pattern.confidence < confidence_threshold:
                    continue
                    
                # Apply context filtering if specified
                if context_filter and pattern.organizational_context != context_filter:
                    continue
                    
                # Client-specific patterns only if client_account_id provided
                if client_account_id and pattern.organizational_context:
                    if f"client_{client_account_id}" not in pattern.organizational_context:
                        continue
                
                patterns.append(pattern)
            
            # Sort by confidence and evidence count
            patterns.sort(key=lambda p: (p.confidence, p.evidence_count), reverse=True)
            
            logger.info(f"Retrieved {len(patterns)} learning patterns for {domain.value}")
            return patterns
            
        except Exception as e:
            logger.error(f"Error retrieving learning patterns: {str(e)}")
            return []
    
    async def suggest_field_mappings(
        self,
        source_columns: List[str],
        target_schema: Dict[str, Any],
        organizational_context: Optional[str] = None,
        confidence_threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Suggest field mappings based on learned patterns"""
        try:
            suggestions = []
            
            # Get field mapping patterns
            patterns = await self.get_learning_patterns(
                LearningDomain.FIELD_MAPPING,
                confidence_threshold,
                organizational_context
            )
            
            for column in source_columns:
                best_match = None
                best_confidence = 0.0
                
                for pattern in patterns:
                    if pattern.pattern_type != "field_mapping":
                        continue
                        
                    # Check if pattern matches this column
                    match_confidence = self._calculate_field_match_confidence(
                        column, pattern.pattern_data
                    )
                    
                    if match_confidence > best_confidence and match_confidence >= confidence_threshold:
                        best_confidence = match_confidence
                        best_match = pattern
                
                if best_match:
                    suggestions.append({
                        "source_column": column,
                        "suggested_mapping": best_match.pattern_data.get("target_field"),
                        "confidence": best_confidence,
                        "reasoning": best_match.pattern_data.get("reasoning", ""),
                        "pattern_id": best_match.pattern_id,
                        "evidence_count": best_match.evidence_count
                    })
            
            logger.info(f"Generated {len(suggestions)} field mapping suggestions")
            return suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting field mappings: {str(e)}")
            return []
    
    async def update_agent_accuracy(
        self,
        agent_name: str,
        domain: LearningDomain,
        task_result: Dict[str, Any],
        execution_time: float
    ) -> None:
        """Update agent accuracy and performance metrics"""
        try:
            # Get or create performance metric
            metric_key = f"{agent_name}_{domain.value}"
            
            if metric_key not in self.agent_performance:
                self.agent_performance[metric_key] = AgentPerformanceMetric(
                    agent_name=agent_name,
                    domain=domain,
                    accuracy_score=0.0,
                    confidence_score=0.0,
                    response_time=0.0,
                    task_count=0,
                    success_rate=0.0,
                    learning_velocity=0.0,
                    last_updated=datetime.now()
                )
            
            metric = self.agent_performance[metric_key]
            
            # Update metrics based on task result
            task_success = task_result.get("success", False)
            task_confidence = task_result.get("confidence", 0.0)
            
            # Calculate new metrics
            metric.task_count += 1
            metric.response_time = (metric.response_time + execution_time) / 2
            metric.confidence_score = (metric.confidence_score + task_confidence) / 2
            
            # Update success rate
            if task_success:
                metric.success_rate = (metric.success_rate * (metric.task_count - 1) + 1.0) / metric.task_count
            else:
                metric.success_rate = (metric.success_rate * (metric.task_count - 1)) / metric.task_count
            
            # Calculate learning velocity (improvement rate)
            recent_feedback = [f for f in self.user_feedback_history 
                             if f.agent_name == agent_name and f.domain == domain
                             and f.timestamp > datetime.now() - timedelta(hours=24)]
            
            if recent_feedback:
                positive_feedback = sum(1 for f in recent_feedback if f.confidence_delta > 0)
                metric.learning_velocity = positive_feedback / len(recent_feedback)
            
            metric.last_updated = datetime.now()
            
            logger.info(f"Updated performance metrics for {agent_name} in {domain.value}")
            
        except Exception as e:
            logger.error(f"Error updating agent accuracy: {str(e)}")
    
    async def get_agent_intelligence_summary(
        self,
        agent_name: str,
        domains: Optional[List[LearningDomain]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive intelligence summary for an agent"""
        try:
            if domains is None:
                domains = list(LearningDomain)
            
            summary = {
                "agent_name": agent_name,
                "overall_performance": {},
                "domain_performance": {},
                "learning_trends": {},
                "recommendations": []
            }
            
            # Aggregate performance across domains
            total_tasks = 0
            avg_accuracy = 0.0
            avg_success_rate = 0.0
            avg_response_time = 0.0
            
            for domain in domains:
                metric_key = f"{agent_name}_{domain.value}"
                if metric_key in self.agent_performance:
                    metric = self.agent_performance[metric_key]
                    
                    summary["domain_performance"][domain.value] = {
                        "accuracy_score": metric.accuracy_score,
                        "success_rate": metric.success_rate,
                        "confidence_score": metric.confidence_score,
                        "response_time": metric.response_time,
                        "task_count": metric.task_count,
                        "learning_velocity": metric.learning_velocity,
                        "last_updated": metric.last_updated.isoformat()
                    }
                    
                    total_tasks += metric.task_count
                    avg_accuracy += metric.accuracy_score * metric.task_count
                    avg_success_rate += metric.success_rate * metric.task_count
                    avg_response_time += metric.response_time * metric.task_count
            
            if total_tasks > 0:
                summary["overall_performance"] = {
                    "average_accuracy": avg_accuracy / total_tasks,
                    "average_success_rate": avg_success_rate / total_tasks,
                    "average_response_time": avg_response_time / total_tasks,
                    "total_tasks_completed": total_tasks
                }
            
            # Generate learning trends
            summary["learning_trends"] = await self._calculate_learning_trends(agent_name)
            
            # Generate recommendations
            summary["recommendations"] = await self._generate_improvement_recommendations(agent_name)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating agent intelligence summary: {str(e)}")
            return {"error": str(e)}
    
    # Private helper methods
    
    def _generate_feedback_id(self, agent_name: str, domain: LearningDomain, context: Dict[str, Any]) -> str:
        """Generate unique feedback ID"""
        content = f"{agent_name}_{domain.value}_{datetime.now().isoformat()}_{str(context)}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _calculate_confidence_delta(
        self,
        feedback_type: str,
        original_prediction: Any,
        corrected_value: Any
    ) -> float:
        """Calculate confidence change based on feedback"""
        if feedback_type == "confirmation":
            return 0.1  # Positive reinforcement
        elif feedback_type == "correction":
            return -0.2  # Negative feedback
        elif feedback_type == "clarification":
            return 0.05  # Slight improvement
        else:
            return 0.0
    
    async def _extract_patterns_from_feedback(
        self,
        feedback: UserFeedback,
        client_account_id: Optional[int] = None
    ) -> None:
        """Extract and store learning patterns from user feedback"""
        try:
            if feedback.feedback_type == "correction":
                # Create new pattern from correction
                pattern_id = self._generate_pattern_id(feedback)
                
                organizational_context = None
                if client_account_id:
                    organizational_context = f"client_{client_account_id}"
                
                pattern = LearningPattern(
                    pattern_id=pattern_id,
                    domain=feedback.domain,
                    pattern_type=self._determine_pattern_type(feedback),
                    confidence=0.6,  # Initial confidence for new pattern
                    evidence_count=1,
                    pattern_data={
                        "original": feedback.original_prediction,
                        "corrected": feedback.corrected_value,
                        "context": feedback.context,
                        "reasoning": f"User correction from {feedback.agent_name}"
                    },
                    created_at=datetime.now(),
                    last_reinforced=datetime.now(),
                    success_rate=0.0,
                    organizational_context=organizational_context
                )
                
                self.learning_patterns[pattern_id] = pattern
                
            elif feedback.feedback_type == "confirmation":
                # Reinforce existing patterns
                await self._reinforce_patterns(feedback)
        
        except Exception as e:
            logger.error(f"Error extracting patterns from feedback: {str(e)}")
    
    def _generate_pattern_id(self, feedback: UserFeedback) -> str:
        """Generate unique pattern ID"""
        content = f"{feedback.domain.value}_{feedback.original_prediction}_{feedback.corrected_value}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _determine_pattern_type(self, feedback: UserFeedback) -> str:
        """Determine pattern type based on feedback domain"""
        type_mapping = {
            LearningDomain.FIELD_MAPPING: "field_mapping",
            LearningDomain.ASSET_CLASSIFICATION: "classification",
            LearningDomain.DATA_QUALITY: "quality_assessment",
            LearningDomain.APPLICATION_DISCOVERY: "application_grouping",
            LearningDomain.DEPENDENCY_ANALYSIS: "dependency_mapping",
            LearningDomain.TECH_DEBT_ASSESSMENT: "risk_scoring",
            LearningDomain.USER_PREFERENCES: "preference_setting"
        }
        return type_mapping.get(feedback.domain, "general")
    
    async def _reinforce_patterns(self, feedback: UserFeedback) -> None:
        """Reinforce existing patterns with positive feedback"""
        try:
            for pattern_id, pattern in self.learning_patterns.items():
                if (pattern.domain == feedback.domain and 
                    self._pattern_matches_feedback(pattern, feedback)):
                    
                    pattern.evidence_count += 1
                    pattern.confidence = min(0.95, pattern.confidence + 0.05)
                    pattern.last_reinforced = datetime.now()
                    
                    logger.info(f"Reinforced pattern {pattern_id} with new evidence")
        
        except Exception as e:
            logger.error(f"Error reinforcing patterns: {str(e)}")
    
    def _pattern_matches_feedback(self, pattern: LearningPattern, feedback: UserFeedback) -> bool:
        """Check if pattern matches the feedback context"""
        # Simple matching logic - can be enhanced with more sophisticated comparison
        pattern_data = pattern.pattern_data
        return (str(pattern_data.get("corrected")) == str(feedback.original_prediction))
    
    def _calculate_field_match_confidence(
        self,
        column_name: str,
        pattern_data: Dict[str, Any]
    ) -> float:
        """Calculate confidence of field mapping match"""
        # Simple string similarity for now - can be enhanced with ML
        pattern_source = pattern_data.get("original", "")
        if isinstance(pattern_source, str):
            similarity = len(set(column_name.lower().split()) & 
                            set(pattern_source.lower().split())) / max(1, len(set(column_name.lower().split())))
            return similarity
        return 0.0
    
    async def _update_agent_performance(self, feedback: UserFeedback) -> None:
        """Update agent performance based on feedback"""
        try:
            metric_key = f"{feedback.agent_name}_{feedback.domain.value}"
            
            if metric_key in self.agent_performance:
                metric = self.agent_performance[metric_key]
                
                # Adjust accuracy based on feedback
                if feedback.feedback_type == "correction":
                    # Decrease accuracy slightly
                    metric.accuracy_score = max(0.0, metric.accuracy_score - 0.05)
                elif feedback.feedback_type == "confirmation":
                    # Increase accuracy slightly
                    metric.accuracy_score = min(1.0, metric.accuracy_score + 0.02)
                
                metric.last_updated = datetime.now()
        
        except Exception as e:
            logger.error(f"Error updating agent performance from feedback: {str(e)}")
    
    async def _calculate_learning_trends(self, agent_name: str) -> Dict[str, Any]:
        """Calculate learning trends for an agent"""
        try:
            recent_feedback = [f for f in self.user_feedback_history 
                             if f.agent_name == agent_name
                             and f.timestamp > datetime.now() - timedelta(days=7)]
            
            if not recent_feedback:
                return {"trend": "stable", "improvement_rate": 0.0}
            
            # Calculate improvement rate
            positive_feedback = sum(1 for f in recent_feedback if f.confidence_delta > 0)
            improvement_rate = positive_feedback / len(recent_feedback)
            
            trend = "improving" if improvement_rate > 0.6 else "stable" if improvement_rate > 0.3 else "declining"
            
            return {
                "trend": trend,
                "improvement_rate": improvement_rate,
                "feedback_count": len(recent_feedback),
                "avg_confidence_delta": statistics.mean([f.confidence_delta for f in recent_feedback])
            }
        
        except Exception as e:
            logger.error(f"Error calculating learning trends: {str(e)}")
            return {"trend": "unknown", "improvement_rate": 0.0}
    
    async def _generate_improvement_recommendations(self, agent_name: str) -> List[str]:
        """Generate improvement recommendations for an agent"""
        try:
            recommendations = []
            
            # Analyze performance across domains
            for domain in LearningDomain:
                metric_key = f"{agent_name}_{domain.value}"
                if metric_key in self.agent_performance:
                    metric = self.agent_performance[metric_key]
                    
                    if metric.success_rate < 0.7:
                        recommendations.append(f"Improve accuracy in {domain.value} - current success rate: {metric.success_rate:.2%}")
                    
                    if metric.response_time > 10.0:
                        recommendations.append(f"Optimize response time in {domain.value} - currently averaging {metric.response_time:.1f}s")
                    
                    if metric.learning_velocity < 0.3:
                        recommendations.append(f"Increase learning velocity in {domain.value} - consider more training data")
            
            return recommendations[:5]  # Limit to top 5 recommendations
        
        except Exception as e:
            logger.error(f"Error generating improvement recommendations: {str(e)}")
            return []

# Global instance for platform-wide learning
learning_system = AgentLearningSystem() 