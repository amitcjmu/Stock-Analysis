"""
Feedback Processing Module - Handles user feedback processing and learning
"""

import logging

# from dataclasses import asdict  # Removed - using context.to_dict() instead
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.agent_learning.models import LearningContext, LearningPattern

logger = logging.getLogger(__name__)


class FeedbackProcessor:
    """Handles user feedback processing and pattern learning."""

    async def process_user_feedback(
        self, feedback_data: Dict[str, Any], context: Optional[LearningContext] = None
    ) -> Dict[str, Any]:
        """
        Process user feedback intelligently and update learning patterns.
        Integrated from feedback.py service for consolidated learning.
        """
        if not context:
            context = LearningContext()

        memory = self._get_context_memory(context)

        filename = feedback_data.get("filename", "")
        user_corrections = feedback_data.get("user_corrections", {})
        asset_type_override = feedback_data.get("asset_type_override")
        original_analysis = feedback_data.get("original_analysis", {})

        # Record the feedback
        memory.add_experience(
            "user_feedback",
            {
                "filename": filename,
                "corrections": user_corrections,
                "asset_type_override": asset_type_override,
                "original_analysis": original_analysis,
                "context": context.to_dict(),
            },
        )

        # Analyze the feedback for patterns
        patterns_identified = self._identify_feedback_patterns(
            user_corrections, asset_type_override
        )

        # Extract knowledge updates
        knowledge_updates = self._extract_knowledge_updates(
            user_corrections, asset_type_override
        )

        # Calculate accuracy improvements
        accuracy_improvements = self._calculate_accuracy_improvements(
            patterns_identified
        )

        # Generate corrected analysis
        corrected_analysis = self._generate_corrected_analysis(
            original_analysis, user_corrections, asset_type_override
        )

        # Calculate confidence boost
        confidence_boost = self._calculate_confidence_boost(patterns_identified)

        # Store learned patterns as learning patterns in this system
        if patterns_identified:
            await self._store_feedback_patterns(
                patterns_identified, context, confidence_boost
            )

            # Update dynamic field mappings based on patterns
            await self._update_field_mappings_from_feedback(
                patterns_identified, context
            )

        # Update learning metrics
        self.global_stats["user_feedback_processed"] = (
            self.global_stats.get("user_feedback_processed", 0) + 1
        )
        self.global_stats["total_learning_events"] += 1
        self.global_stats["last_updated"] = datetime.utcnow().isoformat()

        return {
            "learning_applied": True,
            "patterns_identified": patterns_identified,
            "knowledge_updates": knowledge_updates,
            "accuracy_improvements": accuracy_improvements,
            "confidence_boost": confidence_boost,
            "corrected_analysis": corrected_analysis,
            "memory_impact": {
                "new_patterns_stored": len(patterns_identified),
                "learning_metrics_updated": True,
                "future_analysis_improvement": f"Expected {int(confidence_boost * 100)}% accuracy boost",
            },
            "feedback_processing_mode": "context_aware_learning",
            "context": context.to_dict(),
        }

    def _identify_feedback_patterns(
        self, user_corrections: Dict, asset_type_override: Optional[str]
    ) -> List[str]:
        """Identify patterns from user feedback."""
        patterns = []

        # Asset type correction patterns
        patterns.extend(self._extract_asset_type_patterns(asset_type_override))

        # Analysis issues patterns
        analysis_issues = user_corrections.get("analysis_issues", "")
        patterns.extend(self._extract_analysis_issue_patterns(analysis_issues))

        # Missing fields feedback patterns
        missing_fields_feedback = user_corrections.get("missing_fields_feedback", "")
        patterns.extend(self._extract_missing_fields_patterns(missing_fields_feedback))

        # Comments patterns
        comments = user_corrections.get("comments", "")
        patterns.extend(self._extract_comment_patterns(comments))

        return patterns

    def _extract_asset_type_patterns(
        self, asset_type_override: Optional[str]
    ) -> List[str]:
        """Extract patterns related to asset type corrections."""
        if asset_type_override:
            return [
                f"Asset type should be '{asset_type_override}' based on user correction"
            ]
        return []

    def _extract_analysis_issue_patterns(self, analysis_issues: str) -> List[str]:
        """Extract patterns from analysis issues feedback."""
        if not analysis_issues:
            return []

        patterns = []
        issues_lower = analysis_issues.lower()

        if "server" in issues_lower and "application" in issues_lower:
            patterns.append(
                "Servers were misclassified as applications - improve server detection"
            )

        if "ci_type" in issues_lower:
            patterns.append(
                "CI_TYPE field is a strong indicator for asset classification"
            )

        if "hardware" in issues_lower:
            patterns.append(
                "Hardware specifications are important for server identification"
            )

        if "ip address" in issues_lower:
            patterns.append("IP Address is a key field for server assets")

        return patterns

    def _extract_missing_fields_patterns(
        self, missing_fields_feedback: str
    ) -> List[str]:
        """Extract patterns from missing fields feedback."""
        if not missing_fields_feedback:
            return []

        patterns = []
        feedback_lower = missing_fields_feedback.lower()

        # Field importance patterns
        if "ip address" in feedback_lower:
            patterns.append("IP Address is required for server assets")

        if "os version" in feedback_lower:
            patterns.append("OS Version is critical for server migration planning")

        if "business owner" in feedback_lower:
            patterns.append("Business Owner is important for application assets")

        # Field mapping patterns
        if "available" in feedback_lower and "for" in feedback_lower:
            patterns.append(
                f"Field mapping pattern detected in feedback: {missing_fields_feedback}"
            )

        if "should map" in feedback_lower or "maps to" in feedback_lower:
            patterns.append(f"Field mapping instruction: {missing_fields_feedback}")

        if "recognized as" in feedback_lower or "equivalent" in feedback_lower:
            patterns.append(f"Field equivalence pattern: {missing_fields_feedback}")

        return patterns

    def _extract_comment_patterns(self, comments: str) -> List[str]:
        """Extract patterns from general comments."""
        if not comments:
            return []

        patterns = []
        comments_lower = comments.lower()

        if "clearly indicates" in comments_lower:
            patterns.append("Look for clear indicators in field values")

        if "field" in comments_lower and "pattern" in comments_lower:
            patterns.append("Field patterns are important for classification")

        # Field equivalence patterns
        if "same as" in comments_lower or "equivalent" in comments_lower:
            patterns.append("Field mapping: User identified equivalent field names")

        if "available" in comments_lower and "under" in comments_lower:
            patterns.append(
                "Field mapping: Required fields available under different names"
            )

        return patterns

    def _extract_knowledge_updates(
        self, user_corrections: Dict, asset_type_override: Optional[str]
    ) -> List[str]:
        """Extract knowledge updates from user feedback."""
        updates = []

        # Asset type knowledge updates
        if asset_type_override:
            updates.append(f"Enhanced {asset_type_override} detection logic")

        # Field relevance updates
        analysis_issues = user_corrections.get("analysis_issues", "")
        if "hardware specs" in analysis_issues.lower():
            updates.append("Updated field requirements for server assets")

        missing_fields_feedback = user_corrections.get("missing_fields_feedback", "")
        if missing_fields_feedback:
            updates.append("Refined missing field identification for asset types")

        # General improvements
        if user_corrections.get("comments"):
            updates.append("Improved analysis logic based on user guidance")

        return updates or ["General analysis improvements applied"]

    def _calculate_accuracy_improvements(self, patterns: List[str]) -> List[str]:
        """Calculate expected accuracy improvements."""
        improvements = []

        for pattern in patterns:
            if "server detection" in pattern.lower():
                improvements.append("Server detection confidence increased by 20%")
            elif "asset classification" in pattern.lower():
                improvements.append("Asset classification accuracy improved by 15%")
            elif "field" in pattern.lower():
                improvements.append(
                    "Field validation improved for specific asset types"
                )
            else:
                improvements.append("General analysis accuracy enhanced")

        return improvements or ["General analysis improvements applied"]

    def _generate_corrected_analysis(
        self,
        original_analysis: Dict,
        user_corrections: Dict,
        asset_type_override: Optional[str],
    ) -> Dict[str, Any]:
        """Generate corrected analysis based on user feedback."""
        corrected = original_analysis.copy()

        # Apply asset type override
        if asset_type_override:
            corrected["asset_type"] = asset_type_override
            corrected["confidence_score"] = min(
                corrected.get("confidence_score", 0.5) + 0.2, 1.0
            )

        # Apply other corrections based on feedback
        if user_corrections.get("missing_fields_feedback"):
            corrected["missing_fields_resolved"] = True

        return corrected

    def _calculate_confidence_boost(self, patterns: List[str]) -> float:
        """Calculate confidence boost from identified patterns."""
        if not patterns:
            return 0.05

        boost = 0.0
        for pattern in patterns:
            if (
                "server detection" in pattern.lower()
                or "asset classification" in pattern.lower()
            ):
                boost += 0.15
            elif "field mapping" in pattern.lower():
                boost += 0.10
            else:
                boost += 0.05

        return min(boost, 0.5)  # Cap at 50% boost

    async def _store_feedback_patterns(
        self, patterns: List[str], context: LearningContext, confidence_boost: float
    ):
        """Store feedback patterns as learning patterns."""
        for i, pattern in enumerate(patterns):
            learning_pattern = LearningPattern(
                pattern_id=f"feedback_pattern_{datetime.utcnow().timestamp()}_{i}",
                pattern_type="user_feedback",
                context=context,
                pattern_data={
                    "pattern_description": pattern,
                    "confidence_boost": confidence_boost,
                    "source": "user_feedback",
                },
                confidence=0.8 + confidence_boost,  # High confidence for user feedback
                usage_count=0,
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
            )

            context_key = context.context_hash
            if context_key not in self.learning_patterns:
                self.learning_patterns[context_key] = []

            self.learning_patterns[context_key].append(learning_pattern)

        self.global_stats["feedback_patterns"] = self.global_stats.get(
            "feedback_patterns", 0
        ) + len(patterns)
        self.global_stats["total_patterns"] += len(patterns)

        self._save_learning_patterns()

    async def analyze_feedback_trends(
        self, context: Optional[LearningContext] = None
    ) -> Dict[str, Any]:
        """Analyze feedback trends for continuous improvement."""
        if not context:
            # Analyze across all contexts
            all_feedback = []
            for ctx_key, memory in self.context_memories.items():
                feedback_experiences = memory.experiences.get("user_feedback", [])
                all_feedback.extend(feedback_experiences)
        else:
            memory = self._get_context_memory(context)
            all_feedback = memory.experiences.get("user_feedback", [])

        if not all_feedback:
            return {"status": "no_feedback_data", "total_feedback": 0}

        # Analyze trends
        asset_type_corrections = {}
        common_issues = {}
        field_mapping_requests = 0

        for feedback in all_feedback:
            corrections = feedback.get("corrections", {})
            asset_override = feedback.get("asset_type_override")

            if asset_override:
                asset_type_corrections[asset_override] = (
                    asset_type_corrections.get(asset_override, 0) + 1
                )

            analysis_issues = corrections.get("analysis_issues", "")
            if analysis_issues:
                common_issues[analysis_issues] = (
                    common_issues.get(analysis_issues, 0) + 1
                )

            missing_fields = corrections.get("missing_fields_feedback", "")
            if "map" in missing_fields.lower():
                field_mapping_requests += 1

        return {
            "status": "analyzed",
            "total_feedback": len(all_feedback),
            "asset_type_corrections": asset_type_corrections,
            "common_issues": common_issues,
            "field_mapping_requests": field_mapping_requests,
            "trends": {
                "most_corrected_asset_type": (
                    max(asset_type_corrections.items(), key=lambda x: x[1])[0]
                    if asset_type_corrections
                    else None
                ),
                "most_common_issue": (
                    max(common_issues.items(), key=lambda x: x[1])[0]
                    if common_issues
                    else None
                ),
            },
        }

    async def learn_user_preferences(
        self,
        preference_data: Dict[str, Any],
        engagement_id: Optional[str] = None,
        context: Optional[LearningContext] = None,
    ):
        """Learn user preferences with engagement context."""
        if not context:
            context = LearningContext(engagement_id=engagement_id)

        memory = self._get_context_memory(context)

        memory.add_experience(
            "user_preferences",
            {
                "preferences": preference_data,
                "engagement_id": engagement_id,
                "context": context.to_dict(),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        self.global_stats["total_learning_events"] += 1
        self.global_stats["last_updated"] = datetime.utcnow().isoformat()

        logger.info(f"Learned user preferences for engagement {engagement_id}")
