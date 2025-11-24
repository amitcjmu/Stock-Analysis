"""
Asset Inventory Executor - Base Class
Contains the main AssetInventoryExecutor class with interface methods.

CC: Implements actual asset creation from raw_import_records data
"""

import logging
from typing import Dict, Any
from uuid import UUID

from app.services.asset_service import AssetService
from app.services.asset_service.deduplication import bulk_prepare_conflicts
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.core.context import RequestContext
from ..base_phase_executor import BasePhaseExecutor
from .queries import get_raw_records, get_field_mappings
from .commands import mark_records_processed, persist_asset_inventory_completion
from .transforms import transform_raw_record_to_asset
from .preview_handler import (
    check_preview_and_approval,
    store_preview_data,
    filter_approved_assets,
    mark_assets_created,
)
from .conflict_handler import create_conflict_free_assets, handle_conflicts

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

            # === ASSET PREVIEW AND APPROVAL WORKFLOW (Issue #907) ===
            master_flow_repo = CrewAIFlowStateExtensionsRepository(
                db_session,
                str(client_account_id),
                str(engagement_id),
            )

            # Check preview and approval status
            (
                assets_preview,
                approved_asset_ids,
                assets_already_created,
                updated_assets_map,
            ) = await check_preview_and_approval(master_flow_repo, master_flow_id)

            # If assets were already created, skip this phase
            if assets_already_created:
                logger.info("✅ Assets already created for this flow, skipping")
                return {
                    "status": "completed",
                    "phase": "asset_inventory",
                    "message": "Assets have already been created for this flow",
                    "assets_created": 0,
                    "execution_time": "0.001s",
                }

            # If preview data doesn't exist, store it and pause for user approval
            if not assets_preview:
                return await store_preview_data(
                    master_flow_repo, master_flow_id, assets_data, db_session
                )

            # If preview exists but no approval, wait
            if not approved_asset_ids:
                logger.info(
                    f"⏳ Preview exists ({len(assets_preview)} assets) but no approval yet. "
                    "Waiting for user to approve via /api/v1/asset-preview/{flow_id}/approve"
                )
                return {
                    "status": "paused",
                    "phase": "asset_inventory",
                    "message": (
                        f"Preview ready: {len(assets_preview)} assets waiting for approval"
                    ),
                    "preview_count": len(assets_preview),
                    "preview_ready": True,
                    "phase_state": {
                        "preview_pending_approval": True,
                    },
                }

            # If approval exists, filter assets and proceed with creation
            logger.info(
                f"✅ User approved {len(approved_asset_ids)} assets. "
                "Proceeding with creation..."
            )

            # CRITICAL FIX (Issue #1072): Filter approved assets and merge user edits
            # This ensures user edits from preview screen are used instead of original data
            assets_data = filter_approved_assets(
                assets_data, approved_asset_ids, updated_assets_map
            )

            if not assets_data:
                logger.warning("⚠️ No approved assets to create")
                return {
                    "status": "completed",
                    "phase": "asset_inventory",
                    "message": "No assets were approved for creation",
                    "assets_created": 0,
                    "execution_time": "0.001s",
                }

            # Step 1: Bulk conflict detection (single query per field type) - NEW
            logger.info(
                f"🔄 Processing {len(assets_data)} assets with bulk conflict detection"
            )

            conflict_free, conflicts_data = await bulk_prepare_conflicts(
                asset_service,
                assets_data,
                UUID(client_account_id),
                UUID(engagement_id),
            )

            # Step 2: Create conflict-free assets FIRST (before pausing for conflicts)
            # CC CRITICAL FIX: Must create conflict-free assets BEFORE pausing
            # Otherwise, auto-execution will re-run the phase and create duplicate conflicts
            created_assets, duplicate_assets, failed_count = (
                await create_conflict_free_assets(
                    asset_service, conflict_free, master_flow_id, db_session
                )
            )

            # Step 3: If conflicts detected, store and pause flow - NEW
            if conflicts_data:
                return await handle_conflicts(
                    conflicts_data=conflicts_data,
                    created_assets=created_assets,
                    duplicate_assets=duplicate_assets,
                    failed_count=failed_count,
                    raw_records=raw_records,
                    db_session=db_session,
                    client_account_id=str(client_account_id),
                    engagement_id=str(engagement_id),
                    data_import_id=str(data_import_id),
                    discovery_flow_id=str(discovery_flow_id),
                    master_flow_id=str(master_flow_id),
                )

            # Step 4: No conflicts - proceed with normal completion
            logger.info("✅ No conflicts detected, proceeding with phase completion")

            # Calculate totals BEFORE determining if flow should be marked complete
            total_created = len(created_assets)
            total_duplicates = len(duplicate_assets)
            has_successful_assets = total_created > 0 or total_duplicates > 0

            # Only mark records as processed if we have assets (created or duplicates)
            if has_successful_assets:
                all_assets = created_assets + duplicate_assets
                await mark_records_processed(db_session, raw_records, all_assets)

                # Mark asset_inventory phase as complete and complete the discovery flow
                # This is the final phase of discovery, so mark flow as completed (Qodo Issue #2)
                # BUT only if assets were successfully created or duplicates found
                await persist_asset_inventory_completion(
                    db_session,
                    flow_id=str(discovery_flow_id),
                    client_account_id=str(client_account_id),
                    engagement_id=str(engagement_id),
                    mark_flow_complete=True,  # Single source of truth for completion
                )

                # Mark assets as created in flow_persistence_data (Issue #907)
                await mark_assets_created(
                    master_flow_repo, master_flow_id, len(created_assets), db_session
                )
            else:
                # All assets failed - don't mark flow as complete
                logger.error(
                    f"❌ All assets failed to create - not marking flow as complete. "
                    f"Created: {total_created}, Duplicates: {total_duplicates}, Failed: {failed_count}"
                )
                # Still mark phase as complete to prevent re-execution, but don't mark flow as complete
                await persist_asset_inventory_completion(
                    db_session,
                    flow_id=str(discovery_flow_id),
                    client_account_id=str(client_account_id),
                    engagement_id=str(engagement_id),
                    mark_flow_complete=False,  # Don't mark flow complete if all assets failed
                )

            # Transaction will be committed by caller

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
                message = f"All {failed_count} assets failed to create. Flow not marked as completed."

            # Return status based on whether assets were successfully processed
            return {
                "status": "completed" if has_successful_assets else "failed",
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
