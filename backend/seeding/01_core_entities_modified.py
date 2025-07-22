"""
Seed core entities: Client Account, Engagement, Users, and RBAC setup.
Agent 2 Task 2.2 - Core entities seeding
"""
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.models.client_account import ClientAccount, Engagement, User, UserAccountAssociation
from app.models.rbac import AccessLevel, RoleType, UserRole, UserStatus
from seeding.constants import (
    BASE_TIMESTAMP,
    DEFAULT_PASSWORD,
    DEMO_CLIENT_ID,
    DEMO_COMPANY_DOMAIN,
    DEMO_COMPANY_NAME,
    DEMO_ENGAGEMENT_ID,
    USER_IDS,
    USERS,
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_client_account(db: AsyncSession) -> ClientAccount:
    """Create the demo client account."""
    print("Creating client account...")
    
    client = ClientAccount(
        id=DEMO_CLIENT_ID,
        name=DEMO_COMPANY_NAME,
        slug="democorp",
        description="Demo client account for testing and demonstration purposes",
        industry="Technology",
        company_size="1000-5000",
        headquarters_location="San Francisco, CA",
        primary_contact_name="John Smith",
        primary_contact_email="john.smith@democorp.com",
        primary_contact_phone="+1-555-123-4567",
        subscription_tier="enterprise",
        billing_contact_email="billing@democorp.com",
        settings={
            "notifications_enabled": True,
            "auto_discovery_enabled": True,
            "data_retention_days": 90
        },
        branding={
            "logo_url": "https://democorp.com/logo.png",
            "primary_color": "#0066CC",
            "secondary_color": "#F5F5F5"
        },
        business_objectives={
            "primary_goals": ["Cloud modernization", "Cost optimization", "Improved scalability"],
            "timeframe": "18 months",
            "success_metrics": ["50% reduction in infrastructure costs", "99.9% uptime"],
            "budget_constraints": "$2M for migration",
            "compliance_requirements": ["SOC2", "HIPAA"]
        },
        agent_preferences={
            "confidence_thresholds": {
                "field_mapping": 0.8,
                "data_classification": 0.75,
                "risk_assessment": 0.85,
                "migration_strategy": 0.9
            },
            "learning_preferences": ["conservative", "accuracy_focused"],
            "custom_prompts": {},
            "notification_preferences": {
                "confidence_alerts": True,
                "learning_updates": False,
                "error_notifications": True
            }
        },
        created_at=BASE_TIMESTAMP,
        is_active=True
    )
    
    db.add(client)
    await db.commit()
    await db.refresh(client)
    print(f"✓ Created client account: {client.name}")
    return client


async def create_engagement(db: AsyncSession, client_id: str) -> Engagement:
    """Create the demo engagement."""
    print("Creating engagement...")
    
    engagement = Engagement(
        id=DEMO_ENGAGEMENT_ID,
        client_account_id=client_id,
        name="Cloud Migration Assessment 2024",
        slug="cloud-migration-2024",
        description="Comprehensive cloud migration assessment and planning for DemoCorp's infrastructure",
        engagement_type="migration",
        status="active",
        priority="high",
        start_date=BASE_TIMESTAMP,
        target_completion_date=datetime(2024, 12, 31, tzinfo=timezone.utc),
        engagement_lead_id=USER_IDS["engagement_manager"],
        client_contact_name="Jane Doe",
        client_contact_email="jane.doe@democorp.com",
        migration_scope={
            "target_clouds": ["AWS", "Azure"],
            "migration_strategies": ["Rehost", "Replatform", "Refactor"],
            "excluded_systems": ["Legacy mainframe"],
            "included_environments": ["Production", "Staging", "Development"],
            "business_units": ["Engineering", "Marketing", "Sales"],
            "geographic_scope": ["North America", "Europe"],
            "timeline_constraints": {
                "freeze_periods": ["2024-11-15 to 2024-12-31"],
                "milestones": ["Q2 2024: Assessment", "Q3 2024: Planning", "Q4 2024: Pilot"]
            }
        },
        team_preferences={
            "stakeholders": ["CTO", "VP Engineering", "Cloud Architect"],
            "decision_makers": ["CTO", "CFO"],
            "technical_leads": ["Cloud Architect", "DevOps Lead"],
            "communication_style": "formal",
            "reporting_frequency": "weekly",
            "preferred_meeting_times": ["Tuesday 2PM PST", "Thursday 10AM PST"],
            "escalation_contacts": ["CTO", "VP Engineering"],
            "project_methodology": "agile"
        },
        created_at=BASE_TIMESTAMP,
        is_active=True
    )
    
    db.add(engagement)
    await db.commit()
    await db.refresh(engagement)
    print(f"✓ Created engagement: {engagement.name}")
    return engagement


async def create_users(db: AsyncSession) -> list[User]:
    """Create demo users with different roles."""
    print("Creating users...")
    
    created_users = []
    password_hash = pwd_context.hash(DEFAULT_PASSWORD)
    
    for user_data in USERS:
        # Create User
        user = User(
            id=user_data["id"],
            email=user_data["email"],
            password_hash=password_hash,
            first_name=user_data["full_name"].split()[0],
            last_name=user_data["full_name"].split()[-1] if len(user_data["full_name"].split()) > 1 else "",
            is_active=user_data["is_active"],
            is_verified=user_data["is_verified"],
            default_client_id=DEMO_CLIENT_ID,
            # Don't set default_engagement_id yet to avoid circular dependency
            created_at=BASE_TIMESTAMP
        )
        db.add(user)
        
        # Create UserRole
        role = UserRole(
            user_id=user_data["id"],
            role_type=user_data["role"],
            role_name=user_data["role"].replace("_", " ").title(),
            description=f"{user_data['role']} role for {DEMO_COMPANY_NAME}",
            permissions=get_role_permissions(user_data["role"]),
            scope_type="engagement",
            scope_client_id=DEMO_CLIENT_ID,
            scope_engagement_id=DEMO_ENGAGEMENT_ID,
            is_active=True,
            assigned_at=BASE_TIMESTAMP,
            assigned_by=USER_IDS["engagement_manager"],
            created_at=BASE_TIMESTAMP
        )
        db.add(role)
        
        # Skip ClientAccess - model expects user_profile_id but DB has user_id
        # and user_profiles table doesn't exist
        
        # Create UserAccountAssociation
        association = UserAccountAssociation(
            user_id=user_data["id"],
            client_account_id=DEMO_CLIENT_ID,
            role=user_data["role"],
            created_at=BASE_TIMESTAMP
        )
        db.add(association)
        
        created_users.append(user)
        print(f"✓ Created user: {user_data['email']} ({user_data['role']})")
    
    await db.commit()
    return created_users


def get_role_permissions(role_type: str) -> dict:
    """Get permissions based on role type."""
    base_permissions = {
        "can_create_clients": False,
        "can_manage_engagements": False,
        "can_import_data": False,
        "can_export_data": False,
        "can_view_analytics": True,
        "can_manage_users": False,
        "can_configure_agents": False,
        "can_access_admin_console": False
    }
    
    if role_type == "ENGAGEMENT_MANAGER":
        base_permissions.update({
            "can_manage_engagements": True,
            "can_import_data": True,
            "can_export_data": True,
            "can_manage_users": True,
            "can_configure_agents": True
        })
    elif role_type == "CLIENT_ADMIN":
        base_permissions.update({
            "can_create_clients": True,
            "can_manage_engagements": True,
            "can_import_data": True,
            "can_export_data": True,
            "can_manage_users": True,
            "can_access_admin_console": True
        })
    elif role_type == "ANALYST":
        base_permissions.update({
            "can_import_data": True,
            "can_export_data": True,
            "can_configure_agents": True
        })
    
    return base_permissions


def get_client_permissions(role_type: str) -> dict:
    """Get client-level permissions based on role type."""
    base_permissions = {
        "can_view_data": True,
        "can_import_data": False,
        "can_export_data": False,
        "can_manage_engagements": False,
        "can_configure_client_settings": False,
        "can_manage_client_users": False
    }
    
    if role_type in ["ENGAGEMENT_MANAGER", "CLIENT_ADMIN"]:
        base_permissions.update({
            "can_import_data": True,
            "can_export_data": True,
            "can_manage_engagements": True,
            "can_configure_client_settings": True,
            "can_manage_client_users": True
        })
    elif role_type == "ANALYST":
        base_permissions.update({
            "can_import_data": True,
            "can_export_data": True
        })
    
    return base_permissions


def get_engagement_permissions(role_type: str) -> dict:
    """Get engagement-level permissions based on role type."""
    base_permissions = {
        "can_view_data": True,
        "can_import_data": False,
        "can_export_data": False,
        "can_manage_sessions": False,
        "can_configure_agents": False,
        "can_approve_migration_decisions": False,
        "can_access_sensitive_data": False
    }
    
    if role_type == "ENGAGEMENT_MANAGER":
        return {key: True for key in base_permissions}  # All permissions
    elif role_type == "CLIENT_ADMIN":
        base_permissions.update({
            "can_import_data": True,
            "can_export_data": True,
            "can_manage_sessions": True,
            "can_configure_agents": True,
            "can_access_sensitive_data": True
        })
    elif role_type == "ANALYST":
        base_permissions.update({
            "can_import_data": True,
            "can_export_data": True,
            "can_manage_sessions": True,
            "can_configure_agents": True
        })
    
    return base_permissions


async def update_users_default_engagement(db: AsyncSession, engagement_id: str):
    """Update users with default engagement ID after engagement is created."""
    print("Updating users with default engagement...")
    
    # Update all users with the engagement ID
    result = await db.execute(
        select(User)
    )
    users = result.scalars().all()
    
    for user in users:
        user.default_engagement_id = engagement_id
    
    await db.commit()
    print(f"✓ Updated {len(users)} users with default engagement")


async def main():
    """Main seeding function."""
    print("\n=== Seeding Core Entities ===\n")
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if already seeded
            existing_client = await db.get(ClientAccount, DEMO_CLIENT_ID)
            if existing_client:
                print("⚠️  Core entities already seeded. Skipping...")
                return
            
            # Create entities
            client = await create_client_account(db)
            users = await create_users(db)  # Create users before engagement
            engagement = await create_engagement(db, client.id)
            await update_users_default_engagement(db, engagement.id)  # Update users after engagement
            
            print("\n✅ Successfully seeded core entities:")
            print(f"   - 1 Client Account: {client.name}")
            print(f"   - 1 Engagement: {engagement.name}")
            print(f"   - {len(users)} Users with RBAC setup")
            
        except Exception as e:
            print(f"\n❌ Error seeding core entities: {str(e)}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())