#!/usr/bin/env python3
"""
Debug script to manually process raw import records into assets with correct client context.
This bypasses the CrewAI Flow service to test multi-tenancy.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def main():
    try:
        from sqlalchemy import select

        from app.core.database import AsyncSessionLocal
        from app.models.asset import Asset
        from app.models.data_import import RawImportRecord
        
        print("🚀 Starting manual asset creation for Marathon Petroleum...")
        
        async with AsyncSessionLocal() as session:
            # Get unprocessed raw records for Marathon Petroleum
            query = select(RawImportRecord).where(
                RawImportRecord.client_account_id == "73dee5f1-6a01-43e3-b1b8-dbe6c66f2990"
            ).where(
                RawImportRecord.asset_id.is_(None)
            )
            
            result = await session.execute(query)
            raw_records = result.scalars().all()
            
            print(f"📊 Found {len(raw_records)} unprocessed raw records for Marathon Petroleum")
            
            if not raw_records:
                print("❌ No unprocessed raw records found")
                return
            
            processed_count = 0
            for record in raw_records:
                try:
                    raw_data = record.raw_data
                    print(f"🔄 Processing record {record.row_number}: {raw_data}")
                    
                    # Create asset with correct client context
                    asset_data = {
                        "client_account_id": "73dee5f1-6a01-43e3-b1b8-dbe6c66f2990",  # Marathon Petroleum
                        "engagement_id": record.engagement_id,
                        "name": (raw_data.get("Name") or 
                                raw_data.get("hostname") or 
                                raw_data.get("Hostname") or
                                f"Asset_{record.row_number}"),
                        "hostname": raw_data.get("Hostname") or raw_data.get("hostname"),
                        "asset_type": "server",  # Default for testing
                        "ip_address": raw_data.get("IP_Address") or raw_data.get("ip_address"),
                        "operating_system": raw_data.get("OS") or raw_data.get("operating_system"),
                        "environment": raw_data.get("Environment") or raw_data.get("environment"),
                        "discovery_source": "manual_debug_import",
                        "discovery_method": "debug_script",
                        "discovered_at": datetime.utcnow(),
                        "source_file": f"debug_import_{record.data_import_id}",
                        "created_by": "debug_user"
                    }
                    
                    # Create Asset
                    asset = Asset(**asset_data)
                    session.add(asset)
                    await session.flush()
                    
                    print(f"✅ Created asset {asset.id} for {asset.name}")
                    
                    # Update raw record
                    record.asset_id = asset.id
                    record.is_processed = True
                    record.processed_at = datetime.utcnow()
                    record.processing_notes = "Processed by debug script"
                    
                    processed_count += 1
                    
                except Exception as e:
                    print(f"❌ Error processing record {record.id}: {e}")
                    continue
            
            await session.commit()
            print(f"🎉 Successfully processed {processed_count} raw records into assets")
            
            # Verify the assets were created with correct client context
            asset_query = select(Asset).where(
                Asset.client_account_id == "73dee5f1-6a01-43e3-b1b8-dbe6c66f2990"
            )
            asset_result = await session.execute(asset_query)
            marathon_assets = asset_result.scalars().all()
            
            print(f"🔍 Verification: Marathon Petroleum now has {len(marathon_assets)} assets")
            for asset in marathon_assets[-processed_count:]:  # Show the newly created ones
                print(f"   - {asset.name} ({asset.asset_type}) - {asset.hostname}")
            
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 