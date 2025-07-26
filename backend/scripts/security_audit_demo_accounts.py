#!/usr/bin/env python3
"""
Security Audit Script for Demo Accounts
Detects and prevents unauthorized demo/admin account creation.
"""

import asyncio
import sys
from datetime import datetime
from typing import Any, Dict, List

sys.path.append("/app")

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.client_account import User
from app.models.rbac import UserRole

# SECURITY: Whitelist of legitimate accounts
LEGITIMATE_ACCOUNTS = {
    "chocka@gmail.com": "platform_admin",  # Legitimate platform admin
    "demo@democorp.com": "analyst",  # Legitimate demo user (analyst only)
}

# SECURITY: Blacklist of prohibited demo accounts
PROHIBITED_DEMO_ACCOUNTS = [
    "admin@democorp.com",
    "admin@aiforce.com",
    "admin@demo.com",
    "demo@aiforce.com",
    "test@demo.com",
    "admin@test.com",
]


async def audit_demo_accounts() -> Dict[str, Any]:
    """
    Comprehensive security audit of demo accounts.
    Returns security report with violations and recommendations.
    """
    print("🔍 SECURITY AUDIT: Demo Account Analysis")
    print("=" * 50)

    violations = []
    warnings = []
    secure_accounts = []

    async with AsyncSessionLocal() as db:
        try:
            # Get all users with their roles
            query = select(User, UserRole).outerjoin(
                UserRole, User.id == UserRole.user_id
            )
            result = await db.execute(query)
            users_with_roles = result.all()

            for user, role in users_with_roles:
                if not user:
                    continue

                email = user.email
                role_type = role.role_type if role else "no_role"
                is_active = user.is_active and (role.is_active if role else False)

                # Check for prohibited demo accounts
                if email in PROHIBITED_DEMO_ACCOUNTS:
                    violations.append(
                        {
                            "type": "PROHIBITED_DEMO_ACCOUNT",
                            "email": email,
                            "role": role_type,
                            "active": is_active,
                            "severity": "CRITICAL",
                            "action": "IMMEDIATE_DISABLE",
                        }
                    )

                # Check for unauthorized admin accounts
                elif (
                    email.startswith(("admin@", "demo@"))
                    and email not in LEGITIMATE_ACCOUNTS
                ):
                    violations.append(
                        {
                            "type": "UNAUTHORIZED_DEMO_ADMIN",
                            "email": email,
                            "role": role_type,
                            "active": is_active,
                            "severity": "HIGH",
                            "action": "DISABLE_AND_INVESTIGATE",
                        }
                    )

                # Check for legitimate accounts with wrong roles
                elif email in LEGITIMATE_ACCOUNTS:
                    expected_role = LEGITIMATE_ACCOUNTS[email]
                    if role_type != expected_role:
                        warnings.append(
                            {
                                "type": "ROLE_MISMATCH",
                                "email": email,
                                "expected_role": expected_role,
                                "actual_role": role_type,
                                "severity": "MEDIUM",
                                "action": "VERIFY_ROLE",
                            }
                        )
                    else:
                        secure_accounts.append(
                            {"email": email, "role": role_type, "status": "LEGITIMATE"}
                        )

                # Check for suspicious patterns
                elif "@demo" in email or "@test" in email:
                    warnings.append(
                        {
                            "type": "SUSPICIOUS_DEMO_PATTERN",
                            "email": email,
                            "role": role_type,
                            "active": is_active,
                            "severity": "LOW",
                            "action": "REVIEW",
                        }
                    )

            return {
                "audit_timestamp": datetime.utcnow().isoformat(),
                "total_users": len(users_with_roles),
                "violations": violations,
                "warnings": warnings,
                "secure_accounts": secure_accounts,
                "security_score": calculate_security_score(violations, warnings),
                "recommendations": generate_recommendations(violations, warnings),
            }

        except Exception as e:
            print(f"❌ Audit failed: {e}")
            return {"error": str(e)}


def calculate_security_score(
    violations: List[Dict], warnings: List[Dict]
) -> Dict[str, Any]:
    """Calculate security score based on violations and warnings."""
    critical_count = len([v for v in violations if v.get("severity") == "CRITICAL"])
    high_count = len([v for v in violations if v.get("severity") == "HIGH"])
    medium_count = len([w for w in warnings if w.get("severity") == "MEDIUM"])

    # Calculate score (100 = perfect, 0 = critical violations)
    score = 100
    score -= critical_count * 50  # Critical violations: -50 points each
    score -= high_count * 25  # High violations: -25 points each
    score -= medium_count * 10  # Medium warnings: -10 points each
    score = max(0, score)  # Minimum score is 0

    if score >= 90:
        status = "EXCELLENT"
    elif score >= 70:
        status = "GOOD"
    elif score >= 50:
        status = "NEEDS_IMPROVEMENT"
    else:
        status = "CRITICAL_ISSUES"

    return {
        "score": score,
        "status": status,
        "critical_violations": critical_count,
        "high_violations": high_count,
        "medium_warnings": medium_count,
    }


def generate_recommendations(violations: List[Dict], warnings: List[Dict]) -> List[str]:
    """Generate security recommendations based on audit results."""
    recommendations = []

    if violations:
        recommendations.append(
            "🚨 IMMEDIATE ACTION: Disable all unauthorized demo accounts"
        )
        recommendations.append("🔒 SECURITY: Remove admin privileges from demo accounts")
        recommendations.append(
            "📋 AUDIT: Investigate how unauthorized accounts were created"
        )

    if warnings:
        recommendations.append(
            "⚠️  REVIEW: Verify role assignments for flagged accounts"
        )
        recommendations.append(
            "🔍 MONITOR: Set up automated monitoring for demo account creation"
        )

    recommendations.extend(
        [
            "🛡️  PREVENTION: Implement code guards to prevent unauthorized demo account creation",
            "📝 POLICY: Establish clear demo account creation policies",
            "🔄 REGULAR: Schedule regular security audits of user accounts",
            "🚫 RESTRICTION: Limit demo account creation to authorized personnel only",
        ]
    )

    return recommendations


async def auto_remediate_violations(violations: List[Dict]) -> Dict[str, Any]:
    """
    Automatically remediate critical security violations.
    ONLY disables accounts - does not delete for audit trail.
    """
    print("\n🔧 AUTO-REMEDIATION: Disabling unauthorized accounts")

    remediated = []
    failed = []

    async with AsyncSessionLocal() as db:
        try:
            for violation in violations:
                if violation["severity"] in ["CRITICAL", "HIGH"]:
                    email = violation["email"]

                    try:
                        # Disable the user account
                        user_query = select(User).where(User.email == email)
                        result = await db.execute(user_query)
                        user = result.scalar_one_or_none()

                        if user:
                            # Disable user
                            user.is_active = False
                            user.is_verified = False
                            user.email = (
                                f"DISABLED_{email}_{int(datetime.utcnow().timestamp())}"
                            )
                            user.password_hash = "DISABLED_SECURITY_VIOLATION"

                            # Disable all roles
                            role_query = select(UserRole).where(
                                UserRole.user_id == user.id
                            )
                            role_result = await db.execute(role_query)
                            roles = role_result.scalars().all()

                            for role in roles:
                                role.is_active = False
                                role.role_type = "disabled"

                            remediated.append(
                                {
                                    "email": email,
                                    "action": "DISABLED",
                                    "timestamp": datetime.utcnow().isoformat(),
                                }
                            )

                    except Exception as e:
                        failed.append({"email": email, "error": str(e)})

            await db.commit()

            return {
                "remediated": remediated,
                "failed": failed,
                "total_processed": len(remediated) + len(failed),
            }

        except Exception as e:
            await db.rollback()
            return {"error": str(e)}


async def main():
    """Main security audit function."""
    print("🛡️  AI Modernize Migration Platform - Demo Account Security Audit")
    print("=" * 60)

    # Run security audit
    audit_results = await audit_demo_accounts()

    if "error" in audit_results:
        print(f"❌ Audit failed: {audit_results['error']}")
        return

    # Display results
    print("\n📊 SECURITY AUDIT RESULTS")
    print(f"Audit Time: {audit_results['audit_timestamp']}")
    print(f"Total Users: {audit_results['total_users']}")
    print(
        f"Security Score: {audit_results['security_score']['score']}/100 ({audit_results['security_score']['status']})"
    )

    # Show violations
    if audit_results["violations"]:
        print(f"\n🚨 SECURITY VIOLATIONS ({len(audit_results['violations'])})")
        for violation in audit_results["violations"]:
            print(
                f"  - {violation['type']}: {violation['email']} ({violation['severity']})"
            )

    # Show warnings
    if audit_results["warnings"]:
        print(f"\n⚠️  WARNINGS ({len(audit_results['warnings'])})")
        for warning in audit_results["warnings"]:
            print(f"  - {warning['type']}: {warning['email']} ({warning['severity']})")

    # Show secure accounts
    if audit_results["secure_accounts"]:
        print(f"\n✅ SECURE ACCOUNTS ({len(audit_results['secure_accounts'])})")
        for account in audit_results["secure_accounts"]:
            print(f"  - {account['email']}: {account['role']} ({account['status']})")

    # Auto-remediate if violations found
    if audit_results["violations"]:
        print("\n🔧 STARTING AUTO-REMEDIATION...")
        remediation_results = await auto_remediate_violations(
            audit_results["violations"]
        )

        if "error" not in remediation_results:
            print(f"✅ Remediated {len(remediation_results['remediated'])} violations")
            if remediation_results["failed"]:
                print(
                    f"❌ Failed to remediate {len(remediation_results['failed'])} accounts"
                )

    # Show recommendations
    print("\n📋 SECURITY RECOMMENDATIONS")
    for i, rec in enumerate(audit_results["recommendations"], 1):
        print(f"  {i}. {rec}")

    print("\n🔒 Security audit complete!")


if __name__ == "__main__":
    asyncio.run(main())
