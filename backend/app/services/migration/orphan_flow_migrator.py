"""
Orphan Flow Migration Script
Fixes existing orphaned flows by creating missing master flow records.

This script addresses the critical architecture issue where:
- discovery_flows table has 14 records
- crewai_flow_state_extensions table has 0 records
- All flows are orphaned (no master coordination)

The script creates master flow records for all existing orphaned flows.
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import AsyncSessionLocal
from app.models.discovery_flow import DiscoveryFlow
from app.repositories.crewai_flow_state_extensions_repository import CrewAIFlowStateExtensionsRepository
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

logger = logging.getLogger(__name__)


class OrphanFlowMigrator:
    """
    Migrates orphaned flows to proper master-subordinate architecture.
    """
    
    def __init__(self):
        self.migration_stats = {
            "total_orphaned_flows": 0,
            "master_flows_created": 0,
            "flows_linked": 0,
            "errors": [],
            "migration_timestamp": datetime.utcnow().isoformat()
        }
    
    async def analyze_orphan_situation(self) -> Dict[str, Any]:
        """
        Analyze the current orphan flow situation across all tenants.
        """
        try:
            async with AsyncSessionLocal() as db_session:
                logger.info("🔍 Analyzing orphan flow situation...")
                
                # Count total discovery flows
                discovery_count_stmt = select(func.count(DiscoveryFlow.id))
                discovery_result = await db_session.execute(discovery_count_stmt)
                total_discovery_flows = discovery_result.scalar()
                
                # Count total master flows (should be 0 based on user report)
                from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
                master_count_stmt = select(func.count(CrewAIFlowStateExtensions.id))
                master_result = await db_session.execute(master_count_stmt)
                total_master_flows = master_result.scalar()
                
                # Get discovery flows without corresponding extensions records
                from sqlalchemy import exists
                from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
                
                orphaned_flows_stmt = select(DiscoveryFlow).where(
                    ~exists().where(CrewAIFlowStateExtensions.flow_id == DiscoveryFlow.flow_id)
                )
                orphaned_result = await db_session.execute(orphaned_flows_stmt)
                orphaned_flows = orphaned_result.scalars().all()
                
                # Get discovery flows grouped by client
                client_distribution_stmt = select(
                    DiscoveryFlow.client_account_id,
                    func.count(DiscoveryFlow.id).label('count')
                ).group_by(DiscoveryFlow.client_account_id)
                
                client_result = await db_session.execute(client_distribution_stmt)
                client_distribution = {str(row.client_account_id): row.count for row in client_result}
                
                analysis = {
                    "total_discovery_flows": total_discovery_flows,
                    "total_master_flows": total_master_flows,
                    "orphaned_flows_count": len(orphaned_flows),
                    "orphaned_percentage": (len(orphaned_flows) / total_discovery_flows * 100) if total_discovery_flows > 0 else 0,
                    "client_distribution": client_distribution,
                    "critical_issue": total_master_flows == 0 and total_discovery_flows > 0,
                    "analysis_timestamp": datetime.utcnow().isoformat()
                }
                
                logger.info(f"📊 Orphan Analysis Results:")
                logger.info(f"   Total Discovery Flows: {analysis['total_discovery_flows']}")
                logger.info(f"   Total Master Flows: {analysis['total_master_flows']}")
                logger.info(f"   Orphaned Flows: {analysis['orphaned_flows_count']} ({analysis['orphaned_percentage']:.1f}%)")
                logger.info(f"   Critical Issue: {analysis['critical_issue']}")
                
                return analysis
                
        except Exception as e:
            logger.error(f"❌ Failed to analyze orphan situation: {e}")
            return {"error": str(e), "analysis_timestamp": datetime.utcnow().isoformat()}
    
    async def migrate_orphaned_flows(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Migrate all orphaned flows to proper master-subordinate architecture.
        
        Args:
            dry_run: If True, only simulates the migration without making changes
        """
        try:
            logger.info(f"🚀 Starting orphaned flow migration (dry_run={dry_run})...")
            
            async with AsyncSessionLocal() as db_session:
                # Get all discovery flows without corresponding extensions records
                from sqlalchemy import exists
                from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
                
                orphaned_flows_stmt = select(DiscoveryFlow).where(
                    ~exists().where(CrewAIFlowStateExtensions.flow_id == DiscoveryFlow.flow_id)
                )
                orphaned_result = await db_session.execute(orphaned_flows_stmt)
                orphaned_flows = orphaned_result.scalars().all()
                
                self.migration_stats["total_orphaned_flows"] = len(orphaned_flows)
                
                logger.info(f"📋 Found {len(orphaned_flows)} orphaned flows to migrate")
                
                for flow in orphaned_flows:
                    try:
                        await self._migrate_single_flow(db_session, flow, dry_run)
                        self.migration_stats["flows_linked"] += 1
                        
                    except Exception as flow_error:
                        error_msg = f"Failed to migrate flow {flow.flow_id}: {flow_error}"
                        logger.error(f"❌ {error_msg}")
                        self.migration_stats["errors"].append(error_msg)
                
                if not dry_run:
                    await db_session.commit()
                    logger.info("✅ Migration committed to database")
                else:
                    await db_session.rollback()
                    logger.info("🔄 Dry run completed - no changes made")
                
                logger.info(f"📊 Migration Summary:")
                logger.info(f"   Total Orphaned Flows: {self.migration_stats['total_orphaned_flows']}")
                logger.info(f"   Master Flows Created: {self.migration_stats['master_flows_created']}")
                logger.info(f"   Flows Linked: {self.migration_stats['flows_linked']}")
                logger.info(f"   Errors: {len(self.migration_stats['errors'])}")
                
                return self.migration_stats
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            self.migration_stats["errors"].append(f"Migration failed: {str(e)}")
            return self.migration_stats
    
    async def _migrate_single_flow(self, db_session: AsyncSession, flow: DiscoveryFlow, dry_run: bool):
        """
        Create missing crewai_flow_state_extensions record for orphaned discovery flow.
        Simple approach: both tables have the same flow_id value.
        """
        try:
            logger.info(f"🔧 Creating missing extensions record for: {flow.flow_id}")
            
            # Create extensions repository for this tenant
            extensions_repo = CrewAIFlowStateExtensionsRepository(
                db=db_session,
                client_account_id=str(flow.client_account_id),
                engagement_id=str(flow.engagement_id)
            )
            
            # Check if extensions record already exists (safety check)
            existing_extensions = await extensions_repo.get_by_flow_id_global(str(flow.flow_id))
            if existing_extensions:
                logger.info(f"   Extensions record already exists for {flow.flow_id}, skipping")
                return
            
            if not dry_run:
                # Create extensions record with same flow_id
                extensions_record = await extensions_repo.create_master_flow(
                    flow_id=str(flow.flow_id),  # Same flow_id as discovery flow
                    flow_type="discovery",
                    user_id=flow.user_id,
                    flow_name=flow.flow_name or f"Discovery Flow {str(flow.flow_id)[:8]}",
                    flow_configuration={
                        "data_import_id": str(flow.data_import_id) if flow.data_import_id else None,
                        "migration_source": "orphan_flow_migrator",
                        "original_created_at": flow.created_at.isoformat() if flow.created_at else None,
                        "crewai_state_data": flow.crewai_state_data or {}
                    },
                    initial_state={
                        "migrated_from_orphan": True,
                        "migration_timestamp": datetime.utcnow().isoformat(),
                        "original_flow_status": flow.status,
                        "original_progress": flow.progress_percentage
                    }
                )
                
                logger.info(f"   ✅ Created extensions record: {extensions_record.flow_id}")
                self.migration_stats["master_flows_created"] += 1
            else:
                logger.info(f"   [DRY RUN] Would create extensions record for: {flow.flow_id}")
                self.migration_stats["master_flows_created"] += 1
            
            self.migration_stats["flows_linked"] += 1
            
        except Exception as e:
            logger.error(f"❌ Failed to migrate flow {flow.flow_id}: {e}")
            raise
    
    async def validate_migration_results(self) -> Dict[str, Any]:
        """
        Validate that the migration was successful by checking the database state.
        """
        try:
            logger.info("🔍 Validating migration results...")
            
            async with AsyncSessionLocal() as db_session:
                # Count total discovery flows
                discovery_count_stmt = select(func.count(DiscoveryFlow.id))
                discovery_result = await db_session.execute(discovery_count_stmt)
                total_discovery_flows = discovery_result.scalar()
                
                # Count total master flows
                from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
                master_count_stmt = select(func.count(CrewAIFlowStateExtensions.id))
                master_result = await db_session.execute(master_count_stmt)
                total_master_flows = master_result.scalar()
                
                # Count discovery flows that have corresponding extensions records
                # Join to check for matching flow_id values
                from sqlalchemy import exists
                from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
                
                linked_flows_stmt = select(func.count(DiscoveryFlow.id)).where(
                    exists().where(CrewAIFlowStateExtensions.flow_id == DiscoveryFlow.flow_id)
                )
                linked_result = await db_session.execute(linked_flows_stmt)
                linked_flows = linked_result.scalar()
                
                # Count remaining orphaned flows (discovery flows without extensions records)
                orphaned_flows_stmt = select(func.count(DiscoveryFlow.id)).where(
                    ~exists().where(CrewAIFlowStateExtensions.flow_id == DiscoveryFlow.flow_id)
                )
                orphaned_result = await db_session.execute(orphaned_flows_stmt)
                remaining_orphans = orphaned_result.scalar()
                
                validation = {
                    "total_discovery_flows": total_discovery_flows,
                    "total_master_flows": total_master_flows,
                    "linked_flows": linked_flows,
                    "remaining_orphans": remaining_orphans,
                    "coordination_success_rate": (linked_flows / total_discovery_flows * 100) if total_discovery_flows > 0 else 0,
                    "architecture_healthy": remaining_orphans == 0 and total_master_flows == total_discovery_flows,
                    "validation_timestamp": datetime.utcnow().isoformat()
                }
                
                logger.info(f"📊 Migration Validation Results:")
                logger.info(f"   Total Discovery Flows: {validation['total_discovery_flows']}")
                logger.info(f"   Total Master Flows: {validation['total_master_flows']}")
                logger.info(f"   Linked Flows: {validation['linked_flows']}")
                logger.info(f"   Remaining Orphans: {validation['remaining_orphans']}")
                logger.info(f"   Coordination Success Rate: {validation['coordination_success_rate']:.1f}%")
                logger.info(f"   Architecture Healthy: {validation['architecture_healthy']}")
                
                return validation
                
        except Exception as e:
            logger.error(f"❌ Failed to validate migration results: {e}")
            return {"error": str(e), "validation_timestamp": datetime.utcnow().isoformat()}


async def main():
    """
    Main function for running the orphan flow migration.
    """
    logger.info("🚀 Starting Orphan Flow Migration Script")
    
    migrator = OrphanFlowMigrator()
    
    # Step 1: Analyze current situation
    analysis = await migrator.analyze_orphan_situation()
    print("\n" + "="*50)
    print("ORPHAN FLOW ANALYSIS")
    print("="*50)
    for key, value in analysis.items():
        print(f"{key}: {value}")
    
    if analysis.get("critical_issue"):
        print("\n⚠️  CRITICAL ISSUE DETECTED: All flows are orphaned!")
        
        # Step 2: Run dry run migration
        print("\n" + "="*50)
        print("DRY RUN MIGRATION")
        print("="*50)
        dry_run_results = await migrator.migrate_orphaned_flows(dry_run=True)
        for key, value in dry_run_results.items():
            print(f"{key}: {value}")
        
        # Step 3: Ask for confirmation to run actual migration
        print("\n" + "="*50)
        print("ACTUAL MIGRATION")
        print("="*50)
        
        # For safety, require manual confirmation
        # In production, you might want to add command line args
        run_actual = input("Run actual migration? (yes/no): ").lower().strip()
        
        if run_actual == "yes":
            print("Running actual migration...")
            actual_results = await migrator.migrate_orphaned_flows(dry_run=False)
            for key, value in actual_results.items():
                print(f"{key}: {value}")
            
            # Step 4: Validate results
            print("\n" + "="*50)
            print("MIGRATION VALIDATION")
            print("="*50)
            validation = await migrator.validate_migration_results()
            for key, value in validation.items():
                print(f"{key}: {value}")
        else:
            print("Migration cancelled.")
    else:
        print("\n✅ No critical orphan flow issues detected.")


if __name__ == "__main__":
    asyncio.run(main())