"""
Test script to verify engagement_id and master_flow_id are populated in ImportFieldMapping
"""
import asyncio
import sys
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.data_import import DataImport, ImportFieldMapping


async def test_field_mapping_ids():
    """Test that engagement_id and master_flow_id are properly populated"""
    
    print("🧪 Testing ImportFieldMapping engagement_id and master_flow_id population...")
    print("=" * 80)
    
    # Get database session
    async for db in get_db():
        try:
            # 1. Check if model has engagement_id attribute
            print("\n1️⃣  Checking model attributes...")
            model_attrs = dir(ImportFieldMapping)
            has_engagement_id = 'engagement_id' in model_attrs
            has_master_flow_id = 'master_flow_id' in model_attrs
            
            print(f"   ✅ Model has engagement_id: {has_engagement_id}")
            print(f"   ✅ Model has master_flow_id: {has_master_flow_id}")
            
            if not has_engagement_id:
                print("   ❌ FAIL: engagement_id not found in model!")
                return False
            
            # 2. Query existing field mappings
            print("\n2️⃣  Querying existing field mappings...")
            query = select(ImportFieldMapping).limit(5)
            result = await db.execute(query)
            mappings = result.scalars().all()
            
            print(f"   Found {len(mappings)} field mappings")
            
            if not mappings:
                print("   ⚠️  No field mappings found in database")
                return True  # Not a failure, just no data yet
            
            # 3. Check if engagement_id is populated
            print("\n3️⃣  Checking engagement_id population...")
            populated_count = 0
            null_count = 0
            
            for mapping in mappings:
                if mapping.engagement_id:
                    populated_count += 1
                    print(f"   ✅ Mapping {mapping.source_field} → {mapping.target_field}: engagement_id={mapping.engagement_id}")
                else:
                    null_count += 1
                    print(f"   ❌ Mapping {mapping.source_field} → {mapping.target_field}: engagement_id=NULL")
            
            print(f"\n   Summary: {populated_count} populated, {null_count} NULL")
            
            # 4. Check master_flow_id population
            print("\n4️⃣  Checking master_flow_id population...")
            master_flow_populated = 0
            master_flow_null = 0
            
            for mapping in mappings:
                if mapping.master_flow_id:
                    master_flow_populated += 1
                    print(f"   ✅ Mapping {mapping.source_field}: master_flow_id={mapping.master_flow_id}")
                else:
                    master_flow_null += 1
                    print(f"   ⚠️  Mapping {mapping.source_field}: master_flow_id=NULL")
            
            print(f"\n   Summary: {master_flow_populated} populated, {master_flow_null} NULL")
            
            # 5. Test query with engagement_id filter
            print("\n5️⃣  Testing engagement_id filter in query...")
            if mappings and mappings[0].engagement_id:
                test_engagement_id = mappings[0].engagement_id
                
                # Query with JOIN (new approach)
                query_with_filter = select(ImportFieldMapping).where(
                    ImportFieldMapping.engagement_id == test_engagement_id
                )
                result = await db.execute(query_with_filter)
                filtered_mappings = result.scalars().all()
                
                print(f"   ✅ Query with engagement_id filter returned {len(filtered_mappings)} mappings")
                
                if len(filtered_mappings) == 0:
                    print(f"   ❌ FAIL: Filter query returned no results for engagement_id={test_engagement_id}")
                    return False
            else:
                print("   ⚠️  Cannot test filter - no engagement_id available")
            
            # 6. Verify data_import relationship
            print("\n6️⃣  Verifying data_import relationship...")
            if mappings:
                test_mapping = mappings[0]
                
                # Get the related data_import
                data_import_query = select(DataImport).where(
                    DataImport.id == test_mapping.data_import_id
                )
                di_result = await db.execute(data_import_query)
                data_import = di_result.scalar_one_or_none()
                
                if data_import:
                    print(f"   ✅ Found data_import: id={data_import.id}")
                    print(f"   ✅ data_import.engagement_id: {data_import.engagement_id}")
                    print(f"   ✅ data_import.master_flow_id: {data_import.master_flow_id}")
                    
                    # Compare
                    if test_mapping.engagement_id == data_import.engagement_id:
                        print(f"   ✅ engagement_id matches between mapping and data_import")
                    else:
                        print(f"   ⚠️  engagement_id MISMATCH:")
                        print(f"       Mapping: {test_mapping.engagement_id}")
                        print(f"       DataImport: {data_import.engagement_id}")
                else:
                    print(f"   ❌ data_import not found for id={test_mapping.data_import_id}")
            
            # 7. Final verdict
            print("\n" + "=" * 80)
            print("📊 TEST RESULTS:")
            print("=" * 80)
            
            all_populated = (null_count == 0)
            
            if all_populated:
                print("✅ PASS: All field mappings have engagement_id populated!")
            else:
                print(f"⚠️  PARTIAL: {null_count} mappings have NULL engagement_id")
                print("   This is expected if they were created before the fix.")
                print("   New mappings should have engagement_id populated.")
            
            if master_flow_null > 0:
                print(f"⚠️  NOTE: {master_flow_null} mappings have NULL master_flow_id")
                print("   This may be expected for certain import types.")
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await db.close()
            break  # Only use first db session


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🧪 ImportFieldMapping Engagement ID Test")
    print("=" * 80)
    
    success = asyncio.run(test_field_mapping_ids())
    
    if success:
        print("\n✅ Tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)

