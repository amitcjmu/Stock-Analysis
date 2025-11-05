"""
CrewAI Flow State Extensions Model
Phase 4: Advanced CrewAI Flow analytics and performance tracking
Extended table for CrewAI-specific flow state data and metrics
"""

import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text

from app.core.database import Base
from .collaboration_mixin import CollaborationMixin
from .flow_management_mixin import FlowManagementMixin
from .performance_mixin import PerformanceMixin
from .serialization_mixin import SerializationMixin


class CrewAIFlowStateExtensions(
    Base, CollaborationMixin, FlowManagementMixin, PerformanceMixin, SerializationMixin
):
    """
    Acts as the master record for all CrewAI-driven workflows (flows).
    This table is the central hub for coordinating Discovery, Assessment, and other
    multi-step processes. It stores state, metadata, performance metrics, and
    learning artifacts for each flow.
    """

    __tablename__ = "crewai_flow_state_extensions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Internal primary key for the database record.",
    )
    # Primary flow identifier - CrewAI Flow ID
    flow_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True,
        comment="The unique identifier for a specific CrewAI flow instance. This is the main public ID.",
    )

    # Multi-tenant isolation
    client_account_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Foreign key to the client account this flow belongs to.",
    )
    engagement_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Foreign key to the engagement this flow is part of.",
    )
    user_id = Column(
        String(255),
        nullable=False,
        comment="The user ID of the person who initiated the flow.",
    )

    # Flow metadata
    flow_type = Column(
        String(50),
        nullable=False,
        comment="The type of the flow (e.g., 'discovery', 'assessment', 'planning').",
    )
    flow_name = Column(
        String(255),
        nullable=True,
        comment="A user-friendly name for this flow instance.",
    )
    flow_status = Column(
        String(50),
        nullable=False,
        default="initialized",
        comment="The current status of the flow (e.g., 'running', 'paused', 'completed', 'failed').",
    )
    flow_configuration = Column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="The initial configuration and parameters the flow was started with.",
    )

    # CrewAI Flow persistence data
    flow_persistence_data = Column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="A JSON blob containing the complete state of the flow, allowing it to be paused and resumed.",
    )
    agent_collaboration_log = Column(
        JSONB,
        nullable=True,
        server_default=text("'[]'::jsonb"),
        comment="A log of significant interactions between agents within the crew.",
    )
    memory_usage_metrics = Column(
        JSONB,
        nullable=True,
        server_default=text("'{}'::jsonb"),
        comment="Metrics related to the memory consumption of the agents and tools.",
    )
    knowledge_base_analytics = Column(
        JSONB,
        nullable=True,
        server_default=text("'{}'::jsonb"),
        comment="Analytics on how the knowledge base was accessed and utilized during the flow.",
    )

    # Flow performance metrics
    phase_execution_times = Column(
        JSONB,
        nullable=True,
        server_default=text("'{}'::jsonb"),
        comment="A JSON object storing the execution time for each phase of the flow.",
    )
    agent_performance_metrics = Column(
        JSONB,
        nullable=True,
        server_default=text("'{}'::jsonb"),
        comment="Performance metrics for individual agents, such as task completion time and token usage.",
    )
    crew_coordination_analytics = Column(
        JSONB,
        nullable=True,
        server_default=text("'{}'::jsonb"),
        comment="Analytics on the overall coordination and efficiency of the crew.",
    )

    # Execution metadata for flow processing
    execution_metadata = Column(
        JSONB,
        nullable=True,
        server_default=text("'{}'::jsonb"),
        comment="Metadata about the execution of the flow, including timing, agents used, and performance metrics.",
    )

    # Learning and adaptation data
    learning_patterns = Column(
        JSONB,
        nullable=True,
        server_default=text("'[]'::jsonb"),
        comment="Patterns and insights learned by the agents during the flow execution.",
    )
    user_feedback_history = Column(
        JSONB,
        nullable=True,
        server_default=text("'[]'::jsonb"),
        comment="A log of feedback provided by users at various stages of the flow.",
    )
    adaptation_metrics = Column(
        JSONB,
        nullable=True,
        server_default=text("'{}'::jsonb"),
        comment="Metrics that track how the crew adapts its behavior based on feedback and learning.",
    )

    # Master Flow Orchestrator fields (added in Phase 2)
    phase_transitions = Column(
        JSONB,
        nullable=True,
        server_default=text("'[]'::jsonb"),
        comment="An audit log of all phase transitions (e.g., from 'data_cleansing' to 'asset_inventory').",
    )
    error_history = Column(
        JSONB,
        nullable=True,
        server_default=text("'[]'::jsonb"),
        comment="A log of all errors that occurred during the flow execution.",
    )
    retry_count = Column(
        Integer,
        nullable=False,
        server_default="0",
        comment="The number of times the flow or a specific phase has been retried after a failure.",
    )
    parent_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crewai_flow_state_extensions.flow_id", ondelete="SET NULL"),
        nullable=True,
        comment="If this is a sub-flow, this links to the parent flow's ID.",
    )
    child_flow_ids = Column(
        JSONB,
        nullable=True,
        server_default=text("'[]'::jsonb"),
        comment="A list of flow IDs for any sub-flows spawned by this flow.",
    )
    flow_metadata = Column(
        JSONB,
        nullable=True,
        server_default=text("'{}'::jsonb"),
        comment="A flexible JSON blob for storing any other metadata related to the flow.",
    )

    # Collection flow integration fields
    collection_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("collection_flows.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to associated collection flow if this is a collection-enabled flow.",
    )
    automation_tier = Column(
        String(50),
        nullable=True,
        comment="Automation tier for this flow (e.g., 'basic', 'advanced', 'full').",
    )
    collection_quality_score = Column(
        Float,
        nullable=True,
        comment="Quality score for data collection activities in this flow.",
    )
    data_collection_metadata = Column(
        JSONB,
        nullable=True,
        server_default=text("'{}'::jsonb"),
        comment="Metadata about data collection activities and quality metrics.",
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp when the flow record was created.",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Timestamp of the last update to this flow record.",
    )

    # Relationships - This is the master table, so subordinate tables reference it
    # Note: Subordinate flow tables (discovery_flows, assessment_flows, etc.)
    # should have master_flow_id foreign keys pointing to this table's flow_id

    # Child flow relationships (referencing this table's flow_id)
    discovery_flows = relationship(
        "DiscoveryFlow",
        foreign_keys="DiscoveryFlow.master_flow_id",
        primaryjoin="CrewAIFlowStateExtensions.flow_id == DiscoveryFlow.master_flow_id",
        back_populates="master_flow",
        cascade="all, delete-orphan",
    )

    assessment_flows = relationship(
        "AssessmentFlow",
        foreign_keys="AssessmentFlow.master_flow_id",
        primaryjoin="CrewAIFlowStateExtensions.flow_id == AssessmentFlow.master_flow_id",
        back_populates="master_flow",
        cascade="all, delete-orphan",
    )

    data_imports = relationship(
        "DataImport",
        foreign_keys="DataImport.master_flow_id",
        primaryjoin="CrewAIFlowStateExtensions.flow_id == DataImport.master_flow_id",
        back_populates="master_flow",
        cascade="all, delete-orphan",
    )

    raw_import_records = relationship(
        "RawImportRecord",
        foreign_keys="RawImportRecord.master_flow_id",
        primaryjoin="CrewAIFlowStateExtensions.flow_id == RawImportRecord.master_flow_id",
        back_populates="master_flow",
        cascade="all, delete-orphan",
    )

    # Collection flow relationship (one-to-one with collection_flows)
    collection_flow = relationship(
        "CollectionFlow",
        foreign_keys="CollectionFlow.master_flow_id",
        primaryjoin="CrewAIFlowStateExtensions.flow_id == CollectionFlow.master_flow_id",
        back_populates="master_flow",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Planning flow relationship (added in migration 112)
    planning_flows = relationship(
        "PlanningFlow",
        foreign_keys="PlanningFlow.master_flow_id",
        primaryjoin="CrewAIFlowStateExtensions.flow_id == PlanningFlow.master_flow_id",
        back_populates="master_flow",
        cascade="all, delete-orphan",
    )

    # Decommission flow relationship (added in migration 120)
    decommission_flows = relationship(
        "DecommissionFlow",
        foreign_keys="DecommissionFlow.master_flow_id",
        primaryjoin="CrewAIFlowStateExtensions.flow_id == DecommissionFlow.master_flow_id",
        back_populates="master_flow",
        cascade="all, delete-orphan",
    )

    # Parent-child flow relationships (hierarchical flows)
    parent_flow = relationship(
        "CrewAIFlowStateExtensions",
        remote_side=[flow_id],
        foreign_keys=[parent_flow_id],
        back_populates="child_flows",
    )
    child_flows = relationship(
        "CrewAIFlowStateExtensions", back_populates="parent_flow"
    )

    def __repr__(self):
        return (
            f"<CrewAIFlowStateExtensions(flow_id={self.flow_id}, flow_type={self.flow_type}, "
            f"status={self.flow_status})>"
        )
