"""
Agent Memory Models

This module defines the data models for the agent memory system,
including pattern types and pattern discovery structures.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Column, DateTime, Float, String, Text, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session

from app.core.database import Base


class PatternType(str, Enum):
    """Types of patterns that agents can discover"""

    TECHNOLOGY_CORRELATION = "technology_correlation"
    BUSINESS_VALUE_INDICATOR = "business_value_indicator"
    RISK_FACTOR = "risk_factor"
    MODERNIZATION_OPPORTUNITY = "modernization_opportunity"
    DEPENDENCY_PATTERN = "dependency_pattern"
    SECURITY_VULNERABILITY = "security_vulnerability"
    PERFORMANCE_BOTTLENECK = "performance_bottleneck"
    COMPLIANCE_REQUIREMENT = "compliance_requirement"


class AgentDiscoveredPattern(Base):
    """
    Represents a pattern discovered by agents during asset analysis.
    Part of the Tier 3 (Semantic) memory system.
    """

    __tablename__ = "agent_discovered_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Pattern details
    pattern_type = Column(SQLEnum(PatternType), nullable=False, index=True)
    pattern_name = Column(String(255), nullable=False)
    pattern_description = Column(Text, nullable=False)

    # Discovery metadata
    discovered_by_agent = Column(String(100), nullable=False)
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    confidence_score = Column(Float, default=0.5)

    # Evidence and validation
    evidence_count = Column(Float, default=0)
    evidence_assets = Column(JSON, default=list)  # List of asset IDs
    validation_status = Column(String(50), default="pending")
    validated_by = Column(String(100), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)

    # Reasoning and context
    reasoning = Column(Text, nullable=True)
    supporting_data = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PatternDiscoveryRequest(BaseModel):
    """Request model for pattern discovery"""

    pattern_type: PatternType
    pattern_name: str
    pattern_description: str
    discovered_by_agent: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    evidence_assets: List[str] = Field(default_factory=list)
    reasoning: Optional[str] = None
    supporting_data: Optional[Dict[str, Any]] = None


def create_asset_enrichment_pattern(
    session: Session,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    pattern_type: PatternType,
    pattern_name: str,
    pattern_description: str,
    discovered_by_agent: str,
    confidence_score: float,
    evidence_assets: List[str],
    reasoning: Optional[str] = None,
    supporting_data: Optional[Dict[str, Any]] = None,
) -> AgentDiscoveredPattern:
    """
    Create a new asset enrichment pattern in the database.

    This function is used by agents to store discovered patterns
    as part of the Tier 3 semantic memory system.

    Args:
        session: Database session
        client_account_id: UUID of the client account
        engagement_id: UUID of the engagement
        pattern_type: Type of pattern discovered
        pattern_name: Name of the pattern
        pattern_description: Description of the pattern
        discovered_by_agent: Name of the agent that discovered the pattern
        confidence_score: Confidence score between 0.0 and 1.0
        evidence_assets: List of asset IDs that support this pattern
        reasoning: Optional reasoning for the pattern
        supporting_data: Optional additional data

    Returns:
        AgentDiscoveredPattern: The created pattern

    Raises:
        ValueError: If validation fails
        Exception: If database operation fails
    """
    # Validation
    if not pattern_name or not pattern_name.strip():
        raise ValueError("Pattern name cannot be empty")

    if not pattern_description or not pattern_description.strip():
        raise ValueError("Pattern description cannot be empty")

    if not discovered_by_agent or not discovered_by_agent.strip():
        raise ValueError("Discovered by agent cannot be empty")

    if not 0.0 <= confidence_score <= 1.0:
        raise ValueError("Confidence score must be between 0.0 and 1.0")

    if not isinstance(evidence_assets, list):
        raise ValueError("Evidence assets must be a list")

    pattern = AgentDiscoveredPattern(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        pattern_type=pattern_type,
        pattern_name=pattern_name.strip(),
        pattern_description=pattern_description.strip(),
        discovered_by_agent=discovered_by_agent.strip(),
        confidence_score=confidence_score,
        evidence_count=len(evidence_assets),
        evidence_assets=evidence_assets,
        reasoning=reasoning,
        supporting_data=supporting_data or {},
    )

    try:
        session.add(pattern)
        session.commit()
        session.refresh(pattern)
        return pattern
    except Exception:
        session.rollback()
        raise


def get_patterns_for_agent_reasoning(
    session: Session,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    pattern_types: Optional[List[PatternType]] = None,
    min_confidence: float = 0.6,
    validated_only: bool = False,
) -> List[AgentDiscoveredPattern]:
    """
    Retrieve patterns for agent reasoning and decision-making.

    This function is used by agents to access previously discovered
    patterns from the Tier 3 semantic memory system.
    """
    query = session.query(AgentDiscoveredPattern).filter(
        AgentDiscoveredPattern.client_account_id == client_account_id,
        AgentDiscoveredPattern.engagement_id == engagement_id,
        AgentDiscoveredPattern.confidence_score >= min_confidence,
    )

    if pattern_types:
        query = query.filter(AgentDiscoveredPattern.pattern_type.in_(pattern_types))

    if validated_only:
        query = query.filter(AgentDiscoveredPattern.validation_status == "validated")

    return query.order_by(AgentDiscoveredPattern.confidence_score.desc()).all()


class AgentMemory(BaseModel):
    """
    Base model for agent memory entries.
    Used for serialization/deserialization of memory data.
    """

    id: Optional[str] = None
    agent_id: str
    memory_type: str
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v),
        }
