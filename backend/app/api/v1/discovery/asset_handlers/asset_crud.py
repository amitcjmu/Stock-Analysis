"""
Asset CRUD Handler
Handles Create, Read, Update, Delete operations for assets.
"""

import logging
import math
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


class AssetCRUDHandler:
    """Handles asset CRUD operations with graceful fallbacks."""

    def __init__(self):
        self.persistence_available = False
        self.serialization_available = False
        self._initialize_dependencies()

    def _initialize_dependencies(self):
        """Initialize optional dependencies with graceful fallbacks."""
        try:
            from app.api.v1.discovery.persistence import (
                backup_processed_assets,
                bulk_delete_assets,
                bulk_update_assets,
                find_duplicate_assets,
                get_processed_assets,
                initialize_persistence,
                update_asset_by_id,
            )

            self.get_processed_assets = get_processed_assets
            self.update_asset_by_id = update_asset_by_id
            self.backup_processed_assets = backup_processed_assets
            self.bulk_update_assets = bulk_update_assets
            self.bulk_delete_assets = bulk_delete_assets
            # Don't override the cleanup_duplicates method - we'll import it when needed
            self.find_duplicate_assets = find_duplicate_assets

            # Initialize persistence to load existing assets
            initialize_persistence()
            assets_count = len(get_processed_assets())
            logger.info(
                f"Asset persistence services initialized successfully with {assets_count} assets loaded"
            )

            self.persistence_available = True
        except (ImportError, AttributeError, Exception) as e:
            logger.warning(f"Asset persistence services not available: {e}")
            self.persistence_available = False

        try:
            from app.api.v1.discovery.serialization import clean_for_json_serialization

            self.clean_for_json_serialization = clean_for_json_serialization
            self.serialization_available = True
        except (ImportError, AttributeError, Exception) as e:
            logger.warning(f"Serialization service not available: {e}")
            self.serialization_available = False

    def is_available(self) -> bool:
        """Check if the handler is properly initialized."""
        return True  # Always available with fallbacks

    async def get_assets_paginated(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get paginated processed assets with filtering capabilities.
        """
        try:
            if not self.persistence_available:
                return self._fallback_get_assets(params)

            # Extract parameters
            page = params.get("page", 1)
            page_size = params.get("page_size", 50)
            asset_type = params.get("asset_type")
            environment = params.get("environment")
            department = params.get("department")
            criticality = params.get("criticality")
            search = params.get("search")

            # Get all processed assets
            all_assets = self.get_processed_assets()

            if not all_assets:
                return {
                    "assets": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                }

            # Apply filters
            filtered_assets = self._apply_filters(
                all_assets,
                {
                    "asset_type": asset_type,
                    "environment": environment,
                    "department": department,
                    "criticality": criticality,
                    "search": search,
                },
            )

            # Apply pagination
            total_filtered = len(filtered_assets)
            total_pages = (
                math.ceil(total_filtered / page_size) if total_filtered > 0 else 0
            )
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_assets = filtered_assets[start_idx:end_idx]

            # Transform assets for frontend
            transformed_assets = [
                self._transform_asset_for_frontend(asset) for asset in paginated_assets
            ]

            # Calculate summary statistics
            summary = self._calculate_asset_summary(all_assets)

            return {
                "assets": transformed_assets,
                "total": total_filtered,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "summary": summary,
            }

        except Exception as e:
            logger.error(f"Error getting paginated assets: {e}")
            return self._fallback_get_assets(params)

    async def update_asset(
        self, asset_id: str, asset_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing asset.
        """
        try:
            if not self.persistence_available:
                return self._fallback_update_asset(asset_id, asset_data)

            # Add update timestamp
            asset_data["updated_timestamp"] = pd.Timestamp.now().isoformat()

            # Clean the data if serialization is available
            if self.serialization_available:
                cleaned_data = self.clean_for_json_serialization(asset_data)
            else:
                cleaned_data = asset_data

            # Update the asset
            success = self.update_asset_by_id(asset_id, cleaned_data)

            if not success:
                return {
                    "status": "error",
                    "message": "Asset not found",
                    "asset_id": asset_id,
                }

            logger.info(f"Asset {asset_id} updated successfully")

            return {
                "status": "success",
                "message": f"Asset {asset_id} updated successfully",
                "asset_id": asset_id,
            }

        except Exception as e:
            logger.error(f"Error updating asset {asset_id}: {e}")
            return self._fallback_update_asset(asset_id, asset_data)

    async def bulk_update_assets(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Bulk update multiple assets.
        """
        try:
            if not self.persistence_available:
                return self._fallback_bulk_update(request_data)

            asset_ids = request_data.get("asset_ids", [])
            updates = request_data.get("updates", {})

            if not asset_ids:
                return {"status": "error", "message": "asset_ids are required"}

            if not updates:
                return {"status": "error", "message": "updates are required"}

            # Get raw processed assets directly
            all_raw_assets = self.get_processed_assets()

            # Apply field mapping for frontend compatibility
            backend_updates = self._map_frontend_to_backend_fields(updates)

            # Find and update assets
            updated_count = 0
            found_asset_ids = []

            for asset in all_raw_assets:
                # Check multiple possible ID fields
                asset_id = (
                    asset.get("id") or asset.get("ci_id") or asset.get("asset_id")
                )
                if asset_id and str(asset_id) in asset_ids:
                    found_asset_ids.append(asset_id)
                    # Apply updates directly to the raw asset
                    asset.update(backend_updates)
                    updated_count += 1

            if updated_count > 0:
                # Save the updated assets back to persistence
                self.backup_processed_assets()

                return {
                    "status": "success",
                    "updated_count": updated_count,
                    "message": f"Successfully updated {updated_count} assets",
                }
            else:
                return {
                    "status": "error",
                    "message": "No matching assets found",
                    "requested_ids": asset_ids,
                    "found_matches": found_asset_ids,
                }

        except Exception as e:
            logger.error(f"Error in bulk update: {e}")
            return self._fallback_bulk_update(request_data)

    async def bulk_delete_assets(self, asset_ids: List[str]) -> Dict[str, Any]:
        """
        Bulk delete multiple assets.
        """
        try:
            if not self.persistence_available:
                return self._fallback_bulk_delete(asset_ids)

            if not asset_ids:
                return {"status": "error", "message": "asset_ids are required"}

            deleted_count = self.bulk_delete_assets(asset_ids)

            return {
                "status": "success",
                "deleted_count": deleted_count,
                "message": f"Successfully deleted {deleted_count} assets",
            }

        except Exception as e:
            logger.error(f"Error in bulk delete: {e}")
            return self._fallback_bulk_delete(asset_ids)

    async def find_duplicates(self) -> Dict[str, Any]:
        """Find potential duplicate assets in the inventory."""
        try:
            if not self.persistence_available:
                return self._fallback_find_duplicates()

            # Call the persistence function directly
            duplicates = self.find_duplicate_assets()

            return {
                "status": "success",
                "duplicate_count": len(duplicates),
                "duplicates": duplicates,
            }

        except Exception as e:
            logger.error(f"Error finding duplicates: {e}")
            return self._fallback_find_duplicates()

    def cleanup_duplicates(self) -> Dict[str, Any]:
        """Remove duplicate assets from the inventory."""
        try:
            if not self.persistence_available:
                return self._fallback_cleanup_duplicates()

            # Call the persistence cleanup function with a different alias to avoid naming conflict
            from app.api.v1.discovery.persistence import (
                cleanup_duplicates as persistence_cleanup_func,
            )

            removed_count = persistence_cleanup_func()

            return {
                "status": "success",
                "removed_count": removed_count,
                "message": f"Successfully removed {removed_count} duplicate assets",
            }

        except Exception as e:
            logger.error(f"Error cleaning up duplicates: {e}")
            return self._fallback_cleanup_duplicates()

    def _apply_filters(self, assets: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
        """Apply filtering logic to assets list."""
        filtered_assets = []

        for asset in assets:
            # Asset type filter
            if (
                filters.get("asset_type")
                and asset.get("asset_type", "").lower() != filters["asset_type"].lower()
            ):
                continue

            # Environment filter
            if (
                filters.get("environment")
                and asset.get("environment", "").lower()
                != filters["environment"].lower()
            ):
                continue

            # Department filter (check both department and business_owner fields)
            if filters.get("department"):
                dept_match = False
                dept_fields = ["department", "business_owner", "dept"]
                for field in dept_fields:
                    if asset.get(field, "").lower() == filters["department"].lower():
                        dept_match = True
                        break
                if not dept_match:
                    continue

            # Criticality filter (check both criticality and status fields)
            if filters.get("criticality"):
                crit_fields = ["criticality", "status", "business_criticality"]
                crit_match = False
                for field in crit_fields:
                    if asset.get(field, "").lower() == filters["criticality"].lower():
                        crit_match = True
                        break
                if not crit_match:
                    continue

            # Search filter (search in multiple fields)
            if filters.get("search"):
                search_term = filters["search"].lower()
                search_fields = [
                    "hostname",
                    "asset_name",
                    "ip_address",
                    "operating_system",
                    "asset_type",
                ]
                search_match = False
                for field in search_fields:
                    if search_term in str(asset.get(field, "")).lower():
                        search_match = True
                        break
                if not search_match:
                    continue

            filtered_assets.append(asset)

        return filtered_assets

    def _map_frontend_to_backend_fields(
        self, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map frontend field names to backend storage field names."""
        field_mapping = {
            "type": "asset_type",
            "asset_type": "asset_type",
            "environment": "environment",
            "department": "business_owner",
            "criticality": "status",
            "name": "asset_name",
            "hostname": "hostname",
            "ip_address": "ip_address",
            "operating_system": "operating_system",
        }

        backend_updates = {}
        for frontend_field, value in updates.items():
            backend_field = field_mapping.get(frontend_field, frontend_field)
            backend_updates[backend_field] = value

        return backend_updates

    def _transform_asset_for_frontend(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Transform asset data for frontend consumption."""
        # This method will be implemented in asset_utils.py to avoid duplication
        # For now, return the asset as-is with basic transformation
        transformed = asset.copy()

        # Ensure required fields are present
        transformed["id"] = (
            asset.get("id") or asset.get("ci_id") or asset.get("asset_id", "unknown")
        )
        transformed["name"] = asset.get("asset_name") or asset.get(
            "hostname", "Unknown Asset"
        )
        transformed["type"] = asset.get("asset_type", "Unknown")

        return transformed

    def _calculate_asset_summary(self, assets: List[Dict]) -> Dict[str, Any]:
        """Calculate summary statistics for assets."""
        if not assets:
            return {"total": 0, "by_type": {}, "by_environment": {}}

        # Count by type
        type_counts = {}
        env_counts = {}

        for asset in assets:
            asset_type = asset.get("asset_type", "Unknown")
            environment = asset.get("environment", "Unknown")

            type_counts[asset_type] = type_counts.get(asset_type, 0) + 1
            env_counts[environment] = env_counts.get(environment, 0) + 1

        return {
            "total": len(assets),
            "by_type": type_counts,
            "by_environment": env_counts,
        }

    # Fallback methods
    def _fallback_get_assets(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback method when persistence is not available."""
        return {
            "assets": [],
            "total": 0,
            "page": params.get("page", 1),
            "page_size": params.get("page_size", 50),
            "total_pages": 0,
            "summary": {"total": 0, "by_type": {}, "by_environment": {}},
            "fallback_mode": True,
        }

    def _fallback_update_asset(
        self, asset_id: str, asset_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback update method."""
        return {
            "status": "error",
            "message": "Asset persistence service not available",
            "asset_id": asset_id,
            "fallback_mode": True,
        }

    def _fallback_bulk_update(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback bulk update method."""
        return {
            "status": "error",
            "message": "Bulk update service not available",
            "fallback_mode": True,
        }

    def _fallback_bulk_delete(self, asset_ids: List[str]) -> Dict[str, Any]:
        """Fallback bulk delete method."""
        return {
            "status": "error",
            "message": "Bulk delete service not available",
            "fallback_mode": True,
        }

    def _fallback_find_duplicates(self) -> Dict[str, Any]:
        """Fallback find duplicates method."""
        return {
            "status": "success",
            "duplicate_count": 0,
            "duplicates": [],
            "fallback_mode": True,
        }

    def _fallback_cleanup_duplicates(self) -> Dict[str, Any]:
        """Fallback cleanup duplicates method."""
        return {
            "status": "error",
            "message": "Duplicate cleanup service not available",
            "fallback_mode": True,
        }
