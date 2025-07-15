"""
CrewAI Flow State Extensions Model
Phase 4: Advanced CrewAI Flow analytics and performance tracking
Extended table for CrewAI-specific flow state data and metrics
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, func, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text
import uuid
from datetime import datetime
from typing import Optional, Any

from app.core.database import Base

class CrewAIFlowStateExtensions(Base):
    """
    Acts as the master record for all CrewAI-driven workflows (flows).
    This table is the central hub for coordinating Discovery, Assessment, and other
    multi-step processes. It stores state, metadata, performance metrics, and
    learning artifacts for each flow.
    """
    __tablename__ = "crewai_flow_state_extensions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="Internal primary key for the database record.")
    # Primary flow identifier - CrewAI Flow ID
    flow_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True, comment="The unique identifier for a specific CrewAI flow instance. This is the main public ID.")
    
    # Multi-tenant isolation
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="Foreign key to the client account this flow belongs to.")
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="Foreign key to the engagement this flow is part of.")
    user_id = Column(String(255), nullable=False, comment="The user ID of the person who initiated the flow.")
    
    # Flow metadata
    flow_type = Column(String(50), nullable=False, comment="The type of the flow (e.g., 'discovery', 'assessment', 'planning').")
    flow_name = Column(String(255), nullable=True, comment="A user-friendly name for this flow instance.")
    flow_status = Column(String(50), nullable=False, default="initialized", comment="The current status of the flow (e.g., 'running', 'paused', 'completed', 'failed').")
    flow_configuration = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment="The initial configuration and parameters the flow was started with.")
    
    # CrewAI Flow persistence data
    flow_persistence_data = Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), comment="A JSON blob containing the complete state of the flow, allowing it to be paused and resumed.")
    agent_collaboration_log = Column(JSONB, nullable=True, server_default=text("'[]'::jsonb"), comment="A log of significant interactions between agents within the crew.")
    memory_usage_metrics = Column(JSONB, nullable=True, server_default=text("'{}'::jsonb"), comment="Metrics related to the memory consumption of the agents and tools.")
    knowledge_base_analytics = Column(JSONB, nullable=True, server_default=text("'{}'::jsonb"), comment="Analytics on how the knowledge base was accessed and utilized during the flow.")
    
    # Flow performance metrics
    phase_execution_times = Column(JSONB, nullable=True, server_default=text("'{}'::jsonb"), comment="A JSON object storing the execution time for each phase of the flow.")
    agent_performance_metrics = Column(JSONB, nullable=True, server_default=text("'{}'::jsonb"), comment="Performance metrics for individual agents, such as task completion time and token usage.")
    crew_coordination_analytics = Column(JSONB, nullable=True, server_default=text("'{}'::jsonb"), comment="Analytics on the overall coordination and efficiency of the crew.")
    
    # Learning and adaptation data
    learning_patterns = Column(JSONB, nullable=True, server_default=text("'[]'::jsonb"), comment="Patterns and insights learned by the agents during the flow execution.")
    user_feedback_history = Column(JSONB, nullable=True, server_default=text("'[]'::jsonb"), comment="A log of feedback provided by users at various stages of the flow.")
    adaptation_metrics = Column(JSONB, nullable=True, server_default=text("'{}'::jsonb"), comment="Metrics that track how the crew adapts its behavior based on feedback and learning.")
    
    # Master Flow Orchestrator fields (added in Phase 2)
    phase_transitions = Column(JSONB, nullable=True, server_default=text("'[]'::jsonb"), comment="An audit log of all phase transitions (e.g., from 'data_cleansing' to 'asset_inventory').")
    error_history = Column(JSONB, nullable=True, server_default=text("'[]'::jsonb"), comment="A log of all errors that occurred during the flow execution.")
    retry_count = Column(Integer, nullable=False, server_default='0', comment="The number of times the flow or a specific phase has been retried after a failure.")
    parent_flow_id = Column(UUID(as_uuid=True), ForeignKey('crewai_flow_state_extensions.flow_id', ondelete='SET NULL'), nullable=True, comment="If this is a sub-flow, this links to the parent flow's ID.")
    child_flow_ids = Column(JSONB, nullable=True, server_default=text("'[]'::jsonb"), comment="A list of flow IDs for any sub-flows spawned by this flow.")
    flow_metadata = Column(JSONB, nullable=True, server_default=text("'{}'::jsonb"), comment="A flexible JSON blob for storing any other metadata related to the flow.")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Timestamp when the flow record was created.")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="Timestamp of the last update to this flow record.")
    
    # Relationships - This is the master table, so subordinate tables reference it
    # Note: Subordinate flow tables (discovery_flows, assessment_flows, etc.) 
    # should have master_flow_id foreign keys pointing to this table's flow_id
    
    # Child flow relationships (referencing this table's flow_id)
    discovery_flows = relationship("DiscoveryFlow", foreign_keys="DiscoveryFlow.master_flow_id", 
                                 primaryjoin="CrewAIFlowStateExtensions.flow_id == DiscoveryFlow.master_flow_id",
                                 back_populates="master_flow", cascade="all, delete-orphan")
    
    data_imports = relationship("DataImport", foreign_keys="DataImport.master_flow_id",
                               primaryjoin="CrewAIFlowStateExtensions.flow_id == DataImport.master_flow_id",
                               back_populates="master_flow", cascade="all, delete-orphan")
    
    raw_import_records = relationship("RawImportRecord", foreign_keys="RawImportRecord.master_flow_id",
                                    primaryjoin="CrewAIFlowStateExtensions.flow_id == RawImportRecord.master_flow_id",
                                    back_populates="master_flow", cascade="all, delete-orphan")
    
    # Parent-child flow relationships (hierarchical flows)
    parent_flow = relationship("CrewAIFlowStateExtensions", remote_side=[flow_id], 
                              foreign_keys=[parent_flow_id], back_populates="child_flows")
    child_flows = relationship("CrewAIFlowStateExtensions", back_populates="parent_flow")
    
    def __repr__(self):
        return f"<CrewAIFlowStateExtensions(flow_id={self.flow_id}, flow_type={self.flow_type}, status={self.flow_status})>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "flow_id": str(self.flow_id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "user_id": self.user_id,
            "flow_type": self.flow_type,
            "flow_name": self.flow_name,
            "flow_status": self.flow_status,
            "flow_configuration": self.flow_configuration or {},
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
            "phase_transitions": self.phase_transitions or [],
            "error_history": self.error_history or [],
            "retry_count": self.retry_count,
            "parent_flow_id": str(self.parent_flow_id) if self.parent_flow_id else None,
            "child_flow_ids": self.child_flow_ids or [],
            "flow_metadata": self.flow_metadata or {},
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
            "crew_coordination": self.crew_coordination_analytics or {},
            "phase_transitions_count": len(self.phase_transitions or []),
            "error_count": len(self.error_history or []),
            "retry_count": self.retry_count
        }
    
    def add_phase_transition(self, phase: str, status: str, metadata: dict = None):
        """Add a phase transition record"""
        if not self.phase_transitions:
            self.phase_transitions = []
        
        transition = {
            "phase": phase,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.phase_transitions.append(transition)
    
    def add_error(self, phase: str, error: str, details: dict = None):
        """Add an error to the error history"""
        if not self.error_history:
            self.error_history = []
        
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "error": error,
            "details": details or {},
            "retry_count": self.retry_count
        }
        
        self.error_history.append(error_entry)
        
        # Keep only last 100 errors
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
    
    def add_child_flow(self, child_flow_id: str):
        """Add a child flow ID"""
        if not self.child_flow_ids:
            self.child_flow_ids = []
        
        if child_flow_id not in self.child_flow_ids:
            self.child_flow_ids.append(child_flow_id)
    
    def remove_child_flow(self, child_flow_id: str):
        """Remove a child flow ID"""
        if self.child_flow_ids and child_flow_id in self.child_flow_ids:
            self.child_flow_ids.remove(child_flow_id)
    
    def update_flow_metadata(self, key: str, value: Any):
        """Update a specific key in flow metadata"""
        if not self.flow_metadata:
            self.flow_metadata = {}
        
        self.flow_metadata[key] = value
    
    def get_current_phase(self) -> Optional[str]:
        """Get the current active phase from transitions"""
        if not self.phase_transitions:
            return None
        
        # Find the last active/processing phase
        for transition in reversed(self.phase_transitions):
            if transition.get('status') in ['active', 'processing']:
                return transition.get('phase')
        
        # If no active phase, return the last phase
        if self.phase_transitions:
            return self.phase_transitions[-1].get('phase')
        
        return None 