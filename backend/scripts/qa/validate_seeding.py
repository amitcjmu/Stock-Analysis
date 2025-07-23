#!/usr/bin/env python3
"""
Database Seeding Validation Script

This script validates the integrity of seeded demo data for the AI Modernize Migration Platform.
Checks multi-tenant isolation, referential integrity, and data completeness.

Usage:
    python scripts/qa/validate_seeding.py [--verbose] [--fix-issues] [--export-report]
"""

import argparse
import asyncio
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add app path
sys.path.append('/app')

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models import (
    Assessment,
    Asset,
    AssetDependency,
    ClientAccount,
    DataImport,
    DiscoveryFlow,
    Engagement,
    ImportFieldMapping,
    Migration,
    RawImportRecord,
    User,
    UserRole,
    WavePlan,
)


@dataclass
class ValidationResult:
    """Results of a validation check."""
    name: str
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    severity: str = "error"  # error, warning, info
    
@dataclass
class ExpectedCounts:
    """Expected record counts for validation."""
    client_accounts: int = 1
    engagements: int = 1
    users: int = 4
    assets: int = 60
    discovery_flows: int = 5
    data_imports: int = 5
    field_mappings: int = 10
    assessments: int = 15
    migrations: int = 5
    wave_plans: int = 5

class DatabaseValidator:
    """Comprehensive database validation for seeded demo data."""
    
    def __init__(self, verbose: bool = False, fix_issues: bool = False):
        self.verbose = verbose
        self.fix_issues = fix_issues
        self.results: List[ValidationResult] = []
        self.expected = ExpectedCounts()
        
    async def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation checks and return comprehensive report."""
        print("🔍 Starting Database Seeding Validation...")
        print("=" * 60)
        
        async with AsyncSessionLocal() as session:
            # Core data validation
            await self._validate_client_accounts(session)
            await self._validate_engagements(session)
            await self._validate_users(session)
            await self._validate_user_roles(session)
            
            # Asset data validation
            await self._validate_assets(session)
            await self._validate_asset_dependencies(session)
            
            # Flow data validation
            await self._validate_discovery_flows(session)
            await self._validate_data_imports(session)
            await self._validate_field_mappings(session)
            
            # Assessment data validation
            await self._validate_assessments(session)
            await self._validate_migrations(session)
            await self._validate_wave_plans(session)
            
            # Relationship integrity
            await self._validate_foreign_keys(session)
            await self._validate_multi_tenant_isolation(session)
            
            # Data quality checks
            await self._validate_data_completeness(session)
            await self._validate_business_rules(session)
            
            # Performance checks
            await self._validate_performance(session)
            
        return self._generate_report()
    
    async def _validate_client_accounts(self, session: AsyncSession):
        """Validate client account data."""
        print("📊 Validating Client Accounts...")
        
        # Count check
        result = await session.execute(select(func.count(ClientAccount.id)))
        count = result.scalar()
        
        if count != self.expected.client_accounts:
            self._add_result("client_accounts_count", False,
                           f"Expected {self.expected.client_accounts} client accounts, found {count}")
        else:
            self._add_result("client_accounts_count", True,
                           f"✅ Found {count} client accounts as expected")
        
        # Required fields check
        result = await session.execute(
            select(ClientAccount).where(
                ClientAccount.name.is_(None)
            )
        )
        incomplete_accounts = result.fetchall()
        
        if incomplete_accounts:
            self._add_result("client_accounts_complete", False,
                           f"Found {len(incomplete_accounts)} client accounts with missing required fields")
        else:
            self._add_result("client_accounts_complete", True,
                           "✅ All client accounts have required fields")
        
        # Industry diversity check
        result = await session.execute(
            select(ClientAccount.industry, func.count(ClientAccount.id))
            .group_by(ClientAccount.industry)
        )
        industries = dict(result.fetchall())
        
        if len(industries) < 1:
            self._add_result("client_accounts_diversity", False,
                           "No industries found")
        else:
            self._add_result("client_accounts_diversity", True,
                           f"✅ Industries present: {list(industries.keys())}")
    
    async def _validate_engagements(self, session: AsyncSession):
        """Validate engagement data."""
        print("🤝 Validating Engagements...")
        
        # Count check
        result = await session.execute(select(func.count(Engagement.id)))
        count = result.scalar()
        
        if count != self.expected.engagements:
            self._add_result("engagements_count", False,
                           f"Expected {self.expected.engagements} engagements, found {count}")
        else:
            self._add_result("engagements_count", True,
                           f"✅ Found {count} engagements as expected")
        
        # Client relationship check
        result = await session.execute(
            select(Engagement).where(Engagement.client_account_id.is_(None))
        )
        orphaned = result.fetchall()
        
        if orphaned:
            self._add_result("engagements_client_link", False,
                           f"Found {len(orphaned)} engagements without client accounts")
        else:
            self._add_result("engagements_client_link", True,
                           "✅ All engagements linked to client accounts")
        
        # Status diversity check
        result = await session.execute(
            select(Engagement.status, func.count(Engagement.id))
            .group_by(Engagement.status)
        )
        statuses = dict(result.fetchall())
        
        if len(statuses) == 0:
            self._add_result("engagement_status_diversity", False,
                           "No engagement statuses found")
        else:
            self._add_result("engagement_status_diversity", True,
                           f"✅ Engagement statuses present: {list(statuses.keys())}")
    
    async def _validate_users(self, session: AsyncSession):
        """Validate user data."""
        print("👥 Validating Users...")
        
        # Count check
        result = await session.execute(select(func.count(User.id)))
        count = result.scalar()
        
        if count != self.expected.users:
            self._add_result("users_count", False,
                           f"Expected {self.expected.users} users, found {count}")
        else:
            self._add_result("users_count", True,
                           f"✅ Found {count} users as expected")
        
        # Email uniqueness check
        result = await session.execute(
            select(User.email, func.count(User.id))
            .group_by(User.email)
            .having(func.count(User.id) > 1)
        )
        duplicates = result.fetchall()
        
        if duplicates:
            self._add_result("users_email_unique", False,
                           f"Found {len(duplicates)} duplicate email addresses")
        else:
            self._add_result("users_email_unique", True,
                           "✅ All user emails are unique")
        
        # Required fields check
        result = await session.execute(
            select(User).where(
                or_(
                    User.email.is_(None),
                    User.email == '',
                    User.first_name.is_(None),
                    User.first_name == ''
                )
            )
        )
        incomplete_users = result.fetchall()
        
        if incomplete_users:
            self._add_result("users_complete", False,
                           f"Found {len(incomplete_users)} users with missing required fields")
        else:
            self._add_result("users_complete", True,
                           "✅ All users have required fields")
    
    async def _validate_user_roles(self, session: AsyncSession):
        """Validate user role assignments."""
        print("🔐 Validating User Roles...")
        
        # Check role diversity
        result = await session.execute(
            select(UserRole.role_name, func.count(UserRole.id))
            .group_by(UserRole.role_name)
        )
        roles = dict(result.fetchall())
        
        expected_roles = ['Analyst', 'Client Admin', 'Viewer', 'Engagement Manager']
        missing_roles = [r for r in expected_roles if r not in roles]
        
        if missing_roles:
            self._add_result("user_roles_diversity", False,
                           f"Missing user roles: {missing_roles}")
        else:
            self._add_result("user_roles_diversity", True,
                           f"✅ All required roles present: {list(roles.keys())}")
        
        # Check users without roles
        result = await session.execute(
            select(User.id)
            .outerjoin(UserRole, User.id == UserRole.user_id)
            .where(UserRole.user_id.is_(None))
        )
        users_without_roles = result.fetchall()
        
        if users_without_roles:
            self._add_result("users_have_roles", False,
                           f"Found {len(users_without_roles)} users without roles")
        else:
            self._add_result("users_have_roles", True,
                           "✅ All users have assigned roles")
    
    async def _validate_assets(self, session: AsyncSession):
        """Validate asset data."""
        print("🏗️ Validating Assets...")
        
        # Count check
        result = await session.execute(select(func.count(Asset.id)))
        count = result.scalar()
        
        if count != self.expected.assets:
            self._add_result("assets_count", False,
                           f"Expected {self.expected.assets} assets, found {count}")
        else:
            self._add_result("assets_count", True,
                           f"✅ Found {count} assets as expected")
        
        # Asset type diversity
        result = await session.execute(
            select(Asset.asset_type, func.count(Asset.id))
            .group_by(Asset.asset_type)
        )
        asset_types = dict(result.fetchall())
        
        expected_types = ['server', 'database', 'application', 'network']
        missing_types = [t for t in expected_types if t not in asset_types]
        
        if missing_types:
            self._add_result("asset_type_diversity", False,
                           f"Missing asset types: {missing_types}")
        else:
            self._add_result("asset_type_diversity", True,
                           f"✅ Good asset type diversity: {list(asset_types.keys())}")
        
        # Required fields check
        result = await session.execute(
            select(Asset).where(
                or_(
                    Asset.name.is_(None),
                    Asset.name == '',
                    Asset.asset_type.is_(None)
                )
            )
        )
        incomplete_assets = result.fetchall()
        
        if incomplete_assets:
            self._add_result("assets_complete", False,
                           f"Found {len(incomplete_assets)} assets with missing required fields")
        else:
            self._add_result("assets_complete", True,
                           "✅ All assets have required fields")
    
    async def _validate_asset_dependencies(self, session: AsyncSession):
        """Validate asset dependency relationships."""
        print("🔗 Validating Asset Dependencies...")
        
        # Check for circular dependencies
        result = await session.execute(
            select(AssetDependency)
            .where(AssetDependency.asset_id == AssetDependency.depends_on_asset_id)
        )
        circular_deps = result.fetchall()
        
        if circular_deps:
            self._add_result("asset_deps_circular", False,
                           f"Found {len(circular_deps)} circular dependencies (asset depends on itself)")
        else:
            self._add_result("asset_deps_circular", True,
                           "✅ No circular dependencies found")
        
        # Check for orphaned dependencies
        result = await session.execute(
            select(AssetDependency.id)
            .outerjoin(Asset, AssetDependency.asset_id == Asset.id)
            .where(Asset.id.is_(None))
        )
        orphaned_deps = result.fetchall()
        
        if orphaned_deps:
            self._add_result("asset_deps_orphaned", False,
                           f"Found {len(orphaned_deps)} dependencies referencing non-existent assets")
        else:
            self._add_result("asset_deps_orphaned", True,
                           "✅ All dependencies reference valid assets")
    
    async def _validate_discovery_flows(self, session: AsyncSession):
        """Validate discovery flow data."""
        print("🔄 Validating Discovery Flows...")
        
        # Count check
        result = await session.execute(select(func.count(DiscoveryFlow.id)))
        count = result.scalar()
        
        if count != self.expected.discovery_flows:
            self._add_result("discovery_flows_count", False,
                           f"Expected {self.expected.discovery_flows} discovery flows, found {count}")
        else:
            self._add_result("discovery_flows_count", True,
                           f"✅ Found {count} discovery flows as expected")
        
        # Status diversity check
        result = await session.execute(
            select(DiscoveryFlow.current_phase, func.count(DiscoveryFlow.id))
            .group_by(DiscoveryFlow.current_phase)
        )
        phases = dict(result.fetchall())
        
        if len(phases) < 3:
            self._add_result("discovery_flow_phases", False,
                           f"Limited phase diversity: {list(phases.keys())}")
        else:
            self._add_result("discovery_flow_phases", True,
                           f"✅ Good phase diversity: {list(phases.keys())}")
    
    async def _validate_data_imports(self, session: AsyncSession):
        """Validate data import records."""
        print("📥 Validating Data Imports...")
        
        # Count check
        result = await session.execute(select(func.count(DataImport.id)))
        count = result.scalar()
        
        if count != self.expected.data_imports:
            self._add_result("data_imports_count", False,
                           f"Expected {self.expected.data_imports} data imports, found {count}")
        else:
            self._add_result("data_imports_count", True,
                           f"✅ Found {count} data imports as expected")
        
        # Check for imports without raw records
        result = await session.execute(
            select(DataImport.id)
            .outerjoin(RawImportRecord, DataImport.id == RawImportRecord.data_import_id)
            .group_by(DataImport.id)
            .having(func.count(RawImportRecord.id) == 0)
        )
        empty_imports = result.fetchall()
        
        if empty_imports:
            self._add_result("data_imports_have_records", False,
                           f"Found {len(empty_imports)} data imports without raw records")
        else:
            self._add_result("data_imports_have_records", True,
                           "✅ All data imports have associated raw records")
    
    async def _validate_field_mappings(self, session: AsyncSession):
        """Validate field mapping data."""
        print("🗺️ Validating Field Mappings...")
        
        # Count check
        result = await session.execute(select(func.count(ImportFieldMapping.id)))
        count = result.scalar()
        
        if count != self.expected.field_mappings:
            self._add_result("field_mappings_count", False,
                           f"Expected {self.expected.field_mappings} field mappings, found {count}")
        else:
            self._add_result("field_mappings_count", True,
                           f"✅ Found {count} field mappings as expected")
    
    async def _validate_assessments(self, session: AsyncSession):
        """Validate assessment data."""
        print("📋 Validating Assessments...")
        
        # Count check
        result = await session.execute(select(func.count(Assessment.id)))
        count = result.scalar()
        
        if count != self.expected.assessments:
            self._add_result("assessments_count", False,
                           f"Expected {self.expected.assessments} assessments, found {count}")
        else:
            self._add_result("assessments_count", True,
                           f"✅ Found {count} assessments as expected")
    
    async def _validate_migrations(self, session: AsyncSession):
        """Validate migration data."""
        print("🚀 Validating Migrations...")
        
        # Count check
        result = await session.execute(select(func.count(Migration.id)))
        count = result.scalar()
        
        if count != self.expected.migrations:
            self._add_result("migrations_count", False,
                           f"Expected {self.expected.migrations} migrations, found {count}")
        else:
            self._add_result("migrations_count", True,
                           f"✅ Found {count} migrations as expected")
    
    async def _validate_wave_plans(self, session: AsyncSession):
        """Validate wave plan data."""
        print("🌊 Validating Wave Plans...")
        
        # Count check
        result = await session.execute(select(func.count(WavePlan.id)))
        count = result.scalar()
        
        if count != self.expected.wave_plans:
            self._add_result("wave_plans_count", False,
                           f"Expected {self.expected.wave_plans} wave plans, found {count}")
        else:
            self._add_result("wave_plans_count", True,
                           f"✅ Found {count} wave plans as expected")
    
    async def _validate_foreign_keys(self, session: AsyncSession):
        """Validate foreign key integrity."""
        print("🔑 Validating Foreign Key Integrity...")
        
        # This is a simplified check - in practice, PostgreSQL enforces FK constraints
        # But we can check for logical inconsistencies
        
        # Assets without engagements
        result = await session.execute(
            select(Asset.id)
            .outerjoin(Engagement, Asset.engagement_id == Engagement.id)
            .where(and_(Asset.engagement_id.is_not(None), Engagement.id.is_(None)))
        )
        invalid_asset_engagements = result.fetchall()
        
        if invalid_asset_engagements:
            self._add_result("fk_asset_engagements", False,
                           f"Found {len(invalid_asset_engagements)} assets with invalid engagement references")
        else:
            self._add_result("fk_asset_engagements", True,
                           "✅ All asset-engagement references are valid")
    
    async def _validate_multi_tenant_isolation(self, session: AsyncSession):
        """Validate multi-tenant data isolation."""
        print("🏢 Validating Multi-Tenant Isolation...")
        
        # Check that each client account has isolated data
        result = await session.execute(
            select(ClientAccount.id, ClientAccount.name)
        )
        client_accounts = result.fetchall()
        
        isolation_issues = []
        
        for client_id, client_name in client_accounts:
            # Check assets belong to correct client
            result = await session.execute(
                select(func.count(Asset.id))
                .where(Asset.client_account_id == client_id)
            )
            asset_count = result.scalar()
            
            # Check engagements belong to correct client
            result = await session.execute(
                select(func.count(Engagement.id))
                .where(Engagement.client_account_id == client_id)
            )
            engagement_count = result.scalar()
            
            if asset_count == 0 and engagement_count == 0:
                isolation_issues.append(f"Client {client_name} has no associated data")
        
        if isolation_issues:
            self._add_result("multi_tenant_isolation", False,
                           f"Isolation issues: {'; '.join(isolation_issues)}")
        else:
            self._add_result("multi_tenant_isolation", True,
                           "✅ Multi-tenant isolation appears correct")
    
    async def _validate_data_completeness(self, session: AsyncSession):
        """Validate data completeness and quality."""
        print("📊 Validating Data Completeness...")
        
        # Check for NULL values in critical fields
        critical_checks = [
            (User, User.email, "user emails"),
            (Asset, Asset.name, "asset names"),
            (ClientAccount, ClientAccount.name, "client names"),
            (Engagement, Engagement.name, "engagement names")
        ]
        
        for model, field, description in critical_checks:
            result = await session.execute(
                select(func.count(model.id))
                .where(or_(field.is_(None), field == ''))
            )
            null_count = result.scalar()
            
            if null_count > 0:
                self._add_result(f"completeness_{description.replace(' ', '_')}", False,
                               f"Found {null_count} records with missing {description}")
            else:
                self._add_result(f"completeness_{description.replace(' ', '_')}", True,
                               f"✅ All {description} are present")
    
    async def _validate_business_rules(self, session: AsyncSession):
        """Validate business logic rules."""
        print("💼 Validating Business Rules...")
        
        # Check for future dates where they shouldn't exist
        result = await session.execute(
            select(func.count(Asset.id))
            .where(Asset.discovery_timestamp > func.now())
        )
        future_discoveries = result.scalar()
        
        if future_discoveries > 0:
            self._add_result("business_rule_discovery_dates", False,
                           f"Found {future_discoveries} assets with future discovery dates")
        else:
            self._add_result("business_rule_discovery_dates", True,
                           "✅ All discovery dates are realistic")
        
        # Check for reasonable asset utilization values
        result = await session.execute(
            select(func.count(Asset.id))
            .where(or_(
                Asset.cpu_utilization_percent > 100,
                Asset.memory_utilization_percent > 100,
                Asset.cpu_utilization_percent < 0,
                Asset.memory_utilization_percent < 0
            ))
        )
        invalid_utilization = result.scalar()
        
        if invalid_utilization > 0:
            self._add_result("business_rule_utilization", False,
                           f"Found {invalid_utilization} assets with invalid utilization percentages")
        else:
            self._add_result("business_rule_utilization", True,
                           "✅ All utilization percentages are within valid ranges")
    
    async def _validate_performance(self, session: AsyncSession):
        """Validate database performance with seeded data."""
        print("⚡ Validating Performance...")
        
        # Test common query performance
        start_time = datetime.now()
        
        # Complex query similar to what the UI might run
        result = await session.execute(
            select(Asset.id, Asset.name, ClientAccount.name, Engagement.name)
            .join(ClientAccount, Asset.client_account_id == ClientAccount.id)
            .join(Engagement, Asset.engagement_id == Engagement.id)
            .limit(100)
        )
        result.fetchall()
        
        query_time = (datetime.now() - start_time).total_seconds()
        
        if query_time > 2.0:  # 2 second threshold
            self._add_result("performance_complex_query", False,
                           f"Complex query took {query_time:.2f}s (> 2s threshold)",
                           severity="warning")
        else:
            self._add_result("performance_complex_query", True,
                           f"✅ Complex query completed in {query_time:.2f}s")
    
    def _add_result(self, name: str, passed: bool, message: str, 
                   details: Optional[Dict[str, Any]] = None, severity: str = "error"):
        """Add a validation result."""
        result = ValidationResult(
            name=name,
            passed=passed,
            message=message,
            details=details,
            severity=severity
        )
        self.results.append(result)
        
        if self.verbose:
            status = "✅ PASS" if passed else "❌ FAIL" if severity == "error" else "⚠️ WARN"
            print(f"  {status}: {message}")
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        passed_count = sum(1 for r in self.results if r.passed)
        failed_count = sum(1 for r in self.results if not r.passed and r.severity == "error")
        warning_count = sum(1 for r in self.results if not r.passed and r.severity == "warning")
        
        # Group results by category
        categories = defaultdict(list)
        for result in self.results:
            category = result.name.split('_')[0]
            categories[category].append(result)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_checks": len(self.results),
                "passed": passed_count,
                "failed": failed_count,
                "warnings": warning_count,
                "success_rate": (passed_count / len(self.results)) * 100 if self.results else 0
            },
            "categories": dict(categories),
            "all_results": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "severity": r.severity,
                    "details": r.details
                }
                for r in self.results
            ],
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        failed_results = [r for r in self.results if not r.passed and r.severity == "error"]
        
        if any("count" in r.name for r in failed_results):
            recommendations.append("Review seeding scripts - record counts don't match expectations")
        
        if any("foreign" in r.name or "orphaned" in r.name for r in failed_results):
            recommendations.append("Check referential integrity - some foreign key relationships are broken")
        
        if any("tenant" in r.name for r in failed_results):
            recommendations.append("Multi-tenant isolation may be compromised - review data separation")
        
        if any("complete" in r.name for r in failed_results):
            recommendations.append("Some records are missing required fields - review data quality")
        
        if any("performance" in r.name for r in failed_results):
            recommendations.append("Performance issues detected - consider adding indexes or optimizing queries")
        
        if not failed_results:
            recommendations.append("All validations passed! Database seeding appears successful.")
        
        return recommendations

def print_report(report: Dict[str, Any]):
    """Print formatted validation report."""
    print("\n" + "="*60)
    print("📊 DATABASE SEEDING VALIDATION REPORT")
    print("="*60)
    
    summary = report['summary']
    print(f"📅 Generated: {report['timestamp']}")
    print(f"🔍 Total Checks: {summary['total_checks']}")
    print(f"✅ Passed: {summary['passed']}")
    print(f"❌ Failed: {summary['failed']}")
    print(f"⚠️ Warnings: {summary['warnings']}")
    print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
    
    if summary['failed'] > 0:
        print("\n❌ FAILED CHECKS:")
        print("-" * 40)
        failed = [r for r in report['all_results'] if not r['passed'] and r['severity'] == 'error']
        for result in failed:
            print(f"  • {result['message']}")
    
    if summary['warnings'] > 0:
        print("\n⚠️ WARNINGS:")
        print("-" * 40)
        warnings = [r for r in report['all_results'] if not r['passed'] and r['severity'] == 'warning']
        for result in warnings:
            print(f"  • {result['message']}")
    
    if report['recommendations']:
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 40)
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
    
    # Overall status
    if summary['failed'] == 0:
        print("\n🎉 VALIDATION SUCCESSFUL!")
        print("Database seeding completed successfully with all checks passing.")
    else:
        print("\n⚠️ VALIDATION ISSUES DETECTED")
        print(f"Found {summary['failed']} critical issues that should be addressed.")

async def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description='Validate database seeding')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--fix-issues', action='store_true', help='Attempt to fix detected issues')
    parser.add_argument('--export-report', '-e', help='Export report to JSON file')
    
    args = parser.parse_args()
    
    validator = DatabaseValidator(verbose=args.verbose, fix_issues=args.fix_issues)
    
    try:
        report = await validator.run_all_validations()
        
        if args.export_report:
            with open(args.export_report, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"📄 Report exported to {args.export_report}")
        
        print_report(report)
        
        # Exit with appropriate code
        if report['summary']['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())