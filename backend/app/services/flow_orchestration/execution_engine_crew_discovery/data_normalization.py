"""
Data normalization utilities for Discovery Flow Execution Engine.
Contains asset normalization logic for raw data processing.
"""

from typing import Dict, List

from app.core.logging import get_logger

logger = get_logger(__name__)


class DataNormalizationMixin:
    """Mixin class containing data normalization methods for discovery flows."""

    def _get_mapped_value(self, record: Dict, field: str, mappings: Dict):
        """Get value using field mapping or a resilient direct lookup."""
        if field in mappings:
            source_field = mappings[field]
            value = record.get(source_field)
            logger.debug(f"🔍 Mapped {field} -> {source_field}: '{value}'")
            return value

        # Resilient direct lookup: try exact, case-insensitive, and trimmed keys
        if field in record:
            value = record.get(field)
            logger.debug(f"🔍 Direct {field}: '{value}' (exact key)")
            return value

        # Build a case-insensitive map of record keys
        lowered = {str(k).strip().lower(): v for k, v in record.items()}
        candidate = lowered.get(field.lower().strip())
        if candidate is not None:
            logger.debug(
                f"🔍 Fuzzy direct {field}: '{candidate}' (case/whitespace-insensitive)"
            )
            return candidate

        logger.debug(f"🔍 Direct {field}: 'None' (no mapping)")
        return None

    def _determine_asset_type(self, record: Dict, mappings: Dict) -> str:
        """Determine asset type from record - respect mapped value"""
        asset_type = self._get_mapped_value(record, "asset_type", mappings)
        logger.debug(
            f"🔍 Asset type determination: '{asset_type}' from mappings: {mappings.get('asset_type', 'None')}"
        )
        if asset_type:
            # Map common variations to VALID AssetType enum values
            type_lower = asset_type.lower()
            asset_type_mappings = {
                ("application", "app"): "application",
                ("server", "srv"): "server",
                ("database", "db"): "database",
                ("network", "switch", "router"): "network",
                ("storage", "san", "nas"): "storage",
                ("security", "firewall"): "security_group",
                ("container",): "container",
                ("service",): "application",
                ("cache",): "database",
                ("external",): "other",
            }

            for keywords, mapped_type in asset_type_mappings.items():
                if any(keyword in type_lower for keyword in keywords):
                    return mapped_type

            # Special cases
            if "load" in type_lower and "balancer" in type_lower:
                return "load_balancer"
            if "virtual" in type_lower and "machine" in type_lower:
                return "virtual_machine"

            # Return the original if it's already a valid type
            return type_lower

        # Use 'other' as fallback instead of invalid 'device'
        return "other"  # Default to 'other' from AssetType enum

    async def _load_raw_import_records_map(self, master_flow_id: str) -> Dict[int, str]:
        """Load raw import records mapping for linking"""
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
        return raw_import_records_map

    def _build_asset_data(
        self,
        record: Dict,
        idx: int,
        field_mappings: Dict,
        master_flow_id: str,
        discovery_flow_id: str,
        raw_import_records_map: Dict,
    ) -> Dict:
        """Build normalized asset data from record"""
        logger.info(f"🔨 Building asset data for record {idx+1}")
        logger.info(f"🔨 Available field mappings: {list(field_mappings.keys())}")
        logger.info(f"🔨 Raw record keys: {list(record.keys())}")

        # Get mapped values - CRITICAL FIX: Use "name" not "asset_name"
        asset_name = self._get_mapped_value(record, "name", field_mappings)
        hostname = self._get_mapped_value(record, "hostname", field_mappings)
        ip_address = self._get_mapped_value(record, "ip_address", field_mappings)

        logger.info(
            f"🔨 Mapped values - name: '{asset_name}', hostname: '{hostname}', ip: '{ip_address}'"
        )

        # CRITICAL FIX: Don't generate names - use actual mapped value or skip
        if not asset_name:
            # Log warning but still try to use hostname/ip as fallback
            logger.warning(
                f"No name found for record {idx+1}, using fallback: {hostname or ip_address or 'unnamed'}"
            )
            asset_name = hostname or ip_address or f"unnamed_asset_{idx+1}"

        # Build asset data with explicit flow IDs and raw_import_record linking
        return {
            "name": asset_name,
            "asset_type": self._determine_asset_type(record, field_mappings),
            "hostname": hostname,
            "ip_address": ip_address,
            # Operating system and version
            "operating_system": self._get_mapped_value(
                record, "operating_system", field_mappings
            ),
            "os_version": self._get_mapped_value(record, "os_version", field_mappings),
            # Hardware specifications
            "cpu_cores": self._get_mapped_value(record, "cpu_cores", field_mappings),
            "memory_gb": self._get_mapped_value(record, "memory_gb", field_mappings),
            "storage_gb": self._get_mapped_value(record, "storage_gb", field_mappings),
            # Location and infrastructure
            "location": self._get_mapped_value(record, "location", field_mappings),
            "datacenter": self._get_mapped_value(record, "datacenter", field_mappings),
            "rack_location": self._get_mapped_value(
                record, "rack_location", field_mappings
            ),
            "availability_zone": self._get_mapped_value(
                record, "availability_zone", field_mappings
            ),
            # Business ownership
            "business_owner": self._get_mapped_value(
                record, "business_owner", field_mappings
            ),
            "technical_owner": self._get_mapped_value(
                record, "technical_owner", field_mappings
            ),
            "department": self._get_mapped_value(record, "department", field_mappings),
            # Application details
            "application_name": self._get_mapped_value(
                record, "application_name", field_mappings
            ),
            "technology_stack": self._get_mapped_value(
                record, "technology_stack", field_mappings
            ),
            # Environment and criticality
            "environment": self._get_mapped_value(record, "environment", field_mappings)
            or "production",
            "criticality": self._get_mapped_value(
                record, "criticality", field_mappings
            ),
            "business_criticality": self._get_mapped_value(
                record, "business_criticality", field_mappings
            ),
            # Migration planning
            "migration_complexity": self._get_mapped_value(
                record, "migration_complexity", field_mappings
            ),
            "migration_priority": self._get_mapped_value(
                record, "migration_priority", field_mappings
            ),
            "migration_wave": self._get_mapped_value(
                record, "migration_wave", field_mappings
            ),
            # Performance metrics
            "cpu_utilization_percent": self._get_mapped_value(
                record, "cpu_utilization_percent", field_mappings
            ),
            "memory_utilization_percent": self._get_mapped_value(
                record, "memory_utilization_percent", field_mappings
            ),
            "disk_iops": self._get_mapped_value(record, "disk_iops", field_mappings),
            "network_throughput_mbps": self._get_mapped_value(
                record, "network_throughput_mbps", field_mappings
            ),
            # Quality and completeness scores
            "completeness_score": self._get_mapped_value(
                record, "completeness_score", field_mappings
            ),
            "quality_score": self._get_mapped_value(
                record, "quality_score", field_mappings
            ),
            "confidence_score": self._get_mapped_value(
                record, "confidence_score", field_mappings
            ),
            # Cost information
            "current_monthly_cost": self._get_mapped_value(
                record, "current_monthly_cost", field_mappings
            ),
            "estimated_cloud_cost": self._get_mapped_value(
                record, "estimated_cloud_cost", field_mappings
            ),
            # Import metadata
            "imported_by": self._get_mapped_value(
                record, "imported_by", field_mappings
            ),
            "imported_at": self._get_mapped_value(
                record, "imported_at", field_mappings
            ),
            "source_filename": self._get_mapped_value(
                record, "source_filename", field_mappings
            ),
            # Status
            "status": self._get_mapped_value(record, "status", field_mappings),
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
        raw_import_records_map = await self._load_raw_import_records_map(master_flow_id)

        # Process each record
        for idx, record in enumerate(raw_data):
            asset_data = self._build_asset_data(
                record,
                idx,
                field_mappings,
                master_flow_id,
                discovery_flow_id,
                raw_import_records_map,
            )
            normalized.append(asset_data)

        logger.info(f"✅ Normalized {len(normalized)}/{len(raw_data)} records")
        if normalized:
            # Log sample without sensitive data
            sample = {k: type(v).__name__ for k, v in normalized[0].items()}
            logger.debug(f"📊 Sample asset structure: {sample}")

        return normalized
