#!/usr/bin/env python3
"""
Test script for the new CrewAI Flow data processing with state management.
Verifies that applications and servers are properly classified.
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.append('/app')
sys.path.append('/app/backend')

from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def test_crewai_flow_processing():
    """Test the new CrewAI Flow data processing system."""
    print("🧪 Testing CrewAI Flow Data Processing with State Management...")
    
    try:
        async with AsyncSessionLocal() as session:
            print("\n1. 📊 Current Database State:")
            
            # Check raw import records
            raw_query = await session.execute(text("""
                SELECT data_import_id, COUNT(*) as count, 
                       STRING_AGG(DISTINCT raw_data->>'CITYPE', ', ') as citypes,
                       STRING_AGG(DISTINCT raw_data->>'CIID', ', ') as ciids
                FROM raw_import_records 
                GROUP BY data_import_id
                ORDER BY data_import_id
            """))
            
            print("   📥 Raw Import Records:")
            for row in raw_query:
                print(f"     Session {row[0]}: {row[1]} records")
                print(f"       CITYPEs: {row[2]}")
                print(f"       Sample CIIDs: {row[3][:100]}...")
            
            # Check current CMDB assets breakdown
            cmdb_query = await session.execute(text("""
                SELECT asset_type, COUNT(*) as count
                FROM cmdb_assets 
                GROUP BY asset_type
                ORDER BY count DESC
            """))
            
            print("\n   💾 Current CMDB Assets:")
            total_assets = 0
            for row in cmdb_query:
                total_assets += row[1]
                print(f"     {row[0]}: {row[1]} assets")
            print(f"     📊 TOTAL: {total_assets} assets")
            
            # Test the new CrewAI Flow processing
            print("\n2. 🧠 Testing CrewAI Flow Data Processing...")
            
            # Get a session to test
            session_query = await session.execute(text("""
                SELECT DISTINCT data_import_id 
                FROM raw_import_records 
                WHERE cmdb_asset_id IS NULL
                LIMIT 1
            """))
            session_row = session_query.first()
            
            if not session_row:
                print("   ⚠️  No unprocessed raw records found, creating test data...")
                
                # Check if we can reprocess existing data
                reset_query = await session.execute(text("""
                    UPDATE raw_import_records 
                    SET cmdb_asset_id = NULL, is_processed = FALSE, processed_at = NULL
                    WHERE data_import_id = (
                        SELECT data_import_id FROM raw_import_records LIMIT 1
                    )
                """))
                await session.commit()
                
                # Get the reset session
                session_query = await session.execute(text("""
                    SELECT DISTINCT data_import_id 
                    FROM raw_import_records 
                    WHERE cmdb_asset_id IS NULL
                    LIMIT 1
                """))
                session_row = session_query.first()
            
            if session_row:
                import_session_id = session_row[0]
                print(f"   🎯 Testing with session: {import_session_id}")
                
                # Sample some raw data to see what we're working with
                sample_query = await session.execute(text("""
                    SELECT raw_data
                    FROM raw_import_records 
                    WHERE data_import_id = :session_id
                    LIMIT 5
                """), {"session_id": import_session_id})
                
                print("   📋 Sample Raw Data:")
                for i, row in enumerate(sample_query):
                    raw_data = row[0]
                    citype = raw_data.get('CITYPE', 'Unknown')
                    ciid = raw_data.get('CIID', 'Unknown')
                    name = raw_data.get('NAME', 'Unknown')
                    print(f"     {i+1}. {ciid} | {citype} | {name}")
                
                # Test the CrewAI Flow processing
                try:
                    from app.services.crewai_flow_data_processing import CrewAIFlowDataProcessingService
                    
                    print("\n3. 🚀 Running CrewAI Flow Processing...")
                    flow_service = CrewAIFlowDataProcessingService()
                    
                    # Get demo client and engagement IDs
                    client_query = await session.execute(text("""
                        SELECT client_account_id, name FROM client_accounts WHERE is_mock = true LIMIT 1
                    """))
                    client_row = client_query.first()
                    
                    engagement_query = await session.execute(text("""
                        SELECT engagement_id FROM engagements LIMIT 1
                    """))
                    engagement_row = engagement_query.first()
                    
                    if client_row and engagement_row:
                        result = await flow_service.process_import_session(
                            import_session_id=import_session_id,
                            client_account_id=str(client_row[0]),
                            engagement_id=str(engagement_row[0]),
                            user_id="test_user"
                        )
                        
                        print("\n4. ✅ CrewAI Flow Results:")
                        print(f"   Status: {result.get('status')}")
                        print(f"   Processing Status: {result.get('processing_status')}")
                        print(f"   Total Processed: {result.get('total_processed', 0)}")
                        print(f"   CrewAI Flow Used: {result.get('crewai_flow_used', False)}")
                        
                        if result.get('classification_results'):
                            cr = result['classification_results']
                            print(f"\n   📊 Asset Classification Results:")
                            print(f"     📱 Applications: {cr.get('applications', 0)}")
                            print(f"     🖥️  Servers: {cr.get('servers', 0)}")
                            print(f"     🗄️  Databases: {cr.get('databases', 0)}")
                            print(f"     📦 Other Assets: {cr.get('other_assets', 0)}")
                            print(f"     🔗 Dependencies: {cr.get('dependencies', 0)}")
                        
                        if result.get('processing_errors'):
                            print(f"\n   ⚠️  Processing Errors: {len(result['processing_errors'])}")
                            for error in result['processing_errors'][:3]:
                                print(f"     - {error}")
                        
                        # Verify the results in database
                        print("\n5. 🔍 Verifying Database Results...")
                        
                        verify_query = await session.execute(text("""
                            SELECT asset_type, COUNT(*) as count
                            FROM cmdb_assets 
                            WHERE source_filename LIKE '%' || :session_id || '%'
                            GROUP BY asset_type
                            ORDER BY count DESC
                        """), {"session_id": import_session_id})
                        
                        print("   💾 Newly Created Assets:")
                        total_new = 0
                        for row in verify_query:
                            total_new += row[1]
                            print(f"     {row[0]}: {row[1]} assets")
                        print(f"     📊 TOTAL NEW: {total_new} assets")
                        
                        # Check for applications specifically
                        app_query = await session.execute(text("""
                            SELECT name, asset_type, raw_data->>'CITYPE' as orig_citype
                            FROM cmdb_assets 
                            WHERE asset_type = 'application' 
                            AND source_filename LIKE '%' || :session_id || '%'
                            LIMIT 5
                        """), {"session_id": import_session_id})
                        
                        print("\n   📱 Application Assets Created:")
                        app_count = 0
                        for row in app_query:
                            app_count += 1
                            print(f"     {app_count}. {row[0]} | Type: {row[1]} | Original: {row[2]}")
                        
                        if app_count == 0:
                            print("     ⚠️  No application assets found!")
                            
                            # Debug: Check what happened to application records
                            debug_query = await session.execute(text("""
                                SELECT raw_data->>'CIID' as ciid, 
                                       raw_data->>'CITYPE' as citype,
                                       raw_data->>'NAME' as name,
                                       ca.asset_type as created_type
                                FROM raw_import_records rir
                                LEFT JOIN cmdb_assets ca ON rir.cmdb_asset_id = ca.id
                                WHERE rir.data_import_id = :session_id
                                AND raw_data->>'CITYPE' ILIKE '%application%'
                                LIMIT 5
                            """), {"session_id": import_session_id})
                            
                            print("\n   🔍 Debugging Application Records:")
                            for row in debug_query:
                                print(f"     {row[0]} | Original: {row[1]} | Name: {row[2]} | Created as: {row[3]}")
                        
                    else:
                        print("   ❌ Could not find demo client or engagement for testing")
                        
                except ImportError as e:
                    print(f"   ⚠️  CrewAI Flow service not available: {e}")
                except Exception as e:
                    print(f"   ❌ Error testing CrewAI Flow: {e}")
                    import traceback
                    traceback.print_exc()
            
            else:
                print("   ❌ No raw import records available for testing")
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_crewai_flow_processing()) 