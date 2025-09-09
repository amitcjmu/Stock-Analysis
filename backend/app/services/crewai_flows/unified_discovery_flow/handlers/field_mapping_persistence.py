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

    async def persist_field_mappings_to_database(
        self, mapping_result: Dict[str, Any]
    ) -> None:
        """
        CRITICAL FIX: Persist field mappings to ImportFieldMapping table so UI can display them.
        This was the missing piece causing "0 fields" and "0 mapped" in the UI.
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

            # For direct raw data flows, use flow_id as data_import_id if not set
            if not data_import_id:
                data_import_id = flow_id
                self.logger.info(
                    f"🔄 Using flow_id as data_import_id for direct raw data flow: {data_import_id}"
                )

            if not flow_id or not data_import_id or not client_account_id:
                self.logger.error(
                    f"❌ Missing required IDs: flow_id={flow_id}, "
                    f"data_import_id={data_import_id}, client_account_id={client_account_id}"
                )
                return

            # Import database models and session
            from app.core.database import AsyncSessionLocal
            from app.models.data_import.mapping import ImportFieldMapping
            from app.models.data_import.import_model import DataImport
            from sqlalchemy import delete, select

            async with AsyncSessionLocal() as db:
                try:
                    # Ensure data import record exists (for direct raw data flows)
                    if data_import_id == flow_id:
                        # Check if data import record exists
                        data_import_query = select(DataImport).where(
                            DataImport.id == data_import_id
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
                            await db.commit()
                            self.logger.info(
                                f"✅ Created data import record for direct raw data flow: {data_import_id}"
                            )

                    # Clear existing mappings for this data import to avoid duplicates
                    delete_stmt = delete(ImportFieldMapping).where(
                        ImportFieldMapping.data_import_id == data_import_id
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

                            # Convert confidence to float if it's a string
                            try:
                                confidence = float(confidence)
                            except (ValueError, TypeError):
                                confidence = 0.0

                            # Determine mapping type and status based on source
                            if mapping in field_mappings:
                                match_type = "approved"
                            else:
                                match_type = "suggestion"

                            status = mapping.get("status", "suggested")
                            suggested_by = "crew_generated"

                            if not source_field or not target_field:
                                self.logger.warning(
                                    f"⚠️ Skipping mapping with missing fields: "
                                    f"source={source_field}, target={target_field}"
                                )
                                continue

                            # Create database record
                            field_mapping = ImportFieldMapping(
                                data_import_id=data_import_id,
                                client_account_id=client_account_id,
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
                                f"✅ Added mapping: {source_field} -> {target_field} "
                                f"(confidence: {confidence:.2f})"
                            )

                        except Exception as mapping_error:
                            self.logger.error(
                                f"❌ Failed to persist individual mapping {mapping}: {mapping_error}"
                            )
                            continue

                    # Commit the transaction
                    await db.commit()

                    self.logger.info(
                        f"✅ Successfully persisted {successful_count} field mappings to database"
                    )

                    # Update discovery flow record with completion status
                    await self._update_discovery_flow_field_mapping_status(
                        flow_id, successful_count
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
        self, flow_id: str, total_mappings: int
    ) -> None:
        """Update DiscoveryFlow record with field mapping completion status"""
        try:
            from app.core.database import AsyncSessionLocal
            from app.models.discovery_flow import DiscoveryFlow
            from sqlalchemy import update

            async with AsyncSessionLocal() as db:
                # Update discovery flow record
                update_stmt = (
                    update(DiscoveryFlow)
                    .where(DiscoveryFlow.flow_id == flow_id)
                    .values(
                        field_mapping_completed=True if total_mappings > 0 else False,
                        # Store field mapping metadata in JSON field if it exists
                        field_mappings={
                            "total": total_mappings,
                            "generated_at": self._get_current_timestamp(),
                            "status": "completed" if total_mappings > 0 else "failed",
                        },
                    )
                )

                await db.execute(update_stmt)
                await db.commit()

                self.logger.info(
                    f"✅ Updated DiscoveryFlow record for {flow_id} with "
                    f"{total_mappings} field mappings"
                )

        except Exception as e:
            self.logger.error(f"❌ Failed to update DiscoveryFlow record: {e}")
            # Don't raise - this is metadata, not critical to flow

    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string"""
        return datetime.utcnow().isoformat()
