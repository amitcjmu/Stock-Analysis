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
            discovery_flow_id = flow_context.get(
                "discovery_flow_id"
            )  # The actual discovery flow ID
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

            # Retrieve raw import records for this flow
            raw_records = await self._get_raw_records(
                db_session, master_flow_id, client_account_id, engagement_id
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
                client_account_id=UUID(client_account_id),
                engagement_id=UUID(engagement_id),
                flow_id=UUID(master_flow_id),
                user_id=flow_context.get("user_id"),
            )

            # Initialize AssetService
            asset_service = AssetService(db_session, request_context)

            # Transform raw records to asset data
            assets_data = []
            for record in raw_records:
                asset_data = self._transform_raw_record_to_asset(
                    record, master_flow_id, discovery_flow_id
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

            # Create assets via service with atomic transaction for data integrity
            created_assets = []
            failed_count = 0

            # Use atomic transaction to ensure data consistency
            async with db_session.begin():
                for asset_data in assets_data:
                    try:
                        asset = await asset_service.create_asset(
                            asset_data, flow_id=master_flow_id
                        )
                        if asset:
                            created_assets.append(asset)
                            logger.debug(f"✅ Created asset: {asset.name}")
                        else:
                            failed_count += 1
                            logger.warning(
                                f"⚠️ Asset service returned None for: {asset_data.get('name', 'unnamed')}"
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
                await self._mark_records_processed(
                    db_session, raw_records, created_assets
                )

                # Transaction will be committed automatically when exiting the context

            total_created = len(created_assets)
            logger.info(
                f"🎉 Asset inventory phase completed: {total_created} assets created, {failed_count} failed"
            )

            return {
                "status": "completed",
                "phase": "asset_inventory",
                "message": f"Successfully created {total_created} assets from raw data",
                "assets_created": total_created,
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
        master_flow_id: str,
        client_account_id: str,
        engagement_id: str,
    ) -> List[RawImportRecord]:
        """Get raw import records for the flow with tenant scoping."""
        try:
            stmt = select(RawImportRecord).where(
                RawImportRecord.master_flow_id == UUID(master_flow_id),
                RawImportRecord.client_account_id == UUID(client_account_id),
                RawImportRecord.engagement_id == UUID(engagement_id),
            )
            result = await db.execute(stmt)
            records = result.scalars().all()

            logger.info(
                f"📊 Retrieved {len(records)} raw import records for flow {master_flow_id}"
            )
            return list(records)

        except Exception as e:
            logger.error(f"❌ Failed to retrieve raw import records: {e}")
            raise

    def _transform_raw_record_to_asset(
        self,
        record: RawImportRecord,
        master_flow_id: str,
        discovery_flow_id: str = None,
    ) -> Dict[str, Any]:
        """Transform a raw import record to asset data format."""
        try:
            # CC: CRITICAL FIX - Use cleansed_data instead of raw_data to leverage data cleansing phase
            # This ensures assets are created from processed, validated data rather than raw imports
            cleansed_data = record.cleansed_data or record.raw_data or {}
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
                # Application information
                "application_name": asset_data_source.get("application_name"),
                "technology_stack": asset_data_source.get("technology_stack"),
                # Location information
                "location": asset_data_source.get("location"),
                "datacenter": asset_data_source.get("datacenter"),
                # Discovery metadata
                "discovery_source": "Discovery Flow Import",
                "raw_import_records_id": record.id,
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

    def _classify_asset_type(self, asset_data_source: Dict[str, Any]) -> str:
        """
        Intelligently classify asset type based on available data.

        Args:
            asset_data_source: Dictionary containing asset data (cleansed or raw)

        Returns:
            String representing the asset type classification
        """
        # Use resolved_name if available, otherwise check multiple name fields
        resolved_name = str(asset_data_source.get("resolved_name", "")).lower()
        name = str(asset_data_source.get("name", "")).lower()
        hostname = str(asset_data_source.get("hostname", "")).lower()
        server_name = str(asset_data_source.get("server_name", "")).lower()
        asset_name = str(asset_data_source.get("asset_name", "")).lower()
        app_name = str(asset_data_source.get("application_name", "")).lower()
        asset_type = str(asset_data_source.get("type", "")).lower()

        # Check CI Type field which is common in CMDB imports
        ci_type = str(asset_data_source.get("CI Type", "")).lower()

        # Combine all name fields for comprehensive checking
        all_names = f"{resolved_name} {name} {hostname} {server_name} {asset_name} {app_name}".lower()

        # Priority 1: Check explicit CI Type first (most reliable for CMDB data)
        if ci_type:
            if ci_type in ["application", "app"]:
                return "Application"
            elif ci_type in ["server", "srv"]:
                return "Server"
            elif ci_type in ["database", "db"]:
                return "Database"
            elif ci_type in ["network", "switch", "router", "firewall"]:
                return "Network Device"

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
            return "Database"
        if any(keyword in asset_type for keyword in ["db", "database"]):
            return "Database"

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
            return "Application"
        if asset_data_source.get("application_name") or asset_data_source.get(
            "app_name"
        ):
            return "Application"

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
            return "Network Device"
        if any(keyword in asset_type for keyword in ["network", "switch", "router"]):
            return "Network Device"

        # Priority 5: Server detection (most conservative)
        server_keywords = ["server", "srv", "host", "vm", "virtual", "node"]
        if any(keyword in all_names for keyword in server_keywords) or hostname:
            return "Server"
        if asset_data_source.get("os") or asset_data_source.get("operating_system"):
            return "Server"

        # Priority 6: Storage detection
        storage_keywords = ["storage", "san", "nas", "disk", "volume"]
        if any(keyword in all_names for keyword in storage_keywords):
            return "Storage"

        return "Infrastructure"  # Default fallback


__all__ = ["AssetInventoryExecutor"]
