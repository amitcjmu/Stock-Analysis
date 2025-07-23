"""
Performance Learning Module - Handles performance-based learning and optimization
"""

import logging
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.agent_learning.models import (LearningContext,
                                                PerformanceLearningPattern)

# Performance monitoring integration
try:
    from app.services.monitoring.performance_monitor import performance_monitor
    from app.services.performance.response_optimizer import response_optimizer

    PERFORMANCE_MONITORING_AVAILABLE = True
except ImportError:
    PERFORMANCE_MONITORING_AVAILABLE = False

logger = logging.getLogger(__name__)


class PerformanceLearning:
    """Handles performance-based learning and optimization patterns."""

    async def learn_from_performance_metrics(
        self,
        operation_type: str,
        performance_metrics: Dict[str, float],
        optimization_applied: List[str],
        context: Optional[LearningContext] = None,
    ) -> Dict[str, Any]:
        """Learn optimization patterns from performance metrics."""
        if not PERFORMANCE_MONITORING_AVAILABLE:
            logger.warning("Performance monitoring not available for learning")
            return {
                "learning_applied": False,
                "reason": "performance_monitoring_unavailable",
            }

        if not context:
            context = LearningContext()

        # Calculate improvement factor
        baseline_duration = performance_metrics.get("baseline_duration", 10.0)
        current_duration = performance_metrics.get(
            "current_duration", baseline_duration
        )
        improvement_factor = (
            baseline_duration / current_duration if current_duration > 0 else 1.0
        )

        # Create performance learning pattern
        pattern = PerformanceLearningPattern(
            pattern_id=f"perf_{operation_type}_{datetime.utcnow().timestamp()}",
            operation_type=operation_type,
            performance_metrics=performance_metrics,
            optimization_applied=optimization_applied,
            improvement_factor=improvement_factor,
            context_data=asdict(context),
            created_at=datetime.utcnow(),
        )

        # Store pattern by context
        context_key = context.context_hash
        if context_key not in self.performance_patterns:
            self.performance_patterns[context_key] = []

        self.performance_patterns[context_key].append(pattern)

        # Store in memory
        memory = self._get_context_memory(context)
        memory.add_experience(
            "performance_learning",
            {
                "operation_type": operation_type,
                "improvement_factor": improvement_factor,
                "optimizations": optimization_applied,
                "metrics": performance_metrics,
                "context": asdict(context),
            },
        )

        # Update global stats
        self.global_stats["performance_patterns"] = (
            self.global_stats.get("performance_patterns", 0) + 1
        )
        self.global_stats["total_learning_events"] += 1
        self.global_stats["last_updated"] = datetime.utcnow().isoformat()

        logger.info(
            f"Learned performance pattern for {operation_type} with {improvement_factor:.2f}x improvement"
        )

        return {
            "learning_applied": True,
            "pattern_id": pattern.pattern_id,
            "improvement_factor": improvement_factor,
            "optimizations_learned": optimization_applied,
            "performance_impact": f"{((improvement_factor - 1) * 100):.1f}% improvement",
        }

    async def suggest_performance_optimizations(
        self,
        operation_type: str,
        current_metrics: Dict[str, float],
        context: Optional[LearningContext] = None,
    ) -> Dict[str, Any]:
        """Suggest optimizations based on learned performance patterns."""
        if not context:
            context = LearningContext()

        context_key = context.context_hash
        patterns = self.performance_patterns.get(context_key, [])

        # Find relevant patterns for this operation type
        relevant_patterns = [p for p in patterns if p.operation_type == operation_type]

        if not relevant_patterns:
            # Try global patterns if no context-specific patterns found
            for ctx_patterns in self.performance_patterns.values():
                relevant_patterns.extend(
                    [p for p in ctx_patterns if p.operation_type == operation_type]
                )

        if not relevant_patterns:
            return {
                "suggestions": [],
                "confidence": 0.0,
                "reason": "No performance patterns learned for this operation type",
            }

        # Sort patterns by improvement factor and success rate
        relevant_patterns.sort(
            key=lambda p: p.improvement_factor * p.success_rate, reverse=True
        )

        suggestions = []
        for pattern in relevant_patterns[:3]:  # Top 3 patterns
            # Calculate confidence based on pattern success and usage
            confidence = min(
                0.9, pattern.success_rate * (1 + pattern.usage_count * 0.1)
            )

            suggestion = {
                "optimization_techniques": pattern.optimization_applied,
                "expected_improvement": f"{((pattern.improvement_factor - 1) * 100):.1f}%",
                "confidence": confidence,
                "pattern_usage_count": pattern.usage_count,
                "pattern_success_rate": pattern.success_rate,
            }
            suggestions.append(suggestion)

        return {
            "suggestions": suggestions,
            "operation_type": operation_type,
            "patterns_analyzed": len(relevant_patterns),
            "confidence": (
                sum(s["confidence"] for s in suggestions) / len(suggestions)
                if suggestions
                else 0.0
            ),
        }

    def get_performance_learning_statistics(self) -> Dict[str, Any]:
        """Get performance learning statistics."""
        total_patterns = sum(
            len(patterns) for patterns in self.performance_patterns.values()
        )

        if total_patterns == 0:
            return {
                "total_performance_patterns": 0,
                "contexts_with_performance_data": 0,
                "message": "No performance learning data available",
            }

        # Calculate statistics
        all_patterns = []
        for patterns in self.performance_patterns.values():
            all_patterns.extend(patterns)

        avg_improvement = sum(p.improvement_factor for p in all_patterns) / len(
            all_patterns
        )
        avg_success_rate = sum(p.success_rate for p in all_patterns) / len(all_patterns)

        return {
            "total_performance_patterns": total_patterns,
            "contexts_with_performance_data": len(self.performance_patterns),
            "average_improvement_factor": avg_improvement,
            "average_success_rate": avg_success_rate,
            "performance_learning_grade": (
                "excellent"
                if avg_improvement > 2.0 and avg_success_rate > 0.8
                else "good" if avg_improvement > 1.5 else "needs_improvement"
            ),
        }

    async def track_agent_performance(
        self,
        agent_id: str,
        performance_data: Dict[str, Any],
        context: Optional[LearningContext] = None,
    ):
        """Track agent performance with context isolation."""
        if not context:
            context = LearningContext()

        memory = self._get_context_memory(context)

        memory.add_experience(
            "agent_performance",
            {
                "agent_id": agent_id,
                "performance_data": performance_data,
                "context": asdict(context),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        self.global_stats["agents_tracked"].add(agent_id)
        self.global_stats["total_learning_events"] += 1
        self.global_stats["last_updated"] = datetime.utcnow().isoformat()

        logger.info(
            f"Tracked performance for agent {agent_id} in context {context.context_hash}"
        )

    async def get_agent_accuracy_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get agent accuracy metrics across all contexts."""
        all_metrics = []

        for context_key, memory in self.context_memories.items():
            experiences = memory.experiences.get("agent_performance", [])
            agent_experiences = [
                exp for exp in experiences if exp.get("agent_id") == agent_id
            ]

            if agent_experiences:
                context_metrics = {
                    "context": context_key,
                    "total_tasks": len(agent_experiences),
                    "avg_accuracy": sum(
                        exp.get("performance_data", {}).get("accuracy", 0)
                        for exp in agent_experiences
                    )
                    / len(agent_experiences),
                    "latest_performance": agent_experiences[-1].get(
                        "performance_data", {}
                    ),
                }
                all_metrics.append(context_metrics)

        return {
            "agent_id": agent_id,
            "context_metrics": all_metrics,
            "overall_accuracy": (
                sum(m["avg_accuracy"] for m in all_metrics) / len(all_metrics)
                if all_metrics
                else 0
            ),
            "total_contexts": len(all_metrics),
        }
