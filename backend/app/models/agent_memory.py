"""
Agent Memory Models - Tier 3 Memory for Agent-Discovered Patterns

This module provides the data models for agent-discovered patterns that form
the Tier 3 (long-term semantic) memory in our three-tiered memory architecture.

Tier 1: Conversational (handled by CrewAI LongTermMemory)
Tier 2: Episodic (handled by ChromaDB/vector storage)  
Tier 3: Semantic Patterns (this module - agent_discovered_patterns table)
"""

import uuid
import enum
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, ForeignKey
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func
    from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Column = Integer = String = DateTime = Text = JSON = Float = ForeignKey = object
    def relationship(*args, **kwargs):
        return None
    class func:
        @staticmethod
        def now():
            return None

try:
    from app.core.database import Base
except ImportError:
    Base = object


class PatternType(str, enum.Enum):
    """Types of patterns that agents can discover"""
    # Asset patterns
    ASSET_CATEGORIZATION = "asset_categorization"
    BUSINESS_VALUE_INDICATOR = "business_value_indicator"
    RISK_FACTOR = "risk_factor"
    MODERNIZATION_OPPORTUNITY = "modernization_opportunity"
    
    # Relationship patterns
    DEPENDENCY_PATTERN = "dependency_pattern"
    USAGE_PATTERN = "usage_pattern"
    INTEGRATION_PATTERN = "integration_pattern"
    
    # Migration patterns
    MIGRATION_STRATEGY_INDICATOR = "migration_strategy_indicator"
    CLOUD_READINESS_FACTOR = "cloud_readiness_factor"
    COMPLEXITY_INDICATOR = "complexity_indicator"
    
    # Cross-cutting patterns
    NAMING_CONVENTION = "naming_convention"
    ARCHITECTURE_PATTERN = "architecture_pattern"
    TECHNOLOGY_CORRELATION = "technology_correlation"


class ValidationStatus(str, enum.Enum):
    """Pattern validation status"""
    PENDING = "pending"        # Awaiting human validation
    VALIDATED = "validated"    # Human confirmed pattern is correct
    REJECTED = "rejected"      # Human rejected pattern as incorrect
    SUPERSEDED = "superseded"  # Replaced by newer, better pattern


