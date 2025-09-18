"""
Serialization Mixin for CrewAI Flow State Extensions

This mixin handles the to_dict() method and other serialization-related
functionality for API responses.
"""


class SerializationMixin:
    """Mixin for serialization and API response functionality."""

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
            "execution_metadata": self.execution_metadata or {},
            "learning_patterns": self.learning_patterns or [],
            "user_feedback_history": self.user_feedback_history or [],
            "adaptation_metrics": self.adaptation_metrics or {},
            "phase_transitions": self.phase_transitions or [],
            "error_history": self.error_history or [],
            "retry_count": self.retry_count,
            "parent_flow_id": str(self.parent_flow_id) if self.parent_flow_id else None,
            "child_flow_ids": self.child_flow_ids or [],
            "flow_metadata": self.flow_metadata or {},
            "collection_flow_id": (
                str(self.collection_flow_id) if self.collection_flow_id else None
            ),
            "automation_tier": self.automation_tier,
            "collection_quality_score": self.collection_quality_score,
            "data_collection_metadata": self.data_collection_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
