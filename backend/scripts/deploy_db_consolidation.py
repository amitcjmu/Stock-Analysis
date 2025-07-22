#!/usr/bin/env python3
"""
Database Consolidation Deployment Script
Coordinates the deployment of database consolidation changes
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import List, Optional, Tuple

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class DatabaseConsolidationDeployment:
    """Manages the database consolidation deployment process"""
    
    def __init__(self, database_url: str, dry_run: bool = False):
        self.database_url = database_url
        self.dry_run = dry_run
        self.start_time = datetime.now()
        self.steps_completed = []
        self.errors = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log deployment messages"""
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
    
    def backup_database(self) -> bool:
        """Create database backup before migration"""
        backup_file = f"backup_pre_consolidation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        command = [
            "pg_dump",
            self.database_url,
            "-f", backup_file,
            "--verbose",
            "--no-owner",
            "--no-acl"
        ]
        
        return self.run_command(command, f"Database backup to {backup_file}")
    
    def check_current_schema(self) -> bool:
        """Verify current schema state"""
        self.log("Checking current database schema...")
        
        if self.dry_run:
            self.log("DRY RUN: Would check schema state")
            return True
        
        try:
            conn = psycopg2.connect(self.database_url)
            cur = conn.cursor()
            
            # Check for v3_ tables
            cur.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'v3_%'
            """)
            v3_count = cur.fetchone()[0]
            
            if v3_count > 0:
                self.log(f"Found {v3_count} v3_ prefixed tables that need removal")
            
            # Check for deprecated tables
            deprecated_tables = [
                'workflow_states',
                'discovery_assets',
                'mapping_learning_patterns',
                'session_management',
                'discovery_sessions'
            ]
            
            for table in deprecated_tables:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    )
                """, (table,))
                
                if cur.fetchone()[0]:
                    self.log(f"Found deprecated table: {table}")
            
            cur.close()
            conn.close()
            return True
            
        except Exception as e:
            self.log(f"Schema check failed: {str(e)}", "ERROR")
            return False
    
    def run_alembic_migrations(self) -> bool:
        """Run Alembic database migrations"""
        command = ["alembic", "upgrade", "head"]
        return self.run_command(command, "Alembic database migrations")
    
    def verify_schema_changes(self) -> bool:
        """Verify schema changes were applied correctly"""
        self.log("Verifying schema changes...")
        
        if self.dry_run:
            self.log("DRY RUN: Would verify schema changes")
            return True
        
        try:
            conn = psycopg2.connect(self.database_url)
            cur = conn.cursor()
            
            # Verify no v3_ tables exist
            cur.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'v3_%'
            """)
            v3_count = cur.fetchone()[0]
            
            if v3_count > 0:
                self.log(f"ERROR: Still found {v3_count} v3_ tables", "ERROR")
                return False
            
            # Verify field renames
            field_checks = [
                ('data_imports', 'filename'),
                ('data_imports', 'file_size'),
                ('data_imports', 'mime_type'),
                ('discovery_flows', 'flow_state'),
                ('discovery_flows', 'data_validation_completed')
            ]
            
            for table, column in field_checks:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = %s 
                        AND column_name = %s
                    )
                """, (table, column))
                
                if not cur.fetchone()[0]:
                    self.log(f"ERROR: Column {table}.{column} not found", "ERROR")
                    return False
            
            self.log("✓ All schema changes verified successfully")
            cur.close()
            conn.close()
            return True
            
        except Exception as e:
            self.log(f"Schema verification failed: {str(e)}", "ERROR")
            return False
    
    def update_application_code(self) -> bool:
        """Deploy updated application code"""
        # In a real deployment, this would:
        # 1. Pull latest code from git
        # 2. Build Docker images
        # 3. Deploy to staging/production
        
        self.log("Updating application code...")
        
        if self.dry_run:
            self.log("DRY RUN: Would update application code")
            return True
        
        # For now, just restart the services
        commands = [
            (["docker-compose", "build", "backend"], "Build backend image"),
            (["docker-compose", "up", "-d", "backend"], "Restart backend service")
        ]
        
        for command, description in commands:
            if not self.run_command(command, description):
                return False
        
        return True
    
    def run_post_deployment_tests(self) -> bool:
        """Run tests to verify deployment"""
        command = [
            "docker", "exec", "migration_backend",
            "python", "-m", "pytest",
            "tests/integration/test_db_consolidation_v3.py",
            "-v", "--tb=short"
        ]
        
        return self.run_command(command, "Post-deployment integration tests")
    
    def generate_deployment_report(self):
        """Generate deployment summary report"""
        duration = datetime.now() - self.start_time
        
        report = f"""
========================================
Database Consolidation Deployment Report
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
        
        report += f"\nDeployment Status: {'FAILED' if self.errors else 'SUCCESS'}\n"
        
        if self.dry_run:
            report += "\nNOTE: This was a DRY RUN - no changes were actually made\n"
        
        return report
    
    def deploy(self) -> bool:
        """Execute the full deployment process"""
        self.log("Starting database consolidation deployment...")
        
        steps = [
            ("Check database connection", self.check_database_connection),
            ("Backup database", self.backup_database),
            ("Check current schema", self.check_current_schema),
            ("Run Alembic migrations", self.run_alembic_migrations),
            ("Verify schema changes", self.verify_schema_changes),
            ("Update application code", self.update_application_code),
            ("Run post-deployment tests", self.run_post_deployment_tests)
        ]
        
        for step_name, step_func in steps:
            self.log(f"\n{'='*60}")
            self.log(f"Step: {step_name}")
            self.log('='*60)
            
            if not step_func():
                self.log(f"\n✗ Deployment failed at step: {step_name}", "ERROR")
                break
            
            # Add a small delay between steps
            if not self.dry_run:
                time.sleep(2)
        
        # Generate and display report
        report = self.generate_deployment_report()
        print("\n" + report)
        
        # Save report to file
        report_file = f"deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        self.log(f"Deployment report saved to: {report_file}")
        
        return len(self.errors) == 0


def main():
    parser = argparse.ArgumentParser(description='Deploy database consolidation changes')
    parser.add_argument(
        '--database-url',
        default=os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5433/migration_db'),
        help='PostgreSQL database URL'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform a dry run without making actual changes'
    )
    parser.add_argument(
        '--skip-backup',
        action='store_true',
        help='Skip database backup (not recommended)'
    )
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Skip post-deployment tests'
    )
    
    args = parser.parse_args()
    
    # Confirm deployment
    if not args.dry_run:
        print("\n⚠️  WARNING: This will modify the database schema!")
        print("Make sure you have:")
        print("  1. Backed up the database")
        print("  2. Notified the team")
        print("  3. Scheduled a maintenance window")
        print("")
        response = input("Continue with deployment? (yes/no): ")
        
        if response.lower() != 'yes':
            print("Deployment cancelled.")
            sys.exit(0)
    
    # Create deployer instance
    deployer = DatabaseConsolidationDeployment(
        database_url=args.database_url,
        dry_run=args.dry_run
    )
    
    # Modify deployment based on arguments
    if args.skip_backup:
        deployer.backup_database = lambda: True
    
    if args.skip_tests:
        deployer.run_post_deployment_tests = lambda: True
    
    # Run deployment
    success = deployer.deploy()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()