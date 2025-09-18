"""
Database Operations Module

Handles all database interactions for data cleansing operations.
"""

import logging
import uuid
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DatabaseOperations:
    """Handles database operations for data cleansing"""

    def __init__(self, state, db_session=None):
        self.state = state
        self.db_session = db_session

    async def get_raw_import_records_with_ids(self) -> List[Dict[str, Any]]:
        """Get raw import records with IDs and tenant scoping"""
        from sqlalchemy import select
        from app.models.data_import.core import RawImportRecord

        # Use existing session if available
        if self.db_session:
            session = self.db_session
        else:
            from app.core.database import AsyncSessionLocal

            session = AsyncSessionLocal()

        try:
            data_import_id = getattr(self.state, "data_import_id", None)
            if not data_import_id:
                logger.error("❌ No data_import_id found in state")
                return []

            # WITH TENANT SCOPING - Ensure proper UUID conversion
            query = select(RawImportRecord).where(
                (
                    RawImportRecord.data_import_id == uuid.UUID(data_import_id)
                    if isinstance(data_import_id, str)
                    else data_import_id
                ),
                (
                    RawImportRecord.client_account_id
                    == uuid.UUID(self.state.client_account_id)
                    if isinstance(self.state.client_account_id, str)
                    else self.state.client_account_id
                ),
                (
                    RawImportRecord.engagement_id == uuid.UUID(self.state.engagement_id)
                    if isinstance(self.state.engagement_id, str)
                    else self.state.engagement_id
                ),
            )

            result = await session.execute(query)
            raw_records = result.scalars().all()

            logger.info(f"📊 Found {len(raw_records)} raw import records")

            # Convert to dict format with ID preservation
            records = []
            for record in raw_records:
                record_data = {
                    "raw_import_record_id": str(record.id),  # Preserve for ID mapping
                    "row_number": record.row_number,
                    "raw_data": record.raw_data,
                    "cleansed_data": record.cleansed_data,
                    **record.raw_data,  # Flatten for easy access
                }
                records.append(record_data)

            return records

        finally:
            if not self.db_session:
                await session.close()

    async def update_cleansed_data_sync(
        self, cleaned_data: List[Dict[str, Any]]
    ) -> int:
        """Update raw records with cleansed data - SYNCHRONOUS, no fire-and-forget
        Returns: Number of records successfully updated
        """
        # Use existing session if available, otherwise create new one
        if self.db_session:
            db = self.db_session
            should_commit = False  # Don't commit if using provided session
        else:
            from app.core.database import AsyncSessionLocal

            db = AsyncSessionLocal()
            should_commit = True  # Commit if we created the session

        try:
            from app.services.data_import.storage_manager import ImportStorageManager

            storage_manager = ImportStorageManager(
                db, str(self.state.client_account_id)
            )

            data_import_id = uuid.UUID(self.state.data_import_id)

            # Get the master_flow_id from state (it should be the same as flow_id)
            master_flow_id = getattr(self.state, "master_flow_id", self.state.flow_id)

            updated_count = await storage_manager.update_raw_records_with_cleansed_data(
                data_import_id=data_import_id,
                cleansed_data=cleaned_data,
                validation_results=getattr(self.state, "data_validation_results", None),
                master_flow_id=master_flow_id,  # Pass master_flow_id for proper asset association
            )

            if should_commit:
                await db.commit()

            logger.info(f"✅ Updated {updated_count} raw records with cleansed data")
            return updated_count

        finally:
            if should_commit and db:
                await db.close()

    async def verify_cleansed_data_in_database(self) -> int:
        """Verify that cleansed data exists in the database for this import
        Returns: Count of records with cleansed_data
        """
        from sqlalchemy import select, func
        from app.models.data_import.core import RawImportRecord

        # Use existing session if available
        if self.db_session:
            session = self.db_session
            should_close = False
        else:
            from app.core.database import AsyncSessionLocal

            session = AsyncSessionLocal()
            should_close = True

        try:
            data_import_id = getattr(self.state, "data_import_id", None)
            if not data_import_id:
                logger.error("❌ No data_import_id found in state for verification")
                return 0

            # Count records with cleansed_data (non-null)
            query = select(func.count()).where(
                (
                    RawImportRecord.data_import_id == uuid.UUID(data_import_id)
                    if isinstance(data_import_id, str)
                    else data_import_id
                ),
                (
                    RawImportRecord.client_account_id
                    == uuid.UUID(self.state.client_account_id)
                    if isinstance(self.state.client_account_id, str)
                    else self.state.client_account_id
                ),
                (
                    RawImportRecord.engagement_id == uuid.UUID(self.state.engagement_id)
                    if isinstance(self.state.engagement_id, str)
                    else self.state.engagement_id
                ),
                RawImportRecord.cleansed_data.isnot(
                    None
                ),  # Only count non-null cleansed_data
            )

            result = await session.execute(query)
            count = result.scalar() or 0

            logger.info(
                f"📊 Verification: {count} records have cleansed_data in database"
            )
            return count

        except Exception as e:
            logger.error(f"❌ Failed to verify cleansed data in database: {e}")
            return 0

        finally:
            if should_close and session:
                await session.close()

    async def persist_phase_completion_to_database(self, phase_name: str):
        """Persist phase completion flag to the discovery_flows table"""
        try:
            from sqlalchemy import select
            from app.models.discovery_flow import DiscoveryFlow

            # Use existing session if available, otherwise create new one
            if self.db_session:
                db = self.db_session
                should_commit = False  # Don't commit if using provided session
            else:
                from app.core.database import AsyncSessionLocal

                db = AsyncSessionLocal()
                should_commit = True  # Commit if we created the session

            try:
                # Find the discovery flow by flow_id (not master_flow_id)
                flow_id = (
                    uuid.UUID(self.state.flow_id)
                    if isinstance(self.state.flow_id, str)
                    else self.state.flow_id
                )

                result = await db.execute(
                    select(DiscoveryFlow).where(
                        DiscoveryFlow.flow_id
                        == flow_id,  # Use flow_id, not master_flow_id
                        (
                            DiscoveryFlow.client_account_id
                            == uuid.UUID(self.state.client_account_id)
                            if isinstance(self.state.client_account_id, str)
                            else self.state.client_account_id
                        ),
                        (
                            DiscoveryFlow.engagement_id
                            == uuid.UUID(self.state.engagement_id)
                            if isinstance(self.state.engagement_id, str)
                            else self.state.engagement_id
                        ),
                    )
                )

                discovery_flow = result.scalar_one_or_none()

                if discovery_flow:
                    if phase_name == "data_cleansing":
                        discovery_flow.data_cleansing_completed = True
                        logger.info(
                            f"✅ Updated discovery_flow.data_cleansing_completed = True for flow {self.state.flow_id}"
                        )

                    if should_commit:
                        await db.commit()
                    else:
                        await db.flush()  # Flush changes if not committing

                    logger.info(
                        f"✅ Successfully persisted {phase_name} completion to database"
                    )
                else:
                    logger.warning(
                        f"⚠️ Could not find discovery flow for master_flow_id {self.state.flow_id}"
                    )

            finally:
                if should_commit and db:
                    await db.close()

        except Exception as e:
            logger.error(
                f"❌ Failed to persist {phase_name} completion to database: {e}"
            )
            # Don't raise the exception - phase completion should not fail the whole process
