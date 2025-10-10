#!/usr/bin/env python3
"""
Fix duplicate IP addresses in raw import records for testing
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from sqlalchemy import select, text, update
from app.core.database import get_db
from app.models.data_import.core import RawImportRecord
import json

async def fix_duplicate_ips():
    """Update duplicate IP 10.16.2.1 to unique values"""
    
    async for db in get_db():
        try:
            # Get the latest data import
            query = text("""
                SELECT id FROM data_imports 
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            result = await db.execute(query)
            data_import_id = result.scalar_one_or_none()
            
            if not data_import_id:
                print("❌ No data imports found")
                return
            
            print(f"📋 Working with data_import_id: {data_import_id}")
            
            # Get records with IP 10.16.2.1
            query2 = select(RawImportRecord).where(
                RawImportRecord.data_import_id == data_import_id
            )
            result2 = await db.execute(query2)
            records = result2.scalars().all()
            
            print(f"\n🔍 Found {len(records)} total records")
            
            # Find and fix duplicates
            duplicate_count = 0
            for record in records:
                if record.raw_data.get('IP Address') == '10.16.2.1':
                    duplicate_count += 1
                    hostname = record.raw_data.get('Hostname', 'unknown')
                    
                    # Assign unique IP based on hostname
                    if 'Windbp001app1' in hostname:
                        new_ip = '10.16.2.1'  # Keep first one
                        print(f"✅ Keeping: {hostname} -> {new_ip}")
                    elif 'Windbp002app2' in hostname:
                        new_ip = '10.16.2.2'  # Change second one
                        print(f"🔧 Fixing: {hostname} -> {new_ip} (was 10.16.2.1)")
                        
                        # Update raw_data
                        updated_data = record.raw_data.copy()
                        updated_data['IP Address'] = new_ip
                        
                        # Update cleansed_data if it exists
                        updated_cleansed = record.cleansed_data.copy() if record.cleansed_data else None
                        if updated_cleansed and 'IP Address' in updated_cleansed:
                            updated_cleansed['IP Address'] = new_ip
                        
                        # Update the record
                        record.raw_data = updated_data
                        record.cleansed_data = updated_cleansed
                        db.add(record)
            
            if duplicate_count > 0:
                await db.commit()
                print(f"\n✅ Fixed {duplicate_count} records with duplicate IP 10.16.2.1")
            else:
                print("\n✅ No duplicate IPs found (10.16.2.1)")
            
            # Verify the fix
            print("\n📊 Verification - All IPs in latest import:")
            print("=" * 60)
            query3 = select(RawImportRecord).where(
                RawImportRecord.data_import_id == data_import_id
            ).order_by(RawImportRecord.row_number)
            result3 = await db.execute(query3)
            all_records = result3.scalars().all()
            
            for i, rec in enumerate(all_records, 1):
                hostname = rec.raw_data.get('Hostname', 'N/A')
                ip = rec.raw_data.get('IP Address', 'N/A')
                print(f"{i}. {hostname:20s} -> {ip}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break

if __name__ == "__main__":
    print("🔧 Fixing duplicate IP addresses in test data...\n")
    asyncio.run(fix_duplicate_ips())


