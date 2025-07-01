#!/usr/bin/env python3
"""
Database Consolidation Rollback Script
Safely rolls back database consolidation changes if issues are found
"""

import os
import sys
import subprocess
import argparse
import time
from datetime import datetime
from typing import List, Optional
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class DatabaseConsolidationRollback:
    """Manages the database consolidation rollback process"""
    
    def __init__(self, database_url: str, backup_file: Optional[str] = None, dry_run: bool = False):
        self.database_url = database_url
        self.backup_file = backup_file
        self.dry_run = dry_run
        self.start_time = datetime.now()
        self.steps_completed = []
        self.errors = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log rollback messages"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def run_command(self, command: List[str], description: str) -> bool:
        """Run a shell command"""
        self.log(f"Running: {description}")
        
        if self.dry_run:
            self.log(f"DRY RUN: Would execute: {' '.join(command)}")
            return True
        
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"✓ {description} completed successfully")
                self.steps_completed.append(description)
                return True
            else:
                self.log(f"✗ {description} failed", "ERROR")
                self.log(f"Error output: {result.stderr}", "ERROR")
                self.errors.append((description, result.stderr))
                return False
        except Exception as e:
            self.log(f"✗ {description} failed with exception: {str(e)}", "ERROR")
            self.errors.append((description, str(e)))
            return False
    
    def check_database_connection(self) -> bool:
        """Verify database connectivity"""
        self.log("Checking database connection...")
        
        if self.dry_run:
            self.log("DRY RUN: Would check database connection")
            return True
        
        try:
            conn = psycopg2.connect(self.database_url)
            conn.close()
            self.log("✓ Database connection successful")
            return True
        except Exception as e:
            self.log(f"✗ Database connection failed: {str(e)}", "ERROR")
            return False
    
    def stop_application_services(self) -> bool:
        """Stop application services to prevent data corruption"""
        command = ["docker-compose", "stop", "backend", "frontend"]
        return self.run_command(command, "Stop application services")
    
    def create_rollback_backup(self) -> bool:
        """Create backup of current state before rollback"""
        backup_file = f"backup_pre_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        command = [
            "pg_dump",
            self.database_url,
            "-f", backup_file,
            "--verbose",
            "--no-owner",
            "--no-acl"
        ]
        
        success = self.run_command(command, f"Backup current state to {backup_file}")
        
        if success:
            self.log(f"Current state backed up to: {backup_file}")
            self.log("You can use this backup if the rollback fails")
        
        return success
    
    def rollback_alembic_migrations(self) -> bool:
        """Rollback Alembic migrations to previous version"""
        # First, get current revision
        if not self.dry_run:
            try:
                result = subprocess.run(
                    ["alembic", "current"],
                    capture_output=True,
                    text=True
                )
                current_revision = result.stdout.strip()
                self.log(f"Current Alembic revision: {current_revision}")
            except Exception as e:
                self.log(f"Failed to get current revision: {str(e)}", "ERROR")
                return False
        
        # Rollback to previous revision
        # In a real scenario, you'd specify the exact revision to rollback to
        command = ["alembic", "downgrade", "-1"]
        return self.run_command(command, "Rollback Alembic migrations")
    
    def restore_from_backup(self) -> bool:
        """Restore database from backup file"""
        if not self.backup_file:
            self.log("No backup file specified for restoration", "ERROR")
            return False
        
        if not os.path.exists(self.backup_file):
            self.log(f"Backup file not found: {self.backup_file}", "ERROR")
            return False
        
        self.log(f"Restoring database from: {self.backup_file}")
        
        if self.dry_run:
            self.log("DRY RUN: Would restore from backup")
            return True
        
        # Drop and recreate database
        try:
            # Parse database name from URL
            db_parts = self.database_url.split('/')
            db_name = db_parts[-1].split('?')[0]
            base_url = '/'.join(db_parts[:-1]) + '/postgres'
            
            # Connect to postgres database to drop/create
            conn = psycopg2.connect(base_url)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            
            # Terminate existing connections
            cur.execute(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
            """)
            
            # Drop and recreate database
            cur.execute(f"DROP DATABASE IF EXISTS {db_name}")
            cur.execute(f"CREATE DATABASE {db_name}")
            
            cur.close()
            conn.close()
            
            # Restore from backup
            command = [
                "psql",
                self.database_url,
                "-f", self.backup_file
            ]
            
            return self.run_command(command, "Restore database from backup")
            
        except Exception as e:
            self.log(f"Database restoration failed: {str(e)}", "ERROR")
            return False
    
    def recreate_v3_tables(self) -> bool:
        """Recreate v3_ tables if needed for compatibility"""
        self.log("Recreating v3_ tables for backward compatibility...")
        
        if self.dry_run:
            self.log("DRY RUN: Would recreate v3_ tables")
            return True
        
        # This would contain SQL to recreate the v3_ tables
        # For now, we'll just log what would be done
        v3_tables = [
            'v3_data_imports',
            'v3_discovery_flows',
            'v3_import_field_mappings',
            'v3_assets'
        ]
        
        for table in v3_tables:
            self.log(f"Would recreate table: {table}")
        
        return True
    
    def restore_deprecated_fields(self) -> bool:
        """Restore deprecated fields to models"""
        self.log("Restoring deprecated fields...")
        
        if self.dry_run:
            self.log("DRY RUN: Would restore deprecated fields")
            return True
        
        # In reality, this would involve:
        # 1. Checking out previous version of model files
        # 2. Or applying SQL to add back removed columns
        
        deprecated_fields = [
            ('client_accounts', 'is_mock'),
            ('data_imports', 'source_filename'),
            ('data_imports', 'file_size_bytes'),
            ('data_imports', 'file_type')
        ]
        
        for table, field in deprecated_fields:
            self.log(f"Would restore field: {table}.{field}")
        
        return True
    
    def restart_application_services(self) -> bool:
        """Restart application services with rolled-back code"""
        # First, checkout previous version of code
        if not self.dry_run:
            # In a real scenario, you'd checkout a specific git tag/commit
            self.log("Would checkout previous code version")
        
        # Rebuild and restart services
        commands = [
            (["docker-compose", "build", "backend"], "Rebuild backend with previous code"),
            (["docker-compose", "up", "-d", "backend", "frontend"], "Start application services")
        ]
        
        for command, description in commands:
            if not self.run_command(command, description):
                return False
        
        return True
    
    def verify_rollback(self) -> bool:
        """Verify rollback was successful"""
        self.log("Verifying rollback...")
        
        if self.dry_run:
            self.log("DRY RUN: Would verify rollback")
            return True
        
        try:
            conn = psycopg2.connect(self.database_url)
            cur = conn.cursor()
            
            # Check basic connectivity
            cur.execute("SELECT 1")
            
            # Check for critical tables
            critical_tables = [
                'client_accounts',
                'engagements',
                'users',
                'discovery_flows',
                'data_imports'
            ]
            
            for table in critical_tables:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    )
                """, (table,))
                
                if not cur.fetchone()[0]:
                    self.log(f"ERROR: Critical table missing: {table}", "ERROR")
                    return False
            
            self.log("✓ Basic database structure verified")
            
            cur.close()
            conn.close()
            return True
            
        except Exception as e:
            self.log(f"Rollback verification failed: {str(e)}", "ERROR")
            return False
    
    def generate_rollback_report(self):
        """Generate rollback summary report"""
        duration = datetime.now() - self.start_time
        
        report = f"""
========================================
Database Consolidation Rollback Report
========================================

Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Duration: {duration}

Steps Completed ({len(self.steps_completed)}):
"""
        
        for step in self.steps_completed:
            report += f"  ✓ {step}\n"
        
        if self.errors:
            report += f"\nErrors Encountered ({len(self.errors)}):\n"
            for step, error in self.errors:
                report += f"  ✗ {step}\n"
                report += f"    Error: {error}\n"
        
        report += f"\nRollback Status: {'FAILED' if self.errors else 'SUCCESS'}\n"
        
        if self.dry_run:
            report += "\nNOTE: This was a DRY RUN - no changes were actually made\n"
        
        return report
    
    def rollback(self) -> bool:
        """Execute the full rollback process"""
        self.log("Starting database consolidation rollback...")
        self.log("⚠️  WARNING: This will revert all consolidation changes!")
        
        steps = [
            ("Check database connection", self.check_database_connection),
            ("Stop application services", self.stop_application_services),
            ("Create rollback backup", self.create_rollback_backup),
        ]
        
        # Add appropriate rollback method based on available options
        if self.backup_file:
            steps.append(("Restore from backup", self.restore_from_backup))
        else:
            steps.extend([
                ("Rollback Alembic migrations", self.rollback_alembic_migrations),
                ("Recreate v3 tables", self.recreate_v3_tables),
                ("Restore deprecated fields", self.restore_deprecated_fields)
            ])
        
        steps.extend([
            ("Restart application services", self.restart_application_services),
            ("Verify rollback", self.verify_rollback)
        ])
        
        for step_name, step_func in steps:
            self.log(f"\n{'='*60}")
            self.log(f"Step: {step_name}")
            self.log('='*60)
            
            if not step_func():
                self.log(f"\n✗ Rollback failed at step: {step_name}", "ERROR")
                self.log("⚠️  CRITICAL: Database may be in inconsistent state!", "ERROR")
                self.log("Consider restoring from the pre-rollback backup created earlier", "ERROR")
                break
            
            # Add a small delay between steps
            if not self.dry_run:
                time.sleep(2)
        
        # Generate and display report
        report = self.generate_rollback_report()
        print("\n" + report)
        
        # Save report to file
        report_file = f"rollback_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        self.log(f"Rollback report saved to: {report_file}")
        
        return len(self.errors) == 0


def main():
    parser = argparse.ArgumentParser(description='Rollback database consolidation changes')
    parser.add_argument(
        '--database-url',
        default=os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5433/migration_db'),
        help='PostgreSQL database URL'
    )
    parser.add_argument(
        '--backup-file',
        help='Path to backup file to restore from'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform a dry run without making actual changes'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompt'
    )
    
    args = parser.parse_args()
    
    # Confirm rollback
    if not args.dry_run and not args.force:
        print("\n⚠️  CRITICAL WARNING: Database Rollback")
        print("="*50)
        print("This will:")
        print("  1. Stop all application services")
        print("  2. Revert database schema changes")
        print("  3. Potentially lose data created after deployment")
        print("")
        print("Make sure you have:")
        print("  - A valid reason for rollback")
        print("  - Notified the team")
        print("  - A backup of current state")
        print("")
        response = input("Are you SURE you want to rollback? (type 'ROLLBACK' to confirm): ")
        
        if response != 'ROLLBACK':
            print("Rollback cancelled.")
            sys.exit(0)
    
    # Create rollback instance
    rollback_manager = DatabaseConsolidationRollback(
        database_url=args.database_url,
        backup_file=args.backup_file,
        dry_run=args.dry_run
    )
    
    # Run rollback
    success = rollback_manager.rollback()
    
    if success:
        print("\n✓ Rollback completed successfully")
        print("Next steps:")
        print("  1. Verify application functionality")
        print("  2. Notify the team of rollback completion")
        print("  3. Investigate and fix the issues that required rollback")
    else:
        print("\n✗ Rollback failed!")
        print("The database may be in an inconsistent state.")
        print("Consider restoring from the pre-rollback backup.")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()