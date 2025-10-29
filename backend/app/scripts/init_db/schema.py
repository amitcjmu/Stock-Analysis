"""
Database schema creation functions for initialization.
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset, AssetStatus, MigrationWave
from app.models.client_account import (
    ClientAccount,
    Engagement,
    User,
    UserAccountAssociation,
)
from app.models.rbac import (
    AccessLevel,
    ClientAccess,
    EngagementAccess,
    RoleType,
    UserProfile,
    UserRole,
    UserStatus,
)

# REMOVED: app.models.sixr_analysis
# Use Assessment Flow (Phase 4, Issue #840)
from app.models.tags import AssetEmbedding, AssetTag, Tag

try:
    # Try relative imports first (when used as module)
    from .base import (
        DEMO_CLIENT_ID,
        DEMO_ENGAGEMENT_ID,
        DEMO_USER_ID,
        generate_mock_embedding,
        logger,
    )
    from .seed_data import MOCK_DATA
except ImportError:
    # Fall back to absolute imports (when used as script)
    from base import (
        DEMO_CLIENT_ID,
        DEMO_ENGAGEMENT_ID,
        DEMO_USER_ID,
        generate_mock_embedding,
        logger,
    )
    from seed_data import MOCK_DATA


async def create_mock_client_account(session: AsyncSession) -> uuid.UUID:
    """Creates mock client account if it doesn't exist."""
    client_data = MOCK_DATA["client_accounts"][0]
    client = ClientAccount(id=DEMO_CLIENT_ID, **client_data)
    await session.merge(client)  # Use merge to handle potential pre-existence
    await session.flush()
    logger.info(f"Created mock client account: {client.name}")
    return client.id


async def create_mock_users(
    session: AsyncSession, client_account_id: uuid.UUID
) -> Dict[str, uuid.UUID]:
    """Creates mock users, profiles, roles, and access records."""
    logger.info("Creating mock users, profiles, and roles...")
    user_ids = {}

    for user_data in MOCK_DATA["users"]:
        # Check if user already exists
        existing_user_result = await session.execute(
            select(User).where(User.email == user_data["email"])
        )
        existing_user = existing_user_result.scalars().first()

        if existing_user:
            logger.info(
                f"User {user_data['email']} already exists, skipping creation but fetching ID."
            )
            user_ids[user_data["email"]] = existing_user.id
            # Even if user exists, ensure profile and roles are there for idempotency
            # This is a simplified approach for a seeding script.
            # A more robust implementation would check and update if necessary.
        else:
            # Hash password
            hashed_password = bcrypt.hashpw(
                user_data["password"].encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            # Create user (only demo user, no admin accounts)
            user = User(
                id=DEMO_USER_ID,  # Only demo user, no admin constant needed
                email=user_data["email"],
                password_hash=hashed_password,
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                is_active=True,
                is_verified=user_data.get("is_verified", True),
            )
            session.add(user)
            await session.flush()
            user_id = user.id
            user_ids[user_data["email"]] = user_id
            logger.info(f"Created user: {user.email} with ID: {user_id}")

            # Associate user with client account (demo user only - no admin)
            user_account_association = UserAccountAssociation(
                user_id=user.id,
                client_account_id=client_account_id,
                role="User",  # Demo user gets standard user role, not admin
            )
            session.add(user_account_association)
            logger.info(
                f"Associated {user.email} with client account {client_account_id}"
            )

    # Commit users first to ensure they have IDs before creating dependent objects
    try:
        await session.commit()
    except Exception as e:
        logger.error(f"Error committing initial users: {e}")
        await session.rollback()
        raise

    # Now create profiles and roles for all users
    for email, user_id in user_ids.items():
        # Check for existing profile
        existing_profile_result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        if existing_profile_result.scalars().first():
            logger.info(f"User profile for {email} already exists.")
        else:
            # Only demo user profile creation (no admin profiles)
            user_profile = UserProfile(
                user_id=user_id,
                status=UserStatus.ACTIVE,
                organization="Demo Corporation",
                role_description="Demo User",  # Demo user only, no admin
                requested_access_level=AccessLevel.READ_WRITE,  # Standard access, no admin
                approved_at=datetime.utcnow(),
                approved_by=user_ids.get(
                    "demo@democorp.com", DEMO_USER_ID
                ),  # Self-approved by demo user
            )
            session.add(user_profile)
            logger.info(f"Created user profile for {email}")

        # Check for existing role
        existing_role_result = await session.execute(
            select(UserRole).where(UserRole.user_id == user_id)
        )
        if existing_role_result.scalars().first():
            logger.info(f"User role for {email} already exists.")
        else:
            # Only demo user role creation (analyst level, no admin)
            role_type = RoleType.ANALYST  # Demo user gets analyst role only
            user_role = UserRole(
                user_id=user_id,
                role_type=role_type.value,
                role_name=role_type.name.replace("_", " ").title(),
                description=f"{role_type.name.replace('_', ' ').title()} for Demo Corporation",
                scope_type="client",
                scope_client_id=client_account_id,
                assigned_by=user_ids.get("demo@democorp.com", DEMO_USER_ID),
                is_active=True,
            )
            session.add(user_role)
            logger.info(f"Assigned role '{role_type.name}' to {email}")

        # Check for existing client access
        existing_access_result = await session.execute(
            select(ClientAccess).where(
                ClientAccess.user_profile_id == user_id,
                ClientAccess.client_account_id == client_account_id,
            )
        )
        if existing_access_result.scalars().first():
            logger.info(f"Client access for {email} already exists.")
        else:
            # Only demo user client access (standard level, no admin)
            client_access = ClientAccess(
                user_profile_id=user_id,
                client_account_id=client_account_id,
                access_level=AccessLevel.READ_WRITE,  # Standard access only, no admin
                granted_by=user_ids.get("demo@democorp.com", DEMO_USER_ID),
            )
            session.add(client_access)
            logger.info(f"Granted client access to {email}")

    try:
        await session.commit()
        logger.info("Successfully created/verified mock users, profiles, and roles.")
    except Exception as e:
        logger.error(f"Error committing users and profiles: {e}")
        await session.rollback()
        raise

    return user_ids


async def create_mock_engagement(
    session: AsyncSession, client_account_id: uuid.UUID, user_ids: Dict[str, uuid.UUID]
) -> uuid.UUID:
    """Creates a mock engagement and grants access to users."""
    logger.info("Creating mock engagement...")
    engagement_data = MOCK_DATA["engagements"][0]

    # Check if engagement already exists
    existing_engagement_result = await session.execute(
        select(Engagement).where(
            Engagement.slug == engagement_data["slug"],
            Engagement.client_account_id == client_account_id,
        )
    )
    existing_engagement = existing_engagement_result.scalars().first()

    if existing_engagement:
        logger.info(f"Engagement '{engagement_data['name']}' already exists.")
        engagement_id = existing_engagement.id
    else:
        engagement = Engagement(
            id=DEMO_ENGAGEMENT_ID,
            client_account_id=client_account_id,
            name=engagement_data["name"],
            slug=engagement_data["slug"],
            description=engagement_data["description"],
            engagement_type=engagement_data["engagement_type"],
            status=engagement_data["status"],
            priority=engagement_data["priority"],
            start_date=datetime.utcnow() - timedelta(days=30),
            target_completion_date=datetime.utcnow() + timedelta(days=120),
            client_contact_name=engagement_data["client_contact_name"],
            client_contact_email=engagement_data["client_contact_email"],
            created_by=user_ids["demo@democorp.com"],
        )
        session.add(engagement)
        await session.flush()
        engagement_id = engagement.id
        logger.info(f"Created engagement: {engagement.name}")
        await session.commit()

    # Grant engagement access to all created users
    for email, user_id in user_ids.items():
        existing_access_result = await session.execute(
            select(EngagementAccess).where(
                EngagementAccess.user_profile_id == user_id,
                EngagementAccess.engagement_id == engagement_id,
            )
        )
        if existing_access_result.scalars().first():
            logger.info(f"Engagement access for {email} already exists.")
            continue

        # Only demo user engagement access (analyst level, no admin)
        engagement_access = EngagementAccess(
            user_profile_id=user_id,
            engagement_id=engagement_id,
            access_level=AccessLevel.READ_WRITE,  # Standard access only, no admin
            engagement_role="Analyst",  # Demo user gets analyst role only
            granted_by=user_ids["demo@democorp.com"],
        )
        session.add(engagement_access)
        logger.info(f"Granted engagement access to {email}")

    try:
        await session.commit()
    except Exception as e:
        logger.error(f"Error granting engagement access: {e}")
        await session.rollback()
        raise

    return engagement_id


async def create_mock_tags(
    session: AsyncSession, client_account_id: uuid.UUID
) -> Dict[str, uuid.UUID]:
    """Creates mock tags based on predefined list."""
    tag_ids = {}
    for tag_data in MOCK_DATA["tags"]:
        # Check if tag exists for this client to ensure idempotency
        stmt = select(Tag.id).where(
            Tag.name == tag_data["name"], Tag.client_account_id == client_account_id
        )
        existing_tag_id = await session.execute(stmt)
        tag_id = existing_tag_id.scalar_one_or_none()

        if tag_id:
            tag_ids[tag_data["name"]] = tag_id
            continue

        tag = Tag(
            client_account_id=client_account_id,
            name=tag_data["name"],
            category=tag_data["category"],
            description=tag_data["description"],
            reference_embedding=generate_mock_embedding(tag_data["name"]),
        )
        session.add(tag)
        await session.flush()
        tag_ids[tag_data["name"]] = tag.id
    logger.info(f"Created {len(MOCK_DATA['tags'])} mock tags.")
    return tag_ids


async def create_mock_assets(
    session: AsyncSession,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    user_id: uuid.UUID,
    tag_ids: Dict[str, uuid.UUID],
) -> List[uuid.UUID]:
    """Creates mock assets, embeddings, and associates them with tags."""
    logger.info("Creating mock assets...")
    asset_ids = []

    # This path seems unused in the loop below, but we'll leave the loading logic for now.
    mock_data_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "mock_cmdb_data.json"
    )
    try:
        with open(mock_data_path, "r") as f:
            json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load mock asset data from mock_cmdb_data.json: {e}")

    for data in MOCK_DATA["assets"]:
        strategy = data.get("six_r_strategy")
        if isinstance(strategy, Enum):
            strategy = strategy.value

        asset = Asset(
            name=data["name"],
            hostname=data["hostname"],
            asset_type=data["asset_type"],
            description=data["description"],
            ip_address=data.get("ip_address"),
            operating_system=data.get("operating_system"),
            os_version=data.get("os_version"),
            environment=data.get("environment", "production"),
            status="active",
            migration_status=data.get("status", AssetStatus.DISCOVERED),
            business_owner=data.get("business_owner"),
            technical_owner=data.get("technical_owner"),
            application_name=data.get("application_name"),
            cpu_cores=data.get("cpu_cores"),
            memory_gb=data.get("ram_gb"),
            storage_gb=data.get("storage_gb"),
            business_criticality=data.get("business_criticality"),
            six_r_strategy=strategy,
            migration_complexity=data.get("migration_complexity"),
            migration_wave=data.get("migration_wave"),
            sixr_ready=data.get("sixr_ready"),
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            created_by=user_id,
        )
        session.add(asset)
        await session.flush()

        asset_ids.append(asset.id)

        # Create embedding
        embedding_text = (
            f"{data['name']} {data['description']} {data.get('operating_system', '')}"
        )
        embedding_vector = generate_mock_embedding(embedding_text)
        embedding = AssetEmbedding(
            asset_id=asset.id,
            embedding=embedding_vector,
            embedding_model="text-embedding-ada-002",
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )
        session.add(embedding)

        # Associate tags
        if "tags" in data:
            for tag_name in data["tags"]:
                tag_id = tag_ids.get(tag_name)
                if tag_id:
                    asset_tag = AssetTag(asset_id=asset.id, tag_id=tag_id)
                    session.add(asset_tag)

    logger.info(f"Successfully created {len(asset_ids)} assets.")
    return asset_ids


# DEPRECATED (Phase 4, Issue #840): 6R Analysis replaced by Assessment Flow
# Use AssessmentFlow endpoints at /assessment-flow/* instead
# async def create_mock_sixr_analysis(...):
#     """DEPRECATED: Creates a mock 6R analysis record - Use Assessment Flow instead."""
#     raise NotImplementedError(
#         "6R Analysis mock data removed. Use Assessment Flow at /assessment-flow/* endpoints"
#     )


async def create_mock_migration_waves(
    session: AsyncSession,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    user_id: uuid.UUID,
):
    """Creates mock migration waves and assigns assets to them."""

    wave_data = {
        1: {
            "name": "Wave 1 - Pilot",
            "description": "Pilot migration of non-critical web servers.",
            "status": "planning",
            "start_date_offset": 7,
            "end_date_offset": 37,
        },
        2: {
            "name": "Wave 2 - Core Databases",
            "description": "Replatform core customer databases.",
            "status": "planning",
            "start_date_offset": 45,
            "end_date_offset": 105,
        },
        3: {
            "name": "Wave 3 - Application Refactor",
            "description": "Refactor monolithic CRM application.",
            "status": "planning",
            "start_date_offset": 110,
            "end_date_offset": 200,
        },
    }

    for wave_num, data in wave_data.items():
        # Idempotency check
        stmt = select(MigrationWave).where(
            MigrationWave.wave_number == wave_num,
            MigrationWave.client_account_id == client_account_id,
            MigrationWave.engagement_id == engagement_id,
        )
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            continue

        start_date = datetime.now() + timedelta(days=data["start_date_offset"])
        end_date = datetime.now() + timedelta(days=data["end_date_offset"])

        wave = MigrationWave(
            wave_number=wave_num,
            name=data["name"],
            description=data["description"],
            status=data["status"],
            planned_start_date=start_date,
            planned_end_date=end_date,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            created_by=user_id,
        )
        session.add(wave)

    logger.info("Successfully created mock migration waves.")
