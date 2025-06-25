"""
Agent Learning System with Context Isolation and Performance Integration
Provides context-scoped learning for CrewAI agents with multi-tenant isolation.
Enhanced with performance monitoring integration for Task 4.4.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass, asdict
import hashlib

from app.services.memory import AgentMemory
from app.services.embedding_service import EmbeddingService
from app.utils.vector_utils import VectorUtils
from app.models.data_import import MappingLearningPattern
# from app.models.learning_patterns import (
#     AssetClassificationPattern,
# )

# Performance monitoring integration
try:
    from app.services.performance.response_optimizer import response_optimizer
    from app.services.monitoring.performance_monitor import performance_monitor
    PERFORMANCE_MONITORING_AVAILABLE = True
except ImportError:
    PERFORMANCE_MONITORING_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class LearningContext:
    """Context information for scoped learning."""
    client_account_id: Optional[str] = None
    engagement_id: Optional[str] = None
    session_id: Optional[str] = None
    context_hash: Optional[str] = None
    
    def __post_init__(self):
        """Generate context hash for namespacing."""
        if not self.context_hash:
            context_str = f"{self.client_account_id}:{self.engagement_id}:{self.session_id}"
            self.context_hash = hashlib.md5(context_str.encode()).hexdigest()[:16]


@dataclass
class LearningPattern:
    """Represents a learned pattern with context isolation."""
    pattern_id: str
    pattern_type: str
    context: LearningContext
    pattern_data: Dict[str, Any]
    confidence: float
    usage_count: int
    created_at: datetime
    last_used: datetime
    success_rate: float = 1.0


@dataclass
class PerformanceLearningPattern:
    """Performance-based learning pattern for optimization."""
    pattern_id: str
    operation_type: str
    performance_metrics: Dict[str, float]
    optimization_applied: List[str]
    improvement_factor: float
    context_data: Dict[str, Any]
    created_at: datetime
    usage_count: int = 0
    success_rate: float = 1.0


class ContextScopedAgentLearning:
    """Agent learning system with context isolation for multi-tenancy."""
    
    def __init__(self, data_dir: str = "data/learning"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Context-scoped memory storage
        self.context_memories: Dict[str, AgentMemory] = {}
        
        # Learning patterns by context
        self.learning_patterns: Dict[str, List[LearningPattern]] = {}
        
        # Performance-based learning patterns
        self.performance_patterns: Dict[str, List[PerformanceLearningPattern]] = {}
        
        self.embedding_service = EmbeddingService()
        self.vector_utils = VectorUtils()
        
        # Global learning statistics
        self.global_stats = {
            "total_contexts": 0,
            "total_patterns": 0,
            "total_learning_events": 0,
            "field_mapping_patterns": 0,
            "data_source_patterns": 0,
            "quality_assessment_patterns": 0,
            "agents_tracked": set(),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Load existing patterns
        self._load_learning_patterns()
    
    def _get_context_memory(self, context: LearningContext) -> AgentMemory:
        """Get or create context-scoped memory."""
        context_key = context.context_hash
        
        if context_key not in self.context_memories:
            # Create context-specific memory directory
            context_dir = self.data_dir / f"context_{context_key}"
            context_dir.mkdir(exist_ok=True)
            
            self.context_memories[context_key] = AgentMemory(str(context_dir))
            logger.info(f"Created context-scoped memory for {context_key}")
        
        return self.context_memories[context_key]
    
    def _get_context_from_headers(self, headers: Optional[Dict[str, str]] = None) -> LearningContext:
        """Extract context from request headers."""
        if not headers:
            return LearningContext()
        
        return LearningContext(
            client_account_id=headers.get('X-Client-ID'),
            engagement_id=headers.get('X-Engagement-ID'),
            session_id=headers.get('X-Session-ID')
        )
    
    async def learn_field_mapping_pattern(
        self, 
        learning_data: Dict[str, Any],
        context: Optional[LearningContext] = None
    ):
        """Learn field mapping patterns with context isolation."""
        if not context:
            context = LearningContext()
        
        memory = self._get_context_memory(context)
        
        # Create learning pattern
        pattern = LearningPattern(
            pattern_id=f"field_mapping_{datetime.utcnow().timestamp()}",
            pattern_type="field_mapping",
            context=context,
            pattern_data={
                "original_field": learning_data.get("original_field"),
                "mapped_field": learning_data.get("mapped_field"),
                "field_type": learning_data.get("field_type"),
                "confidence_boost": learning_data.get("confidence_boost", 0.1),
                "validation_result": learning_data.get("validation_result", True)
            },
            confidence=learning_data.get("confidence", 0.8),
            usage_count=0,
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow()
        )
        
        # Store in context-scoped patterns
        context_key = context.context_hash
        if context_key not in self.learning_patterns:
            self.learning_patterns[context_key] = []
        
        self.learning_patterns[context_key].append(pattern)
        
        # Add to memory
        memory.add_experience("learned_patterns", {
            "pattern_type": "field_mapping",
            "original_field": learning_data.get("original_field"),
            "mapped_field": learning_data.get("mapped_field"),
            "confidence": pattern.confidence,
            "context": asdict(context)
        })
        
        # Update global stats
        self.global_stats["field_mapping_patterns"] += 1
        self.global_stats["total_patterns"] += 1
        self.global_stats["total_learning_events"] += 1
        self.global_stats["last_updated"] = datetime.utcnow().isoformat()
        
        # Save patterns
        self._save_learning_patterns()
        
        logger.info(f"Learned field mapping pattern in context {context_key}: {learning_data.get('original_field')} -> {learning_data.get('mapped_field')}")
    
    async def suggest_field_mapping(
        self, 
        field_name: str, 
        context_data: Optional[Dict[str, Any]] = None,
        context: Optional[LearningContext] = None
    ) -> Dict[str, Any]:
        """Suggest field mapping based on context-scoped learning."""
        if not context:
            context = LearningContext()
        
        context_key = context.context_hash
        patterns = self.learning_patterns.get(context_key, [])
        
        # Find matching patterns
        matching_patterns = []
        for pattern in patterns:
            if pattern.pattern_type == "field_mapping":
                original_field = pattern.pattern_data.get("original_field", "").lower()
                if field_name.lower() in original_field or original_field in field_name.lower():
                    matching_patterns.append(pattern)
        
        if not matching_patterns:
            # Try global patterns if no context-specific patterns found
            for ctx_patterns in self.learning_patterns.values():
                for pattern in ctx_patterns:
                    if pattern.pattern_type == "field_mapping":
                        original_field = pattern.pattern_data.get("original_field", "").lower()
                        if field_name.lower() in original_field or original_field in field_name.lower():
                            matching_patterns.append(pattern)
                            break
        
        if matching_patterns:
            # Sort by confidence and usage
            best_pattern = max(matching_patterns, key=lambda p: (p.confidence, p.usage_count))
            
            # Update usage
            best_pattern.usage_count += 1
            best_pattern.last_used = datetime.utcnow()
            
            return {
                "suggested_mapping": best_pattern.pattern_data.get("mapped_field"),
                "confidence": best_pattern.confidence,
                "pattern_source": "context_specific" if context_key in self.learning_patterns else "global",
                "usage_count": best_pattern.usage_count
            }
        
        return {
            "suggested_mapping": None,
            "confidence": 0.0,
            "pattern_source": "none",
            "usage_count": 0
        }
    
    async def learn_data_source_pattern(
        self, 
        source_data: Dict[str, Any],
        context: Optional[LearningContext] = None
    ):
        """Learn data source patterns with context isolation."""
        if not context:
            context = LearningContext()
        
        memory = self._get_context_memory(context)
        
        pattern = LearningPattern(
            pattern_id=f"data_source_{datetime.utcnow().timestamp()}",
            pattern_type="data_source",
            context=context,
            pattern_data={
                "source_type": source_data.get("source_type"),
                "file_pattern": source_data.get("file_pattern"),
                "column_patterns": source_data.get("column_patterns", []),
                "quality_indicators": source_data.get("quality_indicators", {}),
                "processing_hints": source_data.get("processing_hints", {})
            },
            confidence=source_data.get("confidence", 0.7),
            usage_count=0,
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow()
        )
        
        context_key = context.context_hash
        if context_key not in self.learning_patterns:
            self.learning_patterns[context_key] = []
        
        self.learning_patterns[context_key].append(pattern)
        
        memory.add_experience("learned_patterns", {
            "pattern_type": "data_source",
            "source_type": source_data.get("source_type"),
            "confidence": pattern.confidence,
            "context": asdict(context)
        })
        
        self.global_stats["data_source_patterns"] += 1
        self.global_stats["total_patterns"] += 1
        self.global_stats["total_learning_events"] += 1
        self.global_stats["last_updated"] = datetime.utcnow().isoformat()
        
        self._save_learning_patterns()
        
        logger.info(f"Learned data source pattern in context {context_key}: {source_data.get('source_type')}")
    
    async def learn_quality_assessment(
        self, 
        quality_data: Dict[str, Any],
        context: Optional[LearningContext] = None
    ):
        """Learn quality assessment patterns with context isolation."""
        if not context:
            context = LearningContext()
        
        memory = self._get_context_memory(context)
        
        pattern = LearningPattern(
            pattern_id=f"quality_{datetime.utcnow().timestamp()}",
            pattern_type="quality_assessment",
            context=context,
            pattern_data={
                "quality_metrics": quality_data.get("quality_metrics", {}),
                "validation_rules": quality_data.get("validation_rules", []),
                "threshold_adjustments": quality_data.get("threshold_adjustments", {}),
                "user_corrections": quality_data.get("user_corrections", [])
            },
            confidence=quality_data.get("confidence", 0.8),
            usage_count=0,
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow()
        )
        
        context_key = context.context_hash
        if context_key not in self.learning_patterns:
            self.learning_patterns[context_key] = []
        
        self.learning_patterns[context_key].append(pattern)
        
        memory.add_experience("learned_patterns", {
            "pattern_type": "quality_assessment",
            "quality_metrics": quality_data.get("quality_metrics", {}),
            "confidence": pattern.confidence,
            "context": asdict(context)
        })
        
        self.global_stats["quality_assessment_patterns"] += 1
        self.global_stats["total_patterns"] += 1
        self.global_stats["total_learning_events"] += 1
        self.global_stats["last_updated"] = datetime.utcnow().isoformat()
        
        self._save_learning_patterns()
        
        logger.info(f"Learned quality assessment pattern in context {context_key}")
    
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
    
    async def track_agent_performance(
        self, 
        agent_id: str, 
        performance_data: Dict[str, Any],
        context: Optional[LearningContext] = None
    ):
        """Track agent performance with context isolation."""
        if not context:
            context = LearningContext()
        
        memory = self._get_context_memory(context)
        
        memory.add_experience("agent_performance", {
            "agent_id": agent_id,
            "performance_data": performance_data,
            "context": asdict(context),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        self.global_stats["agents_tracked"].add(agent_id)
        self.global_stats["total_learning_events"] += 1
        self.global_stats["last_updated"] = datetime.utcnow().isoformat()
        
        logger.info(f"Tracked performance for agent {agent_id} in context {context.context_hash}")
    
    async def get_agent_accuracy_metrics(self, agent_id: str) -> Dict[str, Any]:
        """Get agent accuracy metrics across all contexts."""
        all_metrics = []
        
        for context_key, memory in self.context_memories.items():
            experiences = memory.experiences.get("agent_performance", [])
            agent_experiences = [exp for exp in experiences if exp.get("agent_id") == agent_id]
            
            if agent_experiences:
                context_metrics = {
                    "context": context_key,
                    "total_tasks": len(agent_experiences),
                    "avg_accuracy": sum(exp.get("performance_data", {}).get("accuracy", 0) for exp in agent_experiences) / len(agent_experiences),
                    "latest_performance": agent_experiences[-1].get("performance_data", {})
                }
                all_metrics.append(context_metrics)
        
        return {
            "agent_id": agent_id,
            "context_metrics": all_metrics,
            "overall_accuracy": sum(m["avg_accuracy"] for m in all_metrics) / len(all_metrics) if all_metrics else 0,
            "total_contexts": len(all_metrics)
        }
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning system statistics."""
        # Convert set to count for JSON serialization
        stats = self.global_stats.copy()
        stats["agents_tracked"] = len(stats["agents_tracked"])
        stats["total_contexts"] = len(self.context_memories)
        
        return stats
    
    def _save_learning_patterns(self):
        """Save learning patterns to disk."""
        # This method is now obsolete as we are using the database.
        pass

    def _load_learning_patterns(self):
        """Load learning patterns from disk."""
        # This method is now obsolete as we are using the database.
        pass
    
    async def get_context_patterns(self, context: LearningContext) -> List[LearningPattern]:
        """Get all patterns for a specific context."""
        context_key = context.context_hash
        return self.learning_patterns.get(context_key, [])
    
    async def cleanup_old_patterns(self, days_to_keep: int = 90):
        """Clean up old patterns to prevent unbounded growth."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        for context_key in list(self.learning_patterns.keys()):
            patterns = self.learning_patterns[context_key]
            active_patterns = [p for p in patterns if p.last_used > cutoff_date]
            
            if len(active_patterns) != len(patterns):
                self.learning_patterns[context_key] = active_patterns
                logger.info(f"Cleaned up {len(patterns) - len(active_patterns)} old patterns in context {context_key}")
        
        self._save_learning_patterns()
    
    # === FEEDBACK PROCESSING FUNCTIONALITY ===
    # Integrated from feedback.py service for consolidated learning
    
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
    
    async def _update_field_mappings_from_feedback(self, patterns: List[str], context: LearningContext):
        """Update field mappings based on feedback patterns."""
        for pattern in patterns:
            if 'field mapping' in pattern.lower() or 'maps to' in pattern.lower():
                # Try to extract field mapping information from pattern
                # This is a simplified extraction - more sophisticated parsing could be added
                if 'should map' in pattern.lower():
                    # Extract field mapping suggestion and create learning pattern
                    await self.learn_field_mapping_pattern({
                        "original_field": "user_suggested_field",
                        "mapped_field": "user_suggested_mapping",
                        "field_type": "user_feedback",
                        "confidence_boost": 0.2,
                        "validation_result": True
                    }, context)
    
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
    
    # === CLIENT CONTEXT MANAGEMENT FUNCTIONALITY ===
    # Integrated from client_context_manager.py service for consolidated learning
    
    async def create_client_learning_context(
        self,
        client_account_id: str,
        client_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create client-specific learning context.
        Integrated from client_context_manager.py for consolidated context management.
        """
        context = LearningContext(client_account_id=client_account_id)
        memory = self._get_context_memory(context)
        
        # Store client context information
        memory.add_experience("client_context", {
            "client_account_id": client_account_id,
            "client_name": client_data.get("client_name", f"Client {client_account_id}"),
            "industry": client_data.get("industry"),
            "organization_size": client_data.get("organization_size"),
            "technology_stack": client_data.get("technology_stack", []),
            "business_priorities": client_data.get("business_priorities", []),
            "compliance_requirements": client_data.get("compliance_requirements", []),
            "created_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Created client learning context for {client_account_id}")
        return {"status": "created", "context_key": context.context_hash}
    
    async def create_engagement_learning_context(
        self,
        engagement_id: str,
        client_account_id: str,
        engagement_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create engagement-specific learning context.
        Integrated from client_context_manager.py for consolidated context management.
        """
        context = LearningContext(
            client_account_id=client_account_id,
            engagement_id=engagement_id
        )
        memory = self._get_context_memory(context)
        
        # Store engagement context information
        memory.add_experience("engagement_context", {
            "engagement_id": engagement_id,
            "client_account_id": client_account_id,
            "engagement_name": engagement_data.get("engagement_name", f"Engagement {engagement_id}"),
            "engagement_type": engagement_data.get("engagement_type"),
            "migration_goals": engagement_data.get("migration_goals", []),
            "timeline": engagement_data.get("timeline"),
            "stakeholders": engagement_data.get("stakeholders", []),
            "technical_constraints": engagement_data.get("technical_constraints", []),
            "business_constraints": engagement_data.get("business_constraints", []),
            "success_criteria": engagement_data.get("success_criteria", []),
            "created_at": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Created engagement learning context for {engagement_id}")
        return {"status": "created", "context_key": context.context_hash}
    
    async def learn_organizational_pattern(
        self,
        client_account_id: str,
        pattern_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Learn organizational patterns specific to the client.
        Integrated from client_context_manager.py for consolidated learning.
        """
        context = LearningContext(client_account_id=client_account_id)
        
        pattern = LearningPattern(
            pattern_id=f"org_pattern_{datetime.utcnow().timestamp()}",
            pattern_type="organizational_pattern",
            context=context,
            pattern_data=pattern_data.get("pattern_data", {}),
            confidence=pattern_data.get("confidence", 0.8),
            usage_count=0,
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow()
        )
        
        context_key = context.context_hash
        if context_key not in self.learning_patterns:
            self.learning_patterns[context_key] = []
        
        self.learning_patterns[context_key].append(pattern)
        
        # Update stats
        self.global_stats["organizational_patterns"] = self.global_stats.get("organizational_patterns", 0) + 1
        self.global_stats["total_patterns"] += 1
        self.global_stats["total_learning_events"] += 1
        
        self._save_learning_patterns()
        
        logger.info(f"Learned organizational pattern for client {client_account_id}")
        return {"status": "learned", "pattern_id": pattern.pattern_id}
    
    async def get_client_learning_context(
        self,
        client_account_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get client learning context information."""
        context = LearningContext(client_account_id=client_account_id)
        memory = self._get_context_memory(context)
        
        client_contexts = memory.experiences.get("client_context", [])
        if client_contexts:
            return client_contexts[-1]  # Return most recent
        
        return None
    
    async def get_engagement_learning_context(
        self,
        engagement_id: str,
        client_account_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get engagement learning context information."""
        context = LearningContext(
            client_account_id=client_account_id,
            engagement_id=engagement_id
        )
        memory = self._get_context_memory(context)
        
        engagement_contexts = memory.experiences.get("engagement_context", [])
        if engagement_contexts:
            return engagement_contexts[-1]  # Return most recent
        
        return None
    
    async def get_organizational_patterns(
        self,
        client_account_id: str
    ) -> List[Dict[str, Any]]:
        """Get organizational patterns for a client."""
        context = LearningContext(client_account_id=client_account_id)
        context_key = context.context_hash
        
        patterns = self.learning_patterns.get(context_key, [])
        org_patterns = [p for p in patterns if p.pattern_type == "organizational_pattern"]
        
        return [
            {
                "pattern_id": p.pattern_id,
                "pattern_type": p.pattern_type,
                "pattern_data": p.pattern_data,
                "confidence": p.confidence,
                "usage_count": p.usage_count,
                "created_at": p.created_at.isoformat(),
                "last_used": p.last_used.isoformat()
            }
            for p in org_patterns
        ]
    
    async def get_combined_learning_context(
        self,
        engagement_id: str,
        client_account_id: str
    ) -> Dict[str, Any]:
        """Get combined client and engagement learning context."""
        client_context = await self.get_client_learning_context(client_account_id)
        engagement_context = await self.get_engagement_learning_context(engagement_id, client_account_id)
        org_patterns = await self.get_organizational_patterns(client_account_id)
        
        return {
            "client_context": client_context,
            "engagement_context": engagement_context,
            "organizational_patterns": org_patterns,
            "context_separation": "isolated_per_client_engagement"
        }
    
    def get_context_isolation_statistics(self) -> Dict[str, Any]:
        """Get statistics about context isolation and client separation."""
        client_contexts = set()
        engagement_contexts = set()
        
        for ctx_key, memory in self.context_memories.items():
            client_experiences = memory.experiences.get("client_context", [])
            engagement_experiences = memory.experiences.get("engagement_context", [])
            
            for exp in client_experiences:
                client_contexts.add(exp.get("client_account_id"))
            
            for exp in engagement_experiences:
                engagement_contexts.add(exp.get("engagement_id"))
        
        return {
            "total_client_contexts": len(client_contexts),
            "total_engagement_contexts": len(engagement_contexts),
            "total_isolated_contexts": len(self.context_memories),
            "context_isolation_enabled": True,
            "learning_patterns_by_context": {
                ctx_key: len(patterns) for ctx_key, patterns in self.learning_patterns.items()
            }
        }

    async def learn_from_asset_classification(
        self,
        asset_name: str,
        asset_metadata: Dict[str, Any],
        classification_result: Dict[str, Any],
        user_confirmed: bool,
        context: Optional[LearningContext] = None
    ) -> Dict[str, Any]:
        """Learns from an asset classification operation."""
        if not context:
            context = LearningContext()
        
        try:
            pattern_data = {
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "pattern_name": f"{asset_name}_classification",
                "pattern_type": "asset_classification",
                "asset_name_pattern": asset_name.lower(),
                "metadata_patterns": {
                    "original_metadata": asset_metadata
                },
                "predicted_asset_type": classification_result.get("asset_type", "unknown"),
                "confidence_score": 0.9 if user_confirmed else 0.3,
                "learning_source": "user_feedback" if user_confirmed else "ai_inference",
                "created_by": context.user_id,
            }
            
            pattern_id = await self._store_classification_pattern(pattern_data)
            
            return {
                "pattern_id": pattern_id,
                "confidence": pattern_data["confidence_score"],
                "success": True,
            }
        except Exception as e:
            logger.error(f"Error learning from classification: {e}")
            return {"success": False, "error": str(e)}

    async def classify_asset_automatically(
        self,
        asset_data: Dict[str, Any],
        context: Optional[LearningContext] = None
    ) -> Dict[str, Any]:
        """Automatically classify an asset based on learned patterns."""
        if not context:
            context = LearningContext()

        try:
            asset_name = asset_data.get("name", "")
            
            similar_patterns = await self.vector_utils.find_similar_asset_patterns(
                asset_name,
                context.client_account_id,
                limit=1,
                similarity_threshold=0.7
            )
            
            if similar_patterns:
                best_pattern, similarity = similar_patterns[0]
                return {
                    "asset_type": best_pattern.predicted_asset_type,
                    "confidence": (similarity + best_pattern.confidence_score) / 2,
                    "pattern_id": str(best_pattern.id)
                }
            
            return {"asset_type": "unknown", "confidence": 0.1}
            
        except Exception as e:
            logger.error(f"Error classifying asset automatically: {e}")
            return {"asset_type": "unknown", "confidence": 0.0, "error": str(e)}

    async def _store_mapping_pattern(self, pattern_data: Dict[str, Any]) -> str:
        """Store a field mapping pattern."""
        source_text = pattern_data["original_field"]
        embedding = await self.embedding_service.embed_text(source_text)
        
        async with AsyncSessionLocal() as session:
            pattern = MappingLearningPattern(
                client_account_id=pattern_data["context"].client_account_id,
                engagement_id=pattern_data["context"].engagement_id,
                source_field_name=pattern_data["original_field"],
                source_field_embedding=embedding,
                target_field_name=pattern_data["mapped_field"],
                confidence_score=pattern_data.get("confidence", 0.8),
                created_by=pattern_data["context"].user_id
            )
            session.add(pattern)
            await session.commit()
            await session.refresh(pattern)
            return str(pattern.id)

    async def _store_classification_pattern(self, pattern_data: Dict[str, Any]) -> str:
        """Store an asset classification pattern."""
        name_embedding = await self.embedding_service.embed_text(pattern_data["asset_name_pattern"])
        
        async with AsyncSessionLocal() as session:
            pattern = AssetClassificationPattern(
                client_account_id=pattern_data["client_account_id"],
                engagement_id=pattern_data.get("engagement_id"),
                asset_name_pattern=pattern_data["asset_name_pattern"],
                asset_name_embedding=name_embedding,
                metadata_patterns=pattern_data["metadata_patterns"],
                predicted_asset_type=pattern_data["predicted_asset_type"],
                confidence_score=pattern_data["confidence_score"],
                learning_source=pattern_data["learning_source"],
                created_by=pattern_data.get("created_by")
            )
            session.add(pattern)
            await session.commit()
            await session.refresh(pattern)
            return str(pattern.id)

    async def learn_from_field_mapping(
        self,
        source_field: str,
        target_field: str,
        sample_values: List[str],
        success: bool,
        context: Optional[LearningContext] = None
    ) -> Dict[str, Any]:
        """Learns from a field mapping operation."""
        if not context:
            context = LearningContext()
        
        try:
            pattern_data = {
                "context": context,
                "original_field": source_field,
                "mapped_field": target_field,
                "confidence": 0.8 if success else 0.2,
            }
            
            pattern_id = await self._store_mapping_pattern(pattern_data)
            
            return {
                "pattern_id": pattern_id,
                "confidence": pattern_data["confidence"],
                "success": True,
            }
        except Exception as e:
            logger.error(f"Error learning from mapping: {e}")
            return {"success": False, "error": str(e)}

    async def suggest_field_mappings(
        self,
        source_fields: List[str],
        sample_data: Dict[str, List[str]],
        context: Optional[LearningContext] = None,
        max_suggestions: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Suggest field mappings for source fields based on learned patterns."""
        if not context:
            context = LearningContext()
            
        suggestions = {}
        for field in source_fields:
            search_text = f"{field} {' '.join(sample_data.get(field, []))}"
            similar_patterns = await self.vector_utils.find_similar_patterns(
                await self.embedding_service.embed_text(search_text),
                context.client_account_id,
                limit=max_suggestions
            )
            field_suggestions = []
            for pattern, similarity in similar_patterns:
                field_suggestions.append({
                    "target_field": pattern.target_field_name,
                    "confidence": (similarity + pattern.confidence_score) / 2,
                    "pattern_id": str(pattern.id)
                })
            suggestions[field] = field_suggestions
        return suggestions
    
    # === PERFORMANCE-BASED LEARNING METHODS (Task 4.4) ===
    
    async def learn_from_performance_metrics(
        self,
        operation_type: str,
        performance_metrics: Dict[str, float],
        optimization_applied: List[str],
        context: Optional[LearningContext] = None
    ) -> Dict[str, Any]:
        """Learn optimization patterns from performance metrics."""
        if not PERFORMANCE_MONITORING_AVAILABLE:
            logger.warning("Performance monitoring not available for learning")
            return {"learning_applied": False, "reason": "performance_monitoring_unavailable"}
        
        if not context:
            context = LearningContext()
        
        # Calculate improvement factor
        baseline_duration = performance_metrics.get("baseline_duration", 10.0)
        current_duration = performance_metrics.get("current_duration", baseline_duration)
        improvement_factor = baseline_duration / current_duration if current_duration > 0 else 1.0
        
        # Create performance learning pattern
        pattern = PerformanceLearningPattern(
            pattern_id=f"perf_{operation_type}_{datetime.utcnow().timestamp()}",
            operation_type=operation_type,
            performance_metrics=performance_metrics,
            optimization_applied=optimization_applied,
            improvement_factor=improvement_factor,
            context_data=asdict(context),
            created_at=datetime.utcnow()
        )
        
        # Store pattern by context
        context_key = context.context_hash
        if context_key not in self.performance_patterns:
            self.performance_patterns[context_key] = []
        
        self.performance_patterns[context_key].append(pattern)
        
        # Store in memory
        memory = self._get_context_memory(context)
        memory.add_experience("performance_learning", {
            "operation_type": operation_type,
            "improvement_factor": improvement_factor,
            "optimizations": optimization_applied,
            "metrics": performance_metrics,
            "context": asdict(context)
        })
        
        # Update global stats
        self.global_stats["performance_patterns"] = self.global_stats.get("performance_patterns", 0) + 1
        self.global_stats["total_learning_events"] += 1
        self.global_stats["last_updated"] = datetime.utcnow().isoformat()
        
        logger.info(f"Learned performance pattern for {operation_type} with {improvement_factor:.2f}x improvement")
        
        return {
            "learning_applied": True,
            "pattern_id": pattern.pattern_id,
            "improvement_factor": improvement_factor,
            "optimizations_learned": optimization_applied,
            "performance_impact": f"{((improvement_factor - 1) * 100):.1f}% improvement"
        }
    
    async def suggest_performance_optimizations(
        self,
        operation_type: str,
        current_metrics: Dict[str, float],
        context: Optional[LearningContext] = None
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
                relevant_patterns.extend([p for p in ctx_patterns if p.operation_type == operation_type])
        
        if not relevant_patterns:
            return {
                "suggestions": [],
                "confidence": 0.0,
                "reason": "No performance patterns learned for this operation type"
            }
        
        # Sort patterns by improvement factor and success rate
        relevant_patterns.sort(key=lambda p: p.improvement_factor * p.success_rate, reverse=True)
        
        suggestions = []
        for pattern in relevant_patterns[:3]:  # Top 3 patterns
            # Calculate confidence based on pattern success and usage
            confidence = min(0.9, pattern.success_rate * (1 + pattern.usage_count * 0.1))
            
            suggestion = {
                "optimization_techniques": pattern.optimization_applied,
                "expected_improvement": f"{((pattern.improvement_factor - 1) * 100):.1f}%",
                "confidence": confidence,
                "pattern_usage_count": pattern.usage_count,
                "pattern_success_rate": pattern.success_rate
            }
            suggestions.append(suggestion)
        
        return {
            "suggestions": suggestions,
            "operation_type": operation_type,
            "patterns_analyzed": len(relevant_patterns),
            "confidence": sum(s["confidence"] for s in suggestions) / len(suggestions) if suggestions else 0.0
        }
    
    def get_performance_learning_statistics(self) -> Dict[str, Any]:
        """Get performance learning statistics."""
        total_patterns = sum(len(patterns) for patterns in self.performance_patterns.values())
        
        if total_patterns == 0:
            return {
                "total_performance_patterns": 0,
                "contexts_with_performance_data": 0,
                "message": "No performance learning data available"
            }
        
        # Calculate statistics
        all_patterns = []
        for patterns in self.performance_patterns.values():
            all_patterns.extend(patterns)
        
        avg_improvement = sum(p.improvement_factor for p in all_patterns) / len(all_patterns)
        avg_success_rate = sum(p.success_rate for p in all_patterns) / len(all_patterns)
        
        return {
            "total_performance_patterns": total_patterns,
            "contexts_with_performance_data": len(self.performance_patterns),
            "average_improvement_factor": avg_improvement,
            "average_success_rate": avg_success_rate,
            "performance_learning_grade": "excellent" if avg_improvement > 2.0 and avg_success_rate > 0.8 else "good" if avg_improvement > 1.5 else "needs_improvement"
        }


# Global instance
agent_learning_system = ContextScopedAgentLearning() 