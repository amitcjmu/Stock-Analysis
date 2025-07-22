#!/usr/bin/env python
"""
Test script to check and generate field mappings for the latest discovery flow
"""
import asyncio

from sqlalchemy import func, select

from app.core.database import get_db
from app.models.data_import import DataImport, ImportFieldMapping, RawImportRecord
from app.models.discovery_flow import DiscoveryFlow


async def test_field_mappings():
    async for db in get_db():
        try:
            # Get latest discovery flow
            flow_result = await db.execute(
                select(DiscoveryFlow).order_by(DiscoveryFlow.created_at.desc()).limit(1)
            )
            flow = flow_result.scalar_one_or_none()
            
            if not flow:
                print("❌ No discovery flow found")
                return
                
            print(f"✅ Found flow: {flow.flow_id}")
            print(f"   Status: {flow.status}")
            print(f"   Name: {flow.flow_name}")
            
            # Get latest data import
            import_result = await db.execute(
                select(DataImport).order_by(DataImport.created_at.desc()).limit(1)
            )
            data_import = import_result.scalar_one_or_none()
            
            if not data_import:
                print("❌ No data import found")
                return
                
            print(f"\n✅ Found data import: {data_import.id}")
            print(f"   Status: {data_import.status}")
            print(f"   Records: {data_import.total_records}")
            
            # Check existing field mappings
            fm_count_result = await db.execute(
                select(func.count(ImportFieldMapping.id)).where(
                    ImportFieldMapping.data_import_id == data_import.id
                )
            )
            existing_count = fm_count_result.scalar()
            
            print(f"\n📊 Existing field mappings: {existing_count}")
            
            if existing_count == 0:
                print("\n🔄 No field mappings found. Generating...")
                
                # Get sample raw record
                raw_result = await db.execute(
                    select(RawImportRecord).where(
                        RawImportRecord.data_import_id == data_import.id
                    ).limit(1)
                )
                raw_record = raw_result.scalar_one_or_none()
                
                if raw_record and raw_record.raw_data:
                    fields = list(raw_record.raw_data.keys())
                    print(f"   Found {len(fields)} fields to map")
                    
                    # Generate field mappings
                    for field in fields[:10]:  # Limit to first 10 for testing
                        mapping = ImportFieldMapping(
                            data_import_id=data_import.id,
                            source_field=field,
                            target_field=field.lower().replace(' ', '_'),
                            mapping_type="ai_suggested",
                            confidence_score=0.8,
                            status="suggested",
                            is_user_defined=False,
                            is_validated=False
                        )
                        db.add(mapping)
                    
                    await db.commit()
                    print(f"   ✅ Generated {min(len(fields), 10)} field mappings")
                else:
                    print("   ❌ No raw data found")
            else:
                # Show sample mappings
                sample_result = await db.execute(
                    select(ImportFieldMapping).where(
                        ImportFieldMapping.data_import_id == data_import.id
                    ).limit(5)
                )
                samples = sample_result.scalars().all()
                
                print("\n📋 Sample field mappings:")
                for m in samples:
                    print(f"   {m.source_field} -> {m.target_field} ({m.status})")
            
            # Check if flow has field mapping data
            print(f"\n🔍 Checking flow phases: {flow.phases}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break

if __name__ == "__main__":
    asyncio.run(test_field_mappings())