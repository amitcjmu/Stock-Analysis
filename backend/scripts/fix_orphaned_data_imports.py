#!/usr/bin/env python3
"""
Data Migration Script - Phase 3: Fix Orphaned Data Imports
============================================================

Fixes orphaned DataImport and RawImportRecord records by linking them to existing 
master flows based on timestamp proximity and tenant context.

This script addresses the data integrity issue where DataImport records exist
without master_flow_id references, causing foreign key constraint violations.

Usage:
    python scripts/fix_orphaned_data_imports.py [--dry-run] [--verbose]

Features:
- Identifies orphaned DataImport records (master_flow_id = NULL)
- Links them to existing master flows using timestamp proximity and tenant matching
- Updates both DataImport and RawImportRecord tables
- Comprehensive logging and rollback capabilities
- Progress tracking for large datasets
"""

import argparse
import asyncio
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import and_, func, or_, text
from sqlalchemy.orm import Session

from app.core.database import AsyncSessionLocal
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.data_import.core import DataImport, RawImportRecord


@dataclass
class OrphanedRecord:
    """Data structure for orphaned records."""
    id: str
    client_account_id: str
    engagement_id: str
    import_name: str
    created_at: datetime
    record_type: str  # 'data_import' or 'raw_import_record'


@dataclass
class MasterFlow:
    """Data structure for master flows."""
    id: str
    flow_id: str
    client_account_id: str
    engagement_id: str
    flow_name: str
    created_at: datetime


@dataclass
class MigrationResult:
    """Result of migration operation."""
    success: bool
    total_processed: int
    linked_successfully: int
    failed_to_link: int
    errors: List[str]


class DataImportMigrator:
    """Handles migration of orphaned data import records."""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.logger = self._setup_logging()
        self.stats = {
            'total_orphaned_data_imports': 0,
            'total_orphaned_raw_records': 0,
            'linked_data_imports': 0,
            'linked_raw_records': 0,
            'failed_links': 0,
            'errors': []
        }
        
    def _setup_logging(self) -> logging.Logger:
        """Configure logging for the migration."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    async def identify_orphaned_records(self, session: Session) -> Tuple[List[OrphanedRecord], List[OrphanedRecord]]:
        """Identify orphaned DataImport and RawImportRecord records."""
        self.logger.info("Identifying orphaned data import records...")
        
        # Find orphaned DataImport records
        orphaned_data_imports = await session.execute(
            text("""
                SELECT id, client_account_id, engagement_id, import_name, created_at
                FROM migration.data_imports 
                WHERE master_flow_id IS NULL
                ORDER BY created_at DESC
            """)
        )
        
        data_import_orphans = []
        for row in orphaned_data_imports.fetchall():
            data_import_orphans.append(OrphanedRecord(
                id=str(row.id),
                client_account_id=str(row.client_account_id),
                engagement_id=str(row.engagement_id),
                import_name=row.import_name,
                created_at=row.created_at,
                record_type='data_import'
            ))
        
        # Find orphaned RawImportRecord records
        orphaned_raw_records = await session.execute(
            text("""
                SELECT id, client_account_id, engagement_id, '', created_at
                FROM migration.raw_import_records 
                WHERE master_flow_id IS NULL
                ORDER BY created_at DESC
            """)
        )
        
        raw_record_orphans = []
        for row in orphaned_raw_records.fetchall():
            raw_record_orphans.append(OrphanedRecord(
                id=str(row.id),
                client_account_id=str(row.client_account_id),
                engagement_id=str(row.engagement_id),
                import_name="",
                created_at=row.created_at,
                record_type='raw_import_record'
            ))
        
        self.stats['total_orphaned_data_imports'] = len(data_import_orphans)
        self.stats['total_orphaned_raw_records'] = len(raw_record_orphans)
        
        self.logger.info(f"Found {len(data_import_orphans)} orphaned data imports")
        self.logger.info(f"Found {len(raw_record_orphans)} orphaned raw import records")
        
        return data_import_orphans, raw_record_orphans
    
    async def get_master_flows(self, session: Session) -> List[MasterFlow]:
        """Get all available master flows for matching."""
        self.logger.info("Retrieving master flows...")
        
        result = await session.execute(
            text("""
                SELECT id, flow_id, client_account_id, engagement_id, flow_name, created_at
                FROM migration.crewai_flow_state_extensions
                WHERE flow_type = 'discovery'
                ORDER BY created_at DESC
            """)
        )
        
        master_flows = []
        for row in result.fetchall():
            master_flows.append(MasterFlow(
                id=str(row.id),
                flow_id=str(row.flow_id),
                client_account_id=str(row.client_account_id),
                engagement_id=str(row.engagement_id),
                flow_name=row.flow_name,
                created_at=row.created_at
            ))
        
        self.logger.info(f"Found {len(master_flows)} master flows available for linking")
        return master_flows
    
    def find_matching_master_flow(self, orphan: OrphanedRecord, master_flows: List[MasterFlow]) -> Optional[MasterFlow]:
        """Find the best matching master flow for an orphaned record."""
        
        # Strategy 1: Exact tenant match + name pattern match
        for flow in master_flows:
            if (flow.client_account_id == orphan.client_account_id and 
                flow.engagement_id == orphan.engagement_id and
                orphan.id in flow.flow_name):
                self.logger.debug(f"Found exact match by name pattern: {flow.flow_name}")
                return flow
        
        # Strategy 2: Tenant match + timestamp proximity (within 5 minutes)
        tenant_matches = [
            flow for flow in master_flows 
            if (flow.client_account_id == orphan.client_account_id and 
                flow.engagement_id == orphan.engagement_id)
        ]
        
        if not tenant_matches:
            self.logger.warning(f"No tenant matches found for orphan {orphan.id}")
            return None
        
        # Find closest by timestamp
        closest_flow = None
        min_time_diff = timedelta.max
        
        for flow in tenant_matches:
            time_diff = abs(flow.created_at - orphan.created_at)
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_flow = flow
        
        # Only accept if within 5 minutes
        if closest_flow and min_time_diff <= timedelta(minutes=5):
            self.logger.debug(f"Found timestamp match within {min_time_diff}: {closest_flow.flow_name}")
            return closest_flow
        
        # Strategy 3: Tenant match + closest chronologically (fallback)
        if tenant_matches:
            closest_flow = min(tenant_matches, key=lambda f: abs(f.created_at - orphan.created_at))
            time_diff = abs(closest_flow.created_at - orphan.created_at)
            self.logger.debug(f"Fallback match with time diff {time_diff}: {closest_flow.flow_name}")
            return closest_flow
        
        return None
    
    async def link_orphaned_data_imports(self, session: Session, orphans: List[OrphanedRecord], master_flows: List[MasterFlow]) -> MigrationResult:
        """Link orphaned DataImport records to master flows."""
        self.logger.info(f"Linking {len(orphans)} orphaned data imports...")
        
        result = MigrationResult(True, len(orphans), 0, 0, [])
        
        for i, orphan in enumerate(orphans):
            try:
                if self.verbose:
                    self.logger.info(f"Processing data import {i+1}/{len(orphans)}: {orphan.id}")
                
                matching_flow = self.find_matching_master_flow(orphan, master_flows)
                if not matching_flow:
                    error_msg = f"No matching master flow found for data import {orphan.id}"
                    self.logger.warning(error_msg)
                    result.errors.append(error_msg)
                    result.failed_to_link += 1
                    continue
                
                if self.dry_run:
                    self.logger.info(f"DRY RUN: Would link data import {orphan.id} to master flow {matching_flow.flow_name}")
                    result.linked_successfully += 1
                else:
                    await session.execute(
                        text("""
                            UPDATE migration.data_imports 
                            SET master_flow_id = :master_flow_id,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = :data_import_id
                        """),
                        {
                            'master_flow_id': matching_flow.id,
                            'data_import_id': orphan.id
                        }
                    )
                    
                    self.logger.info(f"Linked data import {orphan.id} to master flow {matching_flow.flow_name}")
                    result.linked_successfully += 1
                    
            except Exception as e:
                error_msg = f"Error linking data import {orphan.id}: {str(e)}"
                self.logger.error(error_msg)
                result.errors.append(error_msg)
                result.failed_to_link += 1
                continue
        
        if not self.dry_run:
            await session.commit()
            
        self.stats['linked_data_imports'] = result.linked_successfully
        return result
    
    async def link_orphaned_raw_records(self, session: Session, orphans: List[OrphanedRecord], master_flows: List[MasterFlow]) -> MigrationResult:
        """Link orphaned RawImportRecord records to master flows."""
        self.logger.info(f"Linking {len(orphans)} orphaned raw import records...")
        
        result = MigrationResult(True, len(orphans), 0, 0, [])
        
        # Process in batches for better performance
        batch_size = 100
        for batch_start in range(0, len(orphans), batch_size):
            batch = orphans[batch_start:batch_start + batch_size]
            
            for i, orphan in enumerate(batch):
                try:
                    if self.verbose:
                        overall_index = batch_start + i + 1
                        self.logger.info(f"Processing raw record {overall_index}/{len(orphans)}: {orphan.id}")
                    
                    matching_flow = self.find_matching_master_flow(orphan, master_flows)
                    if not matching_flow:
                        error_msg = f"No matching master flow found for raw record {orphan.id}"
                        self.logger.warning(error_msg)
                        result.errors.append(error_msg)
                        result.failed_to_link += 1
                        continue
                    
                    if self.dry_run:
                        self.logger.debug(f"DRY RUN: Would link raw record {orphan.id} to master flow {matching_flow.flow_name}")
                        result.linked_successfully += 1
                    else:
                        await session.execute(
                            text("""
                                UPDATE migration.raw_import_records 
                                SET master_flow_id = :master_flow_id
                                WHERE id = :raw_record_id
                            """),
                            {
                                'master_flow_id': matching_flow.id,
                                'raw_record_id': orphan.id
                            }
                        )
                        
                        result.linked_successfully += 1
                        
                except Exception as e:
                    error_msg = f"Error linking raw record {orphan.id}: {str(e)}"
                    self.logger.error(error_msg)
                    result.errors.append(error_msg)
                    result.failed_to_link += 1
                    continue
            
            if not self.dry_run:
                await session.commit()
                self.logger.info(f"Committed batch {batch_start//batch_size + 1}")
        
        self.stats['linked_raw_records'] = result.linked_successfully
        return result
    
    async def create_rollback_script(self, session: Session) -> str:
        """Create a rollback script for the migration."""
        rollback_script = f"""
