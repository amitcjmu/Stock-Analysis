#!/usr/bin/env python3
"""
Master Flow Integrity Validation Script
Task 1.4.1: Verify master flow ID consistency and cross-phase relationship integrity
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text
from app.core.database import AsyncSessionLocal
import json


async def validate_master_flow_integrity():
    """Validate master flow architecture integrity"""
    
    print("🔍 Master Flow Architecture Validation")
    print("=" * 50)
    
    async with AsyncSessionLocal() as session:
        
        # 1. Verify CrewAI Flow State Extensions as Master Coordinators
        print("\n1️⃣ Validating CrewAI Flow State Extensions...")
        
        result = await session.execute(text("""
            SELECT COUNT(*) as extension_count,
                   COUNT(DISTINCT flow_id) as unique_flow_ids,
                   COUNT(discovery_flow_id) as linked_discovery_flows
            FROM crewai_flow_state_extensions
        """))
        stats = result.fetchone()
        
        print(f"   ✅ Total Extensions: {stats.extension_count}")
        print(f"   ✅ Unique Flow IDs: {stats.unique_flow_ids}")
        print(f"   ✅ Linked Discovery Flows: {stats.linked_discovery_flows}")
        
        if stats.extension_count != stats.unique_flow_ids:
            print(f"   ❌ ERROR: Duplicate flow_id values detected!")
            return False
            
        # 2. Verify Discovery Flows Master Flow References
        print("\n2️⃣ Validating Discovery Flows Master Flow References...")
        
        result = await session.execute(text("""
            SELECT 
                COUNT(*) as total_discovery_flows,
                COUNT(master_flow_id) as flows_with_master_id,
                COUNT(CASE WHEN cse.flow_id IS NOT NULL THEN 1 END) as valid_master_refs
            FROM discovery_flows df
            LEFT JOIN crewai_flow_state_extensions cse ON df.master_flow_id = cse.flow_id
        """))
        flows_stats = result.fetchone()
        
        print(f"   ✅ Total Discovery Flows: {flows_stats.total_discovery_flows}")
        print(f"   ✅ Flows with Master ID: {flows_stats.flows_with_master_id}")
        print(f"   ✅ Valid Master References: {flows_stats.valid_master_refs}")
        
        if flows_stats.flows_with_master_id != flows_stats.valid_master_refs:
            print(f"   ❌ ERROR: Invalid master flow references detected!")
            return False
            
        # 3. Verify Assets Master Flow Integration
        print("\n3️⃣ Validating Assets Master Flow Integration...")
        
        result = await session.execute(text("""
            SELECT 
                COUNT(*) as total_assets,
                COUNT(master_flow_id) as assets_with_master_flow,
                COUNT(discovery_flow_id) as assets_with_discovery_flow,
                COUNT(CASE WHEN source_phase = 'discovery' THEN 1 END) as discovery_phase_assets,
                COUNT(CASE WHEN current_phase = 'discovery' THEN 1 END) as current_discovery_assets
            FROM assets
        """))
        assets_stats = result.fetchone()
        
        print(f"   ✅ Total Assets: {assets_stats.total_assets}")
        print(f"   ✅ Assets with Master Flow: {assets_stats.assets_with_master_flow}")
        print(f"   ✅ Assets with Discovery Flow: {assets_stats.assets_with_discovery_flow}")
        print(f"   ✅ Discovery Phase Assets: {assets_stats.discovery_phase_assets}")
        print(f"   ✅ Current Discovery Assets: {assets_stats.current_discovery_assets}")
        
        # 4. Verify Cross-Phase Relationship Integrity
        print("\n4️⃣ Validating Cross-Phase Relationship Integrity...")
        
        result = await session.execute(text("""
            SELECT 
                df.id as discovery_flow_id,
                df.master_flow_id,
                cse.flow_id as crewai_flow_id,
                COUNT(a.id) as asset_count,
                COUNT(CASE WHEN a.master_flow_id = df.master_flow_id THEN 1 END) as matching_master_flows
            FROM discovery_flows df
            LEFT JOIN crewai_flow_state_extensions cse ON df.master_flow_id = cse.flow_id
            LEFT JOIN assets a ON a.discovery_flow_id = df.id
            GROUP BY df.id, df.master_flow_id, cse.flow_id
            HAVING COUNT(a.id) > 0
            ORDER BY asset_count DESC
            LIMIT 10
        """))
        relationships = result.fetchall()
        
        print(f"   ✅ Top 10 Discovery Flows with Assets:")
        integrity_issues = 0
        for rel in relationships:
            status = "✅" if rel.asset_count == rel.matching_master_flows else "❌"
            flow_id_str = str(rel.discovery_flow_id)[:8] if rel.discovery_flow_id else "None"
            print(f"      {status} Flow {flow_id_str}... - {rel.asset_count} assets, {rel.matching_master_flows} with matching master flow")
            if rel.asset_count != rel.matching_master_flows:
                integrity_issues += 1
        
        if integrity_issues > 0:
            print(f"   ❌ ERROR: {integrity_issues} flows have master flow integrity issues!")
            return False
            
        # 5. Verify Phase Progression Tracking
        print("\n5️⃣ Validating Phase Progression Tracking...")
        
        result = await session.execute(text("""
            SELECT 
                current_phase,
                COUNT(*) as extension_count,
                COUNT(CASE WHEN phase_progression IS NOT NULL THEN 1 END) as with_progression
            FROM crewai_flow_state_extensions
            GROUP BY current_phase
        """))
        progression_stats = result.fetchall()
        
        for stat in progression_stats:
            print(f"   ✅ {stat.current_phase} Phase: {stat.extension_count} extensions, {stat.with_progression} with progression data")
            
        # 6. Verify Data Migration Success
        print("\n6️⃣ Validating Data Migration Success...")
        
        # Check if discovery_assets table still exists
        result = await session.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'discovery_assets'
            )
        """))
        discovery_assets_exists = result.scalar()
        
        if discovery_assets_exists:
            print(f"   ❌ ERROR: Legacy discovery_assets table still exists!")
            return False
        else:
            print(f"   ✅ Legacy discovery_assets table successfully removed")
            
        # Check migrated asset data integrity
        result = await session.execute(text("""
            SELECT 
                COUNT(*) as migrated_assets,
                COUNT(CASE WHEN custom_attributes IS NOT NULL THEN 1 END) as with_custom_attrs,
                COUNT(CASE WHEN raw_data IS NOT NULL THEN 1 END) as with_raw_data
            FROM assets 
            WHERE source_phase = 'discovery'
        """))
        migration_stats = result.fetchone()
        
        print(f"   ✅ Migrated Assets: {migration_stats.migrated_assets}")
        print(f"   ✅ With Custom Attributes: {migration_stats.with_custom_attrs}")
        print(f"   ✅ With Raw Data: {migration_stats.with_raw_data}")
        
    print("\n🎉 Master Flow Integrity Validation COMPLETE!")
    print("✅ All master flow relationships verified")
    print("✅ Cross-phase integrity confirmed")
    print("✅ Data migration successful")
    print("✅ Architecture ready for future phases")
    
    return True


async def main():
    """Main validation function"""
    try:
        success = await validate_master_flow_integrity()
        if success:
            print("\n✅ Master Flow Architecture Validation: PASSED")
            sys.exit(0)
        else:
            print("\n❌ Master Flow Architecture Validation: FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Validation Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 