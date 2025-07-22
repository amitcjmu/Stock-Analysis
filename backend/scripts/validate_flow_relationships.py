#!/usr/bin/env python3
"""
Comprehensive Data Integrity Validation Script - Phase 3
=========================================================

Validates all foreign key relationships and identifies orphaned records across
all flow-related tables in the system.

This script provides comprehensive validation of:
- Master flow relationships
- Data import linkages
- Discovery flow linkages
- Raw import record linkages
- Cross-table referential integrity

Usage:
    python scripts/validate_flow_relationships.py [--verbose] [--export-csv]

Features:
- Comprehensive validation across all flow tables
- Detailed reporting of orphaned records
- CSV export capabilities
- Performance metrics tracking
- Health score calculation
"""

import argparse
import asyncio
import csv
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.database import AsyncSessionLocal


class ValidationResult(NamedTuple):
    """Result of a validation check."""
    table_name: str
    check_name: str
    total_records: int
    valid_records: int
    invalid_records: int
    orphaned_records: int
    health_score: float
    details: Dict[str, Any]


@dataclass
class OrphanedRecord:
    """Represents an orphaned record."""
    table_name: str
    record_id: str
    foreign_key_field: str
    foreign_key_value: Optional[str]
    client_account_id: str
    engagement_id: str
    created_at: datetime
    additional_info: Dict[str, Any]


class FlowRelationshipValidator:
    """Validates all flow-related table relationships."""
    
    def __init__(self, verbose: bool = False, export_csv: bool = False):
        self.verbose = verbose
        self.export_csv = export_csv
        self.logger = self._setup_logging()
        self.validation_results: List[ValidationResult] = []
        self.orphaned_records: List[OrphanedRecord] = []
        self.start_time = datetime.now()
        
    def _setup_logging(self) -> logging.Logger:
        """Configure logging for validation."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    async def validate_master_flow_integrity(self, session: Session) -> ValidationResult:
        """Validate CrewAI Flow State Extensions integrity."""
        self.logger.info("Validating master flow integrity...")
        
        # Count total master flows
        total_result = await session.execute(
            text("SELECT COUNT(*) FROM migration.crewai_flow_state_extensions")
        )
        total_count = total_result.scalar()
        
        # Check for NULL required fields
        null_checks = await session.execute(
            text("""
                SELECT COUNT(*) FROM migration.crewai_flow_state_extensions
                WHERE flow_id IS NULL 
                   OR client_account_id IS NULL 
                   OR engagement_id IS NULL
                   OR flow_type IS NULL
            """)
        )
        invalid_count = null_checks.scalar()
        
        # Check for duplicate flow_ids
        duplicate_check = await session.execute(
            text("""
                SELECT COUNT(*) FROM (
                    SELECT flow_id, COUNT(*) as cnt
                    FROM migration.crewai_flow_state_extensions
                    GROUP BY flow_id
                    HAVING COUNT(*) > 1
                ) duplicates
            """)
        )
        duplicate_count = duplicate_check.scalar()
        
        # Check for valid flow types
        invalid_flow_types = await session.execute(
            text("""
                SELECT COUNT(*) FROM migration.crewai_flow_state_extensions
                WHERE flow_type NOT IN ('discovery', 'assessment', 'planning', 'execution', 'modernize', 'finops', 'observability', 'decommission')
            """)
        )
        invalid_type_count = invalid_flow_types.scalar()
        
        # Check parent-child relationships
        orphaned_children = await session.execute(
            text("""
                SELECT COUNT(*) FROM migration.crewai_flow_state_extensions c1
                WHERE c1.parent_flow_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM migration.crewai_flow_state_extensions c2
                    WHERE c2.flow_id = c1.parent_flow_id
                )
            """)
        )
        orphaned_child_count = orphaned_children.scalar()
        
        total_issues = invalid_count + duplicate_count + invalid_type_count + orphaned_child_count
        valid_count = total_count - total_issues
        health_score = (valid_count / total_count * 100) if total_count > 0 else 0
        
        return ValidationResult(
            table_name="crewai_flow_state_extensions",
            check_name="Master Flow Integrity",
            total_records=total_count,
            valid_records=valid_count,
            invalid_records=total_issues,
            orphaned_records=orphaned_child_count,
            health_score=health_score,
            details={
                "null_required_fields": invalid_count,
                "duplicate_flow_ids": duplicate_count,
                "invalid_flow_types": invalid_type_count,
                "orphaned_children": orphaned_child_count
            }
        )
    
    async def validate_data_import_linkages(self, session: Session) -> ValidationResult:
        """Validate DataImport table linkages."""
        self.logger.info("Validating data import linkages...")
        
        # Count total data imports
        total_result = await session.execute(
            text("SELECT COUNT(*) FROM migration.data_imports")
        )
        total_count = total_result.scalar()
        
        # Check for orphaned master_flow_id references
        orphaned_master_flow = await session.execute(
            text("""
                SELECT COUNT(*) FROM migration.data_imports di
                WHERE di.master_flow_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM migration.crewai_flow_state_extensions cfse
                    WHERE cfse.id = di.master_flow_id
                )
            """)
        )
        orphaned_master_count = orphaned_master_flow.scalar()
        
        # Check for missing master_flow_id
        missing_master_flow = await session.execute(
            text("SELECT COUNT(*) FROM migration.data_imports WHERE master_flow_id IS NULL")
        )
        missing_master_count = missing_master_flow.scalar()
        
        # Check for orphaned client_account_id references
        orphaned_client = await session.execute(
            text("""
                SELECT COUNT(*) FROM migration.data_imports di
                WHERE di.client_account_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM migration.client_accounts ca
                    WHERE ca.id = di.client_account_id
                )
            """)
        )
        orphaned_client_count = orphaned_client.scalar()
        
        # Check for orphaned engagement_id references
        orphaned_engagement = await session.execute(
            text("""
                SELECT COUNT(*) FROM migration.data_imports di
                WHERE di.engagement_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM migration.engagements e
                    WHERE e.id = di.engagement_id
                )
            """)
        )
        orphaned_engagement_count = orphaned_engagement.scalar()
        
        # Find specific orphaned records for detailed reporting
        if missing_master_count > 0:
            orphaned_details = await session.execute(
                text("""
                    SELECT id, client_account_id, engagement_id, import_name, created_at
                    FROM migration.data_imports
                    WHERE master_flow_id IS NULL
                    ORDER BY created_at DESC
                    LIMIT 10
                """)
            )
            
            for row in orphaned_details.fetchall():
                self.orphaned_records.append(OrphanedRecord(
                    table_name="data_imports",
                    record_id=str(row.id),
                    foreign_key_field="master_flow_id",
                    foreign_key_value=None,
                    client_account_id=str(row.client_account_id),
                    engagement_id=str(row.engagement_id),
                    created_at=row.created_at,
                    additional_info={"import_name": row.import_name}
                ))
        
        total_issues = orphaned_master_count + missing_master_count + orphaned_client_count + orphaned_engagement_count
        valid_count = total_count - total_issues
        health_score = (valid_count / total_count * 100) if total_count > 0 else 0
        
        return ValidationResult(
            table_name="data_imports",
            check_name="Data Import Linkages",
            total_records=total_count,
            valid_records=valid_count,
            invalid_records=total_issues,
            orphaned_records=missing_master_count,
            health_score=health_score,
            details={
                "orphaned_master_flow_refs": orphaned_master_count,
                "missing_master_flow_id": missing_master_count,
                "orphaned_client_refs": orphaned_client_count,
                "orphaned_engagement_refs": orphaned_engagement_count
            }
        )
    
    async def validate_raw_import_record_linkages(self, session: Session) -> ValidationResult:
        """Validate RawImportRecord table linkages."""
        self.logger.info("Validating raw import record linkages...")
        
        # Count total raw import records
        total_result = await session.execute(
            text("SELECT COUNT(*) FROM migration.raw_import_records")
        )
        total_count = total_result.scalar()
        
        # Check for orphaned data_import_id references
        orphaned_data_import = await session.execute(
            text("""
                SELECT COUNT(*) FROM migration.raw_import_records rir
                WHERE rir.data_import_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM migration.data_imports di
                    WHERE di.id = rir.data_import_id
                )
            """)
        )
        orphaned_data_import_count = orphaned_data_import.scalar()
        
        # Check for missing master_flow_id
        missing_master_flow = await session.execute(
            text("SELECT COUNT(*) FROM migration.raw_import_records WHERE master_flow_id IS NULL")
        )
        missing_master_count = missing_master_flow.scalar()
        
        # Check for orphaned master_flow_id references
        orphaned_master_flow = await session.execute(
            text("""
                SELECT COUNT(*) FROM migration.raw_import_records rir
                WHERE rir.master_flow_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM migration.crewai_flow_state_extensions cfse
                    WHERE cfse.id = rir.master_flow_id
                )
            """)
        )
        orphaned_master_count = orphaned_master_flow.scalar()
        
        # Check for orphaned asset_id references
        orphaned_asset = await session.execute(
            text("""
                SELECT COUNT(*) FROM migration.raw_import_records rir
                WHERE rir.asset_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM migration.assets a
                    WHERE a.id = rir.asset_id
                )
            """)
        )
        orphaned_asset_count = orphaned_asset.scalar()
        
        # Get sample orphaned records
        if missing_master_count > 0:
            orphaned_details = await session.execute(
                text("""
                    SELECT id, data_import_id, client_account_id, engagement_id, created_at
                    FROM migration.raw_import_records
                    WHERE master_flow_id IS NULL
                    ORDER BY created_at DESC
                    LIMIT 5
                """)
            )
            
            for row in orphaned_details.fetchall():
                self.orphaned_records.append(OrphanedRecord(
                    table_name="raw_import_records",
                    record_id=str(row.id),
                    foreign_key_field="master_flow_id",
                    foreign_key_value=None,
                    client_account_id=str(row.client_account_id) if row.client_account_id else "N/A",
                    engagement_id=str(row.engagement_id) if row.engagement_id else "N/A",
                    created_at=row.created_at,
                    additional_info={"data_import_id": str(row.data_import_id)}
                ))
        
        total_issues = orphaned_data_import_count + missing_master_count + orphaned_master_count + orphaned_asset_count
        valid_count = total_count - total_issues
        health_score = (valid_count / total_count * 100) if total_count > 0 else 0
        
        return ValidationResult(
            table_name="raw_import_records",
            check_name="Raw Import Record Linkages",
            total_records=total_count,
            valid_records=valid_count,
            invalid_records=total_issues,
            orphaned_records=missing_master_count,
            health_score=health_score,
            details={
                "orphaned_data_import_refs": orphaned_data_import_count,
                "missing_master_flow_id": missing_master_count,
                "orphaned_master_flow_refs": orphaned_master_count,
                "orphaned_asset_refs": orphaned_asset_count
            }
        )
    
    async def validate_discovery_flow_linkages(self, session: Session) -> ValidationResult:
        """Validate DiscoveryFlow table linkages."""
        self.logger.info("Validating discovery flow linkages...")
        
        # Count total discovery flows
        total_result = await session.execute(
            text("SELECT COUNT(*) FROM migration.discovery_flows")
        )
        total_count = total_result.scalar()
        
        # Check for missing master_flow_id
        missing_master_flow = await session.execute(
            text("SELECT COUNT(*) FROM migration.discovery_flows WHERE master_flow_id IS NULL")
        )
        missing_master_count = missing_master_flow.scalar()
        
        # Check for orphaned master_flow_id references
        orphaned_master_flow = await session.execute(
            text("""
                SELECT COUNT(*) FROM migration.discovery_flows df
                WHERE df.master_flow_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM migration.crewai_flow_state_extensions cfse
                    WHERE cfse.id = df.master_flow_id
                )
            """)
        )
        orphaned_master_count = orphaned_master_flow.scalar()
        
        # Check for orphaned data_import_id references
        orphaned_data_import = await session.execute(
            text("""
                SELECT COUNT(*) FROM migration.discovery_flows df
                WHERE df.data_import_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM migration.data_imports di
                    WHERE di.id = df.data_import_id
                )
            """)
        )
        orphaned_data_import_count = orphaned_data_import.scalar()
        
        # Check for duplicate flow_ids
        duplicate_flow_ids = await session.execute(
            text("""
                SELECT COUNT(*) FROM (
                    SELECT flow_id, COUNT(*) as cnt
                    FROM migration.discovery_flows
                    GROUP BY flow_id
                    HAVING COUNT(*) > 1
                ) duplicates
            """)
        )
        duplicate_count = duplicate_flow_ids.scalar()
        
        # Get sample orphaned records
        if missing_master_count > 0:
            orphaned_details = await session.execute(
                text("""
                    SELECT id, flow_id, flow_name, client_account_id, engagement_id, created_at
                    FROM migration.discovery_flows
                    WHERE master_flow_id IS NULL
                    ORDER BY created_at DESC
                    LIMIT 5
                """)
            )
            
            for row in orphaned_details.fetchall():
                self.orphaned_records.append(OrphanedRecord(
                    table_name="discovery_flows",
                    record_id=str(row.id),
                    foreign_key_field="master_flow_id",
                    foreign_key_value=None,
                    client_account_id=str(row.client_account_id),
                    engagement_id=str(row.engagement_id),
                    created_at=row.created_at,
                    additional_info={
                        "flow_id": str(row.flow_id),
                        "flow_name": row.flow_name
                    }
                ))
        
        total_issues = missing_master_count + orphaned_master_count + orphaned_data_import_count + duplicate_count
        valid_count = total_count - total_issues
        health_score = (valid_count / total_count * 100) if total_count > 0 else 0
        
        return ValidationResult(
            table_name="discovery_flows",
            check_name="Discovery Flow Linkages",
            total_records=total_count,
            valid_records=valid_count,
            invalid_records=total_issues,
            orphaned_records=missing_master_count,
            health_score=health_score,
            details={
                "missing_master_flow_id": missing_master_count,
                "orphaned_master_flow_refs": orphaned_master_count,
                "orphaned_data_import_refs": orphaned_data_import_count,
                "duplicate_flow_ids": duplicate_count
            }
        )
    
    async def validate_assessment_flow_linkages(self, session: Session) -> ValidationResult:
        """Validate AssessmentFlow table linkages."""
        self.logger.info("Validating assessment flow linkages...")
        
        # Count total assessment flows
        total_result = await session.execute(
            text("SELECT COUNT(*) FROM migration.assessment_flows")
        )
        total_count = total_result.scalar()
        
        if total_count == 0:
            return ValidationResult(
                table_name="assessment_flows",
                check_name="Assessment Flow Linkages",
                total_records=0,
                valid_records=0,
                invalid_records=0,
                orphaned_records=0,
                health_score=100.0,
                details={"note": "No assessment flows found"}
            )
        
        # Check for missing master_flow_id
        missing_master_flow = await session.execute(
            text("SELECT COUNT(*) FROM migration.assessment_flows WHERE master_flow_id IS NULL")
        )
        missing_master_count = missing_master_flow.scalar()
        
        # Check for orphaned master_flow_id references
        orphaned_master_flow = await session.execute(
            text("""
                SELECT COUNT(*) FROM migration.assessment_flows af
                WHERE af.master_flow_id IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM migration.crewai_flow_state_extensions cfse
                    WHERE cfse.id = af.master_flow_id
                )
            """)
        )
        orphaned_master_count = orphaned_master_flow.scalar()
        
        total_issues = missing_master_count + orphaned_master_count
        valid_count = total_count - total_issues
        health_score = (valid_count / total_count * 100) if total_count > 0 else 0
        
        return ValidationResult(
            table_name="assessment_flows",
            check_name="Assessment Flow Linkages",
            total_records=total_count,
            valid_records=valid_count,
            invalid_records=total_issues,
            orphaned_records=missing_master_count,
            health_score=health_score,
            details={
                "missing_master_flow_id": missing_master_count,
                "orphaned_master_flow_refs": orphaned_master_count
            }
        )
    
    async def validate_cross_table_consistency(self, session: Session) -> ValidationResult:
        """Validate consistency across multiple tables."""
        self.logger.info("Validating cross-table consistency...")
        
        # Check for master flows without any child flows
        orphaned_master_flows = await session.execute(
            text("""
                SELECT COUNT(*) FROM migration.crewai_flow_state_extensions cfse
                WHERE cfse.flow_type = 'discovery'
                AND NOT EXISTS (
                    SELECT 1 FROM migration.discovery_flows df
                    WHERE df.master_flow_id = cfse.id
                )
                AND NOT EXISTS (
                    SELECT 1 FROM migration.data_imports di
                    WHERE di.master_flow_id = cfse.id
                )
            """)
        )
        orphaned_master_count = orphaned_master_flows.scalar()
        
        # Check for data imports without raw records
        data_imports_without_records = await session.execute(
            text("""
                SELECT COUNT(*) FROM migration.data_imports di
                WHERE NOT EXISTS (
                    SELECT 1 FROM migration.raw_import_records rir
                    WHERE rir.data_import_id = di.id
                )
            """)
        )
        imports_without_records = data_imports_without_records.scalar()
        
        # Check for mismatched tenant context
        mismatched_tenant_context = await session.execute(
            text("""
                SELECT COUNT(*) FROM migration.data_imports di
                JOIN migration.crewai_flow_state_extensions cfse ON di.master_flow_id = cfse.id
                WHERE di.client_account_id != cfse.client_account_id
                   OR di.engagement_id != cfse.engagement_id
            """)
        )
        mismatched_tenant_count = mismatched_tenant_context.scalar()
        
        # Calculate total issues
        total_issues = orphaned_master_count + imports_without_records + mismatched_tenant_count
        
        # Get total master flows for health score calculation
        total_master_flows = await session.execute(
            text("SELECT COUNT(*) FROM migration.crewai_flow_state_extensions")
        )
        total_count = total_master_flows.scalar()
        
        valid_count = total_count - total_issues
        health_score = (valid_count / total_count * 100) if total_count > 0 else 0
        
        return ValidationResult(
            table_name="cross_table",
            check_name="Cross-Table Consistency",
            total_records=total_count,
            valid_records=valid_count,
            invalid_records=total_issues,
            orphaned_records=orphaned_master_count,
            health_score=health_score,
            details={
                "orphaned_master_flows": orphaned_master_count,
                "data_imports_without_records": imports_without_records,
                "mismatched_tenant_context": mismatched_tenant_count
            }
        )
    
    async def export_results_to_csv(self, filepath: str):
        """Export validation results to CSV."""
        self.logger.info(f"Exporting validation results to {filepath}")
        
        # Export validation results
        results_file = filepath.replace('.csv', '_validation_results.csv')
        with open(results_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['table_name', 'check_name', 'total_records', 'valid_records', 
                         'invalid_records', 'orphaned_records', 'health_score', 'details']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in self.validation_results:
                row = asdict(result)
                row['details'] = str(row['details'])  # Convert dict to string for CSV
                writer.writerow(row)
        
        # Export orphaned records
        orphaned_file = filepath.replace('.csv', '_orphaned_records.csv')
        if self.orphaned_records:
            with open(orphaned_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['table_name', 'record_id', 'foreign_key_field', 'foreign_key_value',
                             'client_account_id', 'engagement_id', 'created_at', 'additional_info']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for record in self.orphaned_records:
                    row = asdict(record)
                    row['additional_info'] = str(row['additional_info'])  # Convert dict to string for CSV
                    writer.writerow(row)
        
        self.logger.info(f"Results exported to {results_file}")
        self.logger.info(f"Orphaned records exported to {orphaned_file}")
    
    async def run_validation(self) -> bool:
        """Run all validation checks."""
        self.logger.info("Starting comprehensive flow relationship validation...")
        
        try:
            async with AsyncSessionLocal() as session:
                # Run all validation checks
                self.validation_results.append(await self.validate_master_flow_integrity(session))
                self.validation_results.append(await self.validate_data_import_linkages(session))
                self.validation_results.append(await self.validate_raw_import_record_linkages(session))
                self.validation_results.append(await self.validate_discovery_flow_linkages(session))
                self.validation_results.append(await self.validate_assessment_flow_linkages(session))
                self.validation_results.append(await self.validate_cross_table_consistency(session))
                
                # Export results if requested
                if self.export_csv:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    csv_file = f"validation_results_{timestamp}.csv"
                    await self.export_results_to_csv(csv_file)
                
                # Print summary
                self._print_summary()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Validation failed: {str(e)}")
            return False
    
    def _print_summary(self):
        """Print comprehensive validation summary."""
        duration = datetime.now() - self.start_time
        
        print("\n" + "="*80)
        print("COMPREHENSIVE FLOW RELATIONSHIP VALIDATION REPORT")
        print("="*80)
        print(f"Validation completed in: {duration}")
        print(f"Total orphaned records found: {len(self.orphaned_records)}")
        print()
        
        # Overall health score
        overall_health = sum(r.health_score for r in self.validation_results) / len(self.validation_results)
        print(f"Overall System Health Score: {overall_health:.1f}%")
        
        if overall_health >= 95:
            print("✅ EXCELLENT - System is in excellent health")
        elif overall_health >= 85:
            print("🟡 GOOD - System is healthy with minor issues")
        elif overall_health >= 70:
            print("🟠 FAIR - System has some issues that should be addressed")
        else:
            print("🔴 POOR - System has significant integrity issues")
        
        print("\nDetailed Results:")
        print("-" * 80)
        
        for result in self.validation_results:
            status = "✅" if result.health_score >= 95 else "🟡" if result.health_score >= 85 else "🔴"
            print(f"{status} {result.check_name} ({result.table_name})")
            print(f"    Total Records: {result.total_records:,}")
            print(f"    Valid Records: {result.valid_records:,}")
            print(f"    Invalid Records: {result.invalid_records:,}")
            print(f"    Orphaned Records: {result.orphaned_records:,}")
            print(f"    Health Score: {result.health_score:.1f}%")
            
            if result.details and self.verbose:
                print("    Details:")
                for key, value in result.details.items():
                    print(f"      {key}: {value}")
            print()
        
        if self.orphaned_records:
            print("Sample Orphaned Records:")
            print("-" * 80)
            
            # Group by table
            by_table = {}
            for record in self.orphaned_records:
                if record.table_name not in by_table:
                    by_table[record.table_name] = []
                by_table[record.table_name].append(record)
            
            for table_name, records in by_table.items():
                print(f"\n{table_name.upper()} ({len(records)} records):")
                for record in records[:3]:  # Show first 3
                    print(f"  ID: {record.record_id}")
                    print(f"  Missing: {record.foreign_key_field}")
                    print(f"  Tenant: {record.client_account_id[:8]}.../{record.engagement_id[:8]}...")
                    print(f"  Created: {record.created_at}")
                    if record.additional_info:
                        print(f"  Info: {record.additional_info}")
                    print()
                
                if len(records) > 3:
                    print(f"  ... and {len(records) - 3} more records")
                    print()
        
        print("="*80)
        print("RECOMMENDATIONS:")
        
        # Generate recommendations based on results
        recommendations = []
        for result in self.validation_results:
            if result.health_score < 100:
                if result.orphaned_records > 0:
                    recommendations.append(f"- Fix {result.orphaned_records} orphaned records in {result.table_name}")
                if result.invalid_records > 0:
                    recommendations.append(f"- Address {result.invalid_records} data integrity issues in {result.table_name}")
        
        if recommendations:
            for rec in recommendations:
                print(rec)
        else:
            print("- No issues found. System is in excellent health!")
        
        print("\nNext Steps:")
        print("1. Run fix_orphaned_data_imports.py to fix orphaned data import records")
        print("2. Review and fix any remaining orphaned records manually")
        print("3. Re-run this validation to verify fixes")
        print("="*80)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Validate flow relationship integrity')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--export-csv', action='store_true', help='Export results to CSV files')
    
    args = parser.parse_args()
    
    validator = FlowRelationshipValidator(verbose=args.verbose, export_csv=args.export_csv)
    success = await validator.run_validation()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())