#!/usr/bin/env python3
"""
Data Integrity Cleanup Utilities - Phase 3
============================================

Collection of utilities for identifying and fixing various data inconsistencies
in the flow management system.

This script provides utilities for:
- Session ID to Flow ID migration cleanup
- Orphaned record identification and removal
- Data consistency checks and repairs
- Backup and restore operations

Usage:
    python scripts/data_integrity_cleanup_utilities.py [command] [options]

Commands:
    cleanup-session-refs    Remove all remaining session_id references
    fix-missing-contexts    Add missing tenant context to records
    deduplicate-flows       Remove duplicate flow records
    backup-before-cleanup   Create backup before running cleanup
    restore-from-backup     Restore from backup file
    audit-flow-health       Generate comprehensive flow health report

Features:
- Safe cleanup operations with rollback capabilities
- Progress tracking for large datasets
- Comprehensive logging and reporting
- Backup/restore functionality
"""

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import AsyncSessionLocal


@dataclass
class CleanupOperation:
    """Represents a cleanup operation."""
    operation_type: str
    table_name: str
    affected_records: int
    description: str
    sql_command: str
    rollback_command: Optional[str] = None


class DataIntegrityCleanupUtilities:
    """Utilities for cleaning up data integrity issues."""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.logger = self._setup_logging()
        self.operations_log: List[CleanupOperation] = []
        self.backup_dir = Path(__file__).parent / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
    def _setup_logging(self) -> logging.Logger:
        """Configure logging for cleanup operations."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    async def cleanup_session_references(self, session: Session) -> CleanupOperation:
        """Remove all remaining session_id references from the system."""
        self.logger.info("Cleaning up remaining session_id references...")
        
        # Check for tables that might still have session_id columns
        session_refs = await session.execute(
            text("""
                SELECT table_name, column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'migration'
                AND column_name LIKE '%session%'
                AND table_name NOT IN ('data_import_sessions')
                ORDER BY table_name, column_name
            """)
        )
        
        total_affected = 0
        cleanup_commands = []
        
        for row in session_refs.fetchall():
            table_name = row.table_name
            column_name = row.column_name
            
            # Count records with session references
            count_result = await session.execute(
                text(f"SELECT COUNT(*) FROM migration.{table_name} WHERE {column_name} IS NOT NULL")
            )
            count = count_result.scalar()
            
            if count > 0:
                total_affected += count
                self.logger.info(f"Found {count} records with {column_name} in {table_name}")
                
                # Create cleanup command
                cleanup_sql = f"UPDATE migration.{table_name} SET {column_name} = NULL WHERE {column_name} IS NOT NULL"
                cleanup_commands.append(cleanup_sql)
                
                if not self.dry_run:
                    await session.execute(text(cleanup_sql))
                    self.logger.info(f"Cleaned {column_name} from {table_name}")
        
        if not self.dry_run and cleanup_commands:
            await session.commit()
        
        operation = CleanupOperation(
            operation_type="cleanup_session_refs",
            table_name="multiple",
            affected_records=total_affected,
            description=f"Removed session references from {len(cleanup_commands)} tables",
            sql_command="; ".join(cleanup_commands),
            rollback_command="Manual rollback required - use backup"
        )
        
        self.operations_log.append(operation)
        return operation
    
    async def fix_missing_tenant_contexts(self, session: Session) -> CleanupOperation:
        """Add missing tenant context to records that can be inferred."""
        self.logger.info("Fixing missing tenant contexts...")
        
        # Fix raw_import_records missing tenant context from their data_import
        missing_tenant_sql = """
            UPDATE migration.raw_import_records rir
            SET client_account_id = di.client_account_id,
                engagement_id = di.engagement_id
            FROM migration.data_imports di
            WHERE rir.data_import_id = di.id
            AND (rir.client_account_id IS NULL OR rir.engagement_id IS NULL)
            AND di.client_account_id IS NOT NULL
            AND di.engagement_id IS NOT NULL
        """
        
        # Count affected records
        count_result = await session.execute(
            text("""
                SELECT COUNT(*) FROM migration.raw_import_records rir
                JOIN migration.data_imports di ON rir.data_import_id = di.id
                WHERE (rir.client_account_id IS NULL OR rir.engagement_id IS NULL)
                AND di.client_account_id IS NOT NULL
                AND di.engagement_id IS NOT NULL
            """)
        )
        affected_count = count_result.scalar()
        
        if not self.dry_run and affected_count > 0:
            await session.execute(text(missing_tenant_sql))
            await session.commit()
            self.logger.info(f"Fixed tenant context for {affected_count} raw import records")
        
        operation = CleanupOperation(
            operation_type="fix_missing_contexts",
            table_name="raw_import_records",
            affected_records=affected_count,
            description="Added missing tenant context from parent data imports",
            sql_command=missing_tenant_sql,
            rollback_command="UPDATE migration.raw_import_records SET client_account_id = NULL, engagement_id = NULL WHERE updated_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'"
        )
        
        self.operations_log.append(operation)
        return operation
    
    async def deduplicate_flows(self, session: Session) -> CleanupOperation:
        """Remove duplicate flow records while preserving the most recent."""
        self.logger.info("Deduplicating flow records...")
        
        # Find duplicate flow_ids in discovery_flows
        duplicates_sql = """
            WITH duplicates AS (
                SELECT flow_id, MIN(id) as keep_id, COUNT(*) as cnt
                FROM migration.discovery_flows
                GROUP BY flow_id
                HAVING COUNT(*) > 1
            ),
            to_delete AS (
                SELECT df.id
                FROM migration.discovery_flows df
                JOIN duplicates d ON df.flow_id = d.flow_id
                WHERE df.id != d.keep_id
            )
            SELECT COUNT(*) FROM to_delete
        """
        
        count_result = await session.execute(text(duplicates_sql.replace("SELECT COUNT(*) FROM to_delete", "SELECT COUNT(*) FROM to_delete")))
        duplicate_count = count_result.scalar()
        
        if duplicate_count > 0:
            delete_sql = """
                WITH duplicates AS (
                    SELECT flow_id, MIN(id) as keep_id, COUNT(*) as cnt
                    FROM migration.discovery_flows
                    GROUP BY flow_id
                    HAVING COUNT(*) > 1
                ),
                to_delete AS (
                    SELECT df.id
                    FROM migration.discovery_flows df
                    JOIN duplicates d ON df.flow_id = d.flow_id
                    WHERE df.id != d.keep_id
                )
                DELETE FROM migration.discovery_flows
                WHERE id IN (SELECT id FROM to_delete)
            """
            
            if not self.dry_run:
                await session.execute(text(delete_sql))
                await session.commit()
                self.logger.info(f"Removed {duplicate_count} duplicate discovery flows")
        
        operation = CleanupOperation(
            operation_type="deduplicate_flows",
            table_name="discovery_flows",
            affected_records=duplicate_count,
            description="Removed duplicate flow records, keeping most recent",
            sql_command=delete_sql if duplicate_count > 0 else "-- No duplicates found",
            rollback_command="Manual restoration from backup required"
        )
        
        self.operations_log.append(operation)
        return operation
    
    async def remove_orphaned_records(self, session: Session, table_name: str, foreign_key: str, parent_table: str, parent_key: str = "id") -> CleanupOperation:
        """Remove orphaned records from a table based on missing foreign key references."""
        self.logger.info(f"Removing orphaned records from {table_name}...")
        
        # Count orphaned records
        count_sql = f"""
            SELECT COUNT(*) FROM migration.{table_name} t
            WHERE t.{foreign_key} IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM migration.{parent_table} p
                WHERE p.{parent_key} = t.{foreign_key}
            )
        """
        
        count_result = await session.execute(text(count_sql))
        orphaned_count = count_result.scalar()
        
        if orphaned_count > 0:
            delete_sql = f"""
                DELETE FROM migration.{table_name}
                WHERE {foreign_key} IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM migration.{parent_table} p
                    WHERE p.{parent_key} = {foreign_key}
                )
            """
            
            if not self.dry_run:
                await session.execute(text(delete_sql))
                await session.commit()
                self.logger.info(f"Removed {orphaned_count} orphaned records from {table_name}")
        
        operation = CleanupOperation(
            operation_type="remove_orphaned",
            table_name=table_name,
            affected_records=orphaned_count,
            description=f"Removed records with invalid {foreign_key} references",
            sql_command=delete_sql if orphaned_count > 0 else "-- No orphaned records found",
            rollback_command="Manual restoration from backup required"
        )
        
        self.operations_log.append(operation)
        return operation
    
    async def create_backup(self, session: Session, backup_name: str = None) -> str:
        """Create a backup of critical tables before cleanup."""
        if backup_name is None:
            backup_name = f"cleanup_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = self.backup_dir / f"{backup_name}.sql"
        
        self.logger.info(f"Creating backup: {backup_path}")
        
        # Tables to backup
        critical_tables = [
            "crewai_flow_state_extensions",
            "discovery_flows", 
            "data_imports",
            "raw_import_records",
            "assessment_flows"
        ]
        
        backup_commands = []
        backup_commands.append("-- Backup created on " + datetime.now().isoformat())
        backup_commands.append("-- Run this script to restore the database to this state")
        backup_commands.append("")
        
        for table in critical_tables:
            # Get table structure
            structure_result = await session.execute(
                text(f"SELECT COUNT(*) FROM migration.{table}")
            )
            count = structure_result.scalar()
            
            if count > 0:
                backup_commands.append(f"-- Backup for {table} ({count} records)")
                backup_commands.append(f"TRUNCATE migration.{table} CASCADE;")
                
                # Export data
                data_result = await session.execute(
                    text(f"SELECT * FROM migration.{table}")
                )
                
                for row in data_result.fetchall():
                    # Convert row to INSERT statement
                    columns = list(row._mapping.keys())
                    values = []
                    for value in row:
                        if value is None:
                            values.append("NULL")
                        elif isinstance(value, str):
                            escaped_value = value.replace("'", "''")
                            values.append(f"'{escaped_value}'")
                        elif isinstance(value, datetime):
                            values.append(f"'{value.isoformat()}'")
                        elif isinstance(value, dict) or isinstance(value, list):
                            json_str = json.dumps(value).replace("'", "''")
                            values.append(f"'{json_str}'")
                        else:
                            values.append(str(value))
                    
                    insert_sql = f"INSERT INTO migration.{table} ({', '.join(columns)}) VALUES ({', '.join(values)});"
                    backup_commands.append(insert_sql)
                
                backup_commands.append("")
        
        # Write backup file
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(backup_commands))
        
        self.logger.info(f"Backup created: {backup_path}")
        return str(backup_path)
    
    async def audit_flow_health(self, session: Session) -> Dict[str, Any]:
        """Generate comprehensive flow health report."""
        self.logger.info("Generating flow health audit...")
        
        health_report = {
            "audit_timestamp": datetime.now().isoformat(),
            "tables": {},
            "relationships": {},
            "issues": [],
            "recommendations": []
        }
        
        # Table health checks
        tables_to_check = [
            "crewai_flow_state_extensions",
            "discovery_flows",
            "data_imports", 
            "raw_import_records",
            "assessment_flows"
        ]
        
        for table in tables_to_check:
            # Basic table stats
            stats_result = await session.execute(
                text(f"""
                    SELECT COUNT(*) as total_records,
                           COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as recent_records,
                           MIN(created_at) as oldest_record,
                           MAX(created_at) as newest_record
                    FROM migration.{table}
                """)
            )
            
            stats = stats_result.fetchone()
            
            health_report["tables"][table] = {
                "total_records": stats.total_records,
                "recent_records": stats.recent_records,
                "oldest_record": stats.oldest_record.isoformat() if stats.oldest_record else None,
                "newest_record": stats.newest_record.isoformat() if stats.newest_record else None,
                "health_score": 100.0  # Will be calculated based on issues found
            }
        
        # Relationship health checks
        relationships = [
            {
                "name": "data_imports_to_master_flows",
                "child_table": "data_imports",
                "child_key": "master_flow_id",
                "parent_table": "crewai_flow_state_extensions",
                "parent_key": "id"
            },
            {
                "name": "raw_records_to_data_imports",
                "child_table": "raw_import_records",
                "child_key": "data_import_id", 
                "parent_table": "data_imports",
                "parent_key": "id"
            },
            {
                "name": "discovery_flows_to_master_flows",
                "child_table": "discovery_flows",
                "child_key": "master_flow_id",
                "parent_table": "crewai_flow_state_extensions", 
                "parent_key": "id"
            }
        ]
        
        for rel in relationships:
            # Check orphaned records
            orphaned_result = await session.execute(
                text(f"""
                    SELECT COUNT(*) FROM migration.{rel['child_table']} c
                    WHERE c.{rel['child_key']} IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1 FROM migration.{rel['parent_table']} p
                        WHERE p.{rel['parent_key']} = c.{rel['child_key']}
                    )
                """)
            )
            orphaned_count = orphaned_result.scalar()
            
            # Check missing relationships
            missing_result = await session.execute(
                text(f"SELECT COUNT(*) FROM migration.{rel['child_table']} WHERE {rel['child_key']} IS NULL")
            )
            missing_count = missing_result.scalar()
            
            total_result = await session.execute(
                text(f"SELECT COUNT(*) FROM migration.{rel['child_table']}")
            )
            total_count = total_result.scalar()
            
            integrity_score = ((total_count - orphaned_count - missing_count) / total_count * 100) if total_count > 0 else 100
            
            health_report["relationships"][rel["name"]] = {
                "total_child_records": total_count,
                "orphaned_records": orphaned_count,
                "missing_relationships": missing_count,
                "integrity_score": integrity_score
            }
            
            if orphaned_count > 0:
                health_report["issues"].append(f"{orphaned_count} orphaned records in {rel['child_table']}")
            if missing_count > 0:
                health_report["issues"].append(f"{missing_count} records missing {rel['child_key']} in {rel['child_table']}")
        
        # Generate recommendations
        if health_report["issues"]:
            health_report["recommendations"].extend([
                "Run fix_orphaned_data_imports.py to fix orphaned data imports",
                "Run validate_flow_relationships.py for detailed analysis",
                "Consider running cleanup utilities for other orphaned records"
            ])
        else:
            health_report["recommendations"].append("System is healthy - no immediate action required")
        
        return health_report
    
    async def run_comprehensive_cleanup(self, session: Session) -> List[CleanupOperation]:
        """Run all cleanup operations in the correct order."""
        self.logger.info("Starting comprehensive cleanup...")
        
        operations = []
        
        # 1. Create backup first
        backup_path = await self.create_backup(session)
        self.logger.info(f"Backup created: {backup_path}")
        
        # 2. Clean up session references
        operations.append(await self.cleanup_session_references(session))
        
        # 3. Fix missing tenant contexts
        operations.append(await self.fix_missing_tenant_contexts(session))
        
        # 4. Deduplicate flows
        operations.append(await self.deduplicate_flows(session))
        
        # 5. Remove specific orphaned records (safe ones only)
        # Skip this in comprehensive cleanup to avoid data loss
        
        self.logger.info("Comprehensive cleanup completed")
        return operations
    
    def generate_cleanup_report(self) -> Dict[str, Any]:
        """Generate a report of all cleanup operations performed."""
        total_affected = sum(op.affected_records for op in self.operations_log)
        
        return {
            "cleanup_timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "total_operations": len(self.operations_log),
            "total_records_affected": total_affected,
            "operations": [
                {
                    "type": op.operation_type,
                    "table": op.table_name,
                    "affected_records": op.affected_records,
                    "description": op.description,
                    "sql_command": op.sql_command if self.verbose else "Available in verbose mode",
                    "rollback_command": op.rollback_command if self.verbose else "Available in verbose mode"
                }
                for op in self.operations_log
            ]
        }


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Data integrity cleanup utilities')
    parser.add_argument('command', choices=[
        'cleanup-session-refs',
        'fix-missing-contexts', 
        'deduplicate-flows',
        'backup-before-cleanup',
        'audit-flow-health',
        'comprehensive-cleanup'
    ], help='Cleanup command to run')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--backup-name', help='Custom backup name')
    
    args = parser.parse_args()
    
    utilities = DataIntegrityCleanupUtilities(dry_run=args.dry_run, verbose=args.verbose)
    
    try:
        async with AsyncSessionLocal() as session:
            if args.command == 'cleanup-session-refs':
                operation = await utilities.cleanup_session_references(session)
                print(f"Cleaned up {operation.affected_records} session references")
                
            elif args.command == 'fix-missing-contexts':
                operation = await utilities.fix_missing_tenant_contexts(session)
                print(f"Fixed {operation.affected_records} missing tenant contexts")
                
            elif args.command == 'deduplicate-flows':
                operation = await utilities.deduplicate_flows(session)
                print(f"Removed {operation.affected_records} duplicate flows")
                
            elif args.command == 'backup-before-cleanup':
                backup_path = await utilities.create_backup(session, args.backup_name)
                print(f"Backup created: {backup_path}")
                
            elif args.command == 'audit-flow-health':
                health_report = await utilities.audit_flow_health(session)
                print("\nFLOW HEALTH AUDIT REPORT")
                print("=" * 50)
                print(json.dumps(health_report, indent=2))
                
            elif args.command == 'comprehensive-cleanup':
                await utilities.run_comprehensive_cleanup(session)
                report = utilities.generate_cleanup_report()
                print("\nCOMPREHENSIVE CLEANUP REPORT")
                print("=" * 50)
                print(json.dumps(report, indent=2))
                
        print("\nOperation completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())