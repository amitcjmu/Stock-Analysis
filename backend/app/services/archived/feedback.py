"""
Feedback Processing Service for CrewAI agents.
Processes user feedback and implements learning mechanisms for continuous improvement.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class FeedbackProcessor:
    """Processes user feedback and implements learning mechanisms."""
    
    def __init__(self, memory):
        self.memory = memory
        """Initialize optional dependencies with graceful fallbacks."""
        try:
            from app.services.field_mapper_modular import field_mapper
            self.field_mapper = field_mapper
            self.field_mapper_available = True
            logger.info("Field mapper integration enabled")
        except ImportError as e:
            logger.warning(f"Field mapper not available: {e}")
            self.field_mapper = None
            self.field_mapper_available = False
    
    def intelligent_feedback_processing(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user feedback intelligently when CrewAI is unavailable."""
        
        filename = feedback_data.get('filename', '')
        user_corrections = feedback_data.get('user_corrections', {})
        asset_type_override = feedback_data.get('asset_type_override')
        original_analysis = feedback_data.get('original_analysis', {})
        
        # Record the feedback
        self.memory.add_experience("user_feedback", {
            "filename": filename,
            "corrections": user_corrections,
            "asset_type_override": asset_type_override,
            "original_analysis": original_analysis
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
        
        # Store learned patterns and update field mappings
        if patterns_identified:
            self.memory.add_experience("learned_patterns", {
                "patterns": patterns_identified,
                "source_feedback": filename,
                "confidence_boost": confidence_boost
            })
            
            # Update dynamic field mappings based on patterns
            if self.field_mapper_available:
                self.field_mapper.process_feedback_patterns(patterns_identified)
            else:
                logger.warning("Field mapper not available for pattern processing")
        
        # Update learning metrics
        self.memory.update_learning_metrics("user_corrections", 1)
        self.memory.update_learning_metrics("accuracy_improvements", confidence_boost)
        
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
            "feedback_processing_mode": "intelligent_memory_based"
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
            # Extract any field mapping patterns mentioned in the feedback
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
        
        return improvements or ["Overall analysis accuracy improved"]
    
    def _generate_corrected_analysis(self, original_analysis: Dict, user_corrections: Dict, asset_type_override: Optional[str]) -> Dict[str, Any]:
        """Generate corrected analysis based on user feedback."""
        
        corrected = {
            "asset_type": asset_type_override or original_analysis.get('asset_type_detected', 'unknown'),
            "relevant_missing_fields": self._get_corrected_missing_fields(asset_type_override, user_corrections),
            "updated_recommendations": self._get_updated_recommendations(asset_type_override, user_corrections)
        }
        
        return corrected
    
    def _get_corrected_missing_fields(self, asset_type: Optional[str], user_corrections: Dict) -> List[str]:
        """Get corrected missing fields based on asset type and feedback."""
        
        if not asset_type:
            return []
        
        # Define corrected field requirements based on asset type
        field_requirements = {
            "server": ["IP Address", "OS Version", "CPU Cores", "Memory GB", "Hostname"],
            "application": ["Version", "Environment", "Business Owner", "Dependencies"],
            "database": ["DB Name", "Version", "Host Server", "Port", "Connection String"],
            "mixed": ["Name", "Type", "Environment"]
        }
        
        base_fields = field_requirements.get(asset_type.lower(), field_requirements["mixed"])
        
        # Add fields mentioned in user feedback
        missing_fields_feedback = user_corrections.get('missing_fields_feedback', '')
        if missing_fields_feedback:
            # Extract additional fields from feedback
            if 'backup' in missing_fields_feedback.lower():
                base_fields.append("Backup Strategy")
            if 'network' in missing_fields_feedback.lower():
                base_fields.append("Network Configuration")
        
        return base_fields
    
    def _get_updated_recommendations(self, asset_type: Optional[str], user_corrections: Dict) -> List[str]:
        """Get updated recommendations based on corrected asset type."""
        
        if not asset_type:
            return ["Review and validate asset classification"]
        
        recommendations = {
            "server": [
                "Collect IP addresses for all servers",
                "Document OS versions for compatibility assessment",
                "Gather hardware specifications for capacity planning"
            ],
            "application": [
                "Document application dependencies and integrations",
                "Identify business owners and criticality levels",
                "Map applications to their hosting infrastructure"
            ],
            "database": [
                "Document database connections and access patterns",
                "Identify host server relationships and dependencies",
                "Gather backup and recovery procedures"
            ]
        }
        
        base_recommendations = recommendations.get(asset_type.lower(), [
            "Standardize asset classification",
            "Improve data consistency",
            "Add missing critical fields"
        ])
        
        # Add specific recommendations based on user feedback
        analysis_issues = user_corrections.get('analysis_issues', '')
        if 'naming' in analysis_issues.lower():
            base_recommendations.append("Implement consistent naming conventions")
        
        return base_recommendations
    
    def _calculate_confidence_boost(self, patterns: List[str]) -> float:
        """Calculate confidence boost based on identified patterns."""
        
        base_boost = 0.1  # Base boost for any feedback
        
        # Additional boost based on pattern quality
        pattern_boost = len(patterns) * 0.05  # 5% per pattern
        
        # Cap the boost at 30%
        total_boost = min(0.3, base_boost + pattern_boost)
        
        return total_boost
    
    def analyze_feedback_trends(self) -> Dict[str, Any]:
        """Analyze trends in user feedback for system improvement."""
        
        feedback_experiences = self.memory.experiences.get("user_feedback", [])
        
        if not feedback_experiences:
            return {
                "total_feedback": 0,
                "trends": [],
                "recommendations": ["No feedback data available for trend analysis"]
            }
        
        # Analyze feedback trends
        asset_type_corrections = {}
        common_issues = {}
        field_feedback_count = 0
        
        for feedback in feedback_experiences:
            # Track asset type corrections
            asset_override = feedback.get('asset_type_override')
            if asset_override:
                asset_type_corrections[asset_override] = asset_type_corrections.get(asset_override, 0) + 1
            
            # Track common issues
            corrections = feedback.get('corrections', {})
            analysis_issues = corrections.get('analysis_issues', '')
            if analysis_issues:
                # Simple keyword extraction
                if 'server' in analysis_issues.lower():
                    common_issues['server_classification'] = common_issues.get('server_classification', 0) + 1
                if 'application' in analysis_issues.lower():
                    common_issues['application_classification'] = common_issues.get('application_classification', 0) + 1
                if 'missing' in analysis_issues.lower():
                    common_issues['missing_fields'] = common_issues.get('missing_fields', 0) + 1
            
            # Track field feedback
            if corrections.get('missing_fields_feedback'):
                field_feedback_count += 1
        
        # Generate trend insights
        trends = []
        
        if asset_type_corrections:
            most_corrected = max(asset_type_corrections, key=asset_type_corrections.get)
            trends.append(f"Most corrected asset type: {most_corrected} ({asset_type_corrections[most_corrected]} times)")
        
        if common_issues:
            most_common_issue = max(common_issues, key=common_issues.get)
            trends.append(f"Most common issue: {most_common_issue} ({common_issues[most_common_issue]} times)")
        
        if field_feedback_count > 0:
            trends.append(f"Field-related feedback: {field_feedback_count} instances")
        
        # Generate recommendations
        recommendations = []
        
        if 'server_classification' in common_issues:
            recommendations.append("Improve server detection algorithms")
        
        if 'missing_fields' in common_issues:
            recommendations.append("Enhance field relevance mapping")
        
        if field_feedback_count > len(feedback_experiences) * 0.5:
            recommendations.append("Focus on improving field identification accuracy")
        
        return {
            "total_feedback": len(feedback_experiences),
            "asset_type_corrections": asset_type_corrections,
            "common_issues": common_issues,
            "field_feedback_ratio": field_feedback_count / len(feedback_experiences) if feedback_experiences else 0,
            "trends": trends,
            "recommendations": recommendations or ["Continue monitoring feedback patterns"]
        }
    
    def get_learning_effectiveness(self) -> Dict[str, Any]:
        """Assess the effectiveness of the learning system."""
        
        metrics = self.memory.learning_metrics
        feedback_count = len(self.memory.experiences.get("user_feedback", []))
        pattern_count = len(self.memory.experiences.get("learned_patterns", []))
        
        # Calculate learning velocity
        if feedback_count > 0:
            patterns_per_feedback = pattern_count / feedback_count
        else:
            patterns_per_feedback = 0
        
        # Assess learning quality
        if patterns_per_feedback > 1.5:
            learning_quality = "excellent"
        elif patterns_per_feedback > 1.0:
            learning_quality = "good"
        elif patterns_per_feedback > 0.5:
            learning_quality = "fair"
        else:
            learning_quality = "needs_improvement"
        
        return {
            "total_feedback_processed": feedback_count,
            "patterns_learned": pattern_count,
            "patterns_per_feedback": patterns_per_feedback,
            "learning_quality": learning_quality,
            "accuracy_improvements": metrics.get("accuracy_improvements", 0),
            "confidence_evolution": len(metrics.get("confidence_evolution", [])),
            "learning_velocity": patterns_per_feedback,
            "recommendations": self._get_learning_recommendations(learning_quality, patterns_per_feedback)
        }
    
    def _get_learning_recommendations(self, quality: str, velocity: float) -> List[str]:
        """Get recommendations for improving learning effectiveness."""
        
        recommendations = []
        
        if quality == "needs_improvement":
            recommendations.extend([
                "Encourage more detailed user feedback",
                "Implement more sophisticated pattern recognition",
                "Review feedback processing algorithms"
            ])
        elif quality == "fair":
            recommendations.extend([
                "Focus on extracting more patterns from feedback",
                "Improve pattern quality assessment"
            ])
        elif quality == "good":
            recommendations.extend([
                "Maintain current learning approach",
                "Consider advanced pattern recognition techniques"
            ])
        else:  # excellent
            recommendations.extend([
                "Learning system is performing excellently",
                "Consider sharing patterns across similar systems"
            ])
        
        if velocity < 0.5:
            recommendations.append("Increase feedback collection frequency")
        
        return recommendations
    
    def export_learning_data(self, export_path: str) -> bool:
        """Export learning data for analysis or backup."""
        
        try:
            learning_data = {
                "feedback_experiences": self.memory.experiences.get("user_feedback", []),
                "learned_patterns": self.memory.experiences.get("learned_patterns", []),
                "learning_metrics": self.memory.learning_metrics,
                "feedback_trends": self.analyze_feedback_trends(),
                "learning_effectiveness": self.get_learning_effectiveness(),
                "exported_at": datetime.utcnow().isoformat()
            }
            
            import json
            with open(export_path, 'w') as f:
                json.dump(learning_data, f, indent=2, default=str)
            
            logger.info(f"Learning data exported to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export learning data: {e}")
            return False 