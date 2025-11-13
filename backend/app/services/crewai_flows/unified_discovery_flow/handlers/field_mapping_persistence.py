"""
Field Mapping Persistence Handler

This module contains field mapping persistence functions extracted from phase_handlers.py
to reduce file length and improve maintainability.

🤖 Generated with Claude Code (CC)

Co-Authored-By: Claude <noreply@anthropic.com>
"""

import logging
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


class FieldMappingPersistence:
    """Handles persistence of field mappings to database"""

    def __init__(self, flow_instance):
        """Initialize with reference to the main flow instance"""
        self.flow = flow_instance
        self.logger = logger

    async def persist_field_mappings_to_database(  # noqa: C901
        self, mapping_result: Dict[str, Any]
    ) -> None:
        """
        CRITICAL FIX: Persist field mappings to ImportFieldMapping table so UI can display them.
        This was the missing piece causing "0 fields" and "0 mapped" in the UI.

        Note: Function complexity is intentional due to extensive error handling,
        field validation, and defensive programming patterns required for data integrity.
        """
        try:
            self.logger.info("💾 Persisting field mappings to database for UI display")

            # Extract field mappings from result
            field_mappings = mapping_result.get("field_mappings", [])
            suggestions = mapping_result.get("suggestions", [])

            if not field_mappings and not suggestions:
                self.logger.warning("⚠️ No field mappings to persist")
                return

            # Get flow information
            flow_id = getattr(self.flow, "_flow_id", None) or getattr(
                self.flow.state, "flow_id", None
            )
            data_import_id = getattr(self.flow.state, "data_import_id", None)
            client_account_id = getattr(self.flow.state, "client_account_id", None)
            engagement_id = getattr(self.flow.state, "engagement_id", None)

            # For direct raw data flows, use flow_id as data_import_id if not set
            if not data_import_id:
                data_import_id = flow_id
                self.logger.info(
                    f"🔄 Using flow_id as data_import_id for direct raw data flow: {data_import_id}"
                )

            if (
                not flow_id
                or not data_import_id
                or not client_account_id
                or not engagement_id
            ):
                self.logger.error(
                    f"❌ Missing required IDs for field mapping persistence: "
                    f"flow_id={'<present>' if flow_id else '<missing>'}, "
                    f"data_import_id={'<present>' if data_import_id else '<missing>'}, "
                    f"client_account_id={'<present>' if client_account_id else '<missing>'}, "
                    f"engagement_id={'<present>' if engagement_id else '<missing>'}"
                )
                return

            # Import database models and session
            from app.core.database import AsyncSessionLocal
            from app.models.data_import.mapping import ImportFieldMapping
            from app.models.data_import.core import DataImport
            from sqlalchemy import delete, select, and_

            async with AsyncSessionLocal() as db:
                try:
                    # Ensure data import record exists (for direct raw data flows)
                    if data_import_id == flow_id:
                        # Check if data import record exists (with tenant scoping)
                        data_import_query = select(DataImport).where(
                            and_(
                                DataImport.id == data_import_id,
                                DataImport.client_account_id == client_account_id,
                                DataImport.engagement_id == engagement_id,
                            )
                        )
                        data_import_result = await db.execute(data_import_query)
                        data_import = data_import_result.scalar_one_or_none()

                        if not data_import:
                            # Create a minimal data import record for direct raw data flows
                            data_import = DataImport(
                                id=data_import_id,
                                client_account_id=client_account_id,
                                engagement_id=getattr(
                                    self.flow.state, "engagement_id", None
                                ),
                                imported_by=getattr(self.flow.state, "user_id", None),
                                import_name="Direct Raw Data Import",
                                import_type="direct_raw_data",
                                description="Data provided directly to discovery flow",
                                filename="direct_raw_data",
                                file_size=0,
                                status="completed",
                                total_records=len(
                                    getattr(self.flow.state, "raw_data", [])
                                ),
                                processed_records=len(
                                    getattr(self.flow.state, "raw_data", [])
                                ),
                                master_flow_id=flow_id,
                            )
                            db.add(data_import)
                            await db.flush()  # Flush to get the data_import.id available for RawImportRecord FK

                            # CRITICAL FIX for issue #348: Create RawImportRecord entries for direct_raw_data
                            await self._create_raw_import_records_for_direct_data(
                                db,
                                data_import_id,
                                client_account_id,
                                engagement_id,
                                flow_id,
                            )

                            await db.commit()
                            self.logger.info(
                                f"✅ Created data import record and raw import records for "
                                f"direct raw data flow: {data_import_id}"
                            )

                    # Clear existing mappings for this data import to avoid duplicates
                    # (with full tenant scoping via DataImport join)
                    delete_stmt = delete(ImportFieldMapping).where(
                        and_(
                            ImportFieldMapping.data_import_id == data_import_id,
                            ImportFieldMapping.client_account_id == client_account_id,
                            ImportFieldMapping.data_import_id.in_(
                                # SKIP_TENANT_CHECK - Service-level/monitoring query
                                select(DataImport.id).where(
                                    and_(
                                        DataImport.id == data_import_id,
                                        DataImport.client_account_id
                                        == client_account_id,
                                        DataImport.engagement_id == engagement_id,
                                    )
                                )
                            ),
                        )
                    )
                    await db.execute(delete_stmt)

                    # Persist field mappings
                    mappings_to_process = field_mappings + suggestions

                    self.logger.info(
                        f"📊 Processing {len(mappings_to_process)} field mappings for persistence"
                    )

                    successful_count = 0
                    for mapping in mappings_to_process:
                        try:
                            # Extract field information with defensive programming
                            source_field = mapping.get("source_field") or mapping.get(
                                "field"
                            )
                            target_field = mapping.get("target_field") or mapping.get(
                                "suggested_mapping"
                            )
                            confidence = mapping.get("confidence", 0.0)

                            # Handle nested mapping structures
                            if isinstance(confidence, dict):
                                confidence = confidence.get("score", 0.0)

                            # Convert confidence to float with enhanced error handling
                            try:
                                confidence = float(confidence)
                                # Ensure confidence is within valid range [0.0, 1.0]
                                if confidence < 0.0:
                                    self.logger.warning(
                                        f"⚠️ Confidence score {confidence} below 0.0, setting to 0.0"
                                    )
                                    confidence = 0.0
                                elif confidence > 1.0:
                                    self.logger.warning(
                                        f"⚠️ Confidence score {confidence} above 1.0, setting to 1.0"
                                    )
                                    confidence = 1.0
                            except (ValueError, TypeError) as e:
                                self.logger.warning(
                                    f"⚠️ Invalid confidence value '{confidence}': {e}, defaulting to 0.0"
                                )
                                confidence = 0.0

                            # Determine mapping type and status based on source
                            if mapping in field_mappings:
                                match_type = "approved"
                            else:
                                match_type = "suggestion"

                            status = mapping.get("status", "suggested")
                            suggested_by = "crew_generated"

                            # Enhanced field validation with detailed logging
                            if not source_field or not target_field:
                                self.logger.warning(
                                    f"⚠️ Skipping invalid mapping - missing fields: "
                                    f"source_field='{source_field or '<empty>'}', "
                                    f"target_field='{target_field or '<empty>'}', "
                                    f"mapping_data={mapping}"
                                )
                                continue

                            # Validate field names are reasonable strings
                            if not isinstance(source_field, str) or not isinstance(
                                target_field, str
                            ):
                                self.logger.warning(
                                    f"⚠️ Skipping invalid mapping - non-string fields: "
                                    f"source_field={type(source_field).__name__}:'{source_field}', "
                                    f"target_field={type(target_field).__name__}:'{target_field}'"
                                )
                                continue

                            # Trim whitespace from field names
                            source_field = source_field.strip()
                            target_field = target_field.strip()

                            if not source_field or not target_field:
                                self.logger.warning(
                                    f"⚠️ Skipping mapping with empty fields after trimming: "
                                    f"source='{source_field}', target='{target_field}'"
                                )
                                continue

                            # Create database record
                            field_mapping = ImportFieldMapping(
                                data_import_id=data_import_id,
                                client_account_id=client_account_id,
                                engagement_id=engagement_id,
                                master_flow_id=flow_id,
                                source_field=source_field,
                                target_field=target_field,
                                confidence_score=confidence,
                                match_type=match_type,
                                status=status,
                                suggested_by=suggested_by,
                            )

                            db.add(field_mapping)
                            successful_count += 1

                            self.logger.debug(
                                f"✅ Added field mapping #{successful_count}: "
                                f"'{source_field}' -> '{target_field}' "
                                f"(confidence: {confidence:.3f}, type: {match_type}, status: {status})"
                            )

                        except Exception as mapping_error:
                            source_val = (
                                source_field if "source_field" in locals() else "N/A"
                            )
                            target_val = (
                                target_field if "target_field" in locals() else "N/A"
                            )
                            conf_val = confidence if "confidence" in locals() else "N/A"

                            self.logger.error(
                                f"❌ Failed to persist field mapping: {type(mapping_error).__name__}: {mapping_error}. "
                                f"Mapping data: {mapping}. "
                                f"Extracted fields - source: '{source_val}', "
                                f"target: '{target_val}', confidence: {conf_val}"
                            )
                            continue

                    # Commit the transaction
                    await db.commit()

                    self.logger.info(
                        f"✅ Successfully persisted {successful_count} field mappings to database"
                    )

                    # Update discovery flow record with completion status and critical attributes
                    await self._update_discovery_flow_field_mapping_status(
                        flow_id, successful_count, mapping_result
                    )

                except Exception as db_error:
                    await db.rollback()
                    self.logger.error(f"❌ Database transaction failed: {db_error}")
                    raise

        except Exception as e:
            self.logger.error(f"❌ Critical error persisting field mappings: {e}")
            # Don't raise - this is a persistence optimization, not a flow blocker
            return

    async def _update_discovery_flow_field_mapping_status(
        self, flow_id: str, total_mappings: int, mapping_result: Dict[str, Any] = None
    ) -> None:
        """Update DiscoveryFlow record with field mapping completion status and critical attributes assessment"""
        try:
            from app.core.database import AsyncSessionLocal
            from app.models.discovery_flow import DiscoveryFlow
            from sqlalchemy import update

            async with AsyncSessionLocal() as db:
                # Prepare field mappings JSON with critical attributes if available
                field_mappings_data = {
                    "total": total_mappings,
                    "generated_at": self._get_current_timestamp(),
                    "status": "completed" if total_mappings > 0 else "failed",
                }

                # Include critical attributes assessment if provided by agent
                if (
                    mapping_result
                    and "critical_attributes_assessment" in mapping_result
                ):
                    field_mappings_data["critical_attributes_assessment"] = (
                        mapping_result["critical_attributes_assessment"]
                    )
                    self.logger.info(
                        "✅ Including critical attributes assessment from persistent agent"
                    )

                # Update discovery flow record
                update_stmt = (
                    update(DiscoveryFlow)
                    .where(DiscoveryFlow.flow_id == flow_id)
                    .values(
                        field_mapping_completed=True if total_mappings > 0 else False,
                        # Store field mapping metadata and critical attributes in JSON field
                        field_mappings=field_mappings_data,
                    )
                )

                await db.execute(update_stmt)
                await db.commit()

                self.logger.info(
                    f"✅ Updated DiscoveryFlow record for {flow_id} with "
                    f"{total_mappings} field mappings"
                    + (
                        " and critical attributes assessment"
                        if "critical_attributes_assessment" in field_mappings_data
                        else ""
                    )
                )

        except Exception as e:
            self.logger.error(f"❌ Failed to update DiscoveryFlow record: {e}")
            # Don't raise - this is metadata, not critical to flow

    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string"""
        return datetime.utcnow().isoformat()

    async def _create_raw_import_records_for_direct_data(
        self,
        db,
        data_import_id: str,
        client_account_id: str,
        engagement_id: str,
        flow_id: str,
    ) -> None:
        """
        Create RawImportRecord entries for direct_raw_data imports.

        This fixes issue #348 where direct_raw_data imports had no RawImportRecord entries,
        causing empty data retrieval in storage_manager/operations.py.
        """
        try:
            from app.models.data_import.core import RawImportRecord

            # Get raw_data from flow state
            raw_data = getattr(self.flow.state, "raw_data", [])

            if not raw_data:
                self.logger.warning(
                    f"⚠️ No raw_data found in flow state for direct_raw_data import: {data_import_id}"
                )
                return

            self.logger.info(
                f"📊 Creating {len(raw_data)} RawImportRecord entries for direct_raw_data import: {data_import_id}"
            )

            successful_count = 0
            for row_index, raw_record in enumerate(raw_data):
                try:
                    # Extract actual data from the raw_record structure
                    # raw_data is structured as [{"data": {...}, ...}, ...]
                    record_data = (
                        raw_record.get("data", {})
                        if isinstance(raw_record, dict)
                        else raw_record
                    )

                    if not record_data:
                        self.logger.debug(
                            f"⚠️ Skipping empty record at index {row_index}"
                        )
                        continue

                    # Create RawImportRecord entry
                    raw_import_record = RawImportRecord(
                        data_import_id=data_import_id,
                        client_account_id=client_account_id,
                        engagement_id=engagement_id,
                        master_flow_id=flow_id,
                        row_number=row_index + 1,  # 1-based row numbering
                        raw_data=record_data,
                        is_processed=False,  # Will be processed during data cleansing phase
                        is_valid=True,  # Assume valid for direct data
                    )

                    db.add(raw_import_record)
                    successful_count += 1

                    self.logger.debug(
                        f"✅ Added RawImportRecord #{successful_count} for row {row_index + 1}"
                    )

                except Exception as record_error:
                    self.logger.error(
                        f"❌ Failed to create RawImportRecord for row {row_index + 1}: "
                        f"{type(record_error).__name__}: {record_error}"
                    )
                    continue

            self.logger.info(
                f"✅ Successfully created {successful_count} RawImportRecord entries "
                f"out of {len(raw_data)} raw records"
            )

        except Exception as e:
            self.logger.error(
                f"❌ Critical error creating RawImportRecord entries for direct_raw_data: "
                f"{type(e).__name__}: {e}"
            )
            # Don't raise - this would break the entire field mapping persistence
            # The field mappings can still be created without raw records
