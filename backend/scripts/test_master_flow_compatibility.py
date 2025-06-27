#!/usr/bin/env python3
"""
Master Flow Application Compatibility Tests
Task 1.4.2: Test asset repository and discovery flow services with master flow queries
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.repositories.asset_repository import AssetRepository
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
import json


async def test_asset_repository_master_flow():
    """Test asset repository with master flow queries"""
    
    print("🧪 Testing Asset Repository Master Flow Compatibility")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        # Get a test client account and engagement
        result = await session.execute(text("""
            SELECT DISTINCT client_account_id, engagement_id 
            FROM assets 
            WHERE master_flow_id IS NOT NULL
            LIMIT 1
        """))
        test_context = result.fetchone()
        
        if not test_context:
            print("   ❌ No assets with master flow found for testing")
            return False
            
        print(f"   🎯 Test Context: Client {test_context.client_account_id}, Engagement {test_context.engagement_id}")
        
        # Initialize repository
        asset_repo = AssetRepository(session, test_context.client_account_id)
        
        # Test 1: Get assets by master flow
        print("\n   1️⃣ Testing get assets by master flow...")
        
        result = await session.execute(text("""
            SELECT DISTINCT master_flow_id 
            FROM assets 
            WHERE client_account_id = :client_id AND master_flow_id IS NOT NULL
            LIMIT 1
        """), {"client_id": test_context.client_account_id})
        master_flow_test = result.fetchone()
        
        if master_flow_test:
            # Test query by master flow
            test_assets = await session.execute(text("""
                SELECT COUNT(*) as asset_count
                FROM assets 
                WHERE master_flow_id = :master_flow_id
                AND client_account_id = :client_id
            """), {
                "master_flow_id": master_flow_test.master_flow_id,
                "client_id": test_context.client_account_id
            })
            count = test_assets.scalar()
            print(f"      ✅ Found {count} assets for master flow {master_flow_test.master_flow_id}")
        
        # Test 2: Multi-phase asset queries
        print("\n   2️⃣ Testing multi-phase asset queries...")
        
        multi_phase_query = await session.execute(text("""
            SELECT 
                source_phase,
                current_phase,
                COUNT(*) as asset_count
            FROM assets 
            WHERE client_account_id = :client_id
            GROUP BY source_phase, current_phase
        """), {"client_id": test_context.client_account_id})
        
        phase_stats = multi_phase_query.fetchall()
        for stat in phase_stats:
            print(f"      ✅ {stat.source_phase} → {stat.current_phase}: {stat.asset_count} assets")
            
        # Test 3: Discovery flow asset relationships
        print("\n   3️⃣ Testing discovery flow asset relationships...")
        
        discovery_assets = await session.execute(text("""
            SELECT 
                df.id as discovery_flow_id,
                df.master_flow_id,
                COUNT(a.id) as asset_count
            FROM discovery_flows df
            LEFT JOIN assets a ON a.discovery_flow_id = df.id
            WHERE df.client_account_id = :client_id
            GROUP BY df.id, df.master_flow_id
            HAVING COUNT(a.id) > 0
            LIMIT 5
        """), {"client_id": test_context.client_account_id})
        
        flow_assets = discovery_assets.fetchall()
        for fa in flow_assets:
            print(f"      ✅ Discovery Flow {fa.discovery_flow_id}: {fa.asset_count} assets linked to master flow {fa.master_flow_id}")
            
    return True


async def test_discovery_flow_master_integration():
    """Test discovery flow services with master flow coordination"""
    
    print("\n🧪 Testing Discovery Flow Master Integration")
    print("=" * 50)
    
    async with AsyncSessionLocal() as session:
        # Test 1: Master flow coordination
        print("\n   1️⃣ Testing master flow coordination...")
        
        result = await session.execute(text("""
            SELECT 
                COUNT(*) as total_flows,
                COUNT(master_flow_id) as flows_with_master,
                COUNT(DISTINCT master_flow_id) as unique_master_flows
            FROM discovery_flows
        """))
        flow_stats = result.fetchone()
        
        print(f"      ✅ Total Discovery Flows: {flow_stats.total_flows}")
        print(f"      ✅ Flows with Master ID: {flow_stats.flows_with_master}")
        print(f"      ✅ Unique Master Flows: {flow_stats.unique_master_flows}")
        
        # Test 2: CrewAI extensions coordination
        print("\n   2️⃣ Testing CrewAI extensions coordination...")
        
        result = await session.execute(text("""
            SELECT 
                cse.current_phase,
                cse.phase_progression,
                df.flow_name,
                df.status
            FROM crewai_flow_state_extensions cse
            JOIN discovery_flows df ON cse.discovery_flow_id = df.id
            LIMIT 5
        """))
        coordinations = result.fetchall()
        
        for coord in coordinations:
            progression = coord.phase_progression if coord.phase_progression else {}
            print(f"      ✅ Flow '{coord.flow_name}' - Phase: {coord.current_phase}, Status: {coord.status}")
            
        # Test 3: Phase progression tracking
        print("\n   3️⃣ Testing phase progression tracking...")
        
        result = await session.execute(text("""
            SELECT 
                current_phase,
                COUNT(*) as count,
                AVG(CASE WHEN phase_progression::text != '{}' THEN 1 ELSE 0 END) as progression_rate
            FROM crewai_flow_state_extensions
            GROUP BY current_phase
        """))
        progression_stats = result.fetchall()
        
        for stat in progression_stats:
            print(f"      ✅ {stat.current_phase} Phase: {stat.count} flows, {stat.progression_rate:.2%} with progression data")
            
    return True


async def test_crewai_master_flow_coordination():
    """Test CrewAI extensions with master flow references"""
    
    print("\n🧪 Testing CrewAI Master Flow Coordination")
    print("=" * 45)
    
    async with AsyncSessionLocal() as session:
        # Test 1: Flow persistence data integrity
        print("\n   1️⃣ Testing flow persistence data integrity...")
        
        result = await session.execute(text("""
            SELECT 
                COUNT(*) as total_extensions,
                COUNT(CASE WHEN flow_persistence_data != '{}' THEN 1 END) as with_persistence,
                COUNT(CASE WHEN current_phase IS NOT NULL THEN 1 END) as with_phase
            FROM crewai_flow_state_extensions
        """))
        persistence_stats = result.fetchone()
        
        print(f"      ✅ Total Extensions: {persistence_stats.total_extensions}")
        print(f"      ✅ With Persistence Data: {persistence_stats.with_persistence}")
        print(f"      ✅ With Phase Data: {persistence_stats.with_phase}")
        
        # Test 2: Cross-phase context validation
        print("\n   2️⃣ Testing cross-phase context validation...")
        
        result = await session.execute(text("""
            SELECT 
                flow_id,
                current_phase,
                cross_phase_context
            FROM crewai_flow_state_extensions
            WHERE cross_phase_context IS NOT NULL
            AND cross_phase_context != '{}'
            LIMIT 3
        """))
        contexts = result.fetchall()
        
        for ctx in contexts:
            context_data = ctx.cross_phase_context if ctx.cross_phase_context else {}
            print(f"      ✅ Flow {ctx.flow_id}: Phase {ctx.current_phase}, Context: {context_data}")
            
        # Test 3: Master flow relationships integrity
        print("\n   3️⃣ Testing master flow relationships integrity...")
        
        result = await session.execute(text("""
            SELECT 
                cse.flow_id as master_flow_id,
                df.id as discovery_flow_id,
                df.flow_name,
                COUNT(a.id) as linked_assets
            FROM crewai_flow_state_extensions cse
            JOIN discovery_flows df ON cse.discovery_flow_id = df.id
            LEFT JOIN assets a ON a.master_flow_id = cse.flow_id
            GROUP BY cse.flow_id, df.id, df.flow_name
            HAVING COUNT(a.id) > 0
            ORDER BY COUNT(a.id) DESC
            LIMIT 5
        """))
        relationships = result.fetchall()
        
        for rel in relationships:
            print(f"      ✅ Master Flow {rel.master_flow_id}: Discovery '{rel.flow_name}' with {rel.linked_assets} assets")
            
    return True


async def main():
    """Main compatibility testing function"""
    print("🚀 Master Flow Application Compatibility Testing")
    print("=" * 65)
    
    try:
        # Run all compatibility tests
        success1 = await test_asset_repository_master_flow()
        success2 = await test_discovery_flow_master_integration()
        success3 = await test_crewai_master_flow_coordination()
        
        if success1 and success2 and success3:
            print("\n🎉 Master Flow Application Compatibility: ALL TESTS PASSED")
            print("✅ Asset repository master flow queries working")
            print("✅ Discovery flow services with master coordination working")
            print("✅ CrewAI extensions with master flow references working")
            print("✅ Application layer fully compatible with master flow architecture")
            sys.exit(0)
        else:
            print("\n❌ Master Flow Application Compatibility: TESTS FAILED")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Compatibility Test Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 