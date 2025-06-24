"""
CrewAI Flow State Extensions Model
Phase 4: Advanced CrewAI Flow analytics and performance tracking
Extended table for CrewAI-specific flow state data and metrics
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text
import uuid
from datetime import datetime

from app.core.database import Base

class CrewAIFlowStateExtensions(Base):
    """
    Extended table for CrewAI-specific flow state data
    Phase 4: Comprehensive flow analytics and performance tracking
    """
    __tablename__ = "crewai_flow_state_extensions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    discovery_flow_id = Column(UUID(as_uuid=True), ForeignKey("discovery_flows.id", ondelete="CASCADE"), nullable=False, index=True)
    flow_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # CrewAI Flow persistence data
    flow_persistence_data = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    agent_collaboration_log = Column(JSONB, nullable=True, server_default=text("'[]'::jsonb"))
    memory_usage_metrics = Column(JSONB, nullable=True, server_default=text("'{}'::jsonb"))
    knowledge_base_analytics = Column(JSONB, nullable=True, server_default=text("'{}'::jsonb"))
    
    # Flow performance metrics
    phase_execution_times = Column(JSONB, nullable=True, server_default=text("'{}'::jsonb"))
    agent_performance_metrics = Column(JSONB, nullable=True, server_default=text("'{}'::jsonb"))
    crew_coordination_analytics = Column(JSONB, nullable=True, server_default=text("'{}'::jsonb"))
    
    # Learning and adaptation data
    learning_patterns = Column(JSONB, nullable=True, server_default=text("'[]'::jsonb"))
    user_feedback_history = Column(JSONB, nullable=True, server_default=text("'[]'::jsonb"))
    adaptation_metrics = Column(JSONB, nullable=True, server_default=text("'{}'::jsonb"))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Updated relationship to discovery_flows
    discovery_flow = relationship("DiscoveryFlow", back_populates="crewai_extensions")
    
    def __repr__(self):
        return f"<CrewAIFlowStateExtensions(discovery_flow_id={self.discovery_flow_id}, flow_id={self.flow_id})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "discovery_flow_id": str(self.discovery_flow_id),
            "flow_id": str(self.flow_id),
            "flow_persistence_data": self.flow_persistence_data or {},
            "agent_collaboration_log": self.agent_collaboration_log or [],
            "memory_usage_metrics": self.memory_usage_metrics or {},
            "knowledge_base_analytics": self.knowledge_base_analytics or {},
            "phase_execution_times": self.phase_execution_times or {},
            "agent_performance_metrics": self.agent_performance_metrics or {},
            "crew_coordination_analytics": self.crew_coordination_analytics or {},
            "learning_patterns": self.learning_patterns or [],
            "user_feedback_history": self.user_feedback_history or [],
            "adaptation_metrics": self.adaptation_metrics or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def add_agent_collaboration_entry(self, agent_name: str, action: str, details: dict):
        """Add entry to agent collaboration log"""
        if not self.agent_collaboration_log:
            self.agent_collaboration_log = []
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent_name,
            "action": action,
            "details": details
        }
        
        self.agent_collaboration_log.append(entry)
        
        # Keep only last 100 entries
        if len(self.agent_collaboration_log) > 100:
            self.agent_collaboration_log = self.agent_collaboration_log[-100:]
    
    def update_memory_usage_metrics(self, metrics: dict):
        """Update memory usage metrics"""
        if not self.memory_usage_metrics:
            self.memory_usage_metrics = {}
        
        self.memory_usage_metrics.update({
            "last_updated": datetime.now().isoformat(),
            **metrics
        })
    
    def add_learning_pattern(self, pattern_type: str, pattern_data: dict):
        """Add learning pattern"""
        if not self.learning_patterns:
            self.learning_patterns = []
        
        pattern = {
            "timestamp": datetime.now().isoformat(),
            "type": pattern_type,
            "data": pattern_data
        }
        
        self.learning_patterns.append(pattern)
        
        # Keep only last 50 patterns
        if len(self.learning_patterns) > 50:
            self.learning_patterns = self.learning_patterns[-50:]
    
    def add_user_feedback(self, feedback_type: str, feedback_data: dict):
        """Add user feedback to history"""
        if not self.user_feedback_history:
            self.user_feedback_history = []
        
        feedback = {
            "timestamp": datetime.now().isoformat(),
            "type": feedback_type,
            "data": feedback_data
        }
        
        self.user_feedback_history.append(feedback)
        
        # Keep only last 30 feedback entries
        if len(self.user_feedback_history) > 30:
            self.user_feedback_history = self.user_feedback_history[-30:]
    
    def update_phase_execution_time(self, phase: str, execution_time_ms: float):
        """Update phase execution time"""
        if not self.phase_execution_times:
            self.phase_execution_times = {}
        
        self.phase_execution_times[phase] = {
            "execution_time_ms": execution_time_ms,
            "completed_at": datetime.now().isoformat()
        }
    
    def get_performance_summary(self) -> dict:
        """Get comprehensive performance summary"""
        return {
            "total_phases": len(self.phase_execution_times or {}),
            "total_execution_time_ms": sum(
                phase.get("execution_time_ms", 0) 
                for phase in (self.phase_execution_times or {}).values()
            ),
            "agent_collaboration_entries": len(self.agent_collaboration_log or []),
            "learning_patterns_count": len(self.learning_patterns or []),
            "user_feedback_count": len(self.user_feedback_history or []),
            "memory_usage": self.memory_usage_metrics or {},
            "crew_coordination": self.crew_coordination_analytics or {}
        } 