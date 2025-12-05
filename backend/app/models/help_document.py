"""
Help Document Model for Contextual AI Chat Assistant

This module defines the data model for help documentation used by the
RAG (Retrieval-Augmented Generation) system to provide context-aware
responses to user queries.

Issue: #1218 - [Feature] Contextual AI Chat Assistant
Milestone: Contextual AI Chat Assistant
"""

import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Column, DateTime, String, Text, func, Index
from sqlalchemy.dialects.postgresql import UUID

try:
    from pgvector.sqlalchemy import Vector

    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = Text  # Fallback

from app.core.database import Base


class HelpDocumentCategory(str, Enum):
    """Categories of help documentation."""

    DISCOVERY = "discovery"
    COLLECTION = "collection"
    ASSESSMENT = "assessment"
    PLANNING = "planning"
    EXECUTE = "execute"
    MODERNIZE = "modernize"
    DECOMMISSION = "decommission"
    FINOPS = "finops"
    ADMIN = "admin"
    GENERAL = "general"
    FAQ = "faq"
    TROUBLESHOOTING = "troubleshooting"


class HelpDocument(Base):
    """
    Help document for RAG-based contextual chat responses.

    Stores help content with vector embeddings for semantic search.
    Used by the Contextual Chat Service to retrieve relevant documentation
    based on user queries.
    """

    __tablename__ = "help_documents"
    __table_args__ = (
        Index("ix_help_documents_category", "category"),
        Index("ix_help_documents_flow_type", "flow_type"),
        Index("ix_help_documents_route", "route"),
        {"schema": "migration", "extend_existing": True},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Document identification
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)

    # Content
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)

    # Categorization
    category = Column(String(50), nullable=False, default="general")
    flow_type = Column(String(50), nullable=True)  # discovery, collection, etc.
    route = Column(String(255), nullable=True)  # Specific page route

    # Metadata
    tags = Column(JSON, default=list)  # List of searchable tags
    related_pages = Column(JSON, default=list)  # Related page routes
    faq_questions = Column(JSON, default=list)  # Related FAQ questions

    # Vector embedding for semantic search (1024 dimensions for thenlper/gte-large)
    embedding = Column(
        Vector(1024) if PGVECTOR_AVAILABLE else Text,
        nullable=True,
        comment="Vector embedding for semantic similarity search",
    )

    # Metadata
    source = Column(String(100), default="manual")  # manual, imported, generated
    version = Column(String(50), default="1.0")
    is_active = Column(
        String(10), default="true"
    )  # Using string for CHECK constraint compatibility

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "title": self.title,
            "slug": self.slug,
            "content": self.content,
            "summary": self.summary,
            "category": self.category,
            "flow_type": self.flow_type,
            "route": self.route,
            "tags": self.tags or [],
            "related_pages": self.related_pages or [],
            "faq_questions": self.faq_questions or [],
            "source": self.source,
            "version": self.version,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Pydantic models for API
class HelpDocumentCreate(BaseModel):
    """Model for creating a new help document."""

    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    summary: Optional[str] = None
    category: str = Field(default="general")
    flow_type: Optional[str] = None
    route: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    related_pages: List[str] = Field(default_factory=list)
    faq_questions: List[str] = Field(default_factory=list)
    source: str = Field(default="manual")
    version: str = Field(default="1.0")


class HelpDocumentResponse(BaseModel):
    """Response model for help documents."""

    id: str
    title: str
    slug: str
    content: str
    summary: Optional[str] = None
    category: str
    flow_type: Optional[str] = None
    route: Optional[str] = None
    tags: List[str] = []
    related_pages: List[str] = []
    faq_questions: List[str] = []
    relevance_score: Optional[float] = None

    class Config:
        from_attributes = True


class HelpSearchResult(BaseModel):
    """Result from help document search."""

    document: HelpDocumentResponse
    relevance_score: float
    matched_content: Optional[str] = None
