"""
Data normalization utilities for Discovery Flow Execution Engine.
Contains asset normalization logic for raw data processing.
"""

from typing import Dict, List

from app.core.logging import get_logger

logger = get_logger(__name__)


class DataNormalizationMixin:
    """Mixin class containing data normalization methods for discovery flows."""

    async def _normalize_assets_for_creation(
        self,
        raw_data: List[Dict],
        field_mappings: Dict,
        master_flow_id: str,
        discovery_flow_id: str,
    ) -> List[Dict]:
        """Normalize raw data for asset creation with proper linking"""
        normalized = []

        # Get raw_import_records if we need to link them
        raw_import_records_map = {}
        if hasattr(self, "db_session"):
            try:
                from app.models.data_import.core import RawImportRecord
                from sqlalchemy import select

                result = await self.db_session.execute(
                    select(RawImportRecord)
                    .where(RawImportRecord.master_flow_id == master_flow_id)
                    .order_by(RawImportRecord.row_number)
                )
                raw_records = result.scalars().all()
                # Map by row number for correlation
                raw_import_records_map = {r.row_number - 1: r.id for r in raw_records}
                logger.info(
                    f"📋 Found {len(raw_import_records_map)} raw_import_records to link"
                )
            except Exception as e:
                logger.warning(f"Could not load raw_import_records for linking: {e}")

        # Process each record
        for idx, record in enumerate(raw_data):
            # Helper functions extracted from database_operations.py
            def get_mapped_value(record, field, mappings):
                """Get value using field mapping or direct field"""
                if field in mappings:
                    source_field = mappings[field]
                    return record.get(source_field)
                return record.get(field)

            def determine_asset_type(record, mappings):
                """Determine asset type from record - respect mapped value"""
                asset_type = get_mapped_value(record, "asset_type", mappings)
                if asset_type:
                    # Map common variations to standard types
                    type_lower = asset_type.lower()
                    if "application" in type_lower or "app" in type_lower:
                        return "application"
                    elif "server" in type_lower:
                        return "server"
                    elif "database" in type_lower or "db" in type_lower:
                        return "database"
                    elif "device" in type_lower or "network" in type_lower:
                        return "device"
                    else:
                        return type_lower

                # Only use fallback if no asset_type mapping exists
                return "device"  # Default

            # Get mapped values - CRITICAL FIX: Use "name" not "asset_name"
            asset_name = get_mapped_value(record, "name", field_mappings)
            hostname = get_mapped_value(record, "hostname", field_mappings)
            ip_address = get_mapped_value(record, "ip_address", field_mappings)

            # CRITICAL FIX: Don't generate names - use actual mapped value or skip
            if not asset_name:
                # Log warning but still try to use hostname/ip as fallback
                logger.warning(
                    f"No name found for record {idx+1}, using fallback: {hostname or ip_address or 'unnamed'}"
                )
                asset_name = hostname or ip_address or f"unnamed_asset_{idx+1}"

            # Build asset data with explicit flow IDs and raw_import_record linking
            asset_data = {
                "name": asset_name,
                "asset_type": determine_asset_type(record, field_mappings),
                "hostname": hostname,
                "ip_address": ip_address,
                "operating_system": get_mapped_value(
                    record, "operating_system", field_mappings
                ),
                "environment": get_mapped_value(record, "environment", field_mappings)
                or "production",
                "status": get_mapped_value(record, "status", field_mappings),
                "location": get_mapped_value(record, "location", field_mappings),
                # Explicit flow IDs
                "master_flow_id": master_flow_id,
                "discovery_flow_id": discovery_flow_id,
                "flow_id": discovery_flow_id,  # Some code expects flow_id
                # CRITICAL: Add tenant context for asset creation
                "client_account_id": str(self.context.client_account_id),
                "engagement_id": str(self.context.engagement_id),
                # Link to raw_import_record if available
                "raw_import_records_id": raw_import_records_map.get(idx),
                # Unmapped fields to custom_attributes
                "custom_attributes": {
                    k: v
                    for k, v in record.items()
                    if k not in field_mappings.values()  # Check against source fields
                },
                "raw_data": record,
            }

            normalized.append(asset_data)

        logger.info(f"✅ Normalized {len(normalized)}/{len(raw_data)} records")
        if normalized:
            # Log sample without sensitive data
            sample = {k: type(v).__name__ for k, v in normalized[0].items()}
            logger.debug(f"📊 Sample asset structure: {sample}")

        return normalized
