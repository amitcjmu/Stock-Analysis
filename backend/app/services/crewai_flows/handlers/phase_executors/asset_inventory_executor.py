"""
Asset Inventory Executor
Handles asset inventory phase execution for the Unified Discovery Flow.

CC: Implements actual asset creation from raw_import_records data
"""

import logging
from typing import Dict, Any, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.data_import.core import RawImportRecord
from app.services.asset_service import AssetService
from .base_phase_executor import BasePhaseExecutor

logger = logging.getLogger(__name__)


class AssetInventoryExecutor(BasePhaseExecutor):
    """
    Handles the asset inventory phase execution.

    CC: Creates actual asset records from raw_import_records data
    """

    def get_phase_name(self) -> str:
        """Get the name of this phase"""
        return "asset_inventory"

    def get_progress_percentage(self) -> float:
        """Get the progress percentage when this phase completes"""
        return 70.0  # Asset inventory is 70% through discovery

    async def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute phase using CrewAI crew - not used, we implement direct execution"""
        # This method is required by the base class but not used in our implementation
        logger.warning(
            "execute_with_crew called but asset inventory uses direct execution"
        )
        return {"status": "delegated_to_direct_execution"}

    def _prepare_crew_input(self) -> Dict[str, Any]:
        """Prepare input data for crew execution"""
        return {"phase": "asset_inventory"}

    async def _store_results(self, results: Dict[str, Any]):
        """Store execution results in state"""
        if hasattr(self.state, "mark_phase_complete"):
            self.state.mark_phase_complete("asset_inventory", results)

    async def execute_asset_creation(
        self, flow_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the asset inventory phase - creates assets from raw data.

        Args:
            flow_context: The flow context containing necessary data

        Returns:
            Dictionary containing the execution results
        """
        try:
            logger.info("🏗️ Starting asset inventory phase execution")

            # Extract context information
            flow_id = flow_context.get("flow_id")
            master_flow_id = flow_context.get("master_flow_id") or flow_id
            # Get the actual discovery flow ID - this is what assets should be linked to
            discovery_flow_id = flow_context.get("discovery_flow_id") or flow_id
            client_account_id = flow_context.get("client_account_id")
            engagement_id = flow_context.get("engagement_id")

            if not all([master_flow_id, client_account_id, engagement_id]):
                raise ValueError(
                    "Missing required context: master_flow_id, client_account_id, engagement_id"
                )

            logger.info(
                f"📋 Processing flow: master_flow_id={master_flow_id}, discovery_flow_id={discovery_flow_id}"
            )

            # Get database session from context
            db_session = flow_context.get("db_session")
            if not db_session:
                raise ValueError("Database session not available in flow context")

            # Retrieve raw import records using data_import_id (not master_flow_id)
            # CC: Raw records are linked by data_import_id, not master_flow_id
            data_import_id = flow_context.get("data_import_id")
            if not data_import_id:
                logger.error(
                    f"❌ data_import_id not provided in flow_context for flow {master_flow_id}"
                )
                return {
                    "status": "failed",
                    "phase": "asset_inventory",
                    "error": "data_import_id not found in flow context",
                    "message": "Cannot retrieve raw records without data_import_id",
                    "assets_created": 0,
                }

            raw_records = await self._get_raw_records(
                db_session, data_import_id, client_account_id, engagement_id
            )

            if not raw_records:
                logger.warning(
                    f"⚠️ No raw import records found for flow {master_flow_id}"
                )
                return {
                    "status": "completed",
                    "phase": "asset_inventory",
                    "message": "No raw data available for asset creation",
                    "assets_created": 0,
                    "execution_time": "0.001s",
                }

            logger.info(f"📊 Found {len(raw_records)} raw records to process")

            # Create RequestContext for AssetService
            request_context = RequestContext(
                client_account_id=str(client_account_id),
                engagement_id=str(engagement_id),
                flow_id=str(master_flow_id),
                user_id=flow_context.get("user_id"),
            )

            # Initialize AssetService
            asset_service = AssetService(db_session, request_context)

            # Retrieve approved field mappings for applying transformations
            field_mappings = await self._get_field_mappings(
                db_session, data_import_id, client_account_id
            )
            logger.info(f"📋 Retrieved {len(field_mappings)} approved field mappings")

            # Transform raw records to asset data
            assets_data = []
            for record in raw_records:
                asset_data = self._transform_raw_record_to_asset(
                    record, master_flow_id, discovery_flow_id, field_mappings
                )
                if asset_data:
                    assets_data.append(asset_data)

            logger.info(f"🔄 Transformed {len(assets_data)} records to asset format")

            if not assets_data:
                logger.warning(
                    "⚠️ No valid asset data could be extracted from raw records"
                )
                return {
                    "status": "completed",
                    "phase": "asset_inventory",
                    "message": "No valid asset data in raw records",
                    "assets_created": 0,
                    "execution_time": "0.001s",
                }

            # Create assets via service (transaction managed by caller)
            # CC: Don't start a new transaction - db_session already has an active transaction
            created_assets = []
            duplicate_assets = []
            failed_count = 0

            for asset_data in assets_data:
                try:
                    # Check if asset exists before creating
                    asset_name = asset_data.get("name") or asset_data.get(
                        "asset_name", "unnamed"
                    )
                    existing_asset = await asset_service._find_existing_asset(
                        name=asset_name,
                        client_id=str(client_account_id),
                        engagement_id=str(engagement_id),
                    )

                    asset = await asset_service.create_asset(
                        asset_data, flow_id=master_flow_id
                    )
                    if asset:
                        if existing_asset and existing_asset.id == asset.id:
                            # Asset was a duplicate - not newly created
                            duplicate_assets.append(asset)
                            logger.debug(f"🔄 Duplicate asset skipped: {asset.name}")
                        else:
                            # Asset was newly created
                            created_assets.append(asset)
                            logger.debug(f"✅ Created asset: {asset.name}")
                    else:
                        failed_count += 1
                        logger.warning(
                            f"⚠️ Asset service returned None for: {asset_name}"
                        )
                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"❌ Failed to create asset {asset_data.get('name', 'unnamed')}: {e}"
                    )
                    # Continue processing other assets in case of individual failures

            # Flush to make asset IDs available for foreign key relationships
            await db_session.flush()

            # Update raw_import_records as processed within the same transaction
            # Include both created and duplicate assets for proper tracking
            all_assets = created_assets + duplicate_assets
            await self._mark_records_processed(db_session, raw_records, all_assets)

            # Transaction will be committed by caller

            total_created = len(created_assets)
            total_duplicates = len(duplicate_assets)
            logger.info(
                f"🎉 Asset inventory phase completed: {total_created} new assets, "
                f"{total_duplicates} duplicates, {failed_count} failed"
            )

            # Build appropriate message based on results
            if total_created > 0 and total_duplicates > 0:
                message = (
                    f"Created {total_created} new assets. {total_duplicates} assets "
                    f"already existed and were skipped."
                )
            elif total_created > 0:
                message = (
                    f"Successfully created {total_created} new assets from raw data"
                )
            elif total_duplicates > 0:
                message = f"All {total_duplicates} assets already exist in inventory. No new assets were created."
            else:
                message = "No assets were created or found"

            return {
                "status": "completed",
                "phase": "asset_inventory",
                "message": message,
                "assets_created": total_created,
                "assets_duplicates": total_duplicates,
                "assets_failed": failed_count,
                "execution_time": "variable",  # Actual execution time
            }

        except Exception as e:
            logger.error(f"❌ Asset inventory phase execution failed: {e}")
            return {
                "status": "failed",
                "phase": "asset_inventory",
                "error": str(e),
                "message": f"Asset inventory phase failed: {str(e)}",
                "assets_created": 0,
            }

    async def _get_raw_records(
        self,
        db: AsyncSession,
        data_import_id: str,
        client_account_id: str,
        engagement_id: str,
    ) -> List[RawImportRecord]:
        """Get raw import records by data_import_id with tenant scoping.

        CC: Raw records are linked by data_import_id, NOT master_flow_id.
        This is the correct field to query as raw records are uploaded via data imports.
        """
        try:
            stmt = select(RawImportRecord).where(
                RawImportRecord.data_import_id == UUID(data_import_id),
                RawImportRecord.client_account_id == UUID(client_account_id),
                RawImportRecord.engagement_id == UUID(engagement_id),
            )
            result = await db.execute(stmt)
            records = result.scalars().all()

            logger.info(
                f"📊 Retrieved {len(records)} raw import records for data_import_id {data_import_id}"
            )
            return list(records)

        except Exception as e:
            logger.error(f"❌ Failed to retrieve raw import records: {e}")
            raise

    async def _get_field_mappings(
        self,
        db: AsyncSession,
        data_import_id: str,
        client_account_id: str,
    ) -> Dict[str, str]:
        """Get approved field mappings for the data import.

        Returns:
            Dictionary mapping source_field to target_field for approved mappings
        """
        try:
            from app.models.data_import.mapping import ImportFieldMapping

            stmt = select(ImportFieldMapping).where(
                ImportFieldMapping.data_import_id == UUID(data_import_id),
                ImportFieldMapping.client_account_id == UUID(client_account_id),
                ImportFieldMapping.status == "approved",
            )
            result = await db.execute(stmt)
            mappings = result.scalars().all()

            # Build lookup dictionary: source_field -> target_field
            mapping_dict = {
                mapping.source_field: mapping.target_field for mapping in mappings
            }

            logger.debug(
                f"📋 Retrieved {len(mapping_dict)} approved field mappings: {mapping_dict}"
            )
            return mapping_dict

        except Exception as e:
            logger.warning(f"⚠️ Failed to retrieve field mappings: {e}")
            return {}  # Return empty dict to allow asset creation to proceed

    def _transform_raw_record_to_asset(
        self,
        record: RawImportRecord,
        master_flow_id: str,
        discovery_flow_id: str = None,
        field_mappings: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Transform a raw import record to asset data format.

        Args:
            record: Raw import record to transform
            master_flow_id: Master flow identifier
            discovery_flow_id: Discovery flow identifier
            field_mappings: Dict mapping source_field to target_field for transformations

        Returns:
            Asset data dictionary ready for AssetService.create_asset()
        """
        try:
            # CC: CRITICAL FIX - Use cleansed_data instead of raw_data to leverage data cleansing phase
            # This ensures assets are created from processed, validated data rather than raw imports
            cleansed_data: Dict[str, Any] = (
                record.cleansed_data or record.raw_data or {}
            )
            # Use cleansed data for asset creation, fallback to raw_data if cleansing hasn't occurred
            asset_data_source = cleansed_data

            # Extract basic asset information with smart name resolution
            name = (
                asset_data_source.get("name")
                or asset_data_source.get("hostname")
                or asset_data_source.get("server_name")
                or asset_data_source.get("asset_name")
                or asset_data_source.get("application_name")
                or f"Asset-{record.row_number}"
            )

            # Determine asset type with intelligent classification
            # Pass the actual resolved name to ensure proper classification
            asset_data_for_classification = {**asset_data_source, "resolved_name": name}
            asset_type = self._classify_asset_type(asset_data_for_classification)

            # Build comprehensive asset data
            asset_data = {
                "name": str(name).strip(),
                "asset_type": asset_type,
                "description": asset_data_source.get(
                    "description",
                    f"Discovered asset from import row {record.row_number}",
                ),
                # Network information
                "hostname": asset_data_source.get("hostname"),
                "ip_address": asset_data_source.get("ip_address"),
                "fqdn": asset_data_source.get("fqdn"),
                # System information
                "operating_system": asset_data_source.get("operating_system"),
                "os_version": asset_data_source.get("os_version"),
                "environment": asset_data_source.get("environment", "Unknown"),
                # Physical/Virtual specifications
                "cpu_cores": asset_data_source.get("cpu_cores"),
                "memory_gb": asset_data_source.get("memory_gb"),
                "storage_gb": asset_data_source.get("storage_gb"),
                # Business context
                "business_owner": asset_data_source.get("business_owner")
                or asset_data_source.get("owner"),
                "technical_owner": asset_data_source.get("technical_owner"),
                "department": asset_data_source.get("department"),
                "criticality": asset_data_source.get("criticality", "Medium"),
                # Apply field mapping for business_criticality if approved mapping exists
                "business_criticality": self._apply_field_mapping(
                    asset_data_source,
                    "criticality",
                    "business_criticality",
                    field_mappings or {},
                    default="Medium",
                ),
                # Application information
                "application_name": asset_data_source.get("application_name"),
                "technology_stack": asset_data_source.get("technology_stack"),
                # Location information
                "location": asset_data_source.get("location"),
                "datacenter": asset_data_source.get("datacenter"),
                # Discovery metadata
                "discovery_source": "Discovery Flow Import",
                "raw_import_records_id": record.id if hasattr(record, "id") else None,
                # Flow association
                "master_flow_id": master_flow_id,
                "flow_id": master_flow_id,  # Backward compatibility
                "discovery_flow_id": discovery_flow_id,  # The actual discovery flow ID for proper association
                # Store complete raw data (preserve original for audit)
                "custom_attributes": asset_data_source,
                "raw_data": record.raw_data,  # Keep original raw data for audit trail
            }

            # Remove None values to avoid database issues
            cleaned_data = {k: v for k, v in asset_data.items() if v is not None}

            logger.debug(
                f"🔄 Transformed record {record.row_number} to asset '{name}' (type: {asset_type})"
            )
            return cleaned_data

        except Exception as e:
            logger.error(f"❌ Failed to transform raw record {record.row_number}: {e}")
            return None

    def _apply_field_mapping(
        self,
        asset_data_source: Dict[str, Any],
        source_field: str,
        target_field: str,
        field_mappings: Dict[str, str],
        default: Any = None,
    ) -> Any:
        """Apply field mapping transformation if approved mapping exists.

        Args:
            asset_data_source: Source data dictionary
            source_field: Name of the source field to map from
            target_field: Name of the target field to map to
            field_mappings: Dict of approved mappings (source -> target)
            default: Default value if no mapping found

        Returns:
            Transformed value or default
        """
        # Check if there's an approved mapping for this source field
        if field_mappings.get(source_field) == target_field:
            # Mapping exists and matches - use the source field value
            value = asset_data_source.get(source_field, default)
            logger.debug(
                f"📋 Applied field mapping: {source_field} → {target_field} = {value}"
            )
            return value
        else:
            # No mapping - return default
            return default

    async def _mark_records_processed(
        self, db: AsyncSession, raw_records: List[RawImportRecord], created_assets: List
    ) -> None:
        """Mark raw import records as processed."""
        try:
            # Create asset mapping for linking
            asset_mapping = {}
            for asset in created_assets:
                if asset.raw_import_records_id:
                    asset_mapping[asset.raw_import_records_id] = asset.id

            # Update records
            for record in raw_records:
                record.is_processed = True
                record.asset_id = asset_mapping.get(record.id)
                # Don't set processed_at here - let the database handle it

            await db.flush()  # Ensure updates are written
            logger.info(f"✅ Marked {len(raw_records)} raw records as processed")

        except Exception as e:
            logger.error(f"❌ Failed to mark records as processed: {e}")
            # Don't raise - asset creation succeeded even if we can't mark records

    def _flatten_cleansed_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten nested cleansed_data structures.

        Args:
            data: Dictionary that may contain nested cleansed_data structures

        Returns:
            Flattened dictionary with all cleansed_data content at top level
        """
        if not isinstance(data, dict):
            return {}

        result = {}
        for key, value in data.items():
            if key == "cleansed_data" and isinstance(value, dict):
                # Recursively flatten nested cleansed_data
                result.update(self._flatten_cleansed_data(value))
            else:
                result[key] = value

        return result

    def _classify_asset_type(self, asset_data_source: Dict[str, Any]) -> str:
        """
        Intelligently classify asset type based on available data.

        Args:
            asset_data_source: Dictionary containing asset data (cleansed or raw)

        Returns:
            String representing the asset type classification
        """
        # CRITICAL FIX: Flatten nested cleansed_data structures before classification
        flattened_data = self._flatten_cleansed_data(asset_data_source)

        # Use resolved_name if available, otherwise check multiple name fields
        resolved_name = str(flattened_data.get("resolved_name", "")).lower()
        name = str(flattened_data.get("name", "")).lower()
        hostname = str(flattened_data.get("hostname", "")).lower()
        server_name = str(flattened_data.get("server_name", "")).lower()
        asset_name = str(flattened_data.get("asset_name", "")).lower()
        app_name = str(flattened_data.get("application_name", "")).lower()
        asset_type = str(flattened_data.get("type", "")).lower()

        # CRITICAL FIX: Check CI Type field with both common field names and case-insensitive matching
        ci_type = (
            str(flattened_data.get("CI Type", "")).lower()
            or str(flattened_data.get("ci_type", "")).lower()
            or str(flattened_data.get("CI_Type", "")).lower()
            or str(flattened_data.get("asset_type", "")).lower()
        )

        # Combine all name fields for comprehensive checking
        all_names = f"{resolved_name} {name} {hostname} {server_name} {asset_name} {app_name}".lower()

        # Add debug logging to track classification process
        has_os = bool(flattened_data.get("OS") or flattened_data.get("os"))
        logger.debug(
            f"🔍 Classifying asset: name='{name}', ci_type='{ci_type}', has_os={has_os}"
        )

        # CRITICAL FIX: Enhanced CI Type detection with better pattern matching
        # Priority 1: Check explicit CI Type first (most reliable for CMDB data)
        if ci_type:
            # Application detection
            if any(app_pattern in ci_type for app_pattern in ["application", "app"]):
                logger.debug(f"✅ Classified as 'application' via CI Type: '{ci_type}'")
                return "application"
            # Server detection
            elif any(srv_pattern in ci_type for srv_pattern in ["server", "srv"]):
                logger.debug(f"✅ Classified as 'server' via CI Type: '{ci_type}'")
                return "server"
            # Database detection
            elif any(db_pattern in ci_type for db_pattern in ["database", "db"]):
                logger.debug(f"✅ Classified as 'database' via CI Type: '{ci_type}'")
                return "database"
            # Network device detection
            elif any(
                net_pattern in ci_type
                for net_pattern in ["network", "switch", "router", "firewall", "device"]
            ):
                logger.debug(f"✅ Classified as 'network' via CI Type: '{ci_type}'")
                return "network"  # Use valid AssetType enum value

        # Priority 2: Database detection (specific patterns)
        database_keywords = [
            "db",
            "database",
            "sql",
            "oracle",
            "mysql",
            "postgres",
            "mongodb",
            "cassandra",
            "redis",
            "mariadb",
            "mssql",
            "sqlite",
        ]
        if any(keyword in all_names for keyword in database_keywords):
            return "database"
        if any(keyword in asset_type for keyword in ["db", "database"]):
            return "database"

        # Priority 3: Application detection (enhanced patterns)
        application_keywords = [
            "app",
            "application",
            "service",
            "api",
            "web",
            "portal",
            "system",
            "platform",
            "tool",
            "suite",
            "software",
            "crm",
            "erp",
            "hr",
            "analytics",
            "email",
            "backup",
            "monitoring",
            "pipeline",
        ]
        if any(keyword in all_names for keyword in application_keywords):
            return "application"
        if flattened_data.get("application_name") or flattened_data.get("app_name"):
            return "application"

        # Priority 4: Network device detection
        network_keywords = [
            "switch",
            "router",
            "firewall",
            "gateway",
            "loadbalancer",
            "lb",
            "proxy",
            "vpn",
            "wifi",
            "access point",
            "hub",
        ]
        if any(keyword in all_names for keyword in network_keywords):
            return "network"  # Use valid AssetType enum value
        if any(keyword in asset_type for keyword in ["network", "switch", "router"]):
            return "network"  # Use valid AssetType enum value

        # Priority 5: Server detection (most conservative) - ENHANCED WITH FLATTENED DATA
        server_keywords = ["server", "srv", "host", "vm", "virtual", "node"]
        # CRITICAL FIX: Check for operating system with multiple field names (both 'OS' and 'operating_system')
        has_os = (
            flattened_data.get("os")
            or flattened_data.get("OS")
            or flattened_data.get("operating_system")
            or flattened_data.get("Operating System")
        )

        if (
            any(keyword in all_names for keyword in server_keywords)
            or hostname
            or has_os
        ):
            return "server"

        # Priority 6: Storage detection
        storage_keywords = ["storage", "san", "nas", "disk", "volume"]
        if any(keyword in all_names for keyword in storage_keywords):
            return "storage"

        logger.debug(f"⚠️ Using default classification 'other' for asset: '{name}'")
        return "other"  # Default fallback using valid AssetType enum value


__all__ = ["AssetInventoryExecutor"]
