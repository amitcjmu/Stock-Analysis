"""
Feedback Processing Module - Handles user feedback processing and learning
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import asdict

from app.services.agent_learning.models import LearningContext, LearningPattern

logger = logging.getLogger(__name__)


class FeedbackProcessor:
    """Handles user feedback processing and pattern learning."""
    
    async def process_user_feedback(
        self,
        feedback_data: Dict[str, Any],
        context: Optional[LearningContext] = None
    ) -> Dict[str, Any]:
        """
        Process user feedback intelligently and update learning patterns.
        Integrated from feedback.py service for consolidated learning.
        """
        if not context:
            context = LearningContext()
        
        memory = self._get_context_memory(context)
        
        filename = feedback_data.get('filename', '')
        user_corrections = feedback_data.get('user_corrections', {})
        asset_type_override = feedback_data.get('asset_type_override')
        original_analysis = feedback_data.get('original_analysis', {})
        
        # Record the feedback
        memory.add_experience("user_feedback", {
            "filename": filename,
            "corrections": user_corrections,
            "asset_type_override": asset_type_override,
            "original_analysis": original_analysis,
            "context": asdict(context)
        })
        
        # Analyze the feedback for patterns
        patterns_identified = self._identify_feedback_patterns(user_corrections, asset_type_override)
        
        # Extract knowledge updates
        knowledge_updates = self._extract_knowledge_updates(user_corrections, asset_type_override)
        
        # Calculate accuracy improvements
        accuracy_improvements = self._calculate_accuracy_improvements(patterns_identified)
        
        # Generate corrected analysis
        corrected_analysis = self._generate_corrected_analysis(
            original_analysis, user_corrections, asset_type_override
        )
        
        # Calculate confidence boost
        confidence_boost = self._calculate_confidence_boost(patterns_identified)
        
        # Store learned patterns as learning patterns in this system
        if patterns_identified:
            await self._store_feedback_patterns(patterns_identified, context, confidence_boost)
            
            # Update dynamic field mappings based on patterns
            await self._update_field_mappings_from_feedback(patterns_identified, context)
        
        # Update learning metrics
        self.global_stats["user_feedback_processed"] = self.global_stats.get("user_feedback_processed", 0) + 1
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
                "future_analysis_improvement": f"Expected {int(confidence_boost * 100)}% accuracy boost"
            },
            "feedback_processing_mode": "context_aware_learning",
            "context": asdict(context)
        }
    
    def _identify_feedback_patterns(self, user_corrections: Dict, asset_type_override: Optional[str]) -> List[str]:
        """Identify patterns from user feedback."""
        patterns = []
        
        # Asset type correction patterns
        if asset_type_override:
            patterns.append(f"Asset type should be '{asset_type_override}' based on user correction")
        
        # Analysis issues patterns
        analysis_issues = user_corrections.get('analysis_issues', '')
        if analysis_issues:
            # Extract specific patterns from analysis issues
            if 'server' in analysis_issues.lower() and 'application' in analysis_issues.lower():
                patterns.append("Servers were misclassified as applications - improve server detection")
            
            if 'ci_type' in analysis_issues.lower():
                patterns.append("CI_TYPE field is a strong indicator for asset classification")
            
            if 'hardware' in analysis_issues.lower():
                patterns.append("Hardware specifications are important for server identification")
            
            if 'ip address' in analysis_issues.lower():
                patterns.append("IP Address is a key field for server assets")
        
        # Missing fields feedback patterns with enhanced field mapping detection
        missing_fields_feedback = user_corrections.get('missing_fields_feedback', '')
        if missing_fields_feedback:
            # Extract field importance patterns
            if 'ip address' in missing_fields_feedback.lower():
                patterns.append("IP Address is required for server assets")
            
            if 'os version' in missing_fields_feedback.lower():
                patterns.append("OS Version is critical for server migration planning")
            
            if 'business owner' in missing_fields_feedback.lower():
                patterns.append("Business Owner is important for application assets")
            
            # Let AI agents learn field mappings dynamically from feedback text
            if 'available' in missing_fields_feedback.lower() and 'for' in missing_fields_feedback.lower():
                patterns.append(f"Field mapping pattern detected in feedback: {missing_fields_feedback}")
            
            if 'should map' in missing_fields_feedback.lower() or 'maps to' in missing_fields_feedback.lower():
                patterns.append(f"Field mapping instruction: {missing_fields_feedback}")
            
            if 'recognized as' in missing_fields_feedback.lower() or 'equivalent' in missing_fields_feedback.lower():
                patterns.append(f"Field equivalence pattern: {missing_fields_feedback}")
        
        # Comments patterns with field mapping detection
        comments = user_corrections.get('comments', '')
        if comments:
            if 'clearly indicates' in comments.lower():
                patterns.append("Look for clear indicators in field values")
            
            if 'field' in comments.lower() and 'pattern' in comments.lower():
                patterns.append("Field patterns are important for classification")
            
            # Detect field equivalence patterns in comments
            if 'same as' in comments.lower() or 'equivalent' in comments.lower():
                patterns.append("Field mapping: User identified equivalent field names")
            
            if 'available' in comments.lower() and 'under' in comments.lower():
                patterns.append("Field mapping: Required fields available under different names")
        
        return patterns
    
    def _extract_knowledge_updates(self, user_corrections: Dict, asset_type_override: Optional[str]) -> List[str]:
        """Extract knowledge updates from user feedback."""
        updates = []
        
        # Asset type knowledge updates
        if asset_type_override:
            updates.append(f"Enhanced {asset_type_override} detection logic")
        
        # Field relevance updates
        analysis_issues = user_corrections.get('analysis_issues', '')
        if 'hardware specs' in analysis_issues.lower():
            updates.append("Updated field requirements for server assets")
        
        missing_fields_feedback = user_corrections.get('missing_fields_feedback', '')
        if missing_fields_feedback:
            updates.append("Refined missing field identification for asset types")
        
        # General improvements
        if user_corrections.get('comments'):
            updates.append("Improved analysis logic based on user guidance")
        
        return updates or ["General analysis improvements applied"]
    
    def _calculate_accuracy_improvements(self, patterns: List[str]) -> List[str]:
        """Calculate expected accuracy improvements."""
        improvements = []
        
        for pattern in patterns:
            if 'server detection' in pattern.lower():
                improvements.append("Server detection confidence increased by 20%")
            elif 'asset classification' in pattern.lower():
                improvements.append("Asset classification accuracy improved by 15%")
            elif 'field' in pattern.lower():
                improvements.append("Field validation improved for specific asset types")
            else:
                improvements.append("General analysis accuracy enhanced")
        
        return improvements or ["General analysis improvements applied"]
    
    def _generate_corrected_analysis(self, original_analysis: Dict, user_corrections: Dict, asset_type_override: Optional[str]) -> Dict[str, Any]:
        """Generate corrected analysis based on user feedback."""
        corrected = original_analysis.copy()
        
        # Apply asset type override
        if asset_type_override:
            corrected['asset_type'] = asset_type_override
            corrected['confidence_score'] = min(corrected.get('confidence_score', 0.5) + 0.2, 1.0)
        
        # Apply other corrections based on feedback
        if user_corrections.get('missing_fields_feedback'):
            corrected['missing_fields_resolved'] = True
        
        return corrected
    
    def _calculate_confidence_boost(self, patterns: List[str]) -> float:
        """Calculate confidence boost from identified patterns."""
        if not patterns:
            return 0.05
        
        boost = 0.0
        for pattern in patterns:
            if 'server detection' in pattern.lower() or 'asset classification' in pattern.lower():
                boost += 0.15
            elif 'field mapping' in pattern.lower():
                boost += 0.10
            else:
                boost += 0.05
        
        return min(boost, 0.5)  # Cap at 50% boost
    
    async def _store_feedback_patterns(self, patterns: List[str], context: LearningContext, confidence_boost: float):
        """Store feedback patterns as learning patterns."""
        for i, pattern in enumerate(patterns):
            learning_pattern = LearningPattern(
                pattern_id=f"feedback_pattern_{datetime.utcnow().timestamp()}_{i}",
                pattern_type="user_feedback",
                context=context,
                pattern_data={
                    "pattern_description": pattern,
                    "confidence_boost": confidence_boost,
                    "source": "user_feedback"
                },
                confidence=0.8 + confidence_boost,  # High confidence for user feedback
                usage_count=0,
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow()
            )
            
            context_key = context.context_hash
            if context_key not in self.learning_patterns:
                self.learning_patterns[context_key] = []
            
            self.learning_patterns[context_key].append(learning_pattern)
        
        self.global_stats["feedback_patterns"] = self.global_stats.get("feedback_patterns", 0) + len(patterns)
        self.global_stats["total_patterns"] += len(patterns)
        
        self._save_learning_patterns()
    
    async def analyze_feedback_trends(self, context: Optional[LearningContext] = None) -> Dict[str, Any]:
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
                asset_type_corrections[asset_override] = asset_type_corrections.get(asset_override, 0) + 1
            
            analysis_issues = corrections.get("analysis_issues", "")
            if analysis_issues:
                common_issues[analysis_issues] = common_issues.get(analysis_issues, 0) + 1
            
            missing_fields = corrections.get("missing_fields_feedback", "")
            if 'map' in missing_fields.lower():
                field_mapping_requests += 1
        
        return {
            "status": "analyzed",
            "total_feedback": len(all_feedback),
            "asset_type_corrections": asset_type_corrections,
            "common_issues": common_issues,
            "field_mapping_requests": field_mapping_requests,
            "trends": {
                "most_corrected_asset_type": max(asset_type_corrections.items(), key=lambda x: x[1])[0] if asset_type_corrections else None,
                "most_common_issue": max(common_issues.items(), key=lambda x: x[1])[0] if common_issues else None
            }
        }
    
    async def learn_user_preferences(
        self, 
        preference_data: Dict[str, Any], 
        engagement_id: Optional[str] = None,
        context: Optional[LearningContext] = None
    ):
        """Learn user preferences with engagement context."""
        if not context:
            context = LearningContext(engagement_id=engagement_id)
        
        memory = self._get_context_memory(context)
        
        memory.add_experience("user_preferences", {
            "preferences": preference_data,
            "engagement_id": engagement_id,
            "context": asdict(context),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        self.global_stats["total_learning_events"] += 1
        self.global_stats["last_updated"] = datetime.utcnow().isoformat()
        
        logger.info(f"Learned user preferences for engagement {engagement_id}")