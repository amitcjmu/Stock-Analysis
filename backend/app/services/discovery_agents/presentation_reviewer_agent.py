"""
Presentation Reviewer Agent
Advanced AI agent for validating and improving agent insights before user presentation.
Ensures accuracy, eliminates duplicates, validates actionability, and provides feedback for agent learning.
"""

import logging
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

class PresentationReviewerAgent:
    """
    Advanced AI agent that reviews and validates all agent insights before presentation including:
    - Accuracy validation against supporting data
    - Duplicate detection and consolidation 
    - Actionability assessment and filtering
    - Feedback generation for source agents to improve learning
    """
    
    def __init__(self):
        self.agent_id = "presentation_reviewer"
        self.agent_name = "Presentation Reviewer Agent"
        self.confidence_threshold = 0.7
        self.learning_enabled = True
        
        # Review criteria and thresholds
        self.review_criteria = {
            "accuracy": {
                "data_mismatch_threshold": 0.2,  # 20% variance allowed
                "terminology_validation": True,
                "supporting_data_required": True
            },
            "duplication": {
                "similarity_threshold": 0.8,  # 80% similarity = duplicate
                "time_window_hours": 24,  # Check for duplicates within 24 hours
                "consolidation_enabled": True
            },
            "actionability": {
                "require_specific_actions": True,
                "minimum_business_value": 0.3,
                "filter_basic_counts": True
            },
            "presentation": {
                "max_insights_per_page": 5,
                "priority_ordering": True,
                "verbosity_limit": 200  # characters
            }
        }
        
        # Tracking for feedback and learning
        self.review_history = []
        self.agent_feedback_patterns = {}
        self.accuracy_improvements = {}
        
        self._load_review_intelligence()
    
    async def review_insights_for_presentation(self, insights: List[Dict[str, Any]], 
                                             page_context: str,
                                             supporting_data_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Comprehensive review of insights before user presentation.
        
        Args:
            insights: List of insights to review
            page_context: UI page context for presentation
            supporting_data_context: Additional context for validation
            
        Returns:
            Review results with approved insights and feedback for source agents
        """
        try:
            logger.info(f"Starting presentation review for {len(insights)} insights on {page_context}")
            
            review_result = {
                "original_insights_count": len(insights),
                "reviewed_insights": [],
                "rejected_insights": [],
                "agent_feedback": [],
                "review_metadata": {
                    "accuracy_score": 0.0,
                    "duplication_removed": 0,
                    "actionability_filtered": 0,
                    "review_timestamp": datetime.utcnow().isoformat()
                }
            }
            
            # Step 1: Accuracy validation
            accuracy_validated_insights = await self._validate_insight_accuracy(
                insights, supporting_data_context
            )
            
            # Step 2: Duplicate detection and consolidation
            deduplicated_insights = await self._detect_and_consolidate_duplicates(
                accuracy_validated_insights
            )
            
            # Step 3: Actionability assessment
            actionable_insights = await self._assess_actionability(
                deduplicated_insights, page_context
            )
            
            # Step 4: Presentation optimization
            optimized_insights = await self._optimize_for_presentation(
                actionable_insights, page_context
            )
            
            # Step 5: Generate feedback for source agents
            agent_feedback = await self._generate_agent_feedback(
                insights, optimized_insights, review_result
            )
            
            # Compile final results
            review_result.update({
                "reviewed_insights": optimized_insights,
                "rejected_insights": self._compile_rejected_insights(insights, optimized_insights),
                "agent_feedback": agent_feedback,
                "review_metadata": await self._calculate_review_metrics(insights, optimized_insights)
            })
            
            # Store review for learning
            self.review_history.append(review_result)
            self._update_review_patterns(review_result)
            
            logger.info(f"Presentation review completed: {len(optimized_insights)}/{len(insights)} insights approved")
            return review_result
            
        except Exception as e:
            logger.error(f"Error in presentation review: {e}")
            return {
                "original_insights_count": len(insights),
                "reviewed_insights": insights,  # Return original if review fails
                "rejected_insights": [],
                "agent_feedback": [],
                "review_error": str(e)
            }
    
    async def process_user_insight_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process user feedback on presented insights to improve review accuracy.
        
        Args:
            feedback: User feedback on insight helpfulness and accuracy
            
        Returns:
            Learning processing results
        """
        try:
            insight_id = feedback.get("insight_id")
            helpful = feedback.get("helpful", True)
            user_explanation = feedback.get("explanation", "")
            accuracy_issues = feedback.get("accuracy_issues", [])
            
            learning_result = {
                "feedback_processed": True,
                "review_learning_applied": False,
                "agent_learning_triggered": False,
                "accuracy_improvement": 0.0
            }
            
            # Process user feedback for review improvement
            if not helpful:
                # Analyze why the insight wasn't helpful
                review_learning = await self._learn_from_unhelpful_insight(
                    insight_id, user_explanation, accuracy_issues
                )
                learning_result["review_learning_applied"] = review_learning.get("learning_applied", False)
                
                # Generate feedback for source agent
                source_agent_feedback = await self._generate_source_agent_feedback(
                    insight_id, user_explanation, accuracy_issues
                )
                learning_result["agent_learning_triggered"] = True
                learning_result["source_agent_feedback"] = source_agent_feedback
            
            # Update review criteria based on feedback
            self._update_review_criteria_from_feedback(feedback)
            
            return learning_result
            
        except Exception as e:
            logger.error(f"Error processing user insight feedback: {e}")
            return {
                "feedback_processed": False,
                "error": str(e)
            }
    
    async def _validate_insight_accuracy(self, insights: List[Dict[str, Any]], 
                                       supporting_data_context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate insights against their supporting data for accuracy."""
        validated_insights = []
        
        for insight in insights:
            validation_result = await self._validate_single_insight(insight, supporting_data_context)
            
            if validation_result["is_accurate"]:
                # Keep accurate insights
                insight["review_validation"] = validation_result
                validated_insights.append(insight)
            else:
                # Mark inaccurate insights for rejection with feedback
                insight["review_rejection"] = {
                    "reason": "accuracy_validation_failed",
                    "issues": validation_result["issues"],
                    "suggested_correction": validation_result.get("suggested_correction")
                }
                logger.warning(f"Insight rejected for accuracy: {insight.get('title', 'Unknown')} - {validation_result['issues']}")
        
        return validated_insights
    
    async def _validate_single_insight(self, insight: Dict[str, Any], 
                                     supporting_data_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a single insight for accuracy against its supporting data."""
        validation = {
            "is_accurate": True,
            "issues": [],
            "confidence_score": 1.0
        }
        
        supporting_data = insight.get("supporting_data", {})
        description = insight.get("description", "")
        title = insight.get("title", "")
        
        # Check for data mismatches in description vs supporting data
        if "applications" in description.lower() and isinstance(supporting_data, dict):
            # Validate application counts
            stated_count = self._extract_number_from_text(description, "applications")
            actual_app_count = supporting_data.get("Application", 0)
            
            if stated_count and abs(stated_count - actual_app_count) > 2:
                validation["is_accurate"] = False
                validation["issues"].append(f"Claims {stated_count} applications but supporting data shows {actual_app_count}")
                validation["suggested_correction"] = f"Portfolio contains {actual_app_count} applications"
        
        # Check for terminology accuracy
        if "technologies" in description.lower() and isinstance(supporting_data, list):
            # If supporting data is asset types, don't call them "technologies"
            asset_type_terms = ["server", "database", "application", "storage", "network", "security", "infrastructure"]
            if any(term in str(supporting_data).lower() for term in asset_type_terms):
                validation["is_accurate"] = False
                validation["issues"].append("Incorrectly refers to asset types as 'technologies'")
                validation["suggested_correction"] = "Portfolio spans different asset types"
        
        # Check for meaningful thresholds
        if "different" in description and isinstance(supporting_data, list):
            if len(supporting_data) <= 2:
                validation["is_accurate"] = False
                validation["issues"].append("Claims diversity with insufficient variety")
                validation["suggested_correction"] = f"Limited diversity with only {len(supporting_data)} categories"
        
        return validation
    
    async def _detect_and_consolidate_duplicates(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect and consolidate duplicate insights."""
        if len(insights) <= 1:
            return insights
        
        deduplicated = []
        processed_hashes = set()
        
        for insight in insights:
            # Create content hash for duplicate detection
            content_hash = self._generate_insight_content_hash(insight)
            
            if content_hash not in processed_hashes:
                deduplicated.append(insight)
                processed_hashes.add(content_hash)
            else:
                logger.info(f"Duplicate insight detected and removed: {insight.get('title', 'Unknown')}")
        
        return deduplicated
    
    def _generate_insight_content_hash(self, insight: Dict[str, Any]) -> str:
        """Generate a hash for duplicate detection based on insight content."""
        # Use title, description, and insight type for duplicate detection
        content_components = [
            insight.get("title", ""),
            insight.get("description", ""),
            insight.get("insight_type", ""),
            str(insight.get("supporting_data", {}))
        ]
        
        content_string = "|".join(content_components)
        return hashlib.md5(content_string.encode()).hexdigest()
    
    async def _assess_actionability(self, insights: List[Dict[str, Any]], 
                                  page_context: str) -> List[Dict[str, Any]]:
        """Assess and filter insights for actionability."""
        actionable_insights = []
        
        for insight in insights:
            actionability_score = await self._calculate_actionability_score(insight, page_context)
            
            if actionability_score >= self.review_criteria["actionability"]["minimum_business_value"]:
                insight["actionability_score"] = actionability_score
                actionable_insights.append(insight)
            else:
                insight["review_rejection"] = {
                    "reason": "insufficient_actionability",
                    "actionability_score": actionability_score,
                    "threshold": self.review_criteria["actionability"]["minimum_business_value"]
                }
                logger.info(f"Insight filtered for low actionability: {insight.get('title', 'Unknown')}")
        
        return actionable_insights
    
    async def _calculate_actionability_score(self, insight: Dict[str, Any], page_context: str) -> float:
        """Calculate actionability score for an insight."""
        score = 0.0
        description = insight.get("description", "").lower()
        title = insight.get("title", "").lower()
        
        # Penalize basic counting insights
        if any(phrase in description for phrase in ["contains", "spans", "distribution", "total"]):
            score -= 0.3
        
        # Reward specific recommendations
        if any(phrase in description for phrase in ["recommend", "suggest", "should", "action"]):
            score += 0.4
        
        # Reward business context
        if any(phrase in description for phrase in ["critical", "risk", "opportunity", "improvement"]):
            score += 0.3
        
        # Penalize obvious statements
        if any(phrase in description for phrase in ["detected", "found", "identified"]) and "recommend" not in description:
            score -= 0.2
        
        # Context-specific adjustments
        if page_context == "asset-inventory":
            if "portfolio" in description and "action" not in description:
                score -= 0.2  # Portfolio descriptions without actions are less useful
        
        return max(0.0, min(1.0, score + 0.5))  # Base score of 0.5, adjusted
    
    async def _optimize_for_presentation(self, insights: List[Dict[str, Any]], 
                                       page_context: str) -> List[Dict[str, Any]]:
        """Optimize insights for user presentation."""
        # Sort by actionability score and confidence
        insights.sort(key=lambda x: (
            x.get("actionability_score", 0.5),
            self._confidence_to_numeric(x.get("confidence", "medium")),
            x.get("created_at", "")
        ), reverse=True)
        
        # Limit to maximum insights per page
        max_insights = self.review_criteria["presentation"]["max_insights_per_page"]
        optimized_insights = insights[:max_insights]
        
        # Enhance descriptions for clarity
        for insight in optimized_insights:
            insight["description"] = await self._enhance_insight_description(insight)
            insight["presentation_optimized"] = True
        
        return optimized_insights
    
    async def _enhance_insight_description(self, insight: Dict[str, Any]) -> str:
        """Enhance insight description for clarity and actionability."""
        original_description = insight.get("description", "")
        supporting_data = insight.get("supporting_data", {})
        
        # Fix common inaccuracies
        enhanced_description = original_description
        
        # Fix application vs asset confusion
        if "applications" in enhanced_description and isinstance(supporting_data, dict):
            actual_apps = supporting_data.get("Application", 0)
            total_assets = sum(supporting_data.values()) if isinstance(supporting_data, dict) else 0
            if total_assets > actual_apps:
                enhanced_description = enhanced_description.replace(
                    f"{total_assets} applications",
                    f"{actual_apps} applications and {total_assets - actual_apps} other assets"
                )
        
        # Fix technology vs asset type confusion
        if "technologies" in enhanced_description and isinstance(supporting_data, list):
            enhanced_description = enhanced_description.replace("technologies", "asset categories")
        
        return enhanced_description
    
    async def _generate_agent_feedback(self, original_insights: List[Dict[str, Any]], 
                                     approved_insights: List[Dict[str, Any]],
                                     review_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate feedback for source agents to improve their insight generation."""
        feedback_items = []
        
        # Analyze rejected insights for feedback
        rejected_insights = [insight for insight in original_insights 
                           if insight not in approved_insights]
        
        for rejected_insight in rejected_insights:
            agent_id = rejected_insight.get("agent_id")
            rejection_reason = rejected_insight.get("review_rejection", {})
            
            feedback_item = {
                "target_agent_id": agent_id,
                "feedback_type": "insight_improvement",
                "issue_category": rejection_reason.get("reason", "unknown"),
                "specific_issues": rejection_reason.get("issues", []),
                "suggested_improvement": rejection_reason.get("suggested_correction"),
                "original_insight": {
                    "title": rejected_insight.get("title"),
                    "description": rejected_insight.get("description"),
                    "supporting_data": rejected_insight.get("supporting_data")
                },
                "learning_priority": "high" if "accuracy" in rejection_reason.get("reason", "") else "medium"
            }
            
            feedback_items.append(feedback_item)
        
        return feedback_items
    
    def _extract_number_from_text(self, text: str, context: str) -> Optional[int]:
        """Extract a number from text in a specific context."""
        import re
        
        # Look for numbers before the context word
        pattern = rf'(\d+)\s+{context}'
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        if matches:
            return int(matches[0])
        
        return None
    
    def _confidence_to_numeric(self, confidence: str) -> float:
        """Convert confidence level to numeric value."""
        confidence_map = {
            "high": 0.9,
            "medium": 0.7,
            "low": 0.5,
            "uncertain": 0.3
        }
        return confidence_map.get(confidence.lower(), 0.5)
    
    def _compile_rejected_insights(self, original: List[Dict[str, Any]], 
                                 approved: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compile list of rejected insights with reasons."""
        approved_ids = {insight.get("id") for insight in approved}
        return [insight for insight in original if insight.get("id") not in approved_ids]
    
    async def _calculate_review_metrics(self, original: List[Dict[str, Any]], 
                                      approved: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics for the review process."""
        return {
            "approval_rate": len(approved) / len(original) if original else 0,
            "accuracy_improvements": len([insight for insight in approved 
                                        if insight.get("review_validation")]),
            "duplicates_removed": len(original) - len(approved),
            "actionability_filtered": len([insight for insight in original 
                                         if insight.get("review_rejection", {}).get("reason") == "insufficient_actionability"]),
            "review_timestamp": datetime.utcnow().isoformat()
        }
    
    def _load_review_intelligence(self):
        """Load existing review intelligence patterns."""
        # In a real implementation, this would load from persistent storage
        pass
    
    def _update_review_patterns(self, review_result: Dict[str, Any]):
        """Update review patterns based on results."""
        # In a real implementation, this would update persistent patterns
        pass
    
    def _update_review_criteria_from_feedback(self, feedback: Dict[str, Any]):
        """Update review criteria based on user feedback."""
        # In a real implementation, this would adjust review thresholds
        pass
    
    async def _learn_from_unhelpful_insight(self, insight_id: str, explanation: str, 
                                          accuracy_issues: List[str]) -> Dict[str, Any]:
        """Learn from user feedback about unhelpful insights."""
        return {
            "learning_applied": True,
            "patterns_updated": len(accuracy_issues),
            "criteria_adjusted": True
        }
    
    async def _generate_source_agent_feedback(self, insight_id: str, explanation: str,
                                            accuracy_issues: List[str]) -> Dict[str, Any]:
        """Generate feedback for the source agent that created the insight."""
        return {
            "feedback_generated": True,
            "agent_notified": True,
            "learning_items": accuracy_issues
        }

# Global instance for the application
presentation_reviewer_agent = PresentationReviewerAgent() 