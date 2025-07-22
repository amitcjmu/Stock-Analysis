#!/usr/bin/env python3
"""
Multi-Tenant Isolation Validation Tests

This script specifically tests multi-tenant data isolation to ensure
proper security boundaries in the AI Modernize Migration Platform.

Usage:
    python scripts/qa/multi_tenant_isolation_tests.py [--verbose] [--client-id ID]
"""

import asyncio
import sys
import argparse
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

# Add app path
sys.path.append('/app')

from sqlalchemy import text, select, func, and_, or_, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models import *

@dataclass
class IsolationTestResult:
    """Results of a multi-tenant isolation test."""
    test_name: str
    client_id: int
    client_name: str
    passed: bool
    message: str
    data_leak_count: int = 0
    details: Optional[Dict[str, Any]] = None

class MultiTenantIsolationTester:
    """Test multi-tenant data isolation across all entities."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[IsolationTestResult] = []
        self.client_accounts: List[Tuple[int, str]] = []
        
    async def run_isolation_tests(self, target_client_id: Optional[int] = None) -> Dict[str, Any]:
        """Run comprehensive multi-tenant isolation tests."""
        print("🏢 Starting Multi-Tenant Isolation Tests...")
        print("=" * 60)
        
        async with AsyncSessionLocal() as session:
            # Get all client accounts
            await self._load_client_accounts(session)
            
            if target_client_id:
                # Test specific client
                client_info = next((c for c in self.client_accounts if c[0] == target_client_id), None)
                if client_info:
                    await self._test_client_isolation(session, client_info[0], client_info[1])
                else:
                    print(f"❌ Client ID {target_client_id} not found")
            else:
                # Test all clients
                for client_id, client_name in self.client_accounts:
                    await self._test_client_isolation(session, client_id, client_name)
            
            # Cross-client contamination tests
            await self._test_cross_client_contamination(session)
            
            # Permission boundary tests
            await self._test_permission_boundaries(session)
        
        return self._generate_isolation_report()
    
    async def _load_client_accounts(self, session: AsyncSession):
        """Load all client accounts for testing."""
        result = await session.execute(
            select(ClientAccount.id, ClientAccount.name)
            .order_by(ClientAccount.name)
        )
        self.client_accounts = result.fetchall()
        
        if self.verbose:
            print(f"📊 Found {len(self.client_accounts)} client accounts:")
            for client_id, name in self.client_accounts:
                print(f"  • {name} (ID: {client_id})")
    
    async def _test_client_isolation(self, session: AsyncSession, client_id: int, client_name: str):
        """Test data isolation for a specific client."""
        print(f"\n🔍 Testing isolation for {client_name} (ID: {client_id})")
        
        # Test each entity type for proper isolation
        await self._test_engagement_isolation(session, client_id, client_name)
        await self._test_asset_isolation(session, client_id, client_name)
        await self._test_user_isolation(session, client_id, client_name)
        await self._test_discovery_flow_isolation(session, client_id, client_name)
        await self._test_data_import_isolation(session, client_id, client_name)
        await self._test_assessment_isolation(session, client_id, client_name)
        await self._test_migration_isolation(session, client_id, client_name)
    
    async def _test_engagement_isolation(self, session: AsyncSession, client_id: int, client_name: str):
        """Test engagement data isolation."""
        # Get engagements for this client
        result = await session.execute(
            select(func.count(Engagement.id))
            .where(Engagement.client_account_id == client_id)
        )
        client_engagements = result.scalar()
        
        # Check for engagements that might be accessible but shouldn't be
        result = await session.execute(
            select(func.count(Engagement.id))
            .where(Engagement.client_account_id != client_id)
        )
        other_engagements = result.scalar()
        
        if other_engagements == 0:
            # This would indicate all engagements belong to this client (unusual)
            self._add_result(
                "engagement_isolation_suspicious",
                client_id, client_name, False,
                f"All engagements appear to belong to {client_name} - suspicious"
            )
        else:
            self._add_result(
                "engagement_isolation",
                client_id, client_name, True,
                f"✅ {client_engagements} engagements isolated, {other_engagements} belong to other clients"
            )
    
    async def _test_asset_isolation(self, session: AsyncSession, client_id: int, client_name: str):
        """Test asset data isolation."""
        # Assets directly owned by client
        result = await session.execute(
            select(func.count(Asset.id))
            .where(Asset.client_account_id == client_id)
        )
        direct_assets = result.scalar()
        
        # Assets owned by client through engagements
        result = await session.execute(
            select(func.count(Asset.id))
            .join(Engagement, Asset.engagement_id == Engagement.id)
            .where(Engagement.client_account_id == client_id)
        )
        engagement_assets = result.scalar()
        
        # Check for assets that belong to other clients but reference this client's engagements
        result = await session.execute(
            select(func.count(Asset.id))
            .join(Engagement, Asset.engagement_id == Engagement.id)
            .where(
                and_(
                    Asset.client_account_id != client_id,
                    Engagement.client_account_id == client_id
                )
            )
        )
        cross_client_assets = result.scalar()
        
        if cross_client_assets > 0:
            self._add_result(
                "asset_isolation_violation",
                client_id, client_name, False,
                f"Found {cross_client_assets} assets with mismatched client/engagement ownership",
                data_leak_count=cross_client_assets
            )
        else:
            self._add_result(
                "asset_isolation",
                client_id, client_name, True,
                f"✅ Asset isolation intact: {direct_assets} direct, {engagement_assets} via engagements"
            )
    
    async def _test_user_isolation(self, session: AsyncSession, client_id: int, client_name: str):
        """Test user access isolation."""
        # Users associated with this client
        result = await session.execute(
            select(func.count(distinct(UserAccountAssociation.user_id)))
            .where(UserAccountAssociation.client_account_id == client_id)
        )
        client_users = result.scalar()
        
        # Check for users with access to multiple clients (system admins are expected)
        result = await session.execute(
            select(
                UserAccountAssociation.user_id,
                func.count(distinct(UserAccountAssociation.client_account_id)).label('client_count')
            )
            .join(User, UserAccountAssociation.user_id == User.id)
            .group_by(UserAccountAssociation.user_id)
            .having(func.count(distinct(UserAccountAssociation.client_account_id)) > 1)
        )
        multi_client_users = result.fetchall()
        
        # Verify multi-client users have appropriate roles
        system_admin_count = 0
        for user_id, client_count in multi_client_users:
            result = await session.execute(
                select(func.count(UserRole.id))
                .where(
                    and_(
                        UserRole.user_id == user_id,
                        UserRole.role == 'system_admin'
                    )
                )
            )
            if result.scalar() > 0:
                system_admin_count += 1
        
        unauthorized_multi_client = len(multi_client_users) - system_admin_count
        
        if unauthorized_multi_client > 0:
            self._add_result(
                "user_isolation_violation",
                client_id, client_name, False,
                f"Found {unauthorized_multi_client} non-admin users with access to multiple clients",
                data_leak_count=unauthorized_multi_client
            )
        else:
            self._add_result(
                "user_isolation",
                client_id, client_name, True,
                f"✅ User isolation correct: {client_users} users, {system_admin_count} system admins"
            )
    
    async def _test_discovery_flow_isolation(self, session: AsyncSession, client_id: int, client_name: str):
        """Test discovery flow isolation."""
        # Discovery flows for this client
        result = await session.execute(
            select(func.count(DiscoveryFlow.id))
            .where(DiscoveryFlow.client_account_id == client_id)
        )
        client_flows = result.scalar()
        
        # Check for flows referencing wrong client through engagement
        result = await session.execute(
            select(func.count(DiscoveryFlow.id))
            .join(Engagement, DiscoveryFlow.engagement_id == Engagement.id)
            .where(
                and_(
                    DiscoveryFlow.client_account_id != client_id,
                    Engagement.client_account_id == client_id
                )
            )
        )
        mismatched_flows = result.scalar()
        
        if mismatched_flows > 0:
            self._add_result(
                "discovery_flow_isolation_violation",
                client_id, client_name, False,
                f"Found {mismatched_flows} discovery flows with client/engagement mismatch",
                data_leak_count=mismatched_flows
            )
        else:
            self._add_result(
                "discovery_flow_isolation",
                client_id, client_name, True,
                f"✅ Discovery flow isolation intact: {client_flows} flows"
            )
    
    async def _test_data_import_isolation(self, session: AsyncSession, client_id: int, client_name: str):
        """Test data import isolation."""
        # Data imports for this client
        result = await session.execute(
            select(func.count(DataImport.id))
            .where(DataImport.client_account_id == client_id)
        )
        client_imports = result.scalar()
        
        # Check raw import records isolation
        result = await session.execute(
            select(func.count(RawImportRecord.id))
            .join(DataImport, RawImportRecord.data_import_id == DataImport.id)
            .where(
                and_(
                    RawImportRecord.client_account_id != client_id,
                    DataImport.client_account_id == client_id
                )
            )
        )
        mismatched_records = result.scalar()
        
        if mismatched_records > 0:
            self._add_result(
                "data_import_isolation_violation",
                client_id, client_name, False,
                f"Found {mismatched_records} raw import records with client mismatch",
                data_leak_count=mismatched_records
            )
        else:
            self._add_result(
                "data_import_isolation",
                client_id, client_name, True,
                f"✅ Data import isolation intact: {client_imports} imports"
            )
    
    async def _test_assessment_isolation(self, session: AsyncSession, client_id: int, client_name: str):
        """Test assessment isolation."""
        # Assessments for this client
        result = await session.execute(
            select(func.count(Assessment.id))
            .where(Assessment.client_account_id == client_id)
        )
        client_assessments = result.scalar()
        
        # Check for assessments on other clients' assets
        result = await session.execute(
            select(func.count(Assessment.id))
            .join(Asset, Assessment.asset_id == Asset.id)
            .where(
                and_(
                    Assessment.client_account_id == client_id,
                    Asset.client_account_id != client_id
                )
            )
        )
        cross_client_assessments = result.scalar()
        
        if cross_client_assessments > 0:
            self._add_result(
                "assessment_isolation_violation",
                client_id, client_name, False,
                f"Found {cross_client_assessments} assessments on other clients' assets",
                data_leak_count=cross_client_assessments
            )
        else:
            self._add_result(
                "assessment_isolation",
                client_id, client_name, True,
                f"✅ Assessment isolation intact: {client_assessments} assessments"
            )
    
    async def _test_migration_isolation(self, session: AsyncSession, client_id: int, client_name: str):
        """Test migration isolation."""
        # Migrations for this client (through engagements)
        result = await session.execute(
            select(func.count(Migration.id))
            .join(Engagement, Migration.engagement_id == Engagement.id)
            .where(Engagement.client_account_id == client_id)
        )
        client_migrations = result.scalar()
        
        # Wave plans for this client
        result = await session.execute(
            select(func.count(WavePlan.id))
            .where(WavePlan.client_account_id == client_id)
        )
        client_wave_plans = result.scalar()
        
        # Check for wave plans referencing other clients' migrations
        result = await session.execute(
            select(func.count(WavePlan.id))
            .join(Migration, WavePlan.migration_id == Migration.id)
            .join(Engagement, Migration.engagement_id == Engagement.id)
            .where(
                and_(
                    WavePlan.client_account_id == client_id,
                    Engagement.client_account_id != client_id
                )
            )
        )
        cross_client_wave_plans = result.scalar()
        
        if cross_client_wave_plans > 0:
            self._add_result(
                "migration_isolation_violation",
                client_id, client_name, False,
                f"Found {cross_client_wave_plans} wave plans referencing other clients' migrations",
                data_leak_count=cross_client_wave_plans
            )
        else:
            self._add_result(
                "migration_isolation",
                client_id, client_name, True,
                f"✅ Migration isolation intact: {client_migrations} migrations, {client_wave_plans} wave plans"
            )
    
    async def _test_cross_client_contamination(self, session: AsyncSession):
        """Test for any cross-client data contamination."""
        print("\n🔍 Testing Cross-Client Data Contamination")
        
        # Test 1: Assets referencing wrong client's engagements
        result = await session.execute(
            select(
                Asset.id.label('asset_id'),
                Asset.client_account_id.label('asset_client'),
                Engagement.client_account_id.label('engagement_client')
            )
            .join(Engagement, Asset.engagement_id == Engagement.id)
            .where(Asset.client_account_id != Engagement.client_account_id)
        )
        contaminated_assets = result.fetchall()
        
        if contaminated_assets:
            self._add_result(
                "cross_client_asset_contamination",
                0, "SYSTEM", False,
                f"Found {len(contaminated_assets)} assets with client/engagement mismatch",
                data_leak_count=len(contaminated_assets),
                details={"contaminated_assets": [dict(r._mapping) for r in contaminated_assets[:10]]}
            )
        else:
            self._add_result(
                "cross_client_asset_contamination",
                0, "SYSTEM", True,
                "✅ No cross-client asset contamination detected"
            )
        
        # Test 2: Discovery flows with client/engagement mismatch
        result = await session.execute(
            select(
                DiscoveryFlow.id.label('flow_id'),
                DiscoveryFlow.client_account_id.label('flow_client'),
                Engagement.client_account_id.label('engagement_client')
            )
            .join(Engagement, DiscoveryFlow.engagement_id == Engagement.id)
            .where(DiscoveryFlow.client_account_id != Engagement.client_account_id)
        )
        contaminated_flows = result.fetchall()
        
        if contaminated_flows:
            self._add_result(
                "cross_client_flow_contamination",
                0, "SYSTEM", False,
                f"Found {len(contaminated_flows)} discovery flows with client/engagement mismatch",
                data_leak_count=len(contaminated_flows)
            )
        else:
            self._add_result(
                "cross_client_flow_contamination",
                0, "SYSTEM", True,
                "✅ No cross-client discovery flow contamination detected"
            )
    
    async def _test_permission_boundaries(self, session: AsyncSession):
        """Test permission boundary enforcement."""
        print("\n🔍 Testing Permission Boundaries")
        
        # Test role distribution
        result = await session.execute(
            select(UserRole.role, func.count(UserRole.id))
            .group_by(UserRole.role)
        )
        role_distribution = dict(result.fetchall())
        
        expected_roles = ['system_admin', 'account_admin', 'engagement_manager', 'analyst']
        missing_roles = [role for role in expected_roles if role not in role_distribution]
        
        if missing_roles:
            self._add_result(
                "permission_role_coverage",
                0, "SYSTEM", False,
                f"Missing expected roles: {missing_roles}"
            )
        else:
            self._add_result(
                "permission_role_coverage",
                0, "SYSTEM", True,
                f"✅ All expected roles present: {list(role_distribution.keys())}"
            )
        
        # Test system admin isolation (should have access to all clients)
        result = await session.execute(
            select(User.id)
            .join(UserRole, User.id == UserRole.user_id)
            .where(UserRole.role == 'system_admin')
        )
        system_admin_users = [r[0] for r in result.fetchall()]
        
        for admin_id in system_admin_users:
            result = await session.execute(
                select(func.count(distinct(UserAccountAssociation.client_account_id)))
                .where(UserAccountAssociation.user_id == admin_id)
            )
            client_access_count = result.scalar()
            
            total_clients = len(self.client_accounts)
            if client_access_count != total_clients:
                self._add_result(
                    "system_admin_access",
                    admin_id, "SYSTEM_ADMIN", False,
                    f"System admin has access to {client_access_count}/{total_clients} clients"
                )
            else:
                self._add_result(
                    "system_admin_access",
                    admin_id, "SYSTEM_ADMIN", True,
                    f"✅ System admin has proper access to all {total_clients} clients"
                )
    
    def _add_result(self, test_name: str, client_id: int, client_name: str, 
                   passed: bool, message: str, data_leak_count: int = 0,
                   details: Optional[Dict[str, Any]] = None):
        """Add a test result."""
        result = IsolationTestResult(
            test_name=test_name,
            client_id=client_id,
            client_name=client_name,
            passed=passed,
            message=message,
            data_leak_count=data_leak_count,
            details=details
        )
        self.results.append(result)
        
        if self.verbose:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status}: {message}")
    
    def _generate_isolation_report(self) -> Dict[str, Any]:
        """Generate comprehensive isolation test report."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        total_data_leaks = sum(r.data_leak_count for r in self.results)
        
        # Group results by client
        client_results = {}
        system_results = []
        
        for result in self.results:
            if result.client_id == 0:
                system_results.append(result)
            else:
                if result.client_name not in client_results:
                    client_results[result.client_name] = []
                client_results[result.client_name].append(result)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "isolation_score": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
                "total_data_leaks": total_data_leaks,
                "clients_tested": len(self.client_accounts)
            },
            "client_results": {
                name: [
                    {
                        "test_name": r.test_name,
                        "passed": r.passed,
                        "message": r.message,
                        "data_leak_count": r.data_leak_count,
                        "details": r.details
                    }
                    for r in results
                ]
                for name, results in client_results.items()
            },
            "system_results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "message": r.message,
                    "data_leak_count": r.data_leak_count,
                    "details": r.details
                }
                for r in system_results
            ],
            "security_assessment": self._assess_security_posture(),
            "recommendations": self._generate_security_recommendations()
        }
        
        return report
    
    def _assess_security_posture(self) -> str:
        """Assess overall security posture based on test results."""
        failed_results = [r for r in self.results if not r.passed]
        total_data_leaks = sum(r.data_leak_count for r in self.results)
        
        if not failed_results:
            return "EXCELLENT - No isolation violations detected"
        elif total_data_leaks == 0:
            return "GOOD - Minor issues but no data leakage"
        elif total_data_leaks < 10:
            return "CONCERNING - Limited data leakage detected"
        else:
            return "CRITICAL - Significant data leakage detected"
    
    def _generate_security_recommendations(self) -> List[str]:
        """Generate security recommendations based on test results."""
        recommendations = []
        failed_results = [r for r in self.results if not r.passed]
        
        if any("contamination" in r.test_name for r in failed_results):
            recommendations.append("URGENT: Fix cross-client data contamination before deployment")
        
        if any("violation" in r.test_name for r in failed_results):
            recommendations.append("Review and fix data isolation violations")
        
        if any("permission" in r.test_name for r in failed_results):
            recommendations.append("Audit and correct user permission assignments")
        
        if any(r.data_leak_count > 0 for r in failed_results):
            recommendations.append("Investigate and remediate all data leakage incidents")
        
        if not failed_results:
            recommendations.append("Multi-tenant isolation is working correctly")
            recommendations.append("Continue regular isolation testing as part of CI/CD")
        
        return recommendations

def print_isolation_report(report: Dict[str, Any]):
    """Print formatted isolation test report."""
    print("\n" + "="*60)
    print("🏢 MULTI-TENANT ISOLATION TEST REPORT")
    print("="*60)
    
    summary = report['summary']
    print(f"📅 Generated: {report['timestamp']}")
    print(f"🔍 Total Tests: {summary['total_tests']}")
    print(f"✅ Passed: {summary['passed_tests']}")
    print(f"❌ Failed: {summary['failed_tests']}")
    print(f"🏆 Isolation Score: {summary['isolation_score']:.1f}%")
    print(f"🚨 Data Leaks: {summary['total_data_leaks']}")
    print(f"🏢 Clients Tested: {summary['clients_tested']}")
    
    # Security assessment
    print(f"\n🔒 SECURITY POSTURE: {report['security_assessment']}")
    
    # Failed tests
    if summary['failed_tests'] > 0:
        print("\n❌ FAILED TESTS:")
        print("-" * 40)
        
        for client_name, results in report['client_results'].items():
            failed_client_tests = [r for r in results if not r['passed']]
            if failed_client_tests:
                print(f"\n{client_name}:")
                for result in failed_client_tests:
                    print(f"  • {result['message']}")
                    if result['data_leak_count'] > 0:
                        print(f"    ⚠️ Data leaks: {result['data_leak_count']}")
        
        failed_system_tests = [r for r in report['system_results'] if not r['passed']]
        if failed_system_tests:
            print("\nSystem-wide:")
            for result in failed_system_tests:
                print(f"  • {result['message']}")
                if result['data_leak_count'] > 0:
                    print(f"    ⚠️ Data leaks: {result['data_leak_count']}")
    
    # Recommendations
    if report['recommendations']:
        print("\n💡 SECURITY RECOMMENDATIONS:")
        print("-" * 40)
        for i, rec in enumerate(report['recommendations'], 1):
            priority = "🚨 URGENT" if "URGENT" in rec else "⚠️"
            print(f"{i}. {priority} {rec}")
    
    # Overall status
    if summary['failed_tests'] == 0:
        print("\n🎉 ALL ISOLATION TESTS PASSED!")
        print("Multi-tenant security is working correctly.")
    else:
        print("\n⚠️ ISOLATION ISSUES DETECTED")
        print(f"Found {summary['failed_tests']} issues that need immediate attention.")

async def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description='Test multi-tenant isolation')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--client-id', '-c', type=int, help='Test specific client only')
    parser.add_argument('--export-report', '-e', help='Export report to JSON file')
    
    args = parser.parse_args()
    
    tester = MultiTenantIsolationTester(verbose=args.verbose)
    
    try:
        report = await tester.run_isolation_tests(args.client_id)
        
        if args.export_report:
            with open(args.export_report, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"📄 Report exported to {args.export_report}")
        
        print_isolation_report(report)
        
        # Exit with appropriate code based on security assessment
        if report['summary']['total_data_leaks'] > 0:
            sys.exit(2)  # Critical security issue
        elif report['summary']['failed_tests'] > 0:
            sys.exit(1)  # Non-critical issues
        else:
            sys.exit(0)  # All tests passed
            
    except Exception as e:
        print(f"❌ Isolation testing failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())