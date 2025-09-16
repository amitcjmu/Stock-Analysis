"""
Demo client and engagement setup.

This module handles creation and cleanup of demo client accounts and engagements.
"""

import uuid
import logging
from datetime import datetime, timezone
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClientAccount, Engagement
from ..base import PlatformRequirements

logger = logging.getLogger(__name__)


class DemoClientSetup:
    """Manages demo client and engagement creation"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.requirements = PlatformRequirements()

    async def create_demo_client(self) -> ClientAccount:
        """Create or recreate demo client with proper cleanup"""
        # Check if a client with the same name or slug exists
        existing = await self.db.execute(
            select(ClientAccount).where(
                (ClientAccount.name == self.requirements.DEMO_CLIENT_NAME)
                | (ClientAccount.slug == "demo-corp")
            )
        )
        existing_client = existing.scalar_one_or_none()

        if existing_client:
            # Delete the existing client with wrong ID
            logger.info(
                f"Removing existing demo client with wrong ID: {existing_client.id}"
            )
            await self._cleanup_existing_client(existing_client.id)

        # Create demo client with fixed UUID for frontend fallback
        client_id = self.requirements.DEMO_CLIENT_ID
        client = ClientAccount(
            id=client_id,
            name=self.requirements.DEMO_CLIENT_NAME,
            slug="demo-corp",
            description="Demo client for platform testing",
            industry="Technology",
            company_size="100-500",
            headquarters_location="Demo City, USA",
            primary_contact_name="Demo Contact",
            primary_contact_email="contact@demo-corp.com",
            contact_phone="+1-555-0000",
        )
        self.db.add(client)
        await self.db.flush()
        logger.info(f"Created demo client: {client.name}")
        return client

    async def create_demo_engagement(self, client_id: uuid.UUID) -> Engagement:
        """Create demo engagement with fixed UUID"""
        engagement_id = self.requirements.DEMO_ENGAGEMENT_ID
        engagement = Engagement(
            id=engagement_id,
            client_account_id=client_id,
            name=self.requirements.DEMO_ENGAGEMENT_NAME,
            slug="demo-cloud-migration",
            description="Demo engagement for testing",
            status="active",
            engagement_type="migration",
            start_date=datetime.now(timezone.utc),
            target_completion_date=datetime(2025, 12, 31, tzinfo=timezone.utc),
        )
        self.db.add(engagement)
        await self.db.flush()
        logger.info(f"Created demo engagement: {engagement.name}")
        return engagement

    async def _cleanup_existing_client(self, client_id: uuid.UUID):
        """Clean up existing client data to prevent conflicts"""
        # First clear user default references
        await self.db.execute(
            text(
                "UPDATE users SET default_engagement_id = NULL "
                "WHERE default_engagement_id IN "
                "(SELECT id FROM engagements WHERE client_account_id = :client_id)"
            ),
            {"client_id": client_id},
        )
        await self.db.execute(
            text(
                "UPDATE users SET default_client_id = NULL WHERE default_client_id = :client_id"
            ),
            {"client_id": client_id},
        )

        # Then delete all references
        cleanup_queries = [
            "DELETE FROM engagement_access WHERE engagement_id IN "
            "(SELECT id FROM engagements WHERE client_account_id = :client_id)",
            "DELETE FROM client_access WHERE client_account_id = :client_id",
            "DELETE FROM user_roles WHERE scope_engagement_id IN "
            "(SELECT id FROM engagements WHERE client_account_id = :client_id)",
            "DELETE FROM user_roles WHERE scope_client_id = :client_id",
            "DELETE FROM user_account_associations WHERE client_account_id = :client_id",
            "DELETE FROM engagements WHERE client_account_id = :client_id",
            "DELETE FROM client_accounts WHERE id = :client_id",
        ]

        for query in cleanup_queries:
            await self.db.execute(text(query), {"client_id": client_id})

        await self.db.commit()

    async def verify_demo_client_exists(self) -> bool:
        """Verify demo client exists with correct configuration"""
        client = await self.db.get(ClientAccount, self.requirements.DEMO_CLIENT_ID)
        return client is not None and client.name == self.requirements.DEMO_CLIENT_NAME

    async def verify_demo_engagement_exists(self) -> bool:
        """Verify demo engagement exists with correct configuration"""
        engagement = await self.db.get(Engagement, self.requirements.DEMO_ENGAGEMENT_ID)
        return (
            engagement is not None
            and engagement.name == self.requirements.DEMO_ENGAGEMENT_NAME
            and engagement.client_account_id == self.requirements.DEMO_CLIENT_ID
        )

    async def get_demo_client_info(self) -> dict:
        """Get demo client information for reporting"""
        client = await self.db.get(ClientAccount, self.requirements.DEMO_CLIENT_ID)
        engagement = await self.db.get(Engagement, self.requirements.DEMO_ENGAGEMENT_ID)

        return {
            "client_exists": client is not None,
            "client_name": client.name if client else None,
            "engagement_exists": engagement is not None,
            "engagement_name": engagement.name if engagement else None,
            "fixed_client_id": str(self.requirements.DEMO_CLIENT_ID),
            "fixed_engagement_id": str(self.requirements.DEMO_ENGAGEMENT_ID),
        }
