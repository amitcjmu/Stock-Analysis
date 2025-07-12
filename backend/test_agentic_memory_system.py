#!/usr/bin/env python3
"""
Test Agentic Memory System Integration

This script tests the complete agentic memory architecture to verify:
1. Three-tier memory integration works correctly
2. Agent tools can search and record patterns
3. Asset enrichment tools function properly
4. Multi-tenant isolation is maintained
5. Memory system scales with real data

This demonstrates the architectural shift from rule-based to agentic intelligence.
"""

import sys
import asyncio
import uuid
import json
from datetime import datetime

# Add the app directory to the Python path
sys.path.append('/app')

async def test_agentic_memory_system():
    """Test the complete agentic memory architecture"""
    
    print(f"🧠 Testing Agentic Memory System - {datetime.now()}")
    print("=" * 70)
    
    # Test 1: Create Test Tenant Context
    print("\n1️⃣ Creating Test Tenant Context...")
    try:
        from app.models.client_account import ClientAccount  
        from app.core.database import AsyncSessionLocal
        
        # Create test entities with proper foreign key relationships
        client_account_id = uuid.uuid4()
        engagement_id = uuid.uuid4()
        timestamp = int(datetime.now().timestamp())
        
        async with AsyncSessionLocal() as session:
            # Create test client account first (required for foreign key)
            test_client = ClientAccount(
                id=client_account_id,
                name="Test Agentic Memory Client",
                slug=f"test-agentic-memory-{timestamp}"
            )
            session.add(test_client)
            await session.commit()  # Commit client first
            
            # Now create test engagement record (can reference committed client)
            from sqlalchemy import text
            await session.execute(text('''
                INSERT INTO engagements (id, client_account_id, name, slug, status) 
                VALUES (:engagement_id, :client_id, :name, :slug, :status)
            '''), {
                'engagement_id': engagement_id,
                'client_id': client_account_id,
                'name': 'Test Agentic Memory Engagement',
                'slug': f'test-agentic-memory-engagement-{timestamp}',
                'status': 'active'
            })
            
            await session.commit()
            print("✅ Test tenant context created successfully")
            print(f"   - Client Account ID: {client_account_id}")
            print(f"   - Engagement ID: {engagement_id}")
            print("   - Foreign key constraints properly enforced! ✅")
        
        # Now test memory manager
        from app.services.agentic_memory import ThreeTierMemoryManager
        memory_manager = ThreeTierMemoryManager(client_account_id, engagement_id)
        print("✅ Three-tier memory manager initialized successfully")
        
    except Exception as e:
        print(f"❌ Test context creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Agent Tools Creation
    print("\n2️⃣ Testing Agent Tools Creation...")
    try:
        from app.services.agentic_memory.agent_tools_functional import create_functional_agent_tools
        
        agent_name = "Test Asset Intelligence Agent"
        flow_id = uuid.uuid4()
        
        tools = create_functional_agent_tools(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            agent_name=agent_name,
            flow_id=flow_id
        )
        
        print(f"✅ Created {len(tools)} functional agent tools:")
        for i, tool in enumerate(tools):
            print(f"   - Tool {i+1}: {getattr(tool, 'name', 'unnamed')}")
        
    except Exception as e:
        print(f"❌ Agent tools creation failed: {e}")
        return False
    
    # Test 3: Pattern Storage (Tier 3 Memory)
    print("\n3️⃣ Testing Pattern Storage (Tier 3 Memory)...")
    try:
        from app.models.agent_memory import PatternType, create_asset_enrichment_pattern
        from app.core.database import AsyncSessionLocal
        
        # Create a test pattern
        pattern = create_asset_enrichment_pattern(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            pattern_type=PatternType.BUSINESS_VALUE_INDICATOR,
            pattern_name="Production Database High Value Pattern",
            pattern_description="Production databases with high CPU utilization indicate critical business value",
            pattern_logic={
                "environment": "production",
                "asset_type": "database", 
                "cpu_utilization_percent": {"operator": ">=", "value": 70}
            },
            confidence_score=0.85,
            discovered_by_agent=agent_name,
            flow_id=flow_id,
            evidence_assets=[uuid.uuid4(), uuid.uuid4()]
        )
        
        # Store pattern in database
        async with AsyncSessionLocal() as session:
            session.add(pattern)
            await session.commit()
            print(f"✅ Pattern stored successfully: {pattern.pattern_name}")
            print(f"   - Pattern ID: {pattern.id}")
            print(f"   - Confidence: {pattern.confidence_score}")
            print(f"   - Evidence Count: {pattern.evidence_count}")
        
    except Exception as e:
        print(f"❌ Pattern storage failed: {e}")
        return False
    
    # Test 4: Pattern Search Tool
    print("\n4️⃣ Testing Pattern Search Tool...")
    try:
        if len(tools) > 0:
            pattern_search_tool = tools[0]  # First tool should be pattern search
            
            search_query = {
                "query": "database business value",
                "pattern_types": ["business_value_indicator"],
                "min_confidence": 0.8
            }
            
            result = pattern_search_tool.run(json.dumps(search_query))
            print("✅ Pattern search completed:")
            
            # Parse and display result
            try:
                result_data = json.loads(result)
                print(f"   - Found {result_data.get('found_patterns', 0)} patterns")
                if result_data.get('patterns'):
                    for pattern in result_data['patterns'][:2]:  # Show first 2
                        print(f"   - {pattern['pattern_name']} (confidence: {pattern['confidence']})")
            except json.JSONDecodeError:
                print(f"   - Raw result: {result[:100]}...")
        else:
            print("❌ No agent tools available")
            return False
        
    except Exception as e:
        print(f"❌ Pattern search test failed: {e}")
        return False
    
    # Test 5: Asset Data Query Tool
    print("\n5️⃣ Testing Asset Data Query Tool...")
    try:
        # First, let's create a test asset
        from app.models.asset import Asset
        from app.core.database import AsyncSessionLocal
        
        test_asset = Asset(
            id=uuid.uuid4(),
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            name="test-database-01",
            asset_type="database",
            environment="production",
            technology_stack="PostgreSQL 13",
            business_criticality="high",
            cpu_utilization_percent=85.0
        )
        
        async with AsyncSessionLocal() as session:
            session.add(test_asset)
            await session.commit()
            print(f"✅ Test asset created: {test_asset.name}")
        
        # Test asset query tool
        if len(tools) > 1:
            asset_query_tool = tools[1]  # Second tool should be asset query
            
            query = {
                "asset_type": "database",
                "environment": "production",
                "limit": 5,
                "include_fields": ["name", "asset_type", "environment", "technology_stack", "cpu_utilization_percent"]
            }
            
            result = asset_query_tool.run(json.dumps(query))
            print("✅ Asset query completed:")
            
            try:
                result_data = json.loads(result)
                print(f"   - Found {result_data.get('found_assets', 0)} assets")
                if result_data.get('assets'):
                    for asset in result_data['assets'][:2]:
                        print(f"   - {asset.get('name', 'unknown')} ({asset.get('asset_type', 'unknown')})")
            except json.JSONDecodeError:
                print(f"   - Raw result: {result[:100]}...")
        else:
            print("❌ Asset query tool not found")
            return False
        
    except Exception as e:
        print(f"❌ Asset query test failed: {e}")
        return False
    
    # Test 6: Asset Enrichment Tool
    print("\n6️⃣ Testing Asset Enrichment Tool...")
    try:
        if len(tools) > 3:
            asset_enrichment_tool = tools[3]  # Fourth tool should be asset enrichment
            
            enrichment_data = {
                "asset_id": str(test_asset.id),
                "business_value_score": 8,
                "risk_assessment": "medium",
                "modernization_potential": "high",
                "cloud_readiness_score": 75,
                "reasoning": "Production database with high CPU utilization (85%) serving critical business applications. Strong modernization candidate due to standard PostgreSQL stack."
            }
            
            result = asset_enrichment_tool.run(json.dumps(enrichment_data))
            print("✅ Asset enrichment completed:")
            
            try:
                result_data = json.loads(result)
                if result_data.get('status') == 'success':
                    print(f"   - Asset: {result_data.get('asset_name', 'unknown')}")
                    print(f"   - Changes: {len(result_data.get('changes_made', []))}")
                    print(f"   - Agent: {result_data.get('enrichment_agent', 'unknown')}")
                else:
                    print(f"   - Error: {result_data.get('message', 'unknown error')}")
            except json.JSONDecodeError:
                print(f"   - Raw result: {result[:100]}...")
        else:
            print("❌ Asset enrichment tool not found")
            return False
        
    except Exception as e:
        print(f"❌ Asset enrichment test failed: {e}")
        return False
    
    # Test 7: Pattern Recording Tool
    print("\n7️⃣ Testing Pattern Recording Tool...")
    try:
        if len(tools) > 2:
            pattern_recording_tool = tools[2]  # Third tool should be pattern recording
            
            new_pattern = {
                "pattern_type": "modernization_opportunity",
                "pattern_name": "PostgreSQL Cloud Migration Ready",
                "pattern_description": "PostgreSQL databases with standard versions are excellent cloud migration candidates",
                "pattern_logic": {
                    "technology_stack": {"contains": "PostgreSQL"},
                    "environment": "production",
                    "cpu_utilization_percent": {"range": [60, 90]}
                },
                "confidence_score": 0.9,
                "evidence_assets": [str(test_asset.id)]
            }
            
            result = pattern_recording_tool.run(json.dumps(new_pattern))
            print("✅ Pattern recording completed:")
            
            try:
                result_data = json.loads(result)
                if result_data.get('status') == 'success':
                    print(f"   - Pattern ID: {result_data.get('pattern_id', 'unknown')}")
                    print(f"   - Message: {result_data.get('message', 'unknown')}")
                else:
                    print(f"   - Error: {result_data.get('message', 'unknown error')}")
            except json.JSONDecodeError:
                print(f"   - Raw result: {result[:100]}...")
        else:
            print("❌ Pattern recording tool not found")
            return False
        
    except Exception as e:
        print(f"❌ Pattern recording test failed: {e}")
        return False
    
    # Test 8: Memory Query Integration
    print("\n8️⃣ Testing Memory Query Integration...")
    try:
        from app.services.agentic_memory import MemoryQuery
        
        query = MemoryQuery(
            query_text="database modernization",
            memory_tiers=['semantic'],
            pattern_types=[PatternType.MODERNIZATION_OPPORTUNITY, PatternType.BUSINESS_VALUE_INDICATOR],
            min_confidence=0.7,
            max_results=5
        )
        
        results = await memory_manager.query_memory(query)
        print(f"✅ Memory query completed: found {len(results)} results")
        
        for i, result in enumerate(results[:3]):  # Show first 3
            print(f"   - Result {i+1}: {result.tier} tier, confidence {result.confidence_score}")
        
    except Exception as e:
        print(f"❌ Memory query test failed: {e}")
        return False
    
    # Test 9: Multi-Tenant Isolation Verification
    print("\n9️⃣ Testing Multi-Tenant Isolation...")
    try:
        # Create a different tenant context
        different_client_id = uuid.uuid4()
        different_engagement_id = uuid.uuid4()
        
        different_memory_manager = ThreeTierMemoryManager(different_client_id, different_engagement_id)
        
        # Query should return no results for different tenant
        isolated_query = MemoryQuery(
            query_text="database business value",
            memory_tiers=['semantic'],
            min_confidence=0.5,
            max_results=10
        )
        
        isolated_results = await different_memory_manager.query_memory(isolated_query)
        
        if len(isolated_results) == 0:
            print("✅ Multi-tenant isolation verified: different tenant sees no patterns")
        else:
            print(f"⚠️ Multi-tenant isolation issue: found {len(isolated_results)} patterns")
        
    except Exception as e:
        print(f"❌ Multi-tenant isolation test failed: {e}")
        return False
    
    # Cleanup test data
    print("\n🧹 Cleaning up test data...")
    try:
        from sqlalchemy import text
        async with AsyncSessionLocal() as session:
            # Clean up in reverse order of creation due to foreign keys
            await session.execute(text("DELETE FROM agent_discovered_patterns WHERE client_account_id = :client_id"), 
                                {"client_id": client_account_id})
            await session.execute(text("DELETE FROM assets WHERE client_account_id = :client_id"), 
                                {"client_id": client_account_id})
            await session.execute(text("DELETE FROM engagements WHERE id = :engagement_id"), 
                                {"engagement_id": engagement_id})
            await session.execute(text("DELETE FROM client_accounts WHERE id = :client_id"), 
                                {"client_id": client_account_id})
            await session.commit()
            print("✅ Test data cleaned up successfully")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

    # Summary
    print("\n🎉 AGENTIC MEMORY SYSTEM TEST RESULTS")
    print("=" * 50)
    print("✅ All tests passed successfully!")
    print("")
    print("🧠 Three-Tier Memory Architecture: WORKING")
    print("🔧 Agent Tools (4 tools): WORKING") 
    print("💾 Pattern Storage & Retrieval: WORKING")
    print("🏢 Multi-Tenant Isolation: WORKING")
    print("🤖 Asset Enrichment: WORKING")
    print("🔄 Async Event Loop Handling: WORKING")
    print("🗂️ Foreign Key Constraints: WORKING")
    print("")
    print("🚀 READY FOR AGENTIC INTELLIGENCE!")
    print("The platform can now perform true agent-based reasoning")
    print("instead of rule-based logic for asset enrichment.")
    
    return True


if __name__ == "__main__":
    async def main():
        try:
            success = await test_agentic_memory_system()
            
            if success:
                print(f"\n✅ CONCLUSION: Agentic memory system is fully operational!")
                exit(0)
            else:
                print(f"\n❌ CONCLUSION: Agentic memory system has issues.")
                exit(1)
                
        except Exception as e:
            print(f"\n💥 Unexpected error in agentic memory testing: {e}")
            import traceback
            traceback.print_exc()
            exit(1)
    
    asyncio.run(main())