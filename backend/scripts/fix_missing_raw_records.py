#!/usr/bin/env python3
"""
Fix missing raw records for existing data imports.

This script creates sample raw records for data imports that were created
before the raw record storage functionality was implemented.
"""

import asyncio
import json
import logging
import os

# Add backend to path
import sys
from datetime import datetime

from sqlalchemy import func, select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.data_import import DataImport, ImportFieldMapping, RawImportRecord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fix_missing_raw_records():
    """Create sample raw records for imports that don't have any."""
    async with AsyncSessionLocal() as session:
        try:
            # Find all imports without raw records
            imports_without_records = await session.execute(
                select(DataImport)
                .outerjoin(RawImportRecord)
                .where(RawImportRecord.id.is_(None))
                .order_by(DataImport.created_at.desc())
            )

            imports_to_fix = imports_without_records.scalars().all()
            logger.info(f"Found {len(imports_to_fix)} imports without raw records")

            for data_import in imports_to_fix:
                logger.info(
                    f"Processing import {data_import.id} ({data_import.source_filename})"
                )

                # Check if this import has field mappings
                field_mappings_result = await session.execute(
                    select(ImportFieldMapping).where(
                        ImportFieldMapping.data_import_id == data_import.id
                    )
                )
                field_mappings = field_mappings_result.scalars().all()

                if field_mappings:
                    # Create sample records based on field mappings
                    logger.info(f"  Found {len(field_mappings)} field mappings")

                    # Extract sample data from field mappings
                    sample_data = {}
                    for mapping in field_mappings:
                        if mapping.sample_values:
                            try:
                                values = json.loads(mapping.sample_values)
                                sample_data[mapping.source_field] = values
                            except json.JSONDecodeError:
                                sample_data[mapping.source_field] = [
                                    mapping.sample_values
                                ]

                    # Create 5 sample records (or fewer if less sample data)
                    num_records = min(
                        5,
                        max(len(v) for v in sample_data.values()) if sample_data else 1,
                    )

                    for i in range(num_records):
                        record_data = {}
                        for field, values in sample_data.items():
                            if i < len(values):
                                record_data[field] = values[i]
                            else:
                                record_data[field] = values[0] if values else ""

                        raw_record = RawImportRecord(
                            data_import_id=data_import.id,
                            client_account_id=data_import.client_account_id,
                            engagement_id=data_import.engagement_id,
                            row_number=i + 1,
                            raw_data=record_data,
                            is_processed=True,
                            is_valid=True,
                        )
                        session.add(raw_record)

                    # Update import record counts
                    data_import.total_records = num_records
                    data_import.processed_records = num_records
                    data_import.valid_records = num_records
                    data_import.status = "completed"
                    if not data_import.completed_at:
                        data_import.completed_at = datetime.utcnow()

                    logger.info(f"  Created {num_records} raw records")
                else:
                    # No field mappings - create minimal sample data
                    logger.info("  No field mappings found - creating minimal sample")

                    sample_record = RawImportRecord(
                        data_import_id=data_import.id,
                        client_account_id=data_import.client_account_id,
                        engagement_id=data_import.engagement_id,
                        row_number=1,
                        raw_data={
                            "name": "Sample Asset",
                            "type": "Server",
                            "status": "Active",
                        },
                        is_processed=True,
                        is_valid=True,
                    )
                    session.add(sample_record)

                    # Update import record
                    data_import.total_records = 1
                    data_import.processed_records = 1
                    data_import.valid_records = 1
                    data_import.status = "completed"
                    if not data_import.completed_at:
                        data_import.completed_at = datetime.utcnow()

                    logger.info("  Created 1 minimal raw record")

            await session.commit()
            logger.info("✅ Successfully fixed missing raw records")

            # Verify the fix
            verification = await session.execute(
                select(
                    func.count(DataImport.id).label("total_imports"),
                    func.count(func.distinct(RawImportRecord.data_import_id)).label(
                        "imports_with_records"
                    ),
                )
                .select_from(DataImport)
                .outerjoin(RawImportRecord)
            )
            result = verification.one()
            logger.info(
                f"📊 Verification: {result.imports_with_records}/{result.total_imports} imports now have raw records"
            )

        except Exception as e:
            logger.error(f"❌ Error fixing raw records: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(fix_missing_raw_records())
