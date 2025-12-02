"""
Asset List Handler for Unified Discovery

Modular handler for asset listing operations with tenant isolation,
pagination support, and defensive programming practices.

This handler follows the established architectural patterns:
- Tenant scoped queries (client_account_id, engagement_id)
- Fallback/placeholder implementations as resilience features
- Proper error handling and secure logging
- Pagination support with configurable page sizes
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.security.secure_logging import mask_id, safe_log_format
from app.models.asset import Asset

logger = logging.getLogger(__name__)

INTERNAL_FIELDS = {
    "raw_import_records_id",
    "raw_data",
    "created_by",
    "updated_by",
    "deleted_by",
    "phase_context",
}


class AssetListHandler:
    """Handler for asset listing operations in unified discovery flows."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        """Initialize the handler with database session and request context."""
        self.db = db
        self.context = context

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Normalize SQLAlchemy column values for JSON responses."""
        if value is None:
            return None

        if isinstance(value, (datetime, date)):
            return value.isoformat()

        if isinstance(value, UUID):
            return str(value)

        if isinstance(value, Decimal):
            return float(value)

        if isinstance(value, Enum):
            return value.value

        return value

    async def list_assets(
        self,
        page_size: int = 50,
        page: int = 1,
        asset_type: Optional[str] = None,
        status_filter: Optional[str] = None,
        flow_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List assets with tenant isolation, pagination, and optional filtering."""
        try:
            page_size = min(max(1, page_size), 200)
            page = max(1, page)
            offset = (page - 1) * page_size

            # Issue #1075 fix: Filter out soft-deleted assets by default
            # Deleted assets should only appear in the Trash view, not the main inventory
            base_query = select(Asset).where(
                and_(
                    Asset.client_account_id == self.context.client_account_id,
                    Asset.engagement_id == self.context.engagement_id,
                    Asset.deleted_at.is_(None),  # Exclude soft-deleted assets
                )
            )

            if asset_type:
                base_query = base_query.where(Asset.asset_type == asset_type.strip())

            if status_filter:
                base_query = base_query.where(Asset.status == status_filter.strip())

            if flow_id:
                try:
                    if isinstance(flow_id, str) and flow_id.strip():
                        base_query = base_query.where(
                            or_(
                                Asset.discovery_flow_id == flow_id.strip(),
                                Asset.master_flow_id == flow_id.strip(),
                                Asset.flow_id == flow_id.strip(),
                            )
                        )
                except Exception as e:
                    logger.warning(
                        safe_log_format(
                            "Invalid flow_id format: {flow_id}, error: {error}",
                            flow_id=mask_id(str(flow_id)),
                            error=str(e),
                        )
                    )

            count_query = select(func.count()).select_from(base_query.subquery())
            count_result = await self.db.execute(count_query)
            total_count = count_result.scalar() or 0

            assets_query = (
                base_query.order_by(Asset.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )

            result = await self.db.execute(assets_query)
            assets = result.scalars().all()

            asset_list = []
            for asset in assets:
                try:
                    asset_data = self._transform_asset_to_dict(asset)
                    asset_list.append(asset_data)
                except Exception as asset_error:
                    logger.warning(
                        safe_log_format(
                            "Error processing asset {asset_id}: {error}",
                            asset_id=mask_id(str(asset.id)),
                            error=str(asset_error),
                        )
                    )
                    continue

            total_pages = (
                (total_count + page_size - 1) // page_size if total_count > 0 else 1
            )
            has_next = page < total_pages
            has_prev = page > 1

            logger.info(
                safe_log_format(
                    "Asset listing completed: {count} assets (page {page}/{total_pages})",
                    count=len(asset_list),
                    page=page,
                    total_pages=total_pages,
                )
            )

            return {
                "success": True,
                "assets": asset_list,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev,
                },
                "filters": {
                    "asset_type": asset_type,
                    "status_filter": status_filter,
                    "flow_id": flow_id,
                },
                "metadata": self._create_metadata_dict(),
            }

        except Exception as e:
            logger.error(
                safe_log_format(
                    "Asset listing failed: {error}, page={page}, size={size}",
                    error=str(e),
                    page=page,
                    size=page_size,
                )
            )
            return {
                "success": False,
                "assets": [],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": 0,
                    "total_pages": 1,
                    "has_next": False,
                    "has_prev": False,
                },
                "error": "Failed to retrieve assets",
                "error_details": str(e),
                "metadata": self._create_metadata_dict(),
            }

    async def get_asset_summary(self) -> Dict[str, Any]:
        """Get asset summary statistics with tenant isolation."""
        try:
            # Issue #1075 fix: Exclude soft-deleted assets from summary
            base_query = select(Asset).where(
                and_(
                    Asset.client_account_id == self.context.client_account_id,
                    Asset.engagement_id == self.context.engagement_id,
                    Asset.deleted_at.is_(None),  # Exclude soft-deleted assets
                )
            )

            total_result = await self.db.execute(
                select(func.count()).select_from(base_query.subquery())
            )
            total_assets = total_result.scalar() or 0

            # Issue #1075 fix: Exclude soft-deleted assets from type counts
            type_query = (
                select(Asset.asset_type, func.count(Asset.id).label("count"))
                .where(
                    and_(
                        Asset.client_account_id == self.context.client_account_id,
                        Asset.engagement_id == self.context.engagement_id,
                        Asset.deleted_at.is_(None),  # Exclude soft-deleted assets
                    )
                )
                .group_by(Asset.asset_type)
            )
            type_result = await self.db.execute(type_query)
            type_distribution = {
                row.asset_type or "unknown": row.count for row in type_result
            }

            status_query = (
                select(Asset.status, func.count(Asset.id).label("count"))
                .where(
                    and_(
                        Asset.client_account_id == self.context.client_account_id,
                        Asset.engagement_id == self.context.engagement_id,
                    )
                )
                .group_by(Asset.status)
            )
            status_result = await self.db.execute(status_query)
            status_distribution = {
                row.status or "unknown": row.count for row in status_result
            }

            servers_count = type_distribution.get("server", 0) + type_distribution.get(
                "virtual_machine", 0
            )
            applications_count = type_distribution.get("application", 0)
            databases_count = type_distribution.get("database", 0)

            dependencies_count = 0
            try:
                from app.models.asset import AssetDependency

                if hasattr(AssetDependency, "client_account_id") and hasattr(
                    AssetDependency, "engagement_id"
                ):
                    dependency_query = select(func.count(AssetDependency.id)).where(
                        and_(
                            AssetDependency.client_account_id
                            == self.context.client_account_id,
                            AssetDependency.engagement_id == self.context.engagement_id,
                        )
                    )
                    dependency_result = await self.db.execute(dependency_query)
                    dependencies_count = dependency_result.scalar() or 0
                else:
                    logger.warning(
                        "AssetDependency missing multi-tenancy fields, skipping count"
                    )
            except ImportError:
                logger.warning("AssetDependency model not found")
            except Exception as dep_error:
                logger.error(f"Error counting dependencies: {dep_error}", exc_info=True)

            return {
                "success": True,
                "summary": {
                    "total_assets": total_assets,
                    "type_distribution": type_distribution,
                    "status_distribution": status_distribution,
                },
                "dashboard_metrics": {
                    "servers": servers_count,
                    "applications": applications_count,
                    "databases": databases_count,
                    "dependencies": dependencies_count,
                },
                "metadata": self._create_metadata_dict(),
            }
        except Exception as e:
            logger.error(safe_log_format("Asset summary failed: {error}", error=str(e)))
            return {
                "success": False,
                "summary": {
                    "total_assets": 0,
                    "type_distribution": {},
                    "status_distribution": {},
                },
                "error": "Failed to retrieve asset summary",
                "metadata": self._create_metadata_dict(),
            }

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()

    def _create_metadata_dict(self) -> Dict[str, Any]:
        """Create standard metadata dictionary for responses."""
        return {
            "client_account_id": str(self.context.client_account_id),
            "engagement_id": str(self.context.engagement_id),
            "query_timestamp": self._get_current_timestamp(),
        }

    def _transform_asset_to_dict(self, asset: Asset) -> Dict[str, Any]:
        """Transform Asset model to dict with comprehensive field coverage."""
        # Serialize every column on the Asset model
        asset_dict: Dict[str, Any] = {}
        for column in Asset.__table__.columns:  # type: ignore[attr-defined]
            column_name = column.name
            if column_name in INTERNAL_FIELDS:
                continue
            value = getattr(asset, column_name, None)
            asset_dict[column_name] = self._serialize_value(value)

        # Provide backwards-compatible defaults and derived fields
        asset_dict["name"] = asset_dict.get("name") or getattr(
            asset, "name", "Unknown Asset"
        )
        asset_dict["asset_name"] = asset_dict.get("asset_name") or asset_dict["name"]
        asset_dict["asset_type"] = asset_dict.get("asset_type") or getattr(
            asset, "asset_type", "unknown"
        )
        asset_dict["status"] = asset_dict.get("status") or getattr(
            asset, "status", "unknown"
        )
        asset_dict["discovery_status"] = asset_dict.get("discovery_status") or getattr(
            asset, "discovery_status", "not_started"
        )
        asset_dict["mapping_status"] = asset_dict.get("mapping_status") or getattr(
            asset, "mapping_status", "not_started"
        )
        asset_dict["assessment_readiness"] = asset_dict.get(
            "assessment_readiness"
        ) or getattr(asset, "assessment_readiness", "not_ready")

        # Preserve legacy/derived fields that are not explicit columns
        if "asset_subtype" not in asset_dict:
            asset_dict["asset_subtype"] = getattr(asset, "asset_subtype", None)

        # Relationships and JSON fields should remain as-is
        asset_dict["dependencies"] = getattr(asset, "dependencies", None)
        asset_dict["dependents"] = getattr(asset, "dependents", None)

        return asset_dict


async def create_asset_list_handler(
    db: AsyncSession, context: RequestContext
) -> AssetListHandler:
    """Factory function to create AssetListHandler instance."""
    return AssetListHandler(db, context)


async def list_assets_for_discovery(
    db: AsyncSession,
    context: RequestContext,
    page_size: int = 50,
    page: int = 1,
    **kwargs,
) -> Dict[str, Any]:
    """Legacy compatibility function for asset listing."""
    handler = await create_asset_list_handler(db, context)
    return await handler.list_assets(page_size=page_size, page=page, **kwargs)


async def get_asset_summary_for_discovery(
    db: AsyncSession,
    context: RequestContext,
) -> Dict[str, Any]:
    """Legacy compatibility function for asset summary."""
    handler = await create_asset_list_handler(db, context)
    return await handler.get_asset_summary()
