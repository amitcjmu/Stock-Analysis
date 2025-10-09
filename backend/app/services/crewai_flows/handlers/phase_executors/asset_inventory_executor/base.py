"""
Asset Inventory Executor - Base Class
Contains the main AssetInventoryExecutor class with interface methods.

CC: Implements actual asset creation from raw_import_records data
"""

import logging
from typing import Dict, Any

from app.services.asset_service import AssetService
from app.core.context import RequestContext
from ..base_phase_executor import BasePhaseExecutor
from .queries import get_raw_records, get_field_mappings
from .commands import mark_records_processed, persist_asset_inventory_completion
from .transforms import transform_raw_record_to_asset

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

    async def execute_asset_creation(  # noqa: C901
        self, flow_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the asset inventory phase - creates assets from raw data.

        Note: Uses direct AssetService execution instead of CrewAI agents.
        Justification: This is a data pipeline fix (field mapping, serialization,
        dashboard metrics), not ADR-022 implementation. Asset creation is a
        deterministic database operation that doesn't require AI reasoning.

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

            raw_records = await get_raw_records(
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
            field_mappings = await get_field_mappings(
                db_session, data_import_id, client_account_id
            )
            logger.info(f"📋 Retrieved {len(field_mappings)} approved field mappings")

            # Transform raw records to asset data
            assets_data = []
            for record in raw_records:
                asset_data = transform_raw_record_to_asset(
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

            # Use batch-optimized method to eliminate N+1 queries
            try:
                results = await asset_service.bulk_create_or_update_assets(
                    assets_data, flow_id=master_flow_id
                )

                # Categorize results by status
                for asset, status in results:
                    if status == "created":
                        created_assets.append(asset)
                        logger.debug(f"✅ Created asset: {asset.name}")
                    elif status == "existed":
                        duplicate_assets.append(asset)
                        logger.debug(f"🔄 Duplicate asset skipped: {asset.name}")
                    # Note: "updated" status won't occur with default upsert=False

            except Exception as e:
                # If batch fails, fall back to individual processing
                logger.warning(
                    f"⚠️ Batch processing failed, falling back to individual: {e}"
                )
                for asset_data in assets_data:
                    try:
                        # Use unified deduplication method (single source of truth)
                        # Hierarchical dedup: name+type → hostname/fqdn/ip → normalization
                        asset, status = await asset_service.create_or_update_asset(
                            asset_data, flow_id=master_flow_id
                        )

                        if status == "created":
                            created_assets.append(asset)
                            logger.debug(f"✅ Created asset: {asset.name}")
                        elif status == "existed":
                            duplicate_assets.append(asset)
                            logger.debug(f"🔄 Duplicate asset skipped: {asset.name}")

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
            await mark_records_processed(db_session, raw_records, all_assets)

            # Mark asset_inventory phase as complete and complete the discovery flow
            # This is the final phase of discovery, so mark flow as completed (Qodo Issue #2)
            await persist_asset_inventory_completion(
                db_session,
                flow_id=str(discovery_flow_id),
                client_account_id=str(client_account_id),
                engagement_id=str(engagement_id),
                mark_flow_complete=True,  # Single source of truth for completion
            )

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


__all__ = ["AssetInventoryExecutor"]
