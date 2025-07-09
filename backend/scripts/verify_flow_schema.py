#!/usr/bin/env python3
"""
Verify Flow Schema Migration

This script verifies that the Phase 4 database migration for flow management
tables has been completed successfully.
"""

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.models.user_active_flows import UserActiveFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.asset import Asset
from app.models.discovery_flow import DiscoveryFlow


async def verify_flow_schema():
    """Verify that all flow management tables and relationships are working."""
    print("🔍 Verifying Flow Schema Migration...")
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Verify user_active_flows table exists and has correct structure
            print("\n1. Checking user_active_flows table...")
            result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'migration' 
                AND table_name = 'user_active_flows'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            
            expected_columns = [
                'id', 'user_id', 'flow_id', 'engagement_id', 
                'activated_at', 'is_current', 'created_at', 'updated_at'
            ]
            
            actual_columns = [col.column_name for col in columns]
            
            if set(expected_columns).issubset(set(actual_columns)):
                print("   ✅ user_active_flows table has all required columns")
                for col in columns:
                    print(f"   - {col.column_name}: {col.data_type} (nullable: {col.is_nullable})")
            else:
                print("   ❌ user_active_flows table missing columns:")
                missing = set(expected_columns) - set(actual_columns)
                print(f"   Missing: {missing}")
                return False
            
            # 2. Verify foreign key constraints
            print("\n2. Checking foreign key constraints...")
            result = await session.execute(text("""
                SELECT conname, contype 
                FROM pg_constraint 
                WHERE conrelid = 'migration.user_active_flows'::regclass 
                AND contype = 'f'
            """))
            fkeys = result.fetchall()
            
            expected_fkeys = ['fk_user_active_flows_user', 'fk_user_active_flows_engagement']
            actual_fkeys = [fk.conname for fk in fkeys]
            
            if set(expected_fkeys).issubset(set(actual_fkeys)):
                print("   ✅ Foreign key constraints exist")
                for fk in fkeys:
                    print(f"   - {fk.conname}")
            else:
                print("   ❌ Missing foreign key constraints")
                return False
            
            # 3. Verify indexes
            print("\n3. Checking indexes...")
            result = await session.execute(text("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE schemaname = 'migration' AND tablename = 'user_active_flows'
            """))
            indexes = result.fetchall()
            
            expected_indexes = [
                'idx_user_active_flows_user_id',
                'idx_user_active_flows_flow_id',
                'idx_user_active_flows_engagement_id',
                'idx_user_active_flows_is_current'
            ]
            
            actual_indexes = [idx.indexname for idx in indexes]
            
            if set(expected_indexes).issubset(set(actual_indexes)):
                print("   ✅ Required indexes exist")
                for idx in indexes:
                    print(f"   - {idx.indexname}")
            else:
                print("   ❌ Missing indexes")
                return False
            
            # 4. Verify model imports work
            print("\n4. Testing model imports...")
            try:
                # Test that all flow models can be imported
                models = [UserActiveFlow, CrewAIFlowStateExtensions, Asset, DiscoveryFlow]
                print("   ✅ All flow models imported successfully")
                for model in models:
                    print(f"   - {model.__name__}")
            except Exception as e:
                print(f"   ❌ Model import failed: {e}")
                return False
            
            # 5. Verify crewai_flow_state_extensions has flow_metadata
            print("\n5. Checking flow_metadata in crewai_flow_state_extensions...")
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns
                WHERE table_schema = 'migration' 
                AND table_name = 'crewai_flow_state_extensions'
                AND column_name = 'flow_metadata'
            """))
            metadata_column = result.fetchone()
            
            if metadata_column:
                print("   ✅ flow_metadata column exists in crewai_flow_state_extensions")
            else:
                print("   ❌ flow_metadata column missing")
                return False
            
            # 6. Verify flow_id usage in asset and discovery_flow models
            print("\n6. Verifying flow_id usage...")
            
            # Check assets table
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns
                WHERE table_schema = 'migration' 
                AND table_name = 'assets'
                AND column_name = 'flow_id'
            """))
            assets_flow_id = result.fetchone()
            
            # Check discovery_flows table
            result = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns
                WHERE table_schema = 'migration' 
                AND table_name = 'discovery_flows'
                AND column_name = 'flow_id'
            """))
            discovery_flow_id = result.fetchone()
            
            if assets_flow_id and discovery_flow_id:
                print("   ✅ flow_id columns exist in assets and discovery_flows")
            else:
                print("   ❌ flow_id columns missing")
                return False
                
            print("\n🎉 All flow schema verification checks passed!")
            return True
            
        except Exception as e:
            print(f"\n❌ Schema verification failed: {e}")
            return False


async def main():
    """Main verification function."""
    success = await verify_flow_schema()
    
    if success:
        print("\n✅ PHASE 4 MIGRATION COMPLETE")
        print("Flow management tables are ready for session-to-flow refactor")
        print("\nNext steps:")
        print("- Update schema files (context.py, flow.py)")
        print("- Update API endpoints to use flow-based context")
        print("- Update service layer for flow management")
    else:
        print("\n❌ PHASE 4 MIGRATION INCOMPLETE")
        print("Please resolve the schema issues before proceeding")


if __name__ == "__main__":
    asyncio.run(main())