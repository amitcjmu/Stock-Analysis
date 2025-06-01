"""
Agent Learning System
Platform-wide learning infrastructure for agent pattern recognition and field mapping learning.
Implements Task C.1: Agent Memory and Learning System.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)

class AgentLearningSystem:
    """
    Platform-wide learning infrastructure for AI agents.
    Manages pattern recognition, field mapping learning, and performance tracking.
    """
    
    def __init__(self, learning_data_path: str = "data/learning"):
        self.learning_data_path = Path(learning_data_path)
        self.learning_data_path.mkdir(parents=True, exist_ok=True)
        
        # Learning categories
        self.learning_categories = {
            "field_mapping_patterns": {},
            "data_source_patterns": {},
            "quality_assessment_patterns": {},
            "user_preference_patterns": {},
            "accuracy_metrics": {},
            "performance_tracking": {}
        }
        
        # Load existing learning data
        self._load_learning_data()
        
        logger.info("Agent Learning System initialized")
    
    # === PATTERN RECOGNITION LEARNING ===
    
    async def learn_field_mapping_pattern(self, learning_data: Dict[str, Any]) -> None:
        """Learn from field mapping corrections and successes."""
        
        original_field = learning_data.get("original_field", "").lower()
        mapped_to = learning_data.get("mapped_to", "")
        confidence_score = learning_data.get("confidence_score", 0.5)
        context = learning_data.get("context", {})
        
        # Store the learning pattern
        pattern_key = self._generate_pattern_key(original_field)
        
        if pattern_key not in self.learning_categories["field_mapping_patterns"]:
            self.learning_categories["field_mapping_patterns"][pattern_key] = {
                "variations": [],
                "most_common_mapping": None,
                "confidence_scores": [],
                "context_patterns": [],
                "learning_count": 0
            }
        
        pattern = self.learning_categories["field_mapping_patterns"][pattern_key]
        pattern["variations"].append({
            "original": original_field,
            "mapped_to": mapped_to,
            "confidence": confidence_score,
            "context": context,
            "learned_at": datetime.utcnow().isoformat()
        })
        pattern["confidence_scores"].append(confidence_score)
        pattern["learning_count"] += 1
        
        # Update most common mapping
        mapping_counts = {}
        for variation in pattern["variations"]:
            mapped_to = variation["mapped_to"]
            mapping_counts[mapped_to] = mapping_counts.get(mapped_to, 0) + 1
        
        pattern["most_common_mapping"] = max(mapping_counts.items(), key=lambda x: x[1])[0]
        
        # Store context patterns
        if context:
            pattern["context_patterns"].append(context)
        
        await self._save_learning_data()
        
        logger.info(f"Learned field mapping pattern: {original_field} -> {mapped_to}")
    
    async def suggest_field_mapping(self, field_name: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Suggest field mapping based on learned patterns."""
        
        field_lower = field_name.lower()
        pattern_key = self._generate_pattern_key(field_lower)
        
        # Direct pattern match
        if pattern_key in self.learning_categories["field_mapping_patterns"]:
            pattern = self.learning_categories["field_mapping_patterns"][pattern_key]
            
            # Calculate confidence based on learning history
            avg_confidence = sum(pattern["confidence_scores"]) / len(pattern["confidence_scores"])
            learning_confidence = min(pattern["learning_count"] / 10, 1.0)  # More learning = higher confidence
            overall_confidence = (avg_confidence + learning_confidence) / 2
            
            return {
                "suggested_mapping": pattern["most_common_mapping"],
                "confidence": overall_confidence,
                "learning_count": pattern["learning_count"],
                "reasoning": f"Based on {pattern['learning_count']} previous mappings",
                "pattern_match": "direct"
            }
        
        # Fuzzy pattern matching
        best_match = await self._find_fuzzy_field_match(field_lower)
        if best_match:
            return best_match
        
        # No learned pattern found
        return {
            "suggested_mapping": None,
            "confidence": 0.0,
            "learning_count": 0,
            "reasoning": "No learned patterns found for this field",
            "pattern_match": "none"
        }
    
    # === DATA SOURCE PATTERN LEARNING ===
    
    async def learn_data_source_pattern(self, source_data: Dict[str, Any]) -> None:
        """Learn patterns from data source analysis corrections."""
        
        source_type = source_data.get("source_type", "unknown")
        columns = source_data.get("columns", [])
        content_indicators = source_data.get("content_indicators", [])
        user_correction = source_data.get("user_correction")
        
        if source_type not in self.learning_categories["data_source_patterns"]:
            self.learning_categories["data_source_patterns"][source_type] = {
                "column_patterns": [],
                "content_patterns": [],
                "confidence_scores": [],
                "learning_count": 0
            }
        
        pattern = self.learning_categories["data_source_patterns"][source_type]
        
        # Learn column patterns
        for column in columns:
            if column.lower() not in pattern["column_patterns"]:
                pattern["column_patterns"].append(column.lower())
        
        # Learn content patterns
        for indicator in content_indicators:
            if indicator not in pattern["content_patterns"]:
                pattern["content_patterns"].append(indicator)
        
        pattern["learning_count"] += 1
        
        # If there was a user correction, update patterns
        if user_correction:
            corrected_type = user_correction.get("corrected_type")
            if corrected_type and corrected_type != source_type:
                # Move patterns to correct type
                await self._transfer_pattern_learning(source_type, corrected_type, columns, content_indicators)
        
        await self._save_learning_data()
        
        logger.info(f"Learned data source pattern for {source_type}")
    
    # === QUALITY ASSESSMENT LEARNING ===
    
    async def learn_quality_assessment(self, quality_data: Dict[str, Any]) -> None:
        """Learn from quality assessment corrections and validations."""
        
        original_classification = quality_data.get("original_classification")
        corrected_classification = quality_data.get("corrected_classification")
        quality_metrics = quality_data.get("quality_metrics", {})
        data_characteristics = quality_data.get("data_characteristics", {})
        
        learning_key = f"{original_classification}_to_{corrected_classification}"
        
        if learning_key not in self.learning_categories["quality_assessment_patterns"]:
            self.learning_categories["quality_assessment_patterns"][learning_key] = {
                "correction_patterns": [],
                "metric_thresholds": {},
                "characteristic_indicators": [],
                "learning_count": 0
            }
        
        pattern = self.learning_categories["quality_assessment_patterns"][learning_key]
        pattern["correction_patterns"].append({
            "original": original_classification,
            "corrected": corrected_classification,
            "metrics": quality_metrics,
            "characteristics": data_characteristics,
            "learned_at": datetime.utcnow().isoformat()
        })
        pattern["learning_count"] += 1
        
        # Update metric thresholds based on corrections
        await self._update_quality_thresholds(pattern, quality_metrics, corrected_classification)
        
        await self._save_learning_data()
        
        logger.info(f"Learned quality assessment pattern: {learning_key}")
    
    # === USER PREFERENCE LEARNING ===
    
    async def learn_user_preferences(self, preference_data: Dict[str, Any], 
                                   engagement_id: Optional[str] = None) -> None:
        """Learn user preferences for client/engagement-specific context."""
        
        preference_type = preference_data.get("type")
        preference_value = preference_data.get("value")
        context = preference_data.get("context", {})
        
        # Store at platform level (general preferences)
        platform_key = f"platform_{preference_type}"
        if platform_key not in self.learning_categories["user_preference_patterns"]:
            self.learning_categories["user_preference_patterns"][platform_key] = {
                "preferences": [],
                "most_common": None,
                "confidence": 0.0
            }
        
        self.learning_categories["user_preference_patterns"][platform_key]["preferences"].append({
            "value": preference_value,
            "context": context,
            "learned_at": datetime.utcnow().isoformat()
        })
        
        # Update most common preference
        await self._update_most_common_preference(platform_key)
        
        # Store at engagement level if provided
        if engagement_id:
            engagement_key = f"engagement_{engagement_id}_{preference_type}"
            if engagement_key not in self.learning_categories["user_preference_patterns"]:
                self.learning_categories["user_preference_patterns"][engagement_key] = {
                    "preferences": [],
                    "most_common": None,
                    "confidence": 0.0
                }
            
            self.learning_categories["user_preference_patterns"][engagement_key]["preferences"].append({
                "value": preference_value,
                "context": context,
                "learned_at": datetime.utcnow().isoformat()
            })
            
            await self._update_most_common_preference(engagement_key)
        
        await self._save_learning_data()
        
        logger.info(f"Learned user preference: {preference_type} = {preference_value}")
    
    # === PERFORMANCE TRACKING ===
    
    async def track_agent_performance(self, agent_id: str, performance_data: Dict[str, Any]) -> None:
        """Track agent performance for accuracy improvement."""
        
        if agent_id not in self.learning_categories["performance_tracking"]:
            self.learning_categories["performance_tracking"][agent_id] = {
                "accuracy_scores": [],
                "performance_metrics": [],
                "improvement_trends": [],
                "last_updated": None
            }
        
        agent_performance = self.learning_categories["performance_tracking"][agent_id]
        
        # Track accuracy metrics
        accuracy_score = performance_data.get("accuracy_score", 0.0)
        agent_performance["accuracy_scores"].append({
            "score": accuracy_score,
            "timestamp": datetime.utcnow().isoformat(),
            "context": performance_data.get("context", {})
        })
        
        # Track performance metrics
        metrics = performance_data.get("metrics", {})
        agent_performance["performance_metrics"].append({
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Calculate improvement trends
        await self._calculate_improvement_trends(agent_id)
        
        agent_performance["last_updated"] = datetime.utcnow().isoformat()
        
        await self._save_learning_data()
        
        logger.info(f"Tracked performance for agent {agent_id}: {accuracy_score}")
    
    # === ACCURACY MONITORING ===
    
    async def get_agent_accuracy_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get accuracy metrics and improvement tracking for an agent."""
        
        if agent_id not in self.learning_categories["performance_tracking"]:
            return {
                "overall_accuracy": 0.0,
                "recent_accuracy": 0.0,
                "improvement_trend": "no_data",
                "total_interactions": 0
            }
        
        agent_performance = self.learning_categories["performance_tracking"][agent_id]
        accuracy_scores = agent_performance["accuracy_scores"]
        
        if not accuracy_scores:
            return {
                "overall_accuracy": 0.0,
                "recent_accuracy": 0.0,
                "improvement_trend": "no_data",
                "total_interactions": 0
            }
        
        # Calculate overall accuracy
        all_scores = [score["score"] for score in accuracy_scores]
        overall_accuracy = sum(all_scores) / len(all_scores)
        
        # Calculate recent accuracy (last 10 interactions)
        recent_scores = all_scores[-10:] if len(all_scores) >= 10 else all_scores
        recent_accuracy = sum(recent_scores) / len(recent_scores)
        
        # Get improvement trend
        improvement_trend = agent_performance.get("improvement_trends", [])
        latest_trend = improvement_trend[-1] if improvement_trend else "stable"
        
        return {
            "overall_accuracy": overall_accuracy,
            "recent_accuracy": recent_accuracy,
            "improvement_trend": latest_trend,
            "total_interactions": len(accuracy_scores),
            "accuracy_history": all_scores[-20:]  # Last 20 scores
        }
    
    # === UTILITY METHODS ===
    
    def _generate_pattern_key(self, field_name: str) -> str:
        """Generate a consistent pattern key for field names."""
        
        # Clean and normalize field name
        clean_name = field_name.lower().strip()
        
        # Remove common separators and replace with underscores
        clean_name = clean_name.replace('-', '_').replace(' ', '_').replace('.', '_')
        
        # Extract key terms
        key_terms = []
        common_terms = ['hostname', 'asset', 'server', 'ip', 'address', 'environment', 
                       'owner', 'department', 'location', 'operating', 'system', 'memory', 'cpu']
        
        for term in common_terms:
            if term in clean_name:
                key_terms.append(term)
        
        return '_'.join(key_terms) if key_terms else clean_name
    
    async def _find_fuzzy_field_match(self, field_name: str) -> Optional[Dict[str, Any]]:
        """Find fuzzy matches for field names based on learned patterns."""
        
        best_match = None
        best_score = 0.0
        
        for pattern_key, pattern in self.learning_categories["field_mapping_patterns"].items():
            # Simple fuzzy matching based on common terms
            score = await self._calculate_field_similarity(field_name, pattern_key)
            
            if score > best_score and score > 0.6:  # Minimum threshold
                best_score = score
                best_match = {
                    "suggested_mapping": pattern["most_common_mapping"],
                    "confidence": score * 0.8,  # Reduce confidence for fuzzy matches
                    "learning_count": pattern["learning_count"],
                    "reasoning": f"Fuzzy match with {pattern_key} (similarity: {score:.2f})",
                    "pattern_match": "fuzzy"
                }
        
        return best_match
    
    async def _calculate_field_similarity(self, field1: str, field2: str) -> float:
        """Calculate similarity between two field names."""
        
        # Simple word-based similarity
        words1 = set(field1.lower().split('_'))
        words2 = set(field2.lower().split('_'))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _transfer_pattern_learning(self, from_type: str, to_type: str, 
                                       columns: List[str], content_indicators: List[str]) -> None:
        """Transfer learning patterns when user corrects source type."""
        
        if to_type not in self.learning_categories["data_source_patterns"]:
            self.learning_categories["data_source_patterns"][to_type] = {
                "column_patterns": [],
                "content_patterns": [],
                "confidence_scores": [],
                "learning_count": 0
            }
        
        to_pattern = self.learning_categories["data_source_patterns"][to_type]
        
        # Transfer column patterns
        for column in columns:
            if column.lower() not in to_pattern["column_patterns"]:
                to_pattern["column_patterns"].append(column.lower())
        
        # Transfer content patterns
        for indicator in content_indicators:
            if indicator not in to_pattern["content_patterns"]:
                to_pattern["content_patterns"].append(indicator)
        
        to_pattern["learning_count"] += 1
    
    async def _update_quality_thresholds(self, pattern: Dict[str, Any], 
                                       quality_metrics: Dict[str, Any], 
                                       correct_classification: str) -> None:
        """Update quality assessment thresholds based on corrections."""
        
        # Update metric thresholds for better classification
        for metric_name, metric_value in quality_metrics.items():
            if metric_name not in pattern["metric_thresholds"]:
                pattern["metric_thresholds"][metric_name] = {
                    "values_for_classification": {},
                    "learned_threshold": None
                }
            
            threshold_data = pattern["metric_thresholds"][metric_name]
            
            if correct_classification not in threshold_data["values_for_classification"]:
                threshold_data["values_for_classification"][correct_classification] = []
            
            threshold_data["values_for_classification"][correct_classification].append(metric_value)
            
            # Calculate learned threshold
            if len(threshold_data["values_for_classification"]) > 1:
                await self._calculate_learned_threshold(threshold_data)
    
    async def _calculate_learned_threshold(self, threshold_data: Dict[str, Any]) -> None:
        """Calculate learned threshold for quality metrics."""
        
        # Simple threshold calculation based on classification values
        classification_values = threshold_data["values_for_classification"]
        
        if len(classification_values) >= 2:
            # Find the value that best separates classifications
            all_values = []
            for classification, values in classification_values.items():
                for value in values:
                    all_values.append((value, classification))
            
            all_values.sort()
            
            # Simple threshold: midpoint between classifications
            if len(all_values) >= 4:
                mid_point = len(all_values) // 2
                threshold_data["learned_threshold"] = all_values[mid_point][0]
    
    async def _update_most_common_preference(self, preference_key: str) -> None:
        """Update the most common preference for a given key."""
        
        pattern = self.learning_categories["user_preference_patterns"][preference_key]
        preferences = pattern["preferences"]
        
        if not preferences:
            return
        
        # Count preference values
        value_counts = {}
        for pref in preferences:
            value = pref["value"]
            value_counts[value] = value_counts.get(value, 0) + 1
        
        # Find most common
        most_common_value = max(value_counts.items(), key=lambda x: x[1])[0]
        pattern["most_common"] = most_common_value
        
        # Calculate confidence based on consensus
        total_prefs = len(preferences)
        most_common_count = value_counts[most_common_value]
        pattern["confidence"] = most_common_count / total_prefs
    
    async def _calculate_improvement_trends(self, agent_id: str) -> None:
        """Calculate improvement trends for an agent."""
        
        agent_performance = self.learning_categories["performance_tracking"][agent_id]
        accuracy_scores = agent_performance["accuracy_scores"]
        
        if len(accuracy_scores) < 5:  # Need minimum data points
            return
        
        # Calculate trend over last 10 scores
        recent_scores = [score["score"] for score in accuracy_scores[-10:]]
        
        # Simple trend calculation
        if len(recent_scores) >= 5:
            first_half = recent_scores[:len(recent_scores)//2]
            second_half = recent_scores[len(recent_scores)//2:]
            
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)
            
            if second_avg > first_avg + 0.05:
                trend = "improving"
            elif second_avg < first_avg - 0.05:
                trend = "declining"
            else:
                trend = "stable"
            
            agent_performance["improvement_trends"].append(trend)
    
    # === DATA PERSISTENCE ===
    
    def _load_learning_data(self) -> None:
        """Load existing learning data from storage."""
        
        try:
            learning_file = self.learning_data_path / "agent_learning.json"
            if learning_file.exists():
                with open(learning_file, 'r') as f:
                    loaded_data = json.load(f)
                    self.learning_categories.update(loaded_data)
                
                logger.info("Loaded existing learning data")
        except Exception as e:
            logger.error(f"Error loading learning data: {e}")
    
    async def _save_learning_data(self) -> None:
        """Save learning data to storage."""
        
        try:
            learning_file = self.learning_data_path / "agent_learning.json"
            with open(learning_file, 'w') as f:
                json.dump(self.learning_categories, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving learning data: {e}")
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get statistics about the learning system."""
        
        return {
            "field_mapping_patterns": len(self.learning_categories["field_mapping_patterns"]),
            "data_source_patterns": len(self.learning_categories["data_source_patterns"]),
            "quality_patterns": len(self.learning_categories["quality_assessment_patterns"]),
            "user_preferences": len(self.learning_categories["user_preference_patterns"]),
            "agents_tracked": len(self.learning_categories["performance_tracking"]),
            "total_learning_events": sum(
                len(category) for category in self.learning_categories.values()
            )
        }

# Global instance for platform-wide learning
agent_learning_system = AgentLearningSystem() 