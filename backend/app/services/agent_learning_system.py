"""
Agent Learning System with Context Isolation
Provides context-scoped learning for CrewAI agents with multi-tenant isolation.
Implements Task 5.1: Context-Scoped Agent Learning
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


class ContextScopedAgentLearning:
    """Agent learning system with context isolation for multi-tenancy."""
    
    def __init__(self, data_dir: str = "data/learning"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Context-scoped memory storage
        self.context_memories: Dict[str, AgentMemory] = {}
        
        # Learning patterns by context
        self.learning_patterns: Dict[str, List[LearningPattern]] = {}
        
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
        patterns_file = self.data_dir / "learning_patterns.json"
        
        # Convert patterns to serializable format
        serializable_patterns = {}
        for context_key, patterns in self.learning_patterns.items():
            serializable_patterns[context_key] = []
            for pattern in patterns:
                pattern_dict = asdict(pattern)
                # Convert datetime objects to ISO strings
                pattern_dict["created_at"] = pattern.created_at.isoformat()
                pattern_dict["last_used"] = pattern.last_used.isoformat()
                serializable_patterns[context_key].append(pattern_dict)
        
        try:
            with open(patterns_file, 'w') as f:
                json.dump(serializable_patterns, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save learning patterns: {e}")
    
    def _load_learning_patterns(self):
        """Load learning patterns from disk."""
        patterns_file = self.data_dir / "learning_patterns.json"
        
        if not patterns_file.exists():
            return
        
        try:
            with open(patterns_file, 'r') as f:
                serializable_patterns = json.load(f)
            
            # Convert back to LearningPattern objects
            for context_key, patterns_data in serializable_patterns.items():
                self.learning_patterns[context_key] = []
                for pattern_dict in patterns_data:
                    # Convert ISO strings back to datetime objects
                    pattern_dict["created_at"] = datetime.fromisoformat(pattern_dict["created_at"])
                    pattern_dict["last_used"] = datetime.fromisoformat(pattern_dict["last_used"])
                    
                    # Reconstruct LearningContext
                    context_data = pattern_dict["context"]
                    context = LearningContext(**context_data)
                    pattern_dict["context"] = context
                    
                    pattern = LearningPattern(**pattern_dict)
                    self.learning_patterns[context_key].append(pattern)
            
            logger.info(f"Loaded {sum(len(patterns) for patterns in self.learning_patterns.values())} learning patterns")
            
        except Exception as e:
            logger.error(f"Failed to load learning patterns: {e}")
    
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


# Global instance
agent_learning_system = ContextScopedAgentLearning() 