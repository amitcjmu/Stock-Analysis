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
from typing import Any, Dict, Optional

from sqlalchemy import and_, select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.security.secure_logging import mask_id, safe_log_format
from app.models.asset import Asset

logger = logging.getLogger(__name__)


class AssetListHandler:
    """Handler for asset listing operations in unified discovery flows."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        """Initialize the handler with database session and request context."""
        self.db = db
        self.context = context

    async def list_assets(
        self,
        page_size: int = 50,
        page: int = 1,
        asset_type: Optional[str] = None,
        status_filter: Optional[str] = None,
        flow_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List assets with tenant isolation and pagination.

        Args:
            page_size: Maximum number of assets per page (default: 50, max: 200)
            page: Page number (1-based)
            asset_type: Optional filter by asset type
            status_filter: Optional filter by asset status
            flow_id: Optional filter by discovery flow ID

        Returns:
            Dict containing assets list, pagination info, and metadata

        Fallback behavior:
            - Returns empty list if no assets found (graceful degradation)
            - Applies conservative pagination limits
            - Handles missing optional fields gracefully
        """
        try:
            # Defensive programming: validate and sanitize inputs
            page_size = min(max(1, page_size), 200)  # Clamp between 1-200
            page = max(1, page)  # Ensure positive page number
            offset = (page - 1) * page_size

            # Build tenant-scoped base query with defensive checks
            base_query = select(Asset).where(
                and_(
                    Asset.client_account_id == self.context.client_account_id,
                    Asset.engagement_id == self.context.engagement_id,
                )
            )

            # Apply optional filters with defensive null checking
            if asset_type:
                base_query = base_query.where(Asset.asset_type == asset_type.strip())

            if status_filter:
                base_query = base_query.where(Asset.status == status_filter.strip())

            if flow_id:
                # Handle both string and UUID flow_id formats defensively
                try:
                    if isinstance(flow_id, str) and flow_id.strip():
                        # CRITICAL FIX: Check multiple flow ID fields for asset visibility
                        # Assets can be associated via discovery_flow_id, master_flow_id, or flow_id
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
                            "Invalid flow_id format in asset listing: {flow_id}, error: {error}",
                            flow_id=mask_id(str(flow_id)),
                            error=str(e),
                        )
                    )
                    # Continue without flow filter rather than failing

            # Get total count for pagination metadata
            count_query = select(func.count()).select_from(base_query.subquery())
            count_result = await self.db.execute(count_query)
            total_count = count_result.scalar() or 0

            # Apply pagination and ordering
            assets_query = (
                base_query.order_by(Asset.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )

            # Execute query with error handling
            result = await self.db.execute(assets_query)
            assets = result.scalars().all()

            # Transform assets to response format with defensive field access
            asset_list = []
            for asset in assets:
                try:
                    asset_data = {
                        "id": str(asset.id),
                        "name": asset.name or "Unknown Asset",
                        "asset_name": asset.asset_name or asset.name,
                        "asset_type": asset.asset_type or "unknown",
                        "asset_subtype": getattr(asset, "asset_subtype", None),
                        # Network and infrastructure
                        "hostname": getattr(asset, "hostname", None),
                        "ip_address": getattr(asset, "ip_address", None),
                        "fqdn": getattr(asset, "fqdn", None),
                        "mac_address": getattr(asset, "mac_address", None),
                        # Operating system
                        "operating_system": getattr(asset, "operating_system", None),
                        "os_version": getattr(asset, "os_version", None),
                        # Hardware specifications
                        "cpu_cores": getattr(asset, "cpu_cores", None),
                        "memory_gb": getattr(asset, "memory_gb", None),
                        "storage_gb": getattr(asset, "storage_gb", None),
                        # Location
                        "location": getattr(asset, "location", None),
                        "datacenter": getattr(asset, "datacenter", None),
                        "rack_location": getattr(asset, "rack_location", None),
                        "availability_zone": getattr(asset, "availability_zone", None),
                        # Business information
                        "business_owner": getattr(asset, "business_owner", None),
                        "technical_owner": getattr(asset, "technical_owner", None),
                        "department": getattr(asset, "department", None),
                        # Application details
                        "application_name": getattr(asset, "application_name", None),
                        "technology_stack": getattr(asset, "technology_stack", None),
                        # Status and readiness
                        "status": asset.status or "unknown",
                        "discovery_status": getattr(
                            asset, "discovery_status", "not_started"
                        ),
                        "mapping_status": getattr(
                            asset, "mapping_status", "not_started"
                        ),
                        "assessment_readiness": getattr(
                            asset, "assessment_readiness", "not_ready"
                        ),
                        # Criticality and environment
                        "environment": getattr(asset, "environment", None),
                        "criticality": getattr(asset, "criticality", None),
                        "business_criticality": getattr(
                            asset, "business_criticality", None
                        ),
                        # Migration planning
                        "migration_priority": getattr(
                            asset, "migration_priority", None
                        ),
                        "migration_complexity": getattr(
                            asset, "migration_complexity", None
                        ),
                        "migration_wave": getattr(asset, "migration_wave", None),
                        "six_r_strategy": getattr(asset, "six_r_strategy", None),
                        "sixr_ready": getattr(asset, "sixr_ready", False),
                        # Quality and completeness
                        "quality_score": getattr(asset, "quality_score", None),
                        "confidence_score": getattr(asset, "confidence_score", None),
                        "completeness_score": getattr(
                            asset, "completeness_score", None
                        ),
                        # Performance metrics
                        "cpu_utilization_percent": getattr(
                            asset, "cpu_utilization_percent", None
                        ),
                        "memory_utilization_percent": getattr(
                            asset, "memory_utilization_percent", None
                        ),
                        "disk_iops": getattr(asset, "disk_iops", None),
                        "network_throughput_mbps": getattr(
                            asset, "network_throughput_mbps", None
                        ),
                        # Cost information
                        "current_monthly_cost": getattr(
                            asset, "current_monthly_cost", None
                        ),
                        "estimated_cloud_cost": getattr(
                            asset, "estimated_cloud_cost", None
                        ),
                        # Flow associations
                        "discovery_flow_id": (
                            str(asset.discovery_flow_id)
                            if asset.discovery_flow_id
                            else None
                        ),
                        "master_flow_id": (
                            str(asset.master_flow_id) if asset.master_flow_id else None
                        ),
                        "flow_id": str(asset.flow_id) if asset.flow_id else None,
                        # Timestamps
                        "created_at": (
                            asset.created_at.isoformat() if asset.created_at else None
                        ),
                        "updated_at": (
                            asset.updated_at.isoformat() if asset.updated_at else None
                        ),
                        "discovery_timestamp": (
                            asset.discovery_timestamp.isoformat()
                            if getattr(asset, "discovery_timestamp", None)
                            else None
                        ),
                    }
                    asset_list.append(asset_data)
                except Exception as asset_error:
                    # Log individual asset processing errors but continue
                    logger.warning(
                        safe_log_format(
                            "Error processing asset {asset_id}: {error}",
                            asset_id=mask_id(str(asset.id)),
                            error=str(asset_error),
                        )
                    )
                    continue

            # Calculate pagination metadata
            total_pages = (
                (total_count + page_size - 1) // page_size if total_count > 0 else 1
            )
            has_next = page < total_pages
            has_prev = page > 1

            # Log successful operation
            logger.info(
                safe_log_format(
                    "Asset listing completed: {count} assets returned (page {page}/{total_pages})",
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
                "metadata": {
                    "client_account_id": str(self.context.client_account_id),
                    "engagement_id": str(self.context.engagement_id),
                    "query_timestamp": self._get_current_timestamp(),
                },
            }

        except Exception as e:
            # Comprehensive error logging with context
            logger.error(
                safe_log_format(
                    "Asset listing failed: {error}, context: page={page}, page_size={page_size}, "
                    "client_account_id={client_id}, engagement_id={engagement_id}",
                    error=str(e),
                    page=page,
                    page_size=page_size,
                    client_id=mask_id(str(self.context.client_account_id)),
                    engagement_id=mask_id(str(self.context.engagement_id)),
                )
            )

            # Fallback response for resilience
            return {
                "success": False,
                "assets": [],  # Empty list fallback
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
                "metadata": {
                    "client_account_id": str(self.context.client_account_id),
                    "engagement_id": str(self.context.engagement_id),
                    "query_timestamp": self._get_current_timestamp(),
                },
            }

    async def get_asset_summary(self) -> Dict[str, Any]:
        """
        Get asset summary statistics for the current tenant context.

        Returns summary counts and distribution information with fallback behavior.
        """
        try:
            # Build tenant-scoped query
            base_query = select(Asset).where(
                and_(
                    Asset.client_account_id == self.context.client_account_id,
                    Asset.engagement_id == self.context.engagement_id,
                )
            )

            # Get total count
            total_result = await self.db.execute(
                select(func.count()).select_from(base_query.subquery())
            )
            total_assets = total_result.scalar() or 0

            # Get asset type distribution
            type_query = (
                select(Asset.asset_type, func.count(Asset.id).label("count"))
                .where(
                    and_(
                        Asset.client_account_id == self.context.client_account_id,
                        Asset.engagement_id == self.context.engagement_id,
                    )
                )
                .group_by(Asset.asset_type)
            )
            type_result = await self.db.execute(type_query)
            type_distribution = {
                row.asset_type or "unknown": row.count for row in type_result
            }

            # Get status distribution
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

            # Calculate dashboard metrics from type distribution
            servers_count = type_distribution.get("server", 0) + type_distribution.get(
                "virtual_machine", 0
            )
            applications_count = type_distribution.get("application", 0)
            databases_count = type_distribution.get("database", 0)

            # Count total dependency records (from asset_dependencies table)
            dependencies_count = 0
            try:
                from app.models.asset import AssetDependency

                # Defensively check for required multi-tenancy fields before querying
                if hasattr(AssetDependency, "client_account_id") and hasattr(AssetDependency, "engagement_id"):
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
                    logger.warning("AssetDependency model is missing required multi-tenancy fields (client_account_id, engagement_id). Skipping dependency count.")

            except ImportError:
                logger.warning("AssetDependency model not found. Skipping dependency count.")
            except Exception as dep_error:
                logger.error(f"An unexpected error occurred while counting dependencies: {dep_error}", exc_info=True)

            return {
                "success": True,
                "summary": {
                    "total_assets": total_assets,
                    "type_distribution": type_distribution,
                    "status_distribution": status_distribution,
                },
                # Dashboard metrics for Discovery page
                "dashboard_metrics": {
                    "servers": servers_count,
                    "applications": applications_count,
                    "databases": databases_count,
                    "dependencies": dependencies_count,
                },
                "metadata": {
                    "client_account_id": str(self.context.client_account_id),
                    "engagement_id": str(self.context.engagement_id),
                    "query_timestamp": self._get_current_timestamp(),
                },
            }

        except Exception as e:
            logger.error(
                safe_log_format(
                    "Asset summary failed: {error}",
                    error=str(e),
                )
            )

            # Fallback summary for resilience
            return {
                "success": False,
                "summary": {
                    "total_assets": 0,
                    "type_distribution": {},
                    "status_distribution": {},
                },
                "error": "Failed to retrieve asset summary",
                "metadata": {
                    "client_account_id": str(self.context.client_account_id),
                    "engagement_id": str(self.context.engagement_id),
                    "query_timestamp": self._get_current_timestamp(),
                },
            }

    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()


# Factory function for handler creation
async def create_asset_list_handler(
    db: AsyncSession, context: RequestContext
) -> AssetListHandler:
    """
    Factory function to create an AssetListHandler instance.

    This follows the established pattern for handler creation with proper
    dependency injection and context management.
    """
    return AssetListHandler(db, context)


# Backward compatibility functions for legacy integration
async def list_assets_for_discovery(
    db: AsyncSession,
    context: RequestContext,
    page_size: int = 50,
    page: int = 1,
    **kwargs,
) -> Dict[str, Any]:
    """
    Legacy compatibility function for asset listing.

    This function provides backward compatibility for existing code
    that may call asset listing functions directly.
    """
    handler = await create_asset_list_handler(db, context)
    return await handler.list_assets(page_size=page_size, page=page, **kwargs)


async def get_asset_summary_for_discovery(
    db: AsyncSession,
    context: RequestContext,
) -> Dict[str, Any]:
    """
    Legacy compatibility function for asset summary.
    """
    handler = await create_asset_list_handler(db, context)
    return await handler.get_asset_summary()
