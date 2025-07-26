#!/usr/bin/env python3
"""
Test script to verify the foreign key constraint fix.

This tests the specific transaction management issue where master_flow_id
foreign key constraints were failing due to transaction timing.
"""

import asyncio
import logging
import uuid as uuid_pkg
from datetime import datetime

from sqlalchemy import text

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.schemas.data_import_schemas import (
    FileMetadata,
    StoreImportRequest,
    UploadContext,
)
from app.services.data_import.import_storage_handler import ImportStorageHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_foreign_key_fix():
    """Test that master flow foreign key constraints work properly"""

    async with AsyncSessionLocal() as db:
        try:
            # Setup test context
            context = RequestContext(
                client_account_id="11111111-1111-1111-1111-111111111111",
                engagement_id="22222222-2222-2222-2222-222222222222",
                user_id="33333333-3333-3333-3333-333333333333",
            )

            # Create test data
            test_data = [
                {"hostname": "server1", "os": "linux", "memory": "16GB"},
                {"hostname": "server2", "os": "windows", "memory": "32GB"},
                {"hostname": "server3", "os": "linux", "memory": "8GB"},
            ]

            # Create import request
            import_id = str(uuid_pkg.uuid4())
            store_request = StoreImportRequest(
                file_data=test_data,
                metadata=FileMetadata(
                    filename="test_servers.csv", size=1024, type="text/csv"
                ),
                upload_context=UploadContext(
                    validation_id=import_id,
                    intended_type="cmdb",
                    upload_timestamp=datetime.utcnow().isoformat(),
                ),
            )

            # Initialize import handler
            handler = ImportStorageHandler(db, context.client_account_id)

            logger.info("🧪 Testing foreign key constraint fix...")

            # Execute import (this should not cause foreign key violations)
            result = await handler.handle_import(store_request, context)

            if result.success:
                logger.info(f"✅ Import successful: {result.flow_id}")

                # Use a fresh database session for verification to avoid transaction issues
                async with AsyncSessionLocal() as verify_db:
                    # Verify master flow exists in database
                    check_master_flow = await verify_db.execute(
                        text(
                            "SELECT flow_id, flow_status FROM crewai_flow_state_extensions WHERE flow_id = :flow_id"
                        ),
                        {"flow_id": result.flow_id},
                    )
                    master_flow = check_master_flow.first()

                    if master_flow:
                        logger.info(
                            f"✅ Master flow found: {master_flow.flow_id} (status: {master_flow.flow_status})"
                        )
                    else:
                        logger.error(f"❌ Master flow not found: {result.flow_id}")
                        return False

                    # Verify data import linkage
                    check_data_import = await verify_db.execute(
                        text(
                            "SELECT id, master_flow_id FROM data_imports WHERE master_flow_id = :flow_id"
                        ),
                        {"flow_id": result.flow_id},
                    )
                    data_imports = check_data_import.fetchall()

                    if data_imports:
                        logger.info(
                            f"✅ Data import linkage successful: {len(data_imports)} records linked"
                        )
                        for di in data_imports:
                            logger.info(
                                f"  - DataImport {di.id} → MasterFlow {di.master_flow_id}"
                            )
                    else:
                        logger.warning("⚠️ No data imports linked to master flow")

                    # Verify field mappings linkage
                    check_field_mappings = await verify_db.execute(
                        text(
                            "SELECT COUNT(*) as count FROM import_field_mappings WHERE master_flow_id = :flow_id"
                        ),
                        {"flow_id": result.flow_id},
                    )
                    field_mapping_count = check_field_mappings.scalar()

                    if field_mapping_count and field_mapping_count > 0:
                        logger.info(
                            f"✅ Field mappings linkage successful: {field_mapping_count} mappings linked"
                        )
                    else:
                        logger.warning("⚠️ No field mappings linked to master flow")

                    # Verify raw import records linkage
                    check_raw_records = await verify_db.execute(
                        text(
                            "SELECT COUNT(*) as count FROM raw_import_records WHERE master_flow_id = :flow_id"
                        ),
                        {"flow_id": result.flow_id},
                    )
                    raw_record_count = check_raw_records.scalar()

                    if raw_record_count and raw_record_count > 0:
                        logger.info(
                            f"✅ Raw import records linkage successful: {raw_record_count} records linked"
                        )
                    else:
                        logger.warning("⚠️ No raw import records linked to master flow")

                logger.info("🎉 Foreign key constraint test completed successfully!")
                return True

            else:
                logger.error(f"❌ Import failed: {result.message}")
                return False

        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return False


async def main():
    """Main test function"""
    logger.info("🚀 Starting foreign key constraint fix test...")

    success = await test_foreign_key_fix()

    if success:
        logger.info("✅ All tests passed! Foreign key constraints are working properly.")
    else:
        logger.error("❌ Test failed! Foreign key constraint issue persists.")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
