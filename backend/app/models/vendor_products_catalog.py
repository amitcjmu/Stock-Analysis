"""
SQLAlchemy models for vendor products catalog system.

This module defines the models for the global vendor/product catalog
and tenant-specific overrides for the collection gaps Phase 1 feature.
"""

import uuid
from typing import Any, Dict

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class VendorProductsCatalog(Base, TimestampMixin):
    """
    Global vendor products catalog.

    This table maintains a centralized catalog of vendor/product combinations
    that can be referenced by tenant-specific overrides and asset links.
    """

    __tablename__ = "vendor_products_catalog"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Vendor and product information
    vendor_name = Column(String(255), nullable=False)
    product_name = Column(String(255), nullable=False)
    normalized_key = Column(String(255), nullable=False)  # For matching/search
    is_global = Column(Boolean, nullable=False, default=True)

    # Relationships
    product_versions = relationship(
        "ProductVersionsCatalog",
        back_populates="catalog_product",
        cascade="all, delete-orphan",
    )
    tenant_products = relationship(
        "TenantVendorProducts",
        back_populates="catalog_reference",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<VendorProductsCatalog(id={self.id}, vendor='{self.vendor_name}', product='{self.product_name}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "vendor_name": self.vendor_name,
            "product_name": self.product_name,
            "normalized_key": self.normalized_key,
            "is_global": self.is_global,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ProductVersionsCatalog(Base, TimestampMixin):
    """
    Product versions catalog.

    This table stores version information for products in the global catalog.
    """

    __tablename__ = "product_versions_catalog"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Reference to catalog product
    catalog_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.vendor_products_catalog.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Version information
    version_label = Column(String(100), nullable=False)
    version_semver = Column(
        String(100), nullable=True
    )  # Semantic version if applicable

    # Relationships
    catalog_product = relationship(
        "VendorProductsCatalog", back_populates="product_versions"
    )
    lifecycle_milestones = relationship(
        "LifecycleMilestones",
        back_populates="catalog_version",
        cascade="all, delete-orphan",
    )
    asset_links = relationship(
        "AssetProductLinks",
        back_populates="catalog_version",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<ProductVersionsCatalog(id={self.id}, version='{self.version_label}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "catalog_id": str(self.catalog_id),
            "version_label": self.version_label,
            "version_semver": self.version_semver,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TenantVendorProducts(Base, TimestampMixin):
    """
    Tenant-specific vendor products.

    This table allows tenants to override or add custom vendor/product combinations
    that are not in the global catalog.
    """

    __tablename__ = "tenant_vendor_products"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenant scoping
    client_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.client_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    engagement_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.engagements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Reference to global catalog (optional for custom products)
    catalog_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.vendor_products_catalog.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Custom product information (for tenant-specific products)
    custom_vendor_name = Column(String(255), nullable=True)
    custom_product_name = Column(String(255), nullable=True)
    normalized_key = Column(String(255), nullable=True)

    # Relationships
    catalog_reference = relationship(
        "VendorProductsCatalog", back_populates="tenant_products"
    )
    tenant_versions = relationship(
        "TenantProductVersions",
        back_populates="tenant_product",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        vendor = self.custom_vendor_name or (
            self.catalog_reference.vendor_name if self.catalog_reference else "Unknown"
        )
        product = self.custom_product_name or (
            self.catalog_reference.product_name if self.catalog_reference else "Unknown"
        )
        return f"<TenantVendorProducts(id={self.id}, vendor='{vendor}', product='{product}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "catalog_id": str(self.catalog_id) if self.catalog_id else None,
            "custom_vendor_name": self.custom_vendor_name,
            "custom_product_name": self.custom_product_name,
            "normalized_key": self.normalized_key,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TenantProductVersions(Base, TimestampMixin):
    """
    Tenant-specific product versions.

    This table stores version information for tenant products, either referencing
    global catalog versions or storing custom version data.
    """

    __tablename__ = "tenant_product_versions"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Reference to tenant product
    tenant_product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.tenant_vendor_products.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Reference to global catalog version (optional)
    catalog_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.product_versions_catalog.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Custom version information
    version_label = Column(String(100), nullable=True)
    version_semver = Column(String(100), nullable=True)

    # Relationships
    tenant_product = relationship(
        "TenantVendorProducts", back_populates="tenant_versions"
    )
    catalog_version = relationship("ProductVersionsCatalog")
    lifecycle_milestones = relationship(
        "LifecycleMilestones",
        back_populates="tenant_version",
        cascade="all, delete-orphan",
    )
    asset_links = relationship(
        "AssetProductLinks",
        back_populates="tenant_version",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        version = self.version_label or (
            self.catalog_version.version_label if self.catalog_version else "Unknown"
        )
        return f"<TenantProductVersions(id={self.id}, version='{version}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "tenant_product_id": (
                str(self.tenant_product_id) if self.tenant_product_id else None
            ),
            "catalog_version_id": (
                str(self.catalog_version_id) if self.catalog_version_id else None
            ),
            "version_label": self.version_label,
            "version_semver": self.version_semver,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class LifecycleMilestones(Base, TimestampMixin):
    """
    Product lifecycle milestones.

    This table tracks important dates in a product's lifecycle such as
    end-of-life, end-of-support, etc.
    """

    __tablename__ = "lifecycle_milestones"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References to version (either catalog or tenant)
    catalog_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.product_versions_catalog.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    tenant_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.tenant_product_versions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Milestone information
    milestone_type = Column(
        String(50), nullable=False
    )  # release, end_of_support, end_of_life, extended_support_end
    milestone_date = Column(Date, nullable=False)
    source = Column(String(255), nullable=True)  # Where this information came from

    # Provenance and tracking
    provenance = Column(JSONB, nullable=False, default=dict)  # Agent/source metadata
    last_checked_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    catalog_version = relationship(
        "ProductVersionsCatalog", back_populates="lifecycle_milestones"
    )
    tenant_version = relationship(
        "TenantProductVersions", back_populates="lifecycle_milestones"
    )

    def __repr__(self):
        return f"<LifecycleMilestones(id={self.id}, type='{self.milestone_type}', date={self.milestone_date})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "catalog_version_id": (
                str(self.catalog_version_id) if self.catalog_version_id else None
            ),
            "tenant_version_id": (
                str(self.tenant_version_id) if self.tenant_version_id else None
            ),
            "milestone_type": self.milestone_type,
            "milestone_date": (
                self.milestone_date.isoformat() if self.milestone_date else None
            ),
            "source": self.source,
            "provenance": self.provenance,
            "last_checked_at": (
                self.last_checked_at.isoformat() if self.last_checked_at else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AssetProductLinks(Base, TimestampMixin):
    """
    Asset-to-product linking table.

    This table establishes relationships between assets and their product versions,
    with confidence scoring and matching metadata.
    """

    __tablename__ = "asset_product_links"
    __table_args__ = {"schema": "migration"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Asset reference
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Product version references (either catalog or tenant)
    catalog_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.product_versions_catalog.id", ondelete="SET NULL"),
        nullable=True,
    )
    tenant_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("migration.tenant_product_versions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Matching metadata
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    matched_by = Column(String(50), nullable=True)  # agent, manual, import, etc.

    # Relationships
    asset = relationship("Asset")
    catalog_version = relationship(
        "ProductVersionsCatalog", back_populates="asset_links"
    )
    tenant_version = relationship("TenantProductVersions", back_populates="asset_links")

    def __repr__(self):
        return f"<AssetProductLinks(id={self.id}, asset_id={self.asset_id}, confidence={self.confidence_score})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "asset_id": str(self.asset_id),
            "catalog_version_id": (
                str(self.catalog_version_id) if self.catalog_version_id else None
            ),
            "tenant_version_id": (
                str(self.tenant_version_id) if self.tenant_version_id else None
            ),
            "confidence_score": self.confidence_score,
            "matched_by": self.matched_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
