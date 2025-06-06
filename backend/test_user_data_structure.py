#!/usr/bin/env python3
"""
Test script to simulate the user's actual data structure and verify CrewAI Flow processing.
Based on the user's screenshots showing applications like HR_Payroll, Finance_ERP with CITYPE fields.
"""

import asyncio
import sys
import uuid
from datetime import datetime

sys.path.append('/app')
sys.path.append('/app/backend')

from app.core.database import AsyncSessionLocal
from app.models.data_import import RawImportRecord
from sqlalchemy import text

# Sample data structure that matches what the user uploaded
SAMPLE_USER_DATA = [
    # Applications from user's screenshots
    {
        "CIID": "APP0001",
        "CITYPE": "Application", 
        "NAME": "HR_Payroll",
        "ENVIRONMENT": "Production",
        "LOCATION": "DC1",
        "OWNER": "John Smith",
        "CPU_CORES": 4,
        "RAM_GB": 16,
        "STORAGE_GB": 500,
        "STATUS": "Installed",
        "RELATED_CI": "SRV0001"
    },
    {
        "CIID": "APP0002",
        "CITYPE": "Application",
        "NAME": "Finance_ERP", 
        "ENVIRONMENT": "Production",
        "LOCATION": "DC1",
        "OWNER": "Jane Doe",
        "CPU_CORES": 8,
        "RAM_GB": 64,
        "STORAGE_GB": 2000,
        "STATUS": "Installed",
        "RELATED_CI": "SRV0003"
    },
    {
        "CIID": "APP0003",
        "CITYPE": "Application",
        "NAME": "CRM_System",
        "ENVIRONMENT": "Production", 
        "LOCATION": "DC2",
        "OWNER": "Mike Johnson",
        "CPU_CORES": 6,
        "RAM_GB": 32,
        "STORAGE_GB": 1000,
        "STATUS": "Installed",
        "RELATED_CI": "SRV0004"
    },
    # Servers from user's screenshots
    {
        "CIID": "SRV0001",
        "CITYPE": "Server",
        "NAME": "srv-hr-01",
        "IP_ADDRESS": "192.168.1.10",
        "ENVIRONMENT": "Production",
        "LOCATION": "DC1", 
        "OS": "Windows Server 2019",
        "OWNER": "John Smith",
        "CPU_CORES": 16,
        "RAM_GB": 32,
        "STORAGE_GB": 500,
        "STATUS": "Installed",
        "RELATED_CI": "APP0001"
    },
    {
        "CIID": "SRV0002",
        "CITYPE": "Server",
        "NAME": "srv-hr-db-01",
        "IP_ADDRESS": "192.168.1.11",
        "ENVIRONMENT": "Production",
        "LOCATION": "DC1",
        "OS": "Red Hat Enterprise Linux 8",
        "OWNER": "John Smith",
        "CPU_CORES": 32,
        "RAM_GB": 64,
        "STORAGE_GB": 1000,
        "STATUS": "Installed",
        "RELATED_CI": "APP0001"
    },
    {
        "CIID": "SRV0003",
        "CITYPE": "Server", 
        "NAME": "srv-erp-01",
        "IP_ADDRESS": "192.168.1.20",
        "ENVIRONMENT": "Production",
        "LOCATION": "DC1",
        "OS": "Windows Server 2019",
        "OWNER": "Jane Doe",
        "CPU_CORES": 64,
        "RAM_GB": 128,
        "STORAGE_GB": 2000,
        "STATUS": "Installed",
        "RELATED_CI": "APP0002"
    }
]

async def test_user_data_structure():
    """Test CrewAI Flow with the user's actual data structure."""
    print("🧪 Testing CrewAI Flow with User's Actual Data Structure...")
    print("   (Applications: HR_Payroll, Finance_ERP, CRM_System)")
    print("   (Servers: srv-hr-01, srv-hr-db-01, srv-erp-01)")
    
    try:
        async with AsyncSessionLocal() as session:
            # Create a new test import session
            test_session_id = str(uuid.uuid4())
            print(f"\n📥 Creating test session: {test_session_id}")
            
            # Get demo client context
            client_query = await session.execute(text("""
                SELECT client_account_id, name FROM client_accounts WHERE is_mock = true LIMIT 1
            """))
            client_row = client_query.first()
            
            engagement_query = await session.execute(text("""
                SELECT engagement_id FROM engagements LIMIT 1
            """))
            engagement_row = engagement_query.first()
            
            if not client_row or not engagement_row:
                print("❌ Could not find demo client or engagement")
                return
            
            client_account_id = str(client_row[0])
            engagement_id = str(engagement_row[0])
            
            # Insert test raw import records with user's data structure
            print("📋 Inserting test raw import records...")
            for i, raw_data in enumerate(SAMPLE_USER_DATA):
                raw_record = RawImportRecord(
                    id=uuid.uuid4(),
                    data_import_id=test_session_id,
                    row_number=i + 1,
                    raw_data=raw_data,
                    created_at=datetime.utcnow()
                )
                session.add(raw_record)
            
            await session.commit()
            print(f"✅ Created {len(SAMPLE_USER_DATA)} test raw records")
            
            # Show what we created
            print("\n📊 Test Data Summary:")
            applications = [d for d in SAMPLE_USER_DATA if d['CITYPE'] == 'Application']
            servers = [d for d in SAMPLE_USER_DATA if d['CITYPE'] == 'Server']
            
            print(f"   📱 Applications: {len(applications)}")
            for app in applications:
                print(f"     - {app['CIID']}: {app['NAME']} (Related: {app.get('RELATED_CI', 'None')})")
            
            print(f"   🖥️  Servers: {len(servers)}")
            for server in servers:
                print(f"     - {server['CIID']}: {server['NAME']} (Related: {server.get('RELATED_CI', 'None')})")
            
            # Now test our CrewAI Flow processing
            print("\n🚀 Testing CrewAI Flow Processing...")
            
            try:
                from app.services.crewai_flow_data_processing import CrewAIFlowDataProcessingService
                
                flow_service = CrewAIFlowDataProcessingService()
                result = await flow_service.process_import_session(
                    import_session_id=test_session_id,
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    user_id="test_user"
                )
                
                print(f"\n✅ CrewAI Flow Results:")
                print(f"   Status: {result.get('status')}")
                print(f"   Processing Status: {result.get('processing_status')}")
                print(f"   Total Processed: {result.get('total_processed', 0)}")
                print(f"   CrewAI Flow Used: {result.get('crewai_flow_used', False)}")
                
                if result.get('classification_results'):
                    cr = result['classification_results']
                    print(f"\n📊 Asset Classification Results:")
                    print(f"   📱 Applications: {cr.get('applications', 0)} (Expected: 3)")
                    print(f"   🖥️  Servers: {cr.get('servers', 0)} (Expected: 3)")
                    print(f"   🗄️  Databases: {cr.get('databases', 0)} (Expected: 0)")
                    print(f"   📦 Other Assets: {cr.get('other_assets', 0)}")
                    print(f"   🔗 Dependencies: {cr.get('dependencies', 0)}")
                    
                    # Check if classification worked correctly
                    apps_correct = cr.get('applications', 0) == 3
                    servers_correct = cr.get('servers', 0) == 3
                    
                    if apps_correct and servers_correct:
                        print("\n🎉 SUCCESS: CrewAI Flow correctly classified applications and servers!")
                    else:
                        print(f"\n⚠️  ISSUE: Expected 3 applications and 3 servers")
                        print(f"   Got {cr.get('applications', 0)} applications and {cr.get('servers', 0)} servers")
                
                # Verify in database
                print(f"\n🔍 Verifying Database Results...")
                verify_query = await session.execute(text("""
                    SELECT asset_type, COUNT(*), STRING_AGG(name, ', ') as names
                    FROM cmdb_assets 
                    WHERE source_filename LIKE '%' || :session_id || '%'
                    GROUP BY asset_type
                    ORDER BY asset_type
                """), {"session_id": test_session_id})
                
                print("   💾 Created Assets:")
                for row in verify_query:
                    print(f"     {row[0]}: {row[1]} assets ({row[2]})")
                
                # Check specific applications
                app_query = await session.execute(text("""
                    SELECT name, asset_type, raw_data->>'CITYPE' as orig_citype, raw_data->>'CIID' as orig_ciid
                    FROM cmdb_assets 
                    WHERE source_filename LIKE '%' || :session_id || '%'
                    AND asset_type = 'application'
                    ORDER BY name
                """), {"session_id": test_session_id})
                
                print(f"\n   📱 Application Assets Created:")
                app_results = list(app_query)
                if app_results:
                    for row in app_results:
                        print(f"     ✅ {row[1]}: {row[0]} (Original: {row[2]}, ID: {row[3]})")
                else:
                    print("     ❌ No application assets found!")
                    
                    # Debug what happened to applications
                    debug_query = await session.execute(text("""
                        SELECT ca.name, ca.asset_type, rir.raw_data->>'CITYPE' as orig_citype, rir.raw_data->>'CIID' as orig_ciid
                        FROM raw_import_records rir
                        JOIN cmdb_assets ca ON rir.cmdb_asset_id = ca.id
                        WHERE rir.data_import_id = :session_id
                        AND rir.raw_data->>'CITYPE' = 'Application'
                        ORDER BY rir.raw_data->>'CIID'
                    """), {"session_id": test_session_id})
                    
                    print(f"\n   🔍 Debugging: What happened to applications?")
                    for row in debug_query:
                        print(f"     {row[3]} ({row[2]}) → Created as {row[1]}: {row[0]}")
                
            except ImportError as e:
                print(f"   ⚠️  CrewAI Flow service not available: {e}")
                print("   Using fallback processing test...")
                
                # Test fallback processing
                from app.api.v1.endpoints.data_import import _determine_asset_type_agentic
                
                print(f"\n🧪 Testing Enhanced Asset Type Classification:")
                for raw_data in SAMPLE_USER_DATA:
                    predicted_type = _determine_asset_type_agentic(raw_data, {})
                    expected_type = raw_data['CITYPE'].lower()
                    correct = predicted_type == expected_type
                    status = "✅" if correct else "❌"
                    print(f"   {status} {raw_data['CIID']}: {raw_data['CITYPE']} → {predicted_type} {'(CORRECT)' if correct else '(WRONG)'}")
                
            except Exception as e:
                print(f"   ❌ Error testing CrewAI Flow: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_user_data_structure()) 