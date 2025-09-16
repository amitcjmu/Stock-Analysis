"""
Base classes and core requirements for database initialization.

This module contains the foundational requirements and utilities that all
database initialization components depend on.
"""

import os
import random
import uuid
from app.models.rbac import RoleType

import logging

logger = logging.getLogger(__name__)

# Conditional import to handle migration scenarios
try:
    from app.models.assessment_flow import EngagementArchitectureStandard

    ASSESSMENT_MODELS_AVAILABLE = True
except Exception as e:
    # Models not available yet (during migration) or schema mismatch
    logger.warning(f"Assessment models not available: {e}")
    ASSESSMENT_MODELS_AVAILABLE = False
    EngagementArchitectureStandard = None


class PlatformRequirements:
    """Core platform requirements that must be enforced"""

    # Platform admin configuration
    PLATFORM_ADMIN_EMAIL = os.getenv("PLATFORM_ADMIN_EMAIL", "chocka@gmail.com")
    PLATFORM_ADMIN_PASSWORD = os.getenv(
        "PLATFORM_ADMIN_PASSWORD", "Password123!"
    )  # nosec B105 - Default only for development
    PLATFORM_ADMIN_FIRST_NAME = os.getenv("PLATFORM_ADMIN_FIRST_NAME", "Platform")
    PLATFORM_ADMIN_LAST_NAME = os.getenv("PLATFORM_ADMIN_LAST_NAME", "Admin")

    # Demo data configuration - Fixed UUIDs for frontend fallback
    DEMO_CLIENT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
    DEMO_CLIENT_NAME = "Demo Corporation"
    DEMO_ENGAGEMENT_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
    DEMO_ENGAGEMENT_NAME = "Demo Cloud Migration Project"
    DEMO_USER_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
    DEMO_USER_EMAIL = "demo@demo-corp.com"
    DEMO_USER_PASSWORD = os.getenv(
        "DEMO_USER_PASSWORD", "Demo123!"
    )  # nosec B105 - Default only for development

    # Demo users (NO CLIENT ADMINS!)
    DEMO_USERS = [
        {
            "email": "manager@demo-corp.com",
            "first_name": "Demo",
            "last_name": "Manager",
            "role": RoleType.ENGAGEMENT_MANAGER,
        },
        {
            "email": "analyst@demo-corp.com",
            "first_name": "Demo",
            "last_name": "Analyst",
            "role": RoleType.ANALYST,
        },
        {
            "email": "viewer@demo-corp.com",
            "first_name": "Demo",
            "last_name": "Viewer",
            "role": RoleType.VIEWER,
        },
    ]

    @staticmethod
    def create_demo_uuid() -> uuid.UUID:
        """Create UUID with -def0-def0-def0- pattern for easy identification (DEFault/DEmo)"""
        start = "".join(
            random.choices("0123456789abcdef", k=8)
        )  # nosec B311 # Demo UUID generation
        end = "".join(
            random.choices("0123456789abcdef", k=12)
        )  # nosec B311 # Demo UUID generation
        uuid_string = f"{start}-def0-def0-def0-{end}"
        return uuid.UUID(uuid_string)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Password hashing using bcrypt to match authentication service"""
        import bcrypt

        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
