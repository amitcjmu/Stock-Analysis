"""
Asset Inventory Executor - Base Class
Contains the main AssetInventoryExecutor class with interface methods.

CC: Implements actual asset creation from raw_import_records data
"""

import logging
from datetime import datetime
from typing import Dict, Any
from uuid import UUID

from app.services.asset_service import AssetService
from app.services.asset_service.deduplication import bulk_prepare_conflicts
from app.models.asset_conflict_resolution import AssetConflictResolution
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.core.context import RequestContext
from ..base_phase_executor import BasePhaseExecutor
from .queries import get_raw_records, get_field_mappings
from .commands import mark_records_processed, persist_asset_inventory_completion
from .transforms import transform_raw_record_to_asset

logger = logging.getLogger(__name__)


def serialize_uuids_for_jsonb(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert all UUID objects to strings for JSONB storage compatibility.

    PostgreSQL JSONB columns cannot directly store Python UUID objects.
    This function recursively converts all UUID instances to strings.

    Args:
        data: Dictionary potentially containing UUID objects

    Returns:
        Dictionary with all UUIDs converted to strings
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, UUID):
            result[key] = str(value)
        elif isinstance(value, dict):
            result[key] = serialize_uuids_for_jsonb(value)
        elif isinstance(value, list):
            result[key] = [
                (
                    serialize_uuids_for_jsonb(item)
                    if isinstance(item, dict)
                    else str(item) if isinstance(item, UUID) else item
                )
                for item in value
            ]
        else:
            result[key] = value
    return result


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
            # Get master flow to check for preview data and approval
            master_flow_repo = CrewAIFlowStateExtensionsRepository(
                db_session,
                str(client_account_id),
                str(engagement_id),
            )

            master_flow = await master_flow_repo.get_by_flow_id(str(master_flow_id))
            if not master_flow:
                logger.error(f"❌ Master flow {master_flow_id} not found")
                raise ValueError(f"Master flow {master_flow_id} not found")

            persistence_data = master_flow.flow_persistence_data or {}

            # Step 0: Check if preview data exists and if assets are approved
            assets_preview = persistence_data.get("assets_preview")
            approved_asset_ids = persistence_data.get("approved_asset_ids")
            assets_already_created = persistence_data.get("assets_created", False)

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
                logger.info(
                    f"📋 Storing {len(assets_data)} assets for preview (Issue #907)"
                )

                # Serialize assets_data for JSONB storage (convert UUIDs to strings)
                serialized_assets = []
                for i, asset in enumerate(assets_data):
                    serialized_asset = serialize_uuids_for_jsonb(asset)
                    # CC FIX (Issue #907): Use 'id' field for frontend compatibility
                    # Frontend AssetPreviewData interface expects 'id', not 'temp_id'
                    serialized_asset["id"] = f"asset-{i}"
                    serialized_assets.append(serialized_asset)

                # Store preview data in flow_persistence_data
                persistence_data["assets_preview"] = serialized_assets
                persistence_data["preview_generated_at"] = datetime.utcnow().isoformat()
                master_flow.flow_persistence_data = persistence_data

                # CC FIX (Issue #907): Mark JSONB column as modified for SQLAlchemy change tracking
                from sqlalchemy.orm.attributes import flag_modified

                flag_modified(master_flow, "flow_persistence_data")

                await db_session.commit()

                logger.info(
                    f"✅ Stored {len(serialized_assets)} assets for preview. "
                    "Waiting for user approval via /api/v1/asset-preview/{flow_id}/approve"
                )

                return {
                    "status": "paused",  # Per ADR-012: Child flow status
                    "phase": "asset_inventory",
                    "message": (
                        f"Preview ready: {len(serialized_assets)} assets transformed. "
                        "Waiting for user approval before database creation."
                    ),
                    "preview_count": len(serialized_assets),
                    "preview_ready": True,
                    "phase_state": {
                        "preview_pending_approval": True,
                    },
                }

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

            # Filter assets_data to only approved assets
            # Match by temp_id which was added during preview generation
            approved_assets_data = []
            for asset in assets_data:
                # During transformation, we need to check if this asset was approved
                # We'll match by index since temp_id was "asset-{i}"
                asset_index = assets_data.index(asset)
                temp_id = f"asset-{asset_index}"
                if temp_id in approved_asset_ids:
                    approved_assets_data.append(asset)

            logger.info(
                f"📋 Filtered to {len(approved_assets_data)} approved assets "
                f"(from {len(assets_data)} total)"
            )

            # Replace assets_data with approved subset
            assets_data = approved_assets_data

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
            logger.info(f"✅ Processing {len(conflict_free)} conflict-free assets")

            created_assets = []
            duplicate_assets = []
            failed_count = 0

            if conflict_free:
                # Create assets via service (transaction managed by caller)
                # CC: Don't start a new transaction - db_session already has an active transaction
                try:
                    results = await asset_service.bulk_create_or_update_assets(
                        conflict_free, flow_id=master_flow_id
                    )

                    # Categorize results by status
                    for asset, status in results:
                        if status == "created":
                            created_assets.append(asset)
                            logger.debug(f"✅ Created asset: {asset.name}")
                        elif status == "existed":
                            duplicate_assets.append(asset)
                            logger.debug(f"🔄 Duplicate asset skipped: {asset.name}")

                except Exception as e:
                    # If batch fails, fall back to individual processing
                    logger.warning(
                        f"⚠️ Batch processing failed, falling back to individual: {e}"
                    )
                    for asset_data in conflict_free:
                        try:
                            asset, status = await asset_service.create_or_update_asset(
                                asset_data, flow_id=master_flow_id
                            )

                            if status == "created":
                                created_assets.append(asset)
                                logger.debug(f"✅ Created asset: {asset.name}")
                            elif status == "existed":
                                duplicate_assets.append(asset)
                                logger.debug(
                                    f"🔄 Duplicate asset skipped: {asset.name}"
                                )

                        except Exception as e:
                            failed_count += 1
                            logger.error(
                                f"❌ Failed to create asset {asset_data.get('name', 'unnamed')}: {e}"
                            )

                # Flush to make asset IDs available for foreign key relationships
                await db_session.flush()

                logger.info(
                    f"✅ Created {len(created_assets)} conflict-free assets, "
                    f"{len(duplicate_assets)} duplicates, {failed_count} failed"
                )

            # Step 3: If conflicts detected, store and pause flow - NEW
            if conflicts_data:
                logger.warning(
                    f"⚠️ Detected {len(conflicts_data)} asset conflicts - pausing for user resolution"
                )

                # Step 3a: Get discovery flow record to obtain PK for FK constraint
                # CC FIX: Need both id (PK) and flow_id for different purposes
                discovery_repo = DiscoveryFlowRepository(
                    db_session, str(client_account_id), str(engagement_id)
                )
                # Query by flow_id (not master_flow_id) since they're typically the same
                flow_record = await discovery_repo.get_by_flow_id(
                    str(discovery_flow_id)
                )
                if not flow_record:
                    raise ValueError(
                        f"Discovery flow not found for flow_id {discovery_flow_id}"
                    )

                flow_pk_id = (
                    flow_record.id
                )  # UUID PK for FK constraint in conflict records
                logger.info(
                    f"📋 Retrieved discovery flow - PK: {flow_pk_id}, flow_id: {discovery_flow_id}"
                )

                # Store conflicts in database
                for conflict in conflicts_data:
                    # Serialize UUID objects for JSONB storage compatibility
                    serialized_new_asset_data = serialize_uuids_for_jsonb(
                        conflict["new_asset_data"]
                    )

                    conflict_record = AssetConflictResolution(
                        client_account_id=UUID(client_account_id),
                        engagement_id=UUID(engagement_id),
                        data_import_id=UUID(data_import_id) if data_import_id else None,
                        discovery_flow_id=flow_pk_id,  # Use PK for FK constraint
                        master_flow_id=UUID(master_flow_id),  # Indexed for filtering
                        conflict_type=conflict["conflict_type"],
                        conflict_key=conflict["conflict_key"],
                        existing_asset_id=conflict["existing_asset_id"],
                        existing_asset_snapshot=conflict["existing_asset_data"],
                        new_asset_data=serialized_new_asset_data,
                        resolution_status="pending",
                    )
                    db_session.add(conflict_record)

                await db_session.flush()

                # Step 3b: Mark raw records as processed for conflict-free assets
                # CC: Track which records have been processed (created as assets)
                all_processed_assets = created_assets + duplicate_assets
                if all_processed_assets:
                    await mark_records_processed(
                        db_session, raw_records, all_processed_assets
                    )
                    logger.info(
                        f"✅ Marked {len(all_processed_assets)} records as processed"
                    )

                # Step 3c: Mark phase as complete to prevent re-execution
                # CC CRITICAL: Set asset_inventory_completed=true even when pausing for conflicts
                # This prevents auto-execution from re-running the phase and creating duplicate conflicts
                await persist_asset_inventory_completion(
                    db_session,
                    flow_id=str(discovery_flow_id),
                    client_account_id=str(client_account_id),
                    engagement_id=str(engagement_id),
                    mark_flow_complete=False,  # Don't mark flow as complete yet (conflicts pending)
                )
                logger.info(
                    "✅ Marked asset_inventory phase as complete (with pending conflicts)"
                )

                # Step 3d: Pause flow via repository - use flow_id for WHERE clause
                # CC FIX: Pass flow_id (business identifier) not id (PK)
                await discovery_repo.set_conflict_resolution_pending(
                    UUID(discovery_flow_id),  # flow_id column for WHERE clause
                    conflict_count=len(conflicts_data),
                    data_import_id=UUID(data_import_id) if data_import_id else None,
                )

                # Step 3e: Return paused status
                return {
                    "status": "paused",  # Child flow status per ADR-012
                    "phase": "asset_inventory",
                    "message": f"Found {len(conflicts_data)} duplicate assets. User resolution required.",
                    "conflict_count": len(conflicts_data),
                    "conflict_free_count": len(conflict_free),
                    "assets_created": len(created_assets),
                    "assets_duplicates": len(duplicate_assets),
                    "assets_failed": failed_count,
                    "data_import_id": str(data_import_id) if data_import_id else None,
                    "phase_state": {
                        "conflict_resolution_pending": True,
                    },
                }

            # Step 4: No conflicts - proceed with normal completion
            logger.info("✅ No conflicts detected, proceeding with phase completion")

            # CC: Assets already created in Step 2, just mark records as processed
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

            # Mark assets as created in flow_persistence_data (Issue #907)
            # This prevents re-creation if phase re-runs
            persistence_data["assets_created"] = True
            persistence_data["assets_created_at"] = datetime.utcnow().isoformat()
            persistence_data["assets_created_count"] = len(created_assets)
            master_flow.flow_persistence_data = persistence_data

            # CC FIX (Issue #907): Mark JSONB column as modified for SQLAlchemy change tracking
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(master_flow, "flow_persistence_data")

            await db_session.flush()  # Persist the flag

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
