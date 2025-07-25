"""
Database Migration Hooks
Ensures critical data requirements are met after migrations.

This module provides hooks that can be called from Alembic migrations
to ensure database consistency and required data existence.
"""

import logging

from app.core.database_initialization import PlatformRequirements
from sqlalchemy import text

logger = logging.getLogger(__name__)


class MigrationHooks:
    """Hooks to be called during database migrations"""

    @staticmethod
    def ensure_user_profiles_sync(op):
        """
        Synchronous version for Alembic migrations.
        Ensures all users have UserProfile records.

        Usage in Alembic migration:
            from app.core.migration_hooks import MigrationHooks

            def upgrade():
                # ... your migration code ...
                MigrationHooks.ensure_user_profiles_sync(op)
        """
        bind = op.get_bind()

        # Find users without profiles
        result = bind.execute(
            text(
                """
            SELECT u.id, u.email
            FROM users u
            LEFT JOIN user_profiles up ON u.id = up.user_id
            WHERE up.user_id IS NULL
        """
            )
        )

        users_without_profiles = result.fetchall()

        for user_id, email in users_without_profiles:
            logger.info(f"Creating UserProfile for user: {email}")

            bind.execute(
                text(
                    """
                INSERT INTO user_profiles (
                    user_id, status, approved_at, registration_reason,
                    organization, role_description, requested_access_level,
                    created_at, updated_at
                ) VALUES (
                    :user_id, 'active', NOW(), 'Migration auto-created',
                    'Unknown', 'User', 'read_only',
                    NOW(), NOW()
                )
            """
                ),
                {"user_id": user_id},
            )

        if users_without_profiles:
            logger.info(f"Created {len(users_without_profiles)} missing user profiles")

    @staticmethod
    def ensure_platform_admin_sync(op):
        """
        Synchronous version for Alembic migrations.
        Ensures platform admin exists with correct configuration.
        """
        bind = op.get_bind()
        requirements = PlatformRequirements()

        # Check if platform admin exists
        result = bind.execute(
            text(
                """
            SELECT id FROM users WHERE email = :email
        """
            ),
            {"email": requirements.PLATFORM_ADMIN_EMAIL},
        )

        admin = result.fetchone()

        if not admin:
            # Create platform admin
            import uuid

            admin_id = str(uuid.uuid4())

            bind.execute(
                text(
                    """
                INSERT INTO users (
                    id, email, password_hash, first_name, last_name,
                    is_active, is_verified, created_at, updated_at
                ) VALUES (
                    :id, :email, :password_hash, :first_name, :last_name,
                    true, true, NOW(), NOW()
                )
            """
                ),
                {
                    "id": admin_id,
                    "email": requirements.PLATFORM_ADMIN_EMAIL,
                    "password_hash": requirements.get_password_hash(
                        requirements.PLATFORM_ADMIN_PASSWORD
                    ),
                    "first_name": requirements.PLATFORM_ADMIN_FIRST_NAME,
                    "last_name": requirements.PLATFORM_ADMIN_LAST_NAME,
                },
            )

            # Create profile
            bind.execute(
                text(
                    """
                INSERT INTO user_profiles (
                    user_id, status, approved_at, registration_reason,
                    organization, role_description, requested_access_level,
                    created_at, updated_at
                ) VALUES (
                    :user_id, 'active', NOW(), 'Platform Administrator',
                    'Platform', 'Platform Administrator', 'super_admin',
                    NOW(), NOW()
                )
            """
                ),
                {"user_id": admin_id},
            )

            logger.info(f"Created platform admin: {requirements.PLATFORM_ADMIN_EMAIL}")
        else:
            # Update password to ensure it's correct
            bind.execute(
                text(
                    """
                UPDATE users
                SET password_hash = :password_hash,
                    is_active = true,
                    is_verified = true,
                    updated_at = NOW()
                WHERE email = :email
            """
                ),
                {
                    "email": requirements.PLATFORM_ADMIN_EMAIL,
                    "password_hash": requirements.get_password_hash(
                        requirements.PLATFORM_ADMIN_PASSWORD
                    ),
                },
            )

            # Ensure profile exists and is active
            bind.execute(
                text(
                    """
                INSERT INTO user_profiles (
                    user_id, status, approved_at, registration_reason,
                    organization, role_description, requested_access_level,
                    created_at, updated_at
                )
                SELECT
                    id, 'active', NOW(), 'Platform Administrator',
                    'Platform', 'Platform Administrator', 'super_admin',
                    NOW(), NOW()
                FROM users
                WHERE email = :email
                ON CONFLICT (user_id) DO UPDATE
                SET status = 'active',
                    approved_at = COALESCE(user_profiles.approved_at, NOW()),
                    updated_at = NOW()
            """
                ),
                {"email": requirements.PLATFORM_ADMIN_EMAIL},
            )

            logger.info(f"Updated platform admin: {requirements.PLATFORM_ADMIN_EMAIL}")

    @staticmethod
    def cleanup_invalid_demo_admins_sync(op):
        """
        Remove any demo client admin accounts (they should not exist).
        """
        bind = op.get_bind()

        # Delete demo client admin roles
        result = bind.execute(
            text(
                """
            DELETE FROM user_roles
            WHERE role_type = 'client_admin'
            AND user_id IN (
                SELECT id FROM users
                WHERE email LIKE '%demo%'
                OR email LIKE '%@demo.%'
            )
            RETURNING id
        """
            )
        )

        deleted_count = result.rowcount
        if deleted_count > 0:
            logger.warning(f"Deleted {deleted_count} invalid demo client admin roles")

    @staticmethod
    def verify_assessment_tables_sync(op):
        """
        Verify that assessment flow tables exist after migration.
        """
        bind = op.get_bind()

        required_tables = [
            "assessment_flows",
            "engagement_architecture_standards",
            "application_architecture_overrides",
            "application_components",
            "tech_debt_analysis",
            "component_treatments",
            "sixr_decisions",
            "assessment_learning_feedback",
        ]

        missing_tables = []
        for table in required_tables:
            try:
                result = bind.execute(text(f"SELECT to_regclass('{table}')"))
                if not result.scalar():
                    missing_tables.append(table)
            except Exception as e:
                logger.warning(f"Could not verify table {table}: {e}")
                missing_tables.append(table)

        if missing_tables:
            logger.error(f"Missing assessment flow tables: {', '.join(missing_tables)}")
        else:
            logger.info("Assessment flow tables verified successfully")

    @staticmethod
    def initialize_engagement_standards_sync(op):
        """
        Initialize architecture standards for existing engagements (synchronous).
        This should be called after assessment tables are created.
        """
        bind = op.get_bind()

        try:
            # Get all active engagements
            result = bind.execute(
                text(
                    """
                SELECT id, name FROM engagements WHERE status = 'active'
            """
                )
            )
            engagements = result.fetchall()

            if not engagements:
                logger.info("No active engagements found for standards initialization")
                return

            # Default standards data (simplified for migration context)
            default_standards = [
                {
                    "requirement_type": "java_versions",
                    "description": "Minimum supported Java versions for cloud migration",
                    "mandatory": True,
                    "requirement_details": '{"rationale": "Java 8 end-of-life considerations"}',
                },
                {
                    "requirement_type": "authentication",
                    "description": "Modern authentication and authorization patterns",
                    "mandatory": True,
                    "requirement_details": '{"required_patterns": ["OAuth2", "OIDC", "SAML"]}',
                },
                {
                    "requirement_type": "containerization",
                    "description": "Container readiness for cloud deployment",
                    "mandatory": False,
                    "requirement_details": '{"container_runtime": ["Docker", "Containerd"]}',
                },
            ]

            standards_created = 0
            for engagement_id, engagement_name in engagements:
                # Check if standards already exist
                existing = bind.execute(
                    text(
                        """
                    SELECT COUNT(*) FROM engagement_architecture_standards
                    WHERE engagement_id = :engagement_id
                """
                    ),
                    {"engagement_id": engagement_id},
                )

                if existing.scalar() > 0:
                    logger.debug(
                        f"Standards already exist for engagement: {engagement_name}"
                    )
                    continue

                # Create standards for this engagement
                for standard in default_standards:
                    import uuid

                    try:
                        bind.execute(
                            text(
                                """
                            INSERT INTO engagement_architecture_standards (
                                id, engagement_id, requirement_type, description,
                                mandatory, requirement_details, created_by,
                                created_at, updated_at
                            ) VALUES (
                                :id, :engagement_id, :requirement_type, :description,
                                :mandatory, :requirement_details::jsonb, :created_by,
                                NOW(), NOW()
                            )
                        """
                            ),
                            {
                                "id": str(uuid.uuid4()),
                                "engagement_id": engagement_id,
                                "requirement_type": standard["requirement_type"],
                                "description": standard["description"],
                                "mandatory": standard["mandatory"],
                                "requirement_details": standard["requirement_details"],
                                "created_by": "migration_init",
                            },
                        )
                        standards_created += 1
                    except Exception as e:
                        logger.error(
                            f"Failed to create standard {standard['requirement_type']} for engagement {engagement_id}: {e}"
                        )
                        continue

                logger.info(f"Initialized standards for engagement: {engagement_name}")

            if standards_created > 0:
                logger.info(
                    f"Successfully created {standards_created} architecture standards"
                )

        except Exception as e:
            logger.error(f"Failed to initialize engagement standards: {e}")
            # Don't raise - this shouldn't block migration

    @staticmethod
    def run_all_hooks(op):
        """
        Run all migration hooks in the correct order.
        This is the main entry point for migrations.
        """
        logger.info("Running database migration hooks...")

        # 1. Ensure platform admin exists
        MigrationHooks.ensure_platform_admin_sync(op)

        # 2. Ensure all users have profiles
        MigrationHooks.ensure_user_profiles_sync(op)

        # 3. Clean up invalid data
        MigrationHooks.cleanup_invalid_demo_admins_sync(op)

        logger.info("Migration hooks completed successfully")

    @staticmethod
    def run_assessment_migration_hooks(op):
        """
        Run assessment flow specific migration hooks.
        Call this from assessment flow migrations.
        """
        logger.info("Running assessment flow migration hooks...")

        # 1. Verify assessment tables exist
        MigrationHooks.verify_assessment_tables_sync(op)

        # 2. Initialize standards for existing engagements
        MigrationHooks.initialize_engagement_standards_sync(op)

        # 3. Run standard hooks as well
        MigrationHooks.run_all_hooks(op)

        logger.info("Assessment flow migration hooks completed successfully")
