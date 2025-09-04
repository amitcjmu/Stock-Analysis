"""
Core Data Import Models
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from app.core.database import Base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base

    Base = declarative_base()


class DataImport(Base):
    """
    Tracks a data import job, including its source, status, and metadata.
    This table serves as the central hub for any data brought into the system.
    """

    __tablename__ = "data_imports"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        comment="Unique identifier for the data import job.",
    )
    client_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("client_accounts.id", ondelete="CASCADE"),
        nullable=True,
        comment="The client account this import belongs to.",
    )
    engagement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("engagements.id", ondelete="CASCADE"),
        nullable=True,
        comment="The engagement this import is associated with.",
    )
    master_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crewai_flow_state_extensions.flow_id", ondelete="CASCADE"),
        nullable=True,
        comment="The master flow ID that was initiated by this data import.",
    )

    import_name = Column(
        String(255),
        nullable=False,
        comment="A user-defined name for the import job for easy identification.",
    )
    import_type = Column(
        String(50),
        nullable=False,
        comment="The type of data being imported (e.g., 'cmdb', 'asset_inventory').",
    )
    description = Column(
        Text,
        nullable=True,
        comment="A detailed description of the data import's purpose or contents.",
    )

    # File metadata (consolidated field names)
    filename = Column(
        String(255), nullable=False, comment="The original name of the imported file."
    )
    file_size = Column(
        Integer, nullable=True, comment="The size of the imported file in bytes."
    )
    mime_type = Column(
        String(100),
        nullable=True,
        comment="The MIME type of the imported file (e.g., 'text/csv').",
    )
    source_system = Column(
        String(100),
        nullable=True,
        comment="The system from which the data was exported (e.g., 'ServiceNow', 'Jira').",
    )

    # Job status and progress
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="The current status of the import job (e.g., 'pending', 'processing', 'completed', 'failed').",
    )
    progress_percentage = Column(
        Float, default=0.0, comment="The completion percentage of the import job."
    )
    total_records = Column(
        Integer,
        nullable=True,
        comment="The total number of records detected in the source file.",
    )
    processed_records = Column(
        Integer,
        default=0,
        comment="The number of records successfully processed so far.",
    )
    failed_records = Column(
        Integer, default=0, comment="The number of records that failed processing."
    )

    # Configuration and user info
    imported_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="The user ID of the person who initiated the import.",
    )

    # Error handling (new fields)
    error_message = Column(
        Text, nullable=True, comment="A summary of the error if the import job failed."
    )
    error_details = Column(
        JSON,
        nullable=True,
        comment="A JSON blob containing detailed error information, such as stack traces.",
    )

    # Timestamps
    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp when the import job processing began.",
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the import job finished (either completed or failed).",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp when the import record was created.",
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        comment="Timestamp of the last update to this record.",
    )

    # Relationships
    raw_records = relationship(
        "RawImportRecord", back_populates="data_import", cascade="all, delete-orphan"
    )
    field_mappings = relationship(
        "ImportFieldMapping", back_populates="data_import", cascade="all, delete-orphan"
    )
    discovery_flows = relationship("DiscoveryFlow", back_populates="data_import")

    # Master flow relationship
    master_flow = relationship(
        "CrewAIFlowStateExtensions",
        foreign_keys=[master_flow_id],
        primaryjoin="DataImport.master_flow_id == CrewAIFlowStateExtensions.flow_id",
        back_populates="data_imports",
    )

    user = relationship("User")
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")

    __table_args__ = (
        {
            "schema": "migration",
            "comment": "Tracks data import jobs, their status, and metadata within a multi-tenant environment.",
        },
    )


class RawImportRecord(Base):
    """
    Stores a single, unaltered row of data as it was imported from a source file.
    This provides an audit trail and allows for reprocessing without re-uploading.
    """

    __tablename__ = "raw_import_records"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        comment="Unique identifier for the raw record.",
    )
    data_import_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.data_imports.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to the parent data import job.",
    )

    # Context IDs for direct querying
    client_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("client_accounts.id"),
        nullable=True,
        comment="Denormalized client account ID for efficient multi-tenant queries.",
    )
    engagement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("engagements.id"),
        nullable=True,
        comment="Denormalized engagement ID for efficient scoping.",
    )
    master_flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crewai_flow_state_extensions.flow_id", ondelete="CASCADE"),
        nullable=True,
        comment="Denormalized master flow ID for linking records to a flow.",
    )

    row_number = Column(
        Integer, nullable=False, comment="The original row number from the source file."
    )
    raw_data = Column(
        JSON,
        nullable=False,
        comment="The original, unaltered data for this row, stored as a JSON object.",
    )
    cleansed_data = Column(
        JSON,
        nullable=True,
        comment="The data after initial cleansing and type casting, before full processing.",
    )

    # Validation and processing status
    validation_errors = Column(
        JSON,
        nullable=True,
        comment="A JSON array of validation errors found for this record.",
    )
    processing_notes = Column(
        Text,
        nullable=True,
        comment="Any notes or warnings generated during the processing of this record.",
    )

    # Status tracking
    is_processed = Column(
        Boolean,
        default=False,
        comment="Flag indicating if this record has been successfully processed and transformed.",
    )
    is_valid = Column(
        Boolean,
        default=True,
        comment="Flag indicating if the raw data passed initial validation checks.",
    )
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assets.id"),
        comment="If an asset is created from this record, this links to it.",
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp when the raw record was created.",
    )
    processed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the record was successfully processed.",
    )

    # Relationships
    data_import = relationship("DataImport", back_populates="raw_records")

    # Master flow relationship
    master_flow = relationship(
        "CrewAIFlowStateExtensions",
        foreign_keys=[master_flow_id],
        primaryjoin="RawImportRecord.master_flow_id == CrewAIFlowStateExtensions.flow_id",
        back_populates="raw_import_records",
    )

    __table_args__ = (
        {
            "schema": "migration",
            "comment": "Stores individual raw data records from imported files before transformation and loading.",
        },
    )


class ImportProcessingStep(Base):
    """
    Logs the execution of a single step within a larger data import pipeline.
    This is used for detailed observability and debugging of import workflows.
    """

    __tablename__ = "import_processing_steps"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        comment="Unique identifier for the processing step log.",
    )
    data_import_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.data_imports.id", ondelete="CASCADE"),
        nullable=False,
        comment="Foreign key to the parent data import job.",
    )

    step_name = Column(
        String(100),
        nullable=False,
        comment="The name of the processing step (e.g., 'validation', 'field_mapping').",
    )
    step_order = Column(
        Integer,
        nullable=False,
        comment="The sequential order of this step in the workflow.",
    )
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        comment="The execution status of this step (e.g., 'pending', 'running', 'completed', 'failed').",
    )

    description = Column(
        Text, nullable=True, comment="A description of what this processing step does."
    )
    input_data = Column(
        JSON,
        nullable=True,
        comment="A snapshot of the input data for this step, for debugging.",
    )
    output_data = Column(
        JSON,
        nullable=True,
        comment="A snapshot of the output data from this step, for debugging.",
    )
    error_details = Column(
        JSON,
        nullable=True,
        comment="A JSON blob containing detailed error information if the step failed.",
    )

    records_processed = Column(
        Integer, nullable=True, comment="The number of records processed in this step."
    )
    duration_seconds = Column(
        Float, nullable=True, comment="The duration of this step in seconds."
    )

    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp when this step started execution.",
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when this step completed or failed.",
    )

    data_import = relationship("DataImport")

    __table_args__ = (
        {
            "schema": "migration",
            "comment": "Tracks the execution and outcome of individual steps in a data import workflow.",
        },
    )