-- Rollback script for data import migration
-- Generated: {datetime.now().isoformat()}

-- Rollback DataImport linkages
UPDATE migration.data_imports 
SET master_flow_id = NULL 
WHERE master_flow_id IS NOT NULL;

-- Rollback RawImportRecord linkages
UPDATE migration.raw_import_records 
SET master_flow_id = NULL 
WHERE master_flow_id IS NOT NULL;

-- Verification queries
SELECT COUNT(*) as orphaned_data_imports FROM migration.data_imports WHERE master_flow_id IS NULL;
SELECT COUNT(*) as orphaned_raw_records FROM migration.raw_import_records WHERE master_flow_id IS NULL;
"""
        
        rollback_file = f"rollback_data_import_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        rollback_path = Path(__file__).parent / rollback_file
        
        with open(rollback_path, 'w') as f:
            f.write(rollback_script)
        
        self.logger.info(f"Rollback script created: {rollback_path}")
        return str(rollback_path)
    
    async def run_migration(self) -> bool:
        """Run the complete migration process."""
        self.logger.info("Starting data import migration process...")
        
        if self.dry_run:
            self.logger.info("DRY RUN MODE - No changes will be made")
        
        try:
            async with AsyncSessionLocal() as session:
                # Step 1: Identify orphaned records
                orphaned_data_imports, orphaned_raw_records = await self.identify_orphaned_records(session)
                
                if not orphaned_data_imports and not orphaned_raw_records:
                    self.logger.info("No orphaned records found. Migration not needed.")
                    return True
                
                # Step 2: Get master flows
                master_flows = await self.get_master_flows(session)
                
                if not master_flows:
                    self.logger.error("No master flows found. Cannot proceed with migration.")
                    return False
                
                # Step 3: Create rollback script
                rollback_path = await self.create_rollback_script(session)
                
                # Step 4: Link orphaned data imports
                if orphaned_data_imports:
                    data_import_result = await self.link_orphaned_data_imports(session, orphaned_data_imports, master_flows)
                    self.stats['errors'].extend(data_import_result.errors)
                
                # Step 5: Link orphaned raw records
                if orphaned_raw_records:
                    raw_record_result = await self.link_orphaned_raw_records(session, orphaned_raw_records, master_flows)
                    self.stats['errors'].extend(raw_record_result.errors)
                
                # Final commit
                if not self.dry_run:
                    await session.commit()
                
                self.logger.info("Migration completed successfully!")
                self._print_summary()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Migration failed: {str(e)}")
            return False
    
    def _print_summary(self):
        """Print migration summary."""
        print("\n" + "="*60)
        print("MIGRATION SUMMARY")
        print("="*60)
        print(f"Total orphaned data imports: {self.stats['total_orphaned_data_imports']}")
        print(f"Total orphaned raw records: {self.stats['total_orphaned_raw_records']}")
        print(f"Linked data imports: {self.stats['linked_data_imports']}")
        print(f"Linked raw records: {self.stats['linked_raw_records']}")
        print(f"Failed links: {self.stats['failed_links']}")
        print(f"Errors: {len(self.stats['errors'])}")
        
        if self.stats['errors'] and self.verbose:
            print("\nError Details:")
            for error in self.stats['errors'][:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more errors")
        
        print("="*60)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Fix orphaned data import records')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    migrator = DataImportMigrator(dry_run=args.dry_run, verbose=args.verbose)
    success = await migrator.run_migration()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())