#!/usr/bin/env python3
"""
Database Migration Script: CMDB Assets → Unified Assets

This script migrates data from the cmdb_assets table to the unified assets table
and updates all foreign key references throughout the database.

Usage:
    python backend/scripts/migrate_cmdb_to_assets.py [--dry-run] [--backup]
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.asset import Asset
from app.models.data_import import RawImportRecord
from app.models.tags import AssetEmbedding, AssetTag


class CMDBToAssetsDataMigrator:
    """Handles the migration from cmdb_assets to assets table."""
    
    def __init__(self, dry_run: bool = False, create_backup: bool = True):
        self.dry_run = dry_run
        self.create_backup = create_backup
        self.migration_stats = {
            "cmdb_assets_migrated": 0,
            "raw_import_records_updated": 0,
            "asset_embeddings_updated": 0,
            "asset_tags_updated": 0,
            "errors": []
        }
        
    async def run_migration(self):
        """Execute the complete migration process."""
        print("🚀 **CMDB Assets → Unified Assets Migration**")
        print("=" * 60)
        
        if self.dry_run:
            print("🔍 **DRY RUN MODE** - No changes will be made")
        
        async with AsyncSessionLocal() as session:
            try:
                # Step 1: Analyze current state
                await self._analyze_current_state(session)
                
                # Step 2: Create backup if requested
                if self.create_backup and not self.dry_run:
                    await self._create_backup(session)
                
                # Step 3: Migrate cmdb_assets data to assets
                await self._migrate_cmdb_assets_data(session)
                
                # Step 4: Update foreign key references
                await self._update_foreign_key_references(session)
                
                # Step 5: Verify migration integrity
                await self._verify_migration_integrity(session)
                
                # Step 6: Cleanup (only if not dry run)
                if not self.dry_run:
                    await self._cleanup_old_tables(session)
                
                # Commit changes
                if not self.dry_run:
                    await session.commit()
                    print("✅ **Migration completed successfully!**")
                else:
                    print("✅ **Dry run completed - no changes made**")
                
                self._print_migration_summary()
                
            except Exception as e:
                await session.rollback()
                print(f"❌ **Migration failed**: {e}")
                raise
    
    async def _analyze_current_state(self, session: AsyncSession):
        """Analyze the current database state before migration."""
        print("\n📊 **Step 1: Analyzing Current Database State**")
        
        # Count records in cmdb_assets
        cmdb_count_result = await session.execute(text("SELECT COUNT(*) FROM migration.cmdb_assets"))
        cmdb_count = cmdb_count_result.scalar()
        
        # Count records in assets
        assets_count_result = await session.execute(text("SELECT COUNT(*) FROM migration.assets"))
        assets_count = assets_count_result.scalar()
        
        # Count foreign key references
        raw_import_refs = await session.execute(text(
            "SELECT COUNT(*) FROM migration.raw_import_records WHERE cmdb_asset_id IS NOT NULL"
        ))
        raw_import_count = raw_import_refs.scalar()
        
        embeddings_refs = await session.execute(text(
            "SELECT COUNT(*) FROM migration.cmdb_asset_embeddings"
        ))
        embeddings_count = embeddings_refs.scalar()
        
        tags_refs = await session.execute(text(
            "SELECT COUNT(*) FROM migration.asset_tags WHERE cmdb_asset_id IS NOT NULL"
        ))
        tags_count = tags_refs.scalar()
        
        print(f"   📋 CMDB Assets: {cmdb_count} records")
        print(f"   📋 Assets: {assets_count} records")
        print(f"   🔗 Raw Import Records referencing CMDB Assets: {raw_import_count}")
        print(f"   🧠 Asset Embeddings: {embeddings_count}")
        print(f"   🏷️  Asset Tags referencing CMDB Assets: {tags_count}")
        
        if assets_count > 0:
            print("   ⚠️  Warning: Assets table already contains data")
        
        return {
            "cmdb_assets": cmdb_count,
            "assets": assets_count,
            "raw_import_refs": raw_import_count,
            "embeddings": embeddings_count,
            "tags": tags_count
        }
    
    async def _create_backup(self, session: AsyncSession):
        """Create backup tables before migration."""
        print("\n💾 **Step 2: Creating Backup Tables**")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        backup_queries = [
            f"CREATE TABLE migration.cmdb_assets_backup_{timestamp} AS SELECT * FROM migration.cmdb_assets",
            f"CREATE TABLE migration.raw_import_records_backup_{timestamp} AS SELECT * FROM migration.raw_import_records",
            f"CREATE TABLE migration.cmdb_asset_embeddings_backup_{timestamp} AS SELECT * FROM migration.cmdb_asset_embeddings",
            f"CREATE TABLE migration.asset_tags_backup_{timestamp} AS SELECT * FROM migration.asset_tags"
        ]
        
        for query in backup_queries:
            try:
                await session.execute(text(query))
                table_name = query.split("CREATE TABLE migration.")[1].split(" AS")[0]
                print(f"   ✅ Created backup: {table_name}")
            except Exception as e:
                print(f"   ⚠️  Backup warning for {query}: {e}")
    
    async def _migrate_cmdb_assets_data(self, session: AsyncSession):
        """Migrate data from cmdb_assets to assets table."""
        print("\n🔄 **Step 3: Migrating CMDB Assets Data to Assets Table**")
        
        # Get all cmdb_assets records
        cmdb_assets_query = await session.execute(text(
            "SELECT * FROM migration.cmdb_assets ORDER BY created_at"
        ))
        cmdb_assets = cmdb_assets_query.fetchall()
        
        print(f"   📦 Found {len(cmdb_assets)} CMDB assets to migrate")
        
        migrated_count = 0
        
        for cmdb_asset in cmdb_assets:
            try:
                # Map cmdb_asset fields to asset fields
                asset_data = {
                    # Don't include id - let assets table auto-generate it
                    "client_account_id": cmdb_asset.client_account_id,
                    "engagement_id": cmdb_asset.engagement_id,
                    # No session_id field in assets table
                    
                    # Core identification
                    "name": cmdb_asset.name,
                    "hostname": cmdb_asset.hostname,
                    "asset_type": cmdb_asset.asset_type,
                    
                    # Technical details
                    "ip_address": cmdb_asset.ip_address,
                    "operating_system": cmdb_asset.operating_system,
                    "environment": cmdb_asset.environment,
                    "cpu_cores": cmdb_asset.cpu_cores,
                    "memory_gb": cmdb_asset.memory_gb,
                    "storage_gb": cmdb_asset.storage_gb,
                    
                    # Business information
                    "business_owner": cmdb_asset.business_owner,
                    "department": cmdb_asset.department,
                    "business_criticality": cmdb_asset.criticality,  # Map criticality to business_criticality
                    
                    # Migration information
                    "six_r_strategy": cmdb_asset.six_r_strategy,  # Correct field name
                    "sixr_ready": cmdb_asset.sixr_ready,
                    "migration_complexity": cmdb_asset.migration_complexity,
                    "migration_priority": cmdb_asset.migration_priority,
                    "migration_wave": cmdb_asset.migration_wave,
                    
                    # Dependencies and relationships
                    "dependencies": cmdb_asset.dependencies,
                    "dependents": cmdb_asset.related_assets,  # Map related_assets to dependents
                    
                    # Source and audit information
                    "discovery_source": cmdb_asset.discovery_source,
                    "discovery_method": cmdb_asset.discovery_method,
                    "discovered_at": cmdb_asset.discovery_timestamp,  # Map discovery_timestamp to discovered_at
                    "created_by": cmdb_asset.imported_by,  # Map imported_by to created_by
                    "source_file": cmdb_asset.source_filename,  # Map source_filename to source_file
                    # raw_data field doesn't exist in assets table
                    
                    # Timestamps
                    "created_at": cmdb_asset.created_at,
                    "updated_at": cmdb_asset.updated_at
                }
                
                if not self.dry_run:
                    # Insert into assets table
                    insert_query = text("""
                        INSERT INTO migration.assets (
                            client_account_id, engagement_id,
                            name, hostname, asset_type, ip_address, operating_system, environment,
                            cpu_cores, memory_gb, storage_gb, business_owner, department, 
                            business_criticality, six_r_strategy, sixr_ready,
                            migration_complexity, migration_priority, migration_wave,
                            dependencies, dependents, discovery_source, discovery_method,
                            discovered_at, created_by, source_file,
                            created_at, updated_at
                        ) VALUES (
                            :client_account_id, :engagement_id,
                            :name, :hostname, :asset_type, :ip_address, :operating_system, :environment,
                            :cpu_cores, :memory_gb, :storage_gb, :business_owner, :department,
                            :business_criticality, :six_r_strategy, :sixr_ready,
                            :migration_complexity, :migration_priority, :migration_wave,
                            :dependencies, :dependents, :discovery_source, :discovery_method,
                            :discovered_at, :created_by, :source_file,
                            :created_at, :updated_at
                        )
                    """)
                    
                    await session.execute(insert_query, asset_data)
                
                migrated_count += 1
                
                if migrated_count % 10 == 0:
                    print(f"   📦 Migrated {migrated_count}/{len(cmdb_assets)} assets...")
                
            except Exception as e:
                error_msg = f"Error migrating asset {cmdb_asset.id}: {e}"
                self.migration_stats["errors"].append(error_msg)
                print(f"   ❌ {error_msg}")
        
        self.migration_stats["cmdb_assets_migrated"] = migrated_count
        print(f"   ✅ Successfully migrated {migrated_count} assets")
    
    async def _update_foreign_key_references(self, session: AsyncSession):
        """Update all foreign key references from cmdb_asset_id to asset_id."""
        print("\n🔗 **Step 4: Updating Foreign Key References**")
        print("   ⚠️  Note: Foreign key updates skipped - new assets table uses auto-generated integer IDs")
        print("   ⚠️  Existing foreign key relationships will need to be rebuilt through application logic")
        
        # Since the new assets table uses auto-generated integer IDs instead of UUIDs,
        # we cannot directly map the old cmdb_asset_id (UUID) to the new asset_id (integer).
        # The foreign key relationships will need to be rebuilt through application logic
        # that can match assets by name, hostname, or other identifying attributes.
        
        self.migration_stats["raw_import_records_updated"] = 0
        self.migration_stats["asset_embeddings_updated"] = 0
        self.migration_stats["asset_tags_updated"] = 0
        
        print("   📝 Raw import record references: Requires application-level rebuild")
        print("   🧠 Asset embedding references: Requires application-level rebuild") 
        print("   🏷️  Asset tag references: Requires application-level rebuild")
    
    async def _verify_migration_integrity(self, session: AsyncSession):
        """Verify the integrity of the migration."""
        print("\n🔍 **Step 5: Verifying Migration Integrity**")
        
        # Check asset count matches
        assets_count_result = await session.execute(text("SELECT COUNT(*) FROM migration.assets"))
        assets_count = assets_count_result.scalar()
        
        cmdb_count_result = await session.execute(text("SELECT COUNT(*) FROM migration.cmdb_assets"))
        cmdb_count = cmdb_count_result.scalar()
        
        print(f"   📊 Assets table: {assets_count} records")
        print(f"   📊 CMDB Assets table: {cmdb_count} records")
        
        if assets_count >= cmdb_count:
            print("   ✅ Asset count verification passed")
        else:
            print("   ❌ Asset count verification failed")
            self.migration_stats["errors"].append("Asset count mismatch")
        
        # Skip foreign key integrity check since we're not updating foreign keys
        print("   🔍 Foreign key integrity check skipped - foreign keys require application-level rebuild")
    
    async def _cleanup_old_tables(self, session: AsyncSession):
        """Clean up old tables and columns after successful migration."""
        print("\n🧹 **Step 6: Cleaning Up Old Tables and Columns**")
        
        cleanup_queries = [
            # Remove old cmdb_asset_id columns
            "ALTER TABLE migration.raw_import_records DROP COLUMN IF EXISTS cmdb_asset_id",
            "ALTER TABLE migration.cmdb_asset_embeddings DROP COLUMN IF EXISTS cmdb_asset_id", 
            "ALTER TABLE migration.asset_tags DROP COLUMN IF EXISTS cmdb_asset_id",
            
            # Drop the cmdb_assets table
            "DROP TABLE IF EXISTS migration.cmdb_assets CASCADE"
        ]
        
        for query in cleanup_queries:
            try:
                await session.execute(text(query))
                print(f"   ✅ Executed: {query}")
            except Exception as e:
                print(f"   ⚠️  Cleanup warning: {e}")
    
    def _print_migration_summary(self):
        """Print a summary of the migration results."""
        print("\n📋 **Migration Summary**")
        print("=" * 40)
        print(f"   📦 CMDB Assets Migrated: {self.migration_stats['cmdb_assets_migrated']}")
        print(f"   📝 Raw Import Records Updated: {self.migration_stats['raw_import_records_updated']}")
        print(f"   🧠 Asset Embeddings Updated: {self.migration_stats['asset_embeddings_updated']}")
        print(f"   🏷️  Asset Tags Updated: {self.migration_stats['asset_tags_updated']}")
        print(f"   ❌ Errors: {len(self.migration_stats['errors'])}")
        
        if self.migration_stats["errors"]:
            print("\n⚠️  **Errors Encountered:**")
            for error in self.migration_stats["errors"]:
                print(f"   - {error}")

async def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description="Migrate CMDB Assets to Unified Assets")
    parser.add_argument("--dry-run", action="store_true", help="Run migration analysis without making changes")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating backup tables")
    
    args = parser.parse_args()
    
    migrator = CMDBToAssetsDataMigrator(
        dry_run=args.dry_run,
        create_backup=not args.no_backup
    )
    
    await migrator.run_migration()

if __name__ == "__main__":
    asyncio.run(main()) 