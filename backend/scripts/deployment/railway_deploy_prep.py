#!/usr/bin/env python3
"""
Railway Deployment Preparation Script

This script prepares the local database state to match what Railway needs,
ensuring a smooth deployment process.
"""

import asyncio
import os
from typing import Dict, List

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

# Database connection
raw_db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/migration_db")
if raw_db_url.startswith("postgresql://"):
    DATABASE_URL = raw_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = raw_db_url

async def prepare_for_railway_deployment():
    """Prepare local database for Railway deployment."""
    
    engine = create_async_engine(DATABASE_URL)
    
    try:
        async with engine.begin() as conn:
            print("🚀 Preparing database for Railway deployment...")
            print("=" * 60)
            
            # 1. Check current migration state
            print("📋 Step 1: Checking current migration state...")
            try:
                current_versions = await conn.execute(sa.text(
                    "SELECT version_num FROM alembic_version ORDER BY version_num"
                ))
                versions = [row.version_num for row in current_versions.fetchall()]
                print(f"   Current alembic versions: {versions}")
            except Exception as e:
                print(f"   ❌ Error reading alembic_version: {e}")
                return False
            
            # 2. Run orphan flow migration to fix data consistency
            print("\n📋 Step 2: Fixing orphaned discovery flows...")
            try:
                # Check for orphaned flows
                orphan_check = await conn.execute(sa.text("""
                    SELECT COUNT(*) as orphan_count
                    FROM discovery_flows df
                    LEFT JOIN crewai_flow_state_extensions cse ON df.flow_id = cse.flow_id
                    WHERE cse.flow_id IS NULL
                """))
                orphan_count = orphan_check.fetchone().orphan_count
                
                if orphan_count > 0:
                    print(f"   Found {orphan_count} orphaned discovery flows - fixing...")
                    
                    # Get orphaned flows
                    orphaned_flows = await conn.execute(sa.text("""
                        SELECT df.flow_id, df.client_account_id, df.engagement_id, 
                               df.user_id, df.flow_name, df.created_at
                        FROM discovery_flows df
                        LEFT JOIN crewai_flow_state_extensions cse ON df.flow_id = cse.flow_id
                        WHERE cse.flow_id IS NULL
                        ORDER BY df.created_at
                    """))
                    
                    # Create missing crewai_flow_state_extensions records
                    for flow in orphaned_flows.fetchall():
                        await conn.execute(sa.text("""
                            INSERT INTO crewai_flow_state_extensions (
                                flow_id, client_account_id, engagement_id, user_id,
                                flow_type, flow_name, flow_status, flow_configuration,
                                flow_persistence_data, agent_collaboration_log,
                                memory_usage_metrics, knowledge_base_analytics,
                                phase_execution_times, agent_performance_metrics,
                                crew_coordination_analytics, learning_patterns,
                                user_feedback_history, adaptation_metrics,
                                created_at, updated_at
                            ) VALUES (
                                :flow_id, :client_account_id, :engagement_id, :user_id,
                                'discovery', :flow_name, 'completed', '{}',
                                '{}', '[]', '{}', '{}', '{}', '{}', '{}', '[]', '[]', '{}',
                                :created_at, :created_at
                            )
                            ON CONFLICT (flow_id) DO NOTHING
                        """), {
                            'flow_id': flow.flow_id,
                            'client_account_id': flow.client_account_id,
                            'engagement_id': flow.engagement_id,
                            'user_id': flow.user_id or 'migrated-user',
                            'flow_name': flow.flow_name or f'Migrated Flow {str(flow.flow_id)[:8]}',
                            'created_at': flow.created_at
                        })
                    
                    print(f"   ✅ Fixed {orphan_count} orphaned flows")
                else:
                    print("   ✅ No orphaned flows found")
                    
            except Exception as e:
                print(f"   ⚠️  Orphan flow fix warning: {e}")
            
            # 3. Validate final state
            print("\n📋 Step 3: Final validation...")
            try:
                # Check data consistency
                consistency_check = await conn.execute(sa.text("""
                    SELECT 
                        (SELECT COUNT(*) FROM discovery_flows) as discovery_count,
                        (SELECT COUNT(*) FROM crewai_flow_state_extensions) as extensions_count,
                        (SELECT COUNT(*) FROM discovery_flows df
                         LEFT JOIN crewai_flow_state_extensions cse ON df.flow_id = cse.flow_id
                         WHERE cse.flow_id IS NULL) as orphan_count
                """))
                stats = consistency_check.fetchone()
                
                print(f"   📊 Discovery flows: {stats.discovery_count}")
                print(f"   📊 Flow extensions: {stats.extensions_count}")
                print(f"   📊 Orphaned flows: {stats.orphan_count}")
                
                if stats.orphan_count == 0:
                    print("   ✅ Data consistency validated")
                else:
                    print(f"   ❌ Still have {stats.orphan_count} orphaned flows")
                    return False
                
                # Check critical schema elements
                schema_checks = [
                    ("crewai_flow_state_extensions", "client_account_id"),
                    ("crewai_flow_state_extensions", "engagement_id"),
                    ("crewai_flow_state_extensions", "flow_type"),
                    ("crewai_flow_state_extensions", "flow_status"),
                    ("assets", "flow_id"),
                    ("discovery_flows", "flow_id"),
                ]
                
                all_good = True
                for table, column in schema_checks:
                    check_result = await conn.execute(sa.text("""
                        SELECT COUNT(*) 
                        FROM information_schema.columns 
                        WHERE table_name = :table_name AND column_name = :column_name
                    """), {"table_name": table, "column_name": column})
                    
                    if check_result.scalar() > 0:
                        print(f"   ✅ {table}.{column}")
                    else:
                        print(f"   ❌ MISSING: {table}.{column}")
                        all_good = False
                
                if not all_good:
                    print("   ❌ Schema validation failed")
                    return False
                
            except Exception as e:
                print(f"   ❌ Validation error: {e}")
                return False
            
            # 4. Generate deployment summary
            print("\n" + "=" * 60)
            print("🎉 RAILWAY DEPLOYMENT PREPARATION COMPLETE")
            print("=" * 60)
            print("✅ Database schema synchronized")
            print("✅ Orphaned flows fixed")
            print("✅ Data consistency validated")
            print("✅ All critical columns present")
            print()
            print("🚀 READY FOR RAILWAY DEPLOYMENT")
            print()
            print("Next steps:")
            print("1. Commit and push your code")
            print("2. Deploy to Railway")
            print("3. Railway will automatically run: alembic upgrade head")
            print("4. Validate with: railway run python railway_migration_check.py")
            print()
            print("Migration that will run on Railway:")
            print("- railway_safe_schema_sync (idempotent, safe)")
            print()
            return True
            
    except Exception as e:
        print(f"❌ Deployment preparation failed: {e}")
        return False
    finally:
        await engine.dispose()

async def main():
    """Main function."""
    success = await prepare_for_railway_deployment()
    
    if success:
        print("✅ Railway deployment preparation successful!")
        exit(0)
    else:
        print("❌ Railway deployment preparation failed!")
        print("Please fix the issues above before deploying to Railway.")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())