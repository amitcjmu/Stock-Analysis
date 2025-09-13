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

    def execute_with_crew(self, crew_input: Dict[str, Any]) -> Dict[str, Any]:
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
            client_account_id = flow_context.get("client_account_id")
            engagement_id = flow_context.get("engagement_id")

            if not all([master_flow_id, client_account_id, engagement_id]):
                raise ValueError(
                    "Missing required context: master_flow_id, client_account_id, engagement_id"
                )

            logger.info(f"📋 Processing flow: {master_flow_id}")

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
                asset_data = self._transform_raw_record_to_asset(record, master_flow_id)
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

            # Create assets via service
            created_assets = []
            failed_count = 0

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

            # Update raw_import_records as processed
            await self._mark_records_processed(db_session, raw_records, created_assets)

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
        self, record: RawImportRecord, master_flow_id: str
    ) -> Dict[str, Any]:
        """Transform a raw import record to asset data format."""
        try:
            raw_data = record.raw_data or {}

            # Extract basic asset information with smart name resolution
            name = (
                raw_data.get("name")
                or raw_data.get("hostname")
                or raw_data.get("server_name")
                or raw_data.get("asset_name")
                or raw_data.get("application_name")
                or f"Asset-{record.row_number}"
            )

            # Determine asset type
            asset_type = raw_data.get("asset_type", "Unknown")
            if not asset_type or asset_type == "Unknown":
                # Intelligent asset type detection
                if raw_data.get("operating_system") or raw_data.get("hostname"):
                    asset_type = "Server"
                elif raw_data.get("application_name"):
                    asset_type = "Application"
                else:
                    asset_type = "Infrastructure"

            # Build comprehensive asset data
            asset_data = {
                "name": str(name).strip(),
                "asset_type": asset_type,
                "description": raw_data.get(
                    "description",
                    f"Discovered asset from import row {record.row_number}",
                ),
                # Network information
                "hostname": raw_data.get("hostname"),
                "ip_address": raw_data.get("ip_address"),
                "fqdn": raw_data.get("fqdn"),
                # System information
                "operating_system": raw_data.get("operating_system"),
                "os_version": raw_data.get("os_version"),
                "environment": raw_data.get("environment", "Unknown"),
                # Physical/Virtual specifications
                "cpu_cores": raw_data.get("cpu_cores"),
                "memory_gb": raw_data.get("memory_gb"),
                "storage_gb": raw_data.get("storage_gb"),
                # Business context
                "business_owner": raw_data.get("business_owner")
                or raw_data.get("owner"),
                "technical_owner": raw_data.get("technical_owner"),
                "department": raw_data.get("department"),
                "criticality": raw_data.get("criticality", "Medium"),
                # Application information
                "application_name": raw_data.get("application_name"),
                "technology_stack": raw_data.get("technology_stack"),
                # Location information
                "location": raw_data.get("location"),
                "datacenter": raw_data.get("datacenter"),
                # Discovery metadata
                "discovery_source": "Discovery Flow Import",
                "raw_import_records_id": record.id,
                # Flow association
                "master_flow_id": master_flow_id,
                "flow_id": master_flow_id,  # Backward compatibility
                # Store complete raw data
                "custom_attributes": raw_data,
                "raw_data": raw_data,
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


__all__ = ["AssetInventoryExecutor"]
