"""
Learning Pattern Models

These models store learned patterns for field mapping, asset classification,
and other AI-driven insights using pgvector for similarity search.
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid

from app.core.database import Base


class MappingLearningPattern(Base):
    """
    Stores learned patterns for field mapping suggestions.
    Uses vector embeddings for similarity-based matching.
    """
    __tablename__ = "mapping_learning_patterns"
    __table_args__ = {'schema': 'migration'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_account_id = Column(String(255), nullable=False, index=True)
    engagement_id = Column(String(255), nullable=True, index=True)
    
    # Source field information
    source_field_name = Column(String(255), nullable=False)
    source_field_embedding = Column(Vector(1536), nullable=False)
    source_sample_values = Column(JSONB, nullable=True)  # Array of sample values
    source_sample_embedding = Column(Vector(1536), nullable=True)  # Embedding of sample values
    
    # Target field information
    target_field_name = Column(String(255), nullable=False)
    target_field_type = Column(String(100), nullable=True)
    
    # Pattern metadata
    pattern_context = Column(JSONB, nullable=True)  # Additional context about the mapping
    confidence_score = Column(Float, default=0.0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Learning metadata
    learned_from_user = Column(Boolean, default=True)  # True if from user feedback, False if synthetic
    learning_source = Column(String(100), nullable=True)  # 'user_feedback', 'synthetic', 'heuristic'
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255), nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index('idx_mapping_patterns_client_source', 'client_account_id', 'source_field_name'),
        Index('idx_mapping_patterns_target', 'target_field_name'),
        Index('idx_mapping_patterns_confidence', 'confidence_score'),
        Index('idx_mapping_patterns_embedding', 'source_field_embedding', postgresql_using='ivfflat'),
        {'schema': 'migration'}
    )


class AssetClassificationPattern(Base):
    """
    Stores learned patterns for automatic asset classification.
    Uses embeddings of asset names and metadata for pattern matching.
    """
    __tablename__ = "asset_classification_patterns"
    __table_args__ = {'schema': 'migration'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_account_id = Column(String(255), nullable=False, index=True)
    engagement_id = Column(String(255), nullable=True, index=True)
    
    # Pattern information
    pattern_name = Column(String(255), nullable=False)  # Human-readable pattern name
    pattern_type = Column(String(100), nullable=False)  # 'name_pattern', 'metadata_pattern', 'hybrid'
    
    # Asset name pattern
    asset_name_pattern = Column(String(500), nullable=True)  # Regex or text pattern
    asset_name_embedding = Column(Vector(1536), nullable=True)  # Embedding of name pattern
    
    # Metadata patterns
    metadata_patterns = Column(JSONB, nullable=True)  # Key-value patterns for metadata
    metadata_embedding = Column(Vector(1536), nullable=True)  # Embedding of metadata
    
    # Classification results
    predicted_asset_type = Column(String(100), nullable=False)
    predicted_application_type = Column(String(100), nullable=True)
    predicted_technology_stack = Column(JSONB, nullable=True)  # Array of technologies
    
    # Pattern performance
    confidence_score = Column(Float, default=0.0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    accuracy_rate = Column(Float, default=0.0)  # success_count / (success_count + failure_count)
    
    # Learning metadata
    learned_from_assets = Column(JSONB, nullable=True)  # Array of asset IDs this was learned from
    learning_source = Column(String(100), nullable=True)  # 'user_feedback', 'clustering', 'heuristic'
    last_applied_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255), nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index('idx_classification_patterns_client_type', 'client_account_id', 'pattern_type'),
        Index('idx_classification_patterns_asset_type', 'predicted_asset_type'),
        Index('idx_classification_patterns_confidence', 'confidence_score'),
        Index('idx_classification_patterns_name_embedding', 'asset_name_embedding', postgresql_using='ivfflat'),
        Index('idx_classification_patterns_metadata_embedding', 'metadata_embedding', postgresql_using='ivfflat'),
        {'schema': 'migration'}
    )


class ConfidenceThreshold(Base):
    """
    Stores dynamic confidence thresholds that adapt based on user feedback.
    Different thresholds for different operations and clients.
    """
    __tablename__ = "confidence_thresholds"
    __table_args__ = {'schema': 'migration'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_account_id = Column(String(255), nullable=False, index=True)
    engagement_id = Column(String(255), nullable=True, index=True)
    
    # Threshold configuration
    operation_type = Column(String(100), nullable=False)  # 'field_mapping', 'asset_classification', 'app_detection'
    threshold_name = Column(String(100), nullable=False)  # 'auto_apply', 'suggest', 'reject'
    threshold_value = Column(Float, nullable=False)
    
    # Adaptation metadata
    initial_value = Column(Float, nullable=False)  # Starting threshold value
    adjustment_count = Column(Integer, default=0)  # Number of times adjusted
    last_adjustment = Column(DateTime(timezone=True), nullable=True)
    
    # Performance tracking
    true_positives = Column(Integer, default=0)  # Correct applications above threshold
    false_positives = Column(Integer, default=0)  # Incorrect applications above threshold
    true_negatives = Column(Integer, default=0)  # Correct rejections below threshold
    false_negatives = Column(Integer, default=0)  # Incorrect rejections below threshold
    
    # Calculated metrics
    precision = Column(Float, default=0.0)  # TP / (TP + FP)
    recall = Column(Float, default=0.0)     # TP / (TP + FN)
    f1_score = Column(Float, default=0.0)   # 2 * (precision * recall) / (precision + recall)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255), nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index('idx_confidence_thresholds_client_operation', 'client_account_id', 'operation_type'),
        Index('idx_confidence_thresholds_operation_name', 'operation_type', 'threshold_name'),
        {'schema': 'migration'}
    )


class UserFeedbackEvent(Base):
    """
    Stores user feedback events for learning pattern improvement.
    Links user corrections to specific patterns for reinforcement learning.
    """
    __tablename__ = "user_feedback_events"
    __table_args__ = {'schema': 'migration'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_account_id = Column(String(255), nullable=False, index=True)
    engagement_id = Column(String(255), nullable=True, index=True)
    
    # Feedback context
    feedback_type = Column(String(100), nullable=False)  # 'field_mapping', 'asset_classification', 'app_detection'
    operation_id = Column(String(255), nullable=True)  # ID of the operation being corrected
    
    # Original suggestion
    original_suggestion = Column(JSONB, nullable=False)  # What the AI suggested
    original_confidence = Column(Float, nullable=True)   # Confidence of original suggestion
    
    # User correction
    user_correction = Column(JSONB, nullable=False)      # What the user corrected it to
    correction_type = Column(String(100), nullable=False)  # 'accept', 'reject', 'modify'
    
    # Pattern references
    related_patterns = Column(JSONB, nullable=True)      # Array of pattern IDs that influenced the suggestion
    
    # Learning impact
    pattern_updates_applied = Column(Boolean, default=False)  # Whether this feedback has been processed
    threshold_updates_applied = Column(Boolean, default=False)  # Whether thresholds were updated
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255), nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index('idx_feedback_events_client_type', 'client_account_id', 'feedback_type'),
        Index('idx_feedback_events_operation', 'operation_id'),
        Index('idx_feedback_events_created', 'created_at'),
        {'schema': 'migration'}
    )


class LearningStatistics(Base):
    """
    Aggregated statistics about learning performance for monitoring and analytics.
    """
    __tablename__ = "learning_statistics"
    __table_args__ = {'schema': 'migration'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_account_id = Column(String(255), nullable=False, index=True)
    engagement_id = Column(String(255), nullable=True, index=True)
    
    # Statistics scope
    statistic_type = Column(String(100), nullable=False)  # 'field_mapping', 'asset_classification', 'overall'
    time_period = Column(String(50), nullable=False)     # 'daily', 'weekly', 'monthly'
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Performance metrics
    total_operations = Column(Integer, default=0)
    successful_operations = Column(Integer, default=0)
    failed_operations = Column(Integer, default=0)
    user_corrections = Column(Integer, default=0)
    
    # Accuracy metrics
    accuracy_rate = Column(Float, default=0.0)
    improvement_rate = Column(Float, default=0.0)  # Compared to previous period
    
    # Pattern metrics
    patterns_created = Column(Integer, default=0)
    patterns_updated = Column(Integer, default=0)
    patterns_retired = Column(Integer, default=0)
    
    # Confidence metrics
    average_confidence = Column(Float, default=0.0)
    threshold_adjustments = Column(Integer, default=0)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes for performance
    __table_args__ = (
        Index('idx_learning_stats_client_type_period', 'client_account_id', 'statistic_type', 'time_period'),
        Index('idx_learning_stats_period_start', 'period_start'),
        {'schema': 'migration'}
    ) 