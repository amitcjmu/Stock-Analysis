"""
Learning service for capturing and improving agent performance.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

from ..models.attribute_schemas import AgentFeedback, LearningPatternUpdate

logger = logging.getLogger(__name__)


class LearningService:
    """Service for machine learning and feedback integration."""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self._feedback_store = []  # Simple in-memory store - would use database in production
        self._learning_patterns = {}
    
    async def record_feedback(self, feedback: AgentFeedback) -> Dict[str, Any]:
        """Record user feedback on agent analysis."""
        
        try:
            # Store feedback
            self._feedback_store.append(feedback)
            
            # Update learning patterns based on feedback
            await self._update_learning_patterns(feedback)
            
            logger.info(f"Recorded feedback for analysis {feedback.analysis_id}")
            
            return {
                "success": True,
                "feedback_id": f"fb_{len(self._feedback_store)}",
                "message": "Feedback recorded successfully",
                "learning_updated": True
            }
            
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to record feedback"
            }
    
    async def get_learning_insights(self) -> Dict[str, Any]:
        """Get learning insights from collected feedback."""
        
        if not self._feedback_store:
            return {
                "total_feedback": 0,
                "accuracy_metrics": {},
                "improvement_suggestions": []
            }
        
        # Calculate feedback statistics
        total_feedback = len(self._feedback_store)
        correct_count = len([f for f in self._feedback_store if f.feedback_type == "correct"])
        incorrect_count = len([f for f in self._feedback_store if f.feedback_type == "incorrect"])
        
        accuracy = correct_count / total_feedback if total_feedback > 0 else 0.0
        
        # Identify common patterns
        attribute_feedback = {}
        for feedback in self._feedback_store:
            attr_name = feedback.attribute_name
            if attr_name not in attribute_feedback:
                attribute_feedback[attr_name] = {"correct": 0, "incorrect": 0}
            
            if feedback.feedback_type == "correct":
                attribute_feedback[attr_name]["correct"] += 1
            elif feedback.feedback_type == "incorrect":
                attribute_feedback[attr_name]["incorrect"] += 1
        
        # Generate improvement suggestions
        improvement_suggestions = []
        for attr_name, stats in attribute_feedback.items():
            total = stats["correct"] + stats["incorrect"]
            if total >= 3 and stats["incorrect"] / total > 0.5:
                improvement_suggestions.append({
                    "attribute": attr_name,
                    "issue": "Low accuracy",
                    "suggestion": f"Review mapping logic for {attr_name}",
                    "accuracy": stats["correct"] / total
                })
        
        return {
            "total_feedback": total_feedback,
            "accuracy_metrics": {
                "overall_accuracy": accuracy,
                "correct_predictions": correct_count,
                "incorrect_predictions": incorrect_count,
                "attribute_breakdown": attribute_feedback
            },
            "improvement_suggestions": improvement_suggestions,
            "learning_patterns": len(self._learning_patterns)
        }
    
    async def _update_learning_patterns(self, feedback: AgentFeedback):
        """Update learning patterns based on feedback."""
        
        pattern_key = f"{feedback.attribute_name}_{feedback.feedback_type}"
        
        if pattern_key not in self._learning_patterns:
            self._learning_patterns[pattern_key] = {
                "attribute_name": feedback.attribute_name,
                "feedback_type": feedback.feedback_type,
                "count": 0,
                "confidence_adjustments": [],
                "corrections": []
            }
        
        pattern = self._learning_patterns[pattern_key]
        pattern["count"] += 1
        
        if feedback.importance_adjustment is not None:
            pattern["confidence_adjustments"].append(feedback.importance_adjustment)
        
        if feedback.user_correction:
            pattern["corrections"].append(feedback.user_correction)
        
        logger.info(f"Updated learning pattern for {feedback.attribute_name}")
    
    async def get_attribute_recommendations(self, attribute_name: str) -> Dict[str, Any]:
        """Get recommendations for a specific attribute based on learning."""
        
        # Look for patterns related to this attribute
        related_patterns = [
            pattern for key, pattern in self._learning_patterns.items()
            if pattern["attribute_name"] == attribute_name
        ]
        
        if not related_patterns:
            return {
                "attribute_name": attribute_name,
                "recommendations": [],
                "confidence_adjustment": 0.0,
                "learned_corrections": []
            }
        
        # Aggregate recommendations
        confidence_adjustments = []
        corrections = []
        
        for pattern in related_patterns:
            confidence_adjustments.extend(pattern["confidence_adjustments"])
            corrections.extend(pattern["corrections"])
        
        # Calculate average confidence adjustment
        avg_confidence_adjustment = 0.0
        if confidence_adjustments:
            avg_confidence_adjustment = sum(confidence_adjustments) / len(confidence_adjustments)
        
        # Generate recommendations
        recommendations = []
        
        if avg_confidence_adjustment < -0.2:
            recommendations.append("Consider reducing importance score for this attribute")
        elif avg_confidence_adjustment > 0.2:
            recommendations.append("Consider increasing importance score for this attribute")
        
        if corrections:
            unique_corrections = list(set(corrections))
            recommendations.extend([f"User suggested: {correction}" for correction in unique_corrections])
        
        return {
            "attribute_name": attribute_name,
            "recommendations": recommendations,
            "confidence_adjustment": avg_confidence_adjustment,
            "learned_corrections": list(set(corrections)),
            "feedback_count": sum(pattern["count"] for pattern in related_patterns)
        }
    
    async def export_learning_data(self) -> Dict[str, Any]:
        """Export learning data for analysis or backup."""
        
        return {
            "feedback_data": [
                {
                    "analysis_id": f.analysis_id,
                    "attribute_name": f.attribute_name,
                    "feedback_type": f.feedback_type,
                    "user_correction": f.user_correction,
                    "importance_adjustment": f.importance_adjustment,
                    "timestamp": f.timestamp.isoformat() if f.timestamp else None
                }
                for f in self._feedback_store
            ],
            "learning_patterns": self._learning_patterns,
            "export_timestamp": datetime.utcnow().isoformat(),
            "total_records": len(self._feedback_store)
        }
    
    async def import_learning_data(self, learning_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import learning data from backup or external source."""
        
        try:
            # Import feedback data
            feedback_data = learning_data.get("feedback_data", [])
            imported_feedback = 0
            
            for fb_data in feedback_data:
                # Convert back to AgentFeedback object
                feedback = AgentFeedback(
                    analysis_id=fb_data["analysis_id"],
                    attribute_name=fb_data["attribute_name"],
                    feedback_type=fb_data["feedback_type"],
                    user_correction=fb_data.get("user_correction"),
                    importance_adjustment=fb_data.get("importance_adjustment"),
                    timestamp=datetime.fromisoformat(fb_data["timestamp"]) if fb_data.get("timestamp") else datetime.utcnow()
                )
                self._feedback_store.append(feedback)
                imported_feedback += 1
            
            # Import learning patterns
            imported_patterns = learning_data.get("learning_patterns", {})
            self._learning_patterns.update(imported_patterns)
            
            logger.info(f"Imported {imported_feedback} feedback records and {len(imported_patterns)} patterns")
            
            return {
                "success": True,
                "imported_feedback": imported_feedback,
                "imported_patterns": len(imported_patterns),
                "message": "Learning data imported successfully"
            }
            
        except Exception as e:
            logger.error(f"Error importing learning data: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to import learning data"
            }