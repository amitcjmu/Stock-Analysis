#!/usr/bin/env python3
"""
Simplified Database Validation

Quick validation of seeded data that works with the actual database structure.
"""

import asyncio
import sys
from typing import Any, Dict

sys.path.append('/app')

from sqlalchemy import text

from app.core.database import AsyncSessionLocal


async def run_simple_validation() -> Dict[str, Any]:
    """Run simplified validation checks."""
    print("🔍 Running Simplified Database Validation")
    print("=" * 50)

    results = {}

    async with AsyncSessionLocal() as session:
        # Basic record counts
        print("📊 Checking Record Counts...")

        counts = {}
        tables = [
            'client_accounts', 'engagements', 'users', 'user_roles',
            'assets', 'discovery_flows', 'data_imports', 'assessments'
        ]

        for table in tables:
            result = await session.execute(text(f"SELECT COUNT(*) FROM migration.{table}"))
            count = result.scalar()
            counts[table] = count
            print(f"  {table}: {count}")

        results['record_counts'] = counts

        # Data quality checks
        print("\n🔍 Checking Data Quality...")

        # Check for required fields
        checks = {}

        # Client accounts with names
        result = await session.execute(text("""
            SELECT COUNT(*) FROM migration.client_accounts
            WHERE name IS NOT NULL AND name != ''
        """))
        checks['client_accounts_with_names'] = result.scalar()

        # Users with emails
        result = await session.execute(text("""
            SELECT COUNT(*) FROM migration.users
            WHERE email IS NOT NULL AND email != ''
        """))
        checks['users_with_emails'] = result.scalar()

        # Assets with names
        result = await session.execute(text("""
            SELECT COUNT(*) FROM migration.assets
            WHERE name IS NOT NULL AND name != ''
        """))
        checks['assets_with_names'] = result.scalar()

        results['data_quality'] = checks

        for check, count in checks.items():
            print(f"  {check}: {count}")

        # Asset type distribution
        print("\n📊 Asset Type Distribution...")
        result = await session.execute(text("""
            SELECT asset_type, COUNT(*)
            FROM migration.assets
            GROUP BY asset_type
            ORDER BY COUNT(*) DESC
        """))
        asset_types = dict(result.fetchall())
        results['asset_types'] = asset_types

        for asset_type, count in asset_types.items():
            print(f"  {asset_type}: {count}")

        # User roles
        print("\n👥 User Role Distribution...")
        result = await session.execute(text("""
            SELECT role_name, COUNT(*)
            FROM migration.user_roles
            GROUP BY role_name
            ORDER BY COUNT(*) DESC
        """))
        roles = dict(result.fetchall())
        results['user_roles'] = roles

        for role, count in roles.items():
            print(f"  {role}: {count}")

        # Discovery flow phases
        print("\n🔄 Discovery Flow Phases...")
        result = await session.execute(text("""
            SELECT current_phase, COUNT(*)
            FROM migration.discovery_flows
            GROUP BY current_phase
            ORDER BY COUNT(*) DESC
        """))
        phases = dict(result.fetchall())
        results['discovery_phases'] = phases

        for phase, count in phases.items():
            print(f"  {phase}: {count}")

        # Relationship integrity check
        print("\n🔗 Relationship Integrity...")

        # Assets with valid client accounts
        result = await session.execute(text("""
            SELECT COUNT(*) FROM migration.assets a
            JOIN migration.client_accounts ca ON a.client_account_id = ca.id
        """))
        valid_asset_clients = result.scalar()

        # Assets with valid engagements
        result = await session.execute(text("""
            SELECT COUNT(*) FROM migration.assets a
            JOIN migration.engagements e ON a.engagement_id = e.id
        """))
        valid_asset_engagements = result.scalar()

        # Users with roles
        result = await session.execute(text("""
            SELECT COUNT(DISTINCT u.id) FROM migration.users u
            JOIN migration.user_roles ur ON u.id = ur.user_id
        """))
        users_with_roles = result.scalar()

        integrity_checks = {
            'assets_with_valid_clients': valid_asset_clients,
            'assets_with_valid_engagements': valid_asset_engagements,
            'users_with_roles': users_with_roles
        }

        results['integrity_checks'] = integrity_checks

        for check, count in integrity_checks.items():
            print(f"  {check}: {count}")

    return results

def assess_validation_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Assess validation results and provide summary."""

    counts = results['record_counts']
    quality = results['data_quality']
    integrity = results['integrity_checks']

    # Calculate scores
    issues = []
    warnings = []

    # Check if we have basic data
    if counts['client_accounts'] == 0:
        issues.append("No client accounts found")
    if counts['users'] == 0:
        issues.append("No users found")
    if counts['assets'] == 0:
        issues.append("No assets found")

    # Check data quality
    if quality['client_accounts_with_names'] != counts['client_accounts']:
        issues.append("Some client accounts missing names")
    if quality['users_with_emails'] != counts['users']:
        issues.append("Some users missing emails")
    if quality['assets_with_names'] != counts['assets']:
        warnings.append("Some assets missing names")

    # Check relationships
    if integrity['assets_with_valid_clients'] != counts['assets']:
        issues.append("Some assets have invalid client references")
    if integrity['assets_with_valid_engagements'] != counts['assets']:
        issues.append("Some assets have invalid engagement references")
    if integrity['users_with_roles'] != counts['users']:
        warnings.append("Some users don't have roles assigned")

    # Overall assessment
    if len(issues) == 0:
        status = "EXCELLENT - All validations passed"
        demo_ready = True
    elif len(issues) <= 2 and len(warnings) <= 3:
        status = "GOOD - Minor issues detected"
        demo_ready = True
    else:
        status = "POOR - Multiple issues detected"
        demo_ready = False

    # Demo scenario assessment
    demo_scenarios = {
        'basic_login': counts['users'] >= 2,
        'asset_inventory': counts['assets'] >= 20,
        'discovery_flows': counts['discovery_flows'] >= 1,
        'multi_user_roles': len(results['user_roles']) >= 2,
        'asset_diversity': len(results['asset_types']) >= 3
    }

    return {
        'overall_status': status,
        'demo_ready': demo_ready,
        'total_issues': len(issues),
        'total_warnings': len(warnings),
        'issues': issues,
        'warnings': warnings,
        'demo_scenarios': demo_scenarios,
        'demo_scenario_score': sum(demo_scenarios.values()) / len(demo_scenarios) * 100
    }

async def main():
    """Main validation execution."""
    try:
        results = await run_simple_validation()
        assessment = assess_validation_results(results)

        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)

        print(f"🎯 Status: {assessment['overall_status']}")
        print(f"🚀 Demo Ready: {'YES' if assessment['demo_ready'] else 'NO'}")
        print(f"❌ Issues: {assessment['total_issues']}")
        print(f"⚠️ Warnings: {assessment['total_warnings']}")
        print(f"📈 Demo Scenario Score: {assessment['demo_scenario_score']:.1f}%")

        if assessment['issues']:
            print("\n❌ CRITICAL ISSUES:")
            for issue in assessment['issues']:
                print(f"  • {issue}")

        if assessment['warnings']:
            print("\n⚠️ WARNINGS:")
            for warning in assessment['warnings']:
                print(f"  • {warning}")

        print("\n🎯 DEMO SCENARIOS:")
        for scenario, ready in assessment['demo_scenarios'].items():
            status = "✅" if ready else "❌"
            print(f"  {status} {scenario.replace('_', ' ').title()}")

        # Data summary
        counts = results['record_counts']
        print("\n📊 DATA SUMMARY:")
        print(f"  • Client Accounts: {counts['client_accounts']}")
        print(f"  • Users: {counts['users']} ({len(results['user_roles'])} roles)")
        print(f"  • Assets: {counts['assets']} ({len(results['asset_types'])} types)")
        print(f"  • Discovery Flows: {counts['discovery_flows']}")
        print(f"  • Engagements: {counts['engagements']}")
        print(f"  • Assessments: {counts['assessments']}")

        if assessment['demo_ready']:
            print("\n🎉 DATABASE VALIDATION SUCCESSFUL!")
            print("The platform is ready for demonstration.")
            return 0
        else:
            print("\n⚠️ VALIDATION ISSUES DETECTED")
            print("Address critical issues before demo.")
            return 1

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
