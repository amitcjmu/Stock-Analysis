"""
SQLAlchemy models for additional asset enrichments.

This module defines models for tech debt, performance metrics,
and cost optimization tracking for assets.

CC Generated to complete Issue #980 - Intelligent Multi-Layer Gap Detection
"""

import uuid
from typing import Any, Dict

from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

from app.models.base import Base, TimestampMixin


class AssetTechDebt(Base, TimestampMixin):
    """
    Asset technical debt tracking.

    This table stores technical debt metrics including modernization priority,
    technical debt score, and debt items that need addressing.
    """

    __tablename__ = "asset_tech_debt"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Asset reference
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,  # One tech debt record per asset
    )

    # Tech debt metrics
    tech_debt_score = Column(
        Float, nullable=True, comment="Technical debt score (0-100, higher = more debt)"
    )
    modernization_priority = Column(
        String(20),
        nullable=True,
        comment="Modernization priority: low, medium, high, critical",
    )
    code_quality_score = Column(
        Float, nullable=True, comment="Code quality score (0-100, higher = better)"
    )

    # Technical debt items and details
    debt_items = Column(
        JSONB,
        nullable=False,
        default=lambda: [],
        comment="List of technical debt items with descriptions",
    )

    # Assessment metadata
    last_assessment_date = Column(
        String(50), nullable=True, comment="Date of last tech debt assessment"
    )
    assessment_method = Column(
        String(100),
        nullable=True,
        comment="Method used for assessment (manual, automated, ai)",
    )

    # Relationships
    asset = relationship("Asset", back_populates="tech_debt")

    def __repr__(self):
        return (
            f"<AssetTechDebt(id={self.id}, asset_id={self.asset_id}, "
            f"score={self.tech_debt_score}, priority='{self.modernization_priority}')>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "tech_debt_score": self.tech_debt_score,
            "modernization_priority": self.modernization_priority,
            "code_quality_score": self.code_quality_score,
            "debt_items": self.debt_items or [],
            "last_assessment_date": self.last_assessment_date,
            "assessment_method": self.assessment_method,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AssetPerformanceMetrics(Base, TimestampMixin):
    """
    Asset performance metrics tracking.

    This table stores resource utilization and performance metrics for assets
    including CPU, memory, disk, and network utilization.
    """

    __tablename__ = "asset_performance_metrics"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Asset reference
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,  # One performance metrics record per asset
    )

    # CPU metrics
    cpu_utilization_avg = Column(
        Float, nullable=True, comment="Average CPU utilization percentage (0-100)"
    )
    cpu_utilization_peak = Column(
        Float, nullable=True, comment="Peak CPU utilization percentage (0-100)"
    )

    # Memory metrics
    memory_utilization_avg = Column(
        Float, nullable=True, comment="Average memory utilization percentage (0-100)"
    )
    memory_utilization_peak = Column(
        Float, nullable=True, comment="Peak memory utilization percentage (0-100)"
    )

    # Disk I/O metrics
    disk_iops_avg = Column(Integer, nullable=True, comment="Average disk IOPS")
    disk_throughput_mbps = Column(
        Float, nullable=True, comment="Average disk throughput in MB/s"
    )

    # Network metrics
    network_throughput_mbps = Column(
        Float, nullable=True, comment="Average network throughput in MB/s"
    )
    network_latency_ms = Column(
        Float, nullable=True, comment="Average network latency in milliseconds"
    )

    # Monitoring period
    monitoring_period_days = Column(
        Integer,
        nullable=True,
        comment="Number of days the metrics were collected over",
    )
    metrics_source = Column(
        String(100),
        nullable=True,
        comment="Source of metrics (e.g., CloudWatch, Azure Monitor)",
    )

    # Additional metrics stored as JSONB
    additional_metrics = Column(
        JSONB,
        nullable=False,
        default=lambda: {},
        comment="Additional performance metrics",
    )

    # Relationships
    asset = relationship("Asset", back_populates="performance_metrics")

    def __repr__(self):
        return (
            f"<AssetPerformanceMetrics(id={self.id}, asset_id={self.asset_id}, "
            f"cpu_avg={self.cpu_utilization_avg}, mem_avg={self.memory_utilization_avg})>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "cpu_utilization_avg": self.cpu_utilization_avg,
            "cpu_utilization_peak": self.cpu_utilization_peak,
            "memory_utilization_avg": self.memory_utilization_avg,
            "memory_utilization_peak": self.memory_utilization_peak,
            "disk_iops_avg": self.disk_iops_avg,
            "disk_throughput_mbps": self.disk_throughput_mbps,
            "network_throughput_mbps": self.network_throughput_mbps,
            "network_latency_ms": self.network_latency_ms,
            "monitoring_period_days": self.monitoring_period_days,
            "metrics_source": self.metrics_source,
            "additional_metrics": self.additional_metrics,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AssetCostOptimization(Base, TimestampMixin):
    """
    Asset cost optimization tracking.

    This table stores cost-related data and optimization opportunities for assets
    including current costs, projected costs, and optimization potential.
    """

    __tablename__ = "asset_cost_optimization"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Asset reference
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,  # One cost optimization record per asset
    )

    # Current costs
    monthly_cost_usd = Column(
        Float, nullable=True, comment="Current monthly cost in USD"
    )
    annual_cost_usd = Column(Float, nullable=True, comment="Current annual cost in USD")

    # Projected costs after migration
    projected_monthly_cost_usd = Column(
        Float, nullable=True, comment="Projected monthly cost after migration in USD"
    )
    projected_annual_cost_usd = Column(
        Float, nullable=True, comment="Projected annual cost after migration in USD"
    )

    # Optimization potential
    optimization_potential_pct = Column(
        Float,
        nullable=True,
        comment="Potential cost savings percentage (0-100)",
    )
    optimization_opportunities = Column(
        JSONB,
        nullable=False,
        default=lambda: [],
        comment="List of identified cost optimization opportunities",
    )

    # Cost breakdown
    cost_breakdown = Column(
        JSONB,
        nullable=False,
        default=lambda: {},
        comment="Breakdown of costs (compute, storage, network, licenses, etc.)",
    )

    # Cost tracking metadata
    cost_calculation_date = Column(
        String(50), nullable=True, comment="Date when costs were last calculated"
    )
    cost_source = Column(
        String(100),
        nullable=True,
        comment="Source of cost data (e.g., AWS Cost Explorer, manual)",
    )

    # Relationships
    asset = relationship("Asset", back_populates="cost_optimization")

    def __repr__(self):
        return (
            f"<AssetCostOptimization(id={self.id}, asset_id={self.asset_id}, "
            f"monthly=${self.monthly_cost_usd}, optimization={self.optimization_potential_pct}%)>"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "monthly_cost_usd": self.monthly_cost_usd,
            "annual_cost_usd": self.annual_cost_usd,
            "projected_monthly_cost_usd": self.projected_monthly_cost_usd,
            "projected_annual_cost_usd": self.projected_annual_cost_usd,
            "optimization_potential_pct": self.optimization_potential_pct,
            "optimization_opportunities": self.optimization_opportunities or [],
            "cost_breakdown": self.cost_breakdown,
            "cost_calculation_date": self.cost_calculation_date,
            "cost_source": self.cost_source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