class AgentDiscoveredPattern(Base):
    """
    Tier 3 Memory: Agent-discovered semantic patterns for long-term learning
    
    This table stores patterns that agents discover during asset analysis,
    enabling them to learn and apply insights across engagements while
    maintaining multi-tenant isolation.
    """
    
    __tablename__ = "agent_discovered_patterns"
    
    # Primary Key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Multi-tenant isolation
    client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    engagement_id = Column(PostgresUUID(as_uuid=True), ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Pattern identification
    pattern_type = Column(String(50), nullable=False, index=True)
    pattern_name = Column(String(200), nullable=False)
    pattern_description = Column(Text)
    
    # Pattern content and confidence
    pattern_data = Column(JSON, nullable=False)  # The actual pattern logic/rules discovered
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    evidence_count = Column(Integer, nullable=False, default=1)  # Number of examples that support this pattern
    
    # Agent and discovery metadata
    discovered_by_agent = Column(String(100), nullable=False)  # Agent role/name that discovered pattern
    discovery_context = Column(JSON)  # Context when pattern was discovered (flow_id, asset_ids, etc.)
    flow_id = Column(PostgresUUID(as_uuid=True), nullable=True)  # Flow where pattern was discovered
    
    # Usage and validation tracking
    times_referenced = Column(Integer, nullable=False, default=0)  # How often this pattern has been used
    last_referenced_at = Column(DateTime(timezone=True))
    validation_status = Column(String(20), nullable=False, default='pending')
    validated_by_user = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client_account = relationship("ClientAccount")
    engagement = relationship("Engagement")
    validator = relationship("User", foreign_keys=[validated_by_user])
    
    def __repr__(self):
        return f"<AgentDiscoveredPattern(id={self.id}, type='{self.pattern_type}', name='{self.pattern_name}', confidence={self.confidence_score})>"
    
    @property
    def is_validated(self) -> bool:
        """Check if pattern has been validated by a human"""
        return self.validation_status == ValidationStatus.VALIDATED
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if pattern has high confidence (>= 0.8)"""
        return self.confidence_score >= 0.8
    
    @property
    def is_frequently_used(self) -> bool:
        """Check if pattern is frequently referenced (>= 5 times)"""
        return self.times_referenced >= 5
    
    def increment_usage(self):
        """Increment usage counter and update last referenced timestamp"""
        self.times_referenced += 1
        self.last_referenced_at = datetime.utcnow()
    
    def get_pattern_summary(self) -> Dict[str, Any]:
        """Get a summary of the pattern for agent consumption"""
        return {
            'id': str(self.id),
            'type': self.pattern_type,
            'name': self.pattern_name,
            'description': self.pattern_description,
            'confidence': self.confidence_score,
            'validated': self.is_validated,
            'evidence_count': self.evidence_count,
            'times_used': self.times_referenced,
            'pattern_data': self.pattern_data
        }


# Helper functions for pattern management

def create_asset_enrichment_pattern(
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    pattern_type: PatternType,
    pattern_name: str,
    pattern_description: str,
    pattern_logic: Dict[str, Any],
    confidence_score: float,
    discovered_by_agent: str,
    flow_id: Optional[uuid.UUID] = None,
    evidence_assets: Optional[List[uuid.UUID]] = None
) -> AgentDiscoveredPattern:
    """
    Create a new agent-discovered pattern for asset enrichment
    
    Args:
        client_account_id: Multi-tenant isolation
        engagement_id: Engagement scope
        pattern_type: Type of pattern discovered
        pattern_name: Human-readable pattern name
        pattern_description: Detailed pattern description
        pattern_logic: The actual pattern logic/rules as JSON
        confidence_score: Agent confidence in pattern (0.0 to 1.0)
        discovered_by_agent: Agent that discovered the pattern
        flow_id: Flow where pattern was discovered
        evidence_assets: Asset IDs that support this pattern
        
    Returns:
        AgentDiscoveredPattern instance
    """
    
    # Prepare discovery context
    discovery_context = {
        'flow_id': str(flow_id) if flow_id else None,
        'evidence_assets': [str(asset_id) for asset_id in (evidence_assets or [])],
        'discovery_timestamp': datetime.utcnow().isoformat()
    }
    
    pattern = AgentDiscoveredPattern(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        pattern_type=pattern_type.value,
        pattern_name=pattern_name,
        pattern_description=pattern_description,
        pattern_data=pattern_logic,
        confidence_score=confidence_score,
        evidence_count=len(evidence_assets) if evidence_assets else 1,
        discovered_by_agent=discovered_by_agent,
        discovery_context=discovery_context,
        flow_id=flow_id
    )
    
    return pattern


def get_patterns_for_agent_reasoning(
    session,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    pattern_types: Optional[List[PatternType]] = None,
    min_confidence: float = 0.6,
    validated_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Retrieve patterns for agent reasoning during asset enrichment
    
    Args:
        session: Database session
        client_account_id: Multi-tenant filter
        engagement_id: Engagement filter  
        pattern_types: Specific pattern types to retrieve
        min_confidence: Minimum confidence threshold
        validated_only: Only return human-validated patterns
        
    Returns:
        List of pattern summaries for agent consumption
    """
    
    from sqlalchemy import select
    
    query = select(AgentDiscoveredPattern).where(
        AgentDiscoveredPattern.client_account_id == client_account_id,
        AgentDiscoveredPattern.engagement_id == engagement_id,
        AgentDiscoveredPattern.confidence_score >= min_confidence
    )
    
    if pattern_types:
        type_values = [pt.value for pt in pattern_types]
        query = query.where(AgentDiscoveredPattern.pattern_type.in_(type_values))
    
    if validated_only:
        query = query.where(AgentDiscoveredPattern.validation_status == ValidationStatus.VALIDATED.value)
    
    # Order by confidence and usage
    query = query.order_by(
        AgentDiscoveredPattern.confidence_score.desc(),
        AgentDiscoveredPattern.times_referenced.desc()
    )
    
    # Simplified execution - handle both sync and async cases
    try:
        # Try async execution first
        import asyncio
        if asyncio.iscoroutinefunction(session.execute):
            # This function should be called from an async context
            # For now, return empty list to avoid blocking
            return []
        else:
            # Sync execution
            result = session.execute(query)
            patterns = result.scalars().all()
    except Exception as e:
        # Fallback for any execution issues
        print(f"Query execution error: {e}")
        return []
    
    # Update usage statistics
    try:
        for pattern in patterns:
            pattern.increment_usage()
        
        # Commit changes
        if hasattr(session, 'commit'):
            if asyncio.iscoroutinefunction(session.commit):
                # Skip commit for async - handle in calling code
                pass
            else:
                session.commit()
    except Exception as e:
        print(f"Pattern usage update error: {e}")
    
    return [pattern.get_pattern_summary() for pattern in patterns]