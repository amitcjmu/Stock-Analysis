#!/usr/bin/env python3
"""
Test script to re-create assets with the case-insensitive field fix.
Run this from the backend container to test the fix for Bug #521.
"""
import asyncio
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.data_import.core import RawImportRecord
from app.models.asset import Asset
from app.models.discovery_flow import DiscoveryFlow
from app.services.crewai_flows.handlers.phase_executors.asset_inventory_executor.transforms import (
    transform_raw_record_to_asset,
)


async def recreate_assets_for_flow():
    """Delete existing assets and recreate them using the fixed transform function."""

    flow_id = UUID("82e33f42-b162-497b-89c2-916ce0a7ec2c")
    client_account_id = UUID("11111111-1111-1111-1111-111111111111")
    engagement_id = UUID("22222222-2222-2222-2222-222222222222")

    # Create database engine
    engine = create_async_engine(str(settings.DATABASE_URL), echo=True)
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        try:
            print(f"\n🔍 Starting asset recreation for flow: {flow_id}")

            # Step 1: Delete existing assets
            print("\n🗑️  Deleting existing assets...")
            delete_stmt = delete(Asset).where(Asset.discovery_flow_id == flow_id)
            result = await session.execute(delete_stmt)
            deleted_count = result.rowcount
            await session.commit()
            print(f"✅ Deleted {deleted_count} existing assets")

            # Step 2: Get raw import records
            print("\n📥 Fetching raw import records...")

            # Get the data_import_id from discovery_flows
            flow_stmt = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
            flow_result = await session.execute(flow_stmt)
            discovery_flow = flow_result.scalar_one_or_none()

            if not discovery_flow:
                print(f"❌ Discovery flow not found: {flow_id}")
                return

            print(
                f"✅ Found discovery flow, data_import_id: {discovery_flow.data_import_id}"
            )

            # Get raw records
            records_stmt = (
                select(RawImportRecord)
                .where(RawImportRecord.data_import_id == discovery_flow.data_import_id)
                .order_by(RawImportRecord.row_number)
            )
            records_result = await session.execute(records_stmt)
            raw_records = records_result.scalars().all()

            print(f"✅ Found {len(raw_records)} raw import records")

            # Step 3: Transform and create assets
            print("\n🔄 Transforming records to assets...")
            created_assets = []

            for record in raw_records:
                # Show first record's raw data for debugging
                if record.row_number == 1:
                    print("\n📋 Sample raw data from first record:")
                    if record.cleansed_data:
                        print(
                            f"   Cleansed data keys: "
                            f"{list(record.cleansed_data.keys())[:10]}"
                        )
                    if record.raw_data:
                        print(f"   Raw data keys: {list(record.raw_data.keys())[:10]}")

                # Transform using the fixed function
                asset_data = transform_raw_record_to_asset(
                    record=record,
                    master_flow_id=(
                        str(discovery_flow.master_flow_id)
                        if discovery_flow.master_flow_id
                        else str(flow_id)
                    ),
                    discovery_flow_id=str(flow_id),
                    field_mappings={},
                )

                # Create asset model
                asset = Asset(
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    **asset_data,
                )

                session.add(asset)
                created_assets.append(
                    {
                        "name": asset.name,
                        "type": asset.asset_type,
                        "os": asset.operating_system,
                    }
                )

                print(
                    f"   ✅ Asset {record.row_number}: {asset.name} "
                    f"(type: {asset.asset_type}, OS: {asset.operating_system})"
                )

            # Commit all assets
            await session.commit()
            print(f"\n✅ Successfully created {len(created_assets)} assets")

            # Step 4: Verify results
            print("\n📊 Verification Summary:")
            print(f"   Total assets created: {len(created_assets)}")
            print(
                f"   Assets with real names: {sum(1 for a in created_assets if not a['name'].startswith('Asset-'))}"
            )
            print(
                f"   Assets with 'other' type: {sum(1 for a in created_assets if a['type'] == 'other')}"
            )
            print(
                f"   Assets with OS data: {sum(1 for a in created_assets if a['os'])}"
            )

            # Show sample
            print("\n📋 Sample assets (first 3):")
            for asset in created_assets[:3]:
                print(
                    f"   - {asset['name']} | Type: {asset['type']} | OS: {asset['os'] or 'N/A'}"
                )

        except Exception as e:
            print(f"\n❌ Error during asset recreation: {e}")
            import traceback

            traceback.print_exc()
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(recreate_assets_for_flow())
