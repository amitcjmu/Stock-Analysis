"""
Tenant management operations for demo data seeding.
Handles creation and verification of demo tenant data.
"""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ClientAccount,
    Engagement,
    User,
    UserRole,
    UserAccountAssociation,
)
from .base import BaseDemoSeeder


class TenantManager(BaseDemoSeeder):
    """Manages demo tenant creation and verification"""

    async def ensure_demo_tenant_exists(self, db: AsyncSession) -> bool:
        """Ensure demo tenant (client account, engagement, user) exists"""
        print("🏢 Ensuring demo tenant exists...")

        # Check if client account exists
        client = await db.get(ClientAccount, self.demo_client_id)
        if not client:
            print("  Creating demo client account...")
            client = ClientAccount(
                id=self.demo_client_id,
                name="Demo Corporation",
                slug="demo-corp",
                description="Demo client for structured data seeding",
                industry="Technology",
                company_size="1000-5000",
                headquarters_location="San Francisco, CA",
                primary_contact_name="Demo Admin",
                primary_contact_email="admin@demo-corp.com",
                contact_phone="+1-555-DEMO",
            )
            db.add(client)

        # Check if engagement exists
        engagement = await db.get(Engagement, self.demo_engagement_id)
        if not engagement:
            print("  Creating demo engagement...")
            engagement = Engagement(
                id=self.demo_engagement_id,
                client_account_id=self.demo_client_id,
                name="Cloud Migration Assessment Demo",
                slug="migration-demo",
                description="Demonstration engagement for structured seeding",
                status="active",
                engagement_type="migration",
                start_date=datetime.now(timezone.utc),
            )
            db.add(engagement)

        # Check if user exists
        user = await db.get(User, self.demo_user_id)
        if not user:
            print("  Creating demo user...")
            user = User(
                id=self.demo_user_id,
                email="demo@demo-corp.com",
                first_name="Demo",
                last_name="User",
                password_hash="hashed_demo_password",  # In real deployment, use proper hashing
                is_active=True,
                is_verified=True,
                default_client_id=self.demo_client_id,
                default_engagement_id=self.demo_engagement_id,
            )
            db.add(user)

            # Create user role
            user_role = UserRole(
                user_id=self.demo_user_id,
                client_account_id=self.demo_client_id,
                engagement_id=self.demo_engagement_id,
                role="engagement_manager",
            )
            db.add(user_role)

            # Create user-client association
            association = UserAccountAssociation(
                user_id=self.demo_user_id,
                client_account_id=self.demo_client_id,
                role="engagement_manager",
            )
            db.add(association)

        await db.commit()
        print("✅ Demo tenant ensured")
        return True
