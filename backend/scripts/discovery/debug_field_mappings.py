#!/usr/bin/env python3
"""
Field Mapping Debug Script

This script helps debug field mapping issues by:
1. Checking field mappings in the database
2. Analyzing raw import data
3. Comparing with assets table
4. Identifying where field mapping application fails

Usage:
    python debug_field_mappings.py --flow-id <flow_id>
    python debug_field_mappings.py --data-import-id <data_import_id>
"""

import asyncio
import sys
import os
import argparse
from typing import Dict, List, Any, Optional

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost:5433/migration_db')

from app.core.database import get_db
from app.models.data_import.mapping import ImportFieldMapping
from app.models.data_import.core import RawImportRecord, DataImport
from app.models.asset import Asset
from app.models.discovery_flow import DiscoveryFlow
from sqlalchemy import select, and_, func


async def debug_field_mappings(flow_id: str = None, data_import_id: str = None):
    """Debug field mapping issues for a specific flow or data import"""
    
    async for db in get_db():
        try:
            print("🔍 Field Mapping Debug Analysis")
            print("=" * 50)
            
            # Step 1: Find the data import ID if not provided
            if not data_import_id and flow_id:
                print(f"🔍 Looking up data import for flow: {flow_id}")
                flow_query = select(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_id)
                flow_result = await db.execute(flow_query)
                discovery_flow = flow_result.scalar_one_or_none()
                
                if discovery_flow:
                    data_import_id = str(discovery_flow.data_import_id)
                    print(f"✅ Found data import ID: {data_import_id}")
                else:
                    print(f"❌ No discovery flow found for flow_id: {flow_id}")
                    return
            
            if not data_import_id:
                print("❌ No data import ID provided")
                return
            
            # Step 2: Check field mappings
            print(f"\n📋 Field Mappings Analysis")
            print("-" * 30)
            
            mappings_query = select(ImportFieldMapping).where(
                ImportFieldMapping.data_import_id == data_import_id
            )
            mappings_result = await db.execute(mappings_query)
            mappings = mappings_result.scalars().all()
            
            print(f"Total field mappings: {len(mappings)}")
            
            if mappings:
                # Check approval status
                approved_count = sum(1 for m in mappings if m.status == 'approved')
                total_count = len(mappings)
                approval_percentage = (approved_count / total_count * 100) if total_count > 0 else 0
                
                print(f"Approved mappings: {approved_count}/{total_count} ({approval_percentage:.1f}%)")
                
                # Show all mappings
                print(f"\nAll field mappings:")
                for i, mapping in enumerate(mappings):
                    status_emoji = "✅" if mapping.status == "approved" else "❌"
                    print(f"  {i+1}. {status_emoji} {mapping.source_field} -> {mapping.target_field} (Status: {mapping.status})")
                
                # Test the exact query used in the code
                client_account_id = '11111111-1111-1111-1111-111111111111'
                
                exact_query = select(ImportFieldMapping).where(
                    and_(
                        ImportFieldMapping.data_import_id == data_import_id,
                        ImportFieldMapping.status == 'approved',
                        ImportFieldMapping.client_account_id == client_account_id
                    )
                )
                
                exact_result = await db.execute(exact_query)
                exact_mappings = exact_result.scalars().all()
                
                print(f"\nExact query results (as used in code): {len(exact_mappings)} approved mappings")
                
                if exact_mappings:
                    field_mappings_dict = {
                        m.target_field: m.source_field
                        for m in exact_mappings
                        if m.target_field and m.target_field != "UNMAPPED"
                    }
                    print(f"Field mappings dictionary: {field_mappings_dict}")
                else:
                    print("❌ No approved mappings found with exact query!")
            
            # Step 3: Check raw import records
            print(f"\n📊 Raw Import Records Analysis")
            print("-" * 30)
            
            raw_records_query = select(RawImportRecord).where(
                RawImportRecord.data_import_id == data_import_id
            ).order_by(RawImportRecord.row_number).limit(3)
            
            raw_result = await db.execute(raw_records_query)
            raw_records = raw_result.scalars().all()
            
            print(f"Total raw records: {len(raw_records)}")
            
            if raw_records:
                print(f"\nSample raw record (row {raw_records[0].row_number}):")
                print(f"Raw data keys: {list(raw_records[0].raw_data.keys()) if raw_records[0].raw_data else 'None'}")
                if raw_records[0].raw_data:
                    print(f"Sample values:")
                    for key, value in list(raw_records[0].raw_data.items())[:5]:
                        print(f"  {key}: {value}")
                
                print(f"\nCleansed data keys: {list(raw_records[0].cleansed_data.keys()) if raw_records[0].cleansed_data else 'None'}")
                if raw_records[0].cleansed_data:
                    print(f"Sample cleansed values:")
                    for key, value in list(raw_records[0].cleansed_data.items())[:5]:
                        print(f"  {key}: {value}")
            
            # Step 4: Check assets table
            print(f"\n🏢 Assets Table Analysis")
            print("-" * 30)
            
            assets_query = select(Asset).limit(10)
            
            assets_result = await db.execute(assets_query)
            assets = assets_result.scalars().all()
            
            print(f"Assets created: {len(assets)}")
            
            if assets:
                print(f"\nSample assets:")
                for i, asset in enumerate(assets[:3]):
                    print(f"  Asset {i+1}:")
                    print(f"    Name: {asset.name}")
                    print(f"    Hostname: {asset.hostname}")
                    print(f"    IP Address: {asset.ip_address}")
                    print(f"    Asset Type: {asset.asset_type}")
                    print(f"    Environment: {asset.environment}")
                    print(f"    Operating System: {asset.operating_system}")
            
            # Step 5: Field Mapping Application Test
            print(f"\n🧪 Field Mapping Application Test")
            print("-" * 30)
            
            if raw_records and exact_mappings:
                field_mappings_dict = {
                    m.target_field: m.source_field
                    for m in exact_mappings
                    if m.target_field and m.target_field != "UNMAPPED"
                }
                
                test_record = raw_records[0].cleansed_data or raw_records[0].raw_data
                
                print(f"Testing field mapping application:")
                print(f"Available mappings: {field_mappings_dict}")
                print(f"Test record keys: {list(test_record.keys())}")
                
                for target_field, source_field in list(field_mappings_dict.items())[:5]:
                    mapped_value = test_record.get(source_field)
                    direct_value = test_record.get(target_field)
                    print(f"  {target_field}: mapped='{mapped_value}' (from {source_field}), direct='{direct_value}'")
            
            # Step 6: Summary and Recommendations
            print(f"\n📝 Summary and Recommendations")
            print("-" * 30)
            
            if not mappings:
                print("❌ CRITICAL: No field mappings found!")
                print("   → Check if field mapping phase completed successfully")
                print("   → Verify field mapping approval process")
            elif approved_count == 0:
                print("❌ CRITICAL: No approved field mappings!")
                print("   → Approve field mappings in the UI")
                print("   → Check approval threshold (80% required)")
            elif approval_percentage < 80:
                print(f"⚠️ WARNING: Only {approval_percentage:.1f}% mappings approved (need 80%)")
                print("   → Approve more field mappings")
            else:
                print("✅ Field mappings look good!")
            
            if not raw_records:
                print("❌ CRITICAL: No raw import records found!")
                print("   → Check if data import completed successfully")
            elif not raw_records[0].cleansed_data:
                print("⚠️ WARNING: No cleansed data found!")
                print("   → Check if data cleansing phase completed")
            
            if not assets:
                print("❌ CRITICAL: No assets created!")
                print("   → Check if asset inventory phase executed")
                print("   → Verify asset creation process")
            elif assets and (not assets[0].hostname or not assets[0].ip_address):
                print("⚠️ WARNING: Assets created but missing key fields!")
                print("   → Field mapping application may have failed")
                print("   → Check debug logs during asset creation phase")
            else:
                print("✅ Assets created successfully with field-mapped data!")
            
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            import traceback
            traceback.print_exc()
        
        break


async def main():
    parser = argparse.ArgumentParser(description='Debug field mapping issues')
    parser.add_argument('--flow-id', help='Flow ID to debug')
    parser.add_argument('--data-import-id', help='Data import ID to debug')
    
    args = parser.parse_args()
    
    if not args.flow_id and not args.data_import_id:
        print("❌ Please provide either --flow-id or --data-import-id")
        return
    
    await debug_field_mappings(args.flow_id, args.data_import_id)


if __name__ == "__main__":
    asyncio.run(main())

