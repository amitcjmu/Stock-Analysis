"""CrewAI Flow State Extensions Model

Extended table for CrewAI-specific flow state data including persistence,
performance metrics, learning patterns, and resumption support.
"""
from sqlalchemy import Column, String, UUID, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class CrewAIFlowStateExtensions(Base):
    """Extended CrewAI-specific flow state data."""
    
    __tablename__ = "crewai_flow_state_extensions"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    workflow_state_id = Column(UUID(as_uuid=True), ForeignKey('workflow_states.id', ondelete='CASCADE'), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # Denormalized for easier queries
    flow_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # CrewAI Flow persistence data
    flow_persistence_data = Column(JSONB, nullable=False, default={})  # CrewAI Flow @persist() decorator data
    agent_collaboration_log = Column(JSONB, nullable=False, default=[])  # Log of agent interactions
    memory_usage_metrics = Column(JSONB, nullable=False, default={})  # Memory usage tracking
    knowledge_base_analytics = Column(JSONB, nullable=False, default={})  # KB usage metrics
    
    # Flow performance metrics
    phase_execution_times = Column(JSONB, nullable=False, default={})  # Execution time per phase
    agent_performance_metrics = Column(JSONB, nullable=False, default={})  # Individual agent performance
    crew_coordination_analytics = Column(JSONB, nullable=False, default={})  # Crew coordination metrics
    
    # Learning and adaptation data
    learning_patterns = Column(JSONB, nullable=False, default=[])  # Patterns learned during execution
    user_feedback_history = Column(JSONB, nullable=False, default=[])  # User feedback and corrections
    adaptation_metrics = Column(JSONB, nullable=False, default={})  # Flow adaptation based on feedback
    
    # Flow resumption support
    resumption_checkpoints = Column(JSONB, nullable=False, default=[])  # Checkpoints for resumption
    state_snapshots = Column(JSONB, nullable=False, default=[])  # Periodic state snapshots
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now(), index=True)
    
    # Relationship to workflow_states
    workflow_state = relationship("WorkflowState", back_populates="crewai_extensions", foreign_keys=[workflow_state_id])
    
    def __repr__(self):
        return f"<CrewAIFlowStateExtensions(id={self.id}, session_id={self.session_id}, flow_id={self.flow_id})>"
    
    @property
    def flow_analytics_summary(self) -> dict:
        """Get a summary of flow analytics and performance."""
        return {
            "session_id": str(self.session_id),
            "flow_id": str(self.flow_id),
            "performance_summary": {
                "total_phases": len(self.phase_execution_times) if self.phase_execution_times else 0,
                "total_agents": len(self.agent_performance_metrics) if self.agent_performance_metrics else 0,
                "collaboration_events": len(self.agent_collaboration_log) if self.agent_collaboration_log else 0,
                "learning_patterns_count": len(self.learning_patterns) if self.learning_patterns else 0,
                "feedback_count": len(self.user_feedback_history) if self.user_feedback_history else 0,
                "checkpoints_count": len(self.resumption_checkpoints) if self.resumption_checkpoints else 0
            },
            "memory_usage": self.memory_usage_metrics,
            "knowledge_base_usage": self.knowledge_base_analytics,
            "last_updated": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def add_collaboration_event(self, event: dict):
        """Add a new agent collaboration event."""
        if not self.agent_collaboration_log:
            self.agent_collaboration_log = []
        
        event_with_timestamp = {
            **event,
            "timestamp": func.now().isoformat(),
            "event_id": len(self.agent_collaboration_log) + 1
        }
        self.agent_collaboration_log.append(event_with_timestamp)
    
    def add_learning_pattern(self, pattern: dict):
        """Add a new learning pattern discovered during execution."""
        if not self.learning_patterns:
            self.learning_patterns = []
        
        pattern_with_metadata = {
            **pattern,
            "discovered_at": func.now().isoformat(),
            "pattern_id": len(self.learning_patterns) + 1
        }
        self.learning_patterns.append(pattern_with_metadata)
    
    def add_user_feedback(self, feedback: dict):
        """Add user feedback to the history."""
        if not self.user_feedback_history:
            self.user_feedback_history = []
        
        feedback_with_metadata = {
            **feedback,
            "received_at": func.now().isoformat(),
            "feedback_id": len(self.user_feedback_history) + 1
        }
        self.user_feedback_history.append(feedback_with_metadata)
    
    def create_resumption_checkpoint(self, checkpoint_data: dict):
        """Create a new resumption checkpoint."""
        if not self.resumption_checkpoints:
            self.resumption_checkpoints = []
        
        checkpoint = {
            **checkpoint_data,
            "checkpoint_id": len(self.resumption_checkpoints) + 1,
            "created_at": func.now().isoformat(),
            "checkpoint_type": checkpoint_data.get("type", "manual")
        }
        self.resumption_checkpoints.append(checkpoint)
    
    def get_latest_checkpoint(self) -> dict:
        """Get the most recent resumption checkpoint."""
        if not self.resumption_checkpoints:
            return {}
        
        return max(self.resumption_checkpoints, key=lambda x: x.get("created_at", ""))
    
    @classmethod
    def create_for_flow(
        cls,
        workflow_state_id: str,
        session_id: str,
        flow_id: str,
        initial_persistence_data: dict = None
    ) -> 'CrewAIFlowStateExtensions':
        """Create a new extensions record for a flow."""
        return cls(
            workflow_state_id=workflow_state_id,
            session_id=session_id,
            flow_id=flow_id,
            flow_persistence_data=initial_persistence_data or {}
        ) 