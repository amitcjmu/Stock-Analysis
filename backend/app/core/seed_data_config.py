"""
Seed Data Configuration
Centralized configuration for all demo and test data.

This configuration ensures consistent demo data creation across the platform.
All demo data uses recognizable UUID patterns for easy identification.
"""

import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List


class DemoDataConfig:
    """Configuration for demo data creation"""

    # Fixed demo IDs for frontend fallback - ALWAYS created first
    FIXED_DEMO_CLIENT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
    FIXED_DEMO_ENGAGEMENT_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
    FIXED_DEMO_USER_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")

    # UUID Pattern for additional demo data: XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX (DEFault/DEmo pattern)
    DEMO_UUID_MIDDLE = "def0-def0-def0"

    @classmethod
    def create_demo_uuid(cls) -> uuid.UUID:
        """Create a demo UUID with recognizable pattern (def0 = DEFault/DEmo)"""
        start = "".join(random.choices("0123456789abcdef", k=8))
        end = "".join(random.choices("0123456789abcdef", k=12))
        uuid_string = f"{start}-{cls.DEMO_UUID_MIDDLE}-{end}"
        return uuid.UUID(uuid_string)

    @classmethod
    def is_demo_uuid(cls, uuid_value: str) -> bool:
        """Check if a UUID is a demo UUID"""
        return cls.DEMO_UUID_MIDDLE in str(uuid_value)


class PlatformAdminConfig:
    """Platform admin configuration - NEVER CHANGE THESE"""

    EMAIL = "chocka@gmail.com"
    PASSWORD = "Password123!"
    FIRST_NAME = "Platform"
    LAST_NAME = "Admin"
    ORGANIZATION = "Platform"

    # Platform admin should never have client/engagement context
    DEFAULT_CLIENT_ID = None
    DEFAULT_ENGAGEMENT_ID = None


class DemoClientConfig:
    """Demo client configuration"""

    NAME = "Demo Corporation"
    SLUG = "demo-corp"
    DESCRIPTION = "Demo client for platform testing and demonstrations"
    INDUSTRY = "Technology"
    COMPANY_SIZE = "100-500"
    HEADQUARTERS = "Demo City, USA"
    PRIMARY_CONTACT_NAME = "Demo Contact"
    PRIMARY_CONTACT_EMAIL = "contact@demo-corp.com"
    CONTACT_PHONE = "+1-555-0000"

    # Demo client metadata
    METADATA = {
        "demo": True,
        "created_for": "platform_testing",
        "features": ["discovery", "migration", "analytics"],
    }


class DemoEngagementConfig:
    """Demo engagement configuration"""

    NAME = "Demo Cloud Migration Project"
    SLUG = "demo-cloud-migration"
    DESCRIPTION = "Demo engagement for testing migration workflows"
    STATUS = "active"
    ENGAGEMENT_TYPE = "migration"

    # Engagement timeline
    START_DATE = datetime.now(timezone.utc)
    TARGET_COMPLETION_DATE = datetime(2025, 12, 31, tzinfo=timezone.utc)

    # Engagement metadata
    METADATA = {
        "demo": True,
        "scope": "full_migration",
        "target_cloud": "multi_cloud",
        "workloads": 50,
        "applications": 25,
    }


class DemoUserConfig:
    """Demo user configurations - NO CLIENT ADMINS!"""

    # Common password for all demo users
    PASSWORD = "Demo123!"

    # Demo users list with their roles
    USERS = [
        {
            "email": "manager@demo-corp.com",
            "first_name": "Demo",
            "last_name": "Manager",
            "role": "engagement_manager",
            "role_display": "Engagement Manager",
            "description": "Manages demo engagement activities",
            "permissions": {
                "can_import_data": True,
                "can_export_data": True,
                "can_view_analytics": True,
                "can_manage_sessions": True,
                "can_configure_agents": True,
                "can_manage_users": False,  # Cannot create users
                "can_access_admin_console": False,
            },
        },
        {
            "email": "analyst@demo-corp.com",
            "first_name": "Demo",
            "last_name": "Analyst",
            "role": "analyst",
            "role_display": "Migration Analyst",
            "description": "Analyzes migration data and patterns",
            "permissions": {
                "can_import_data": True,
                "can_export_data": True,
                "can_view_analytics": True,
                "can_run_analysis": True,
                "can_manage_sessions": False,
                "can_configure_agents": False,
                "can_manage_users": False,
                "can_access_admin_console": False,
            },
        },
        {
            "email": "viewer@demo-corp.com",
            "first_name": "Demo",
            "last_name": "Viewer",
            "role": "viewer",
            "role_display": "Read-Only Viewer",
            "description": "Views reports and analytics",
            "permissions": {
                "can_import_data": False,
                "can_export_data": True,  # Can export reports
                "can_view_analytics": True,
                "can_run_analysis": False,
                "can_manage_sessions": False,
                "can_configure_agents": False,
                "can_manage_users": False,
                "can_access_admin_console": False,
            },
        },
    ]

    # IMPORTANT: NO demo client admins!
    # Only platform admin can create client admins
    FORBIDDEN_ROLES = ["client_admin", "platform_admin"]


class DemoAssetConfig:
    """Demo asset configurations"""

    # Sample applications
    APPLICATIONS = [
        {
            "name": "Customer Portal",
            "type": "web_application",
            "technology_stack": ["Java", "Spring Boot", "PostgreSQL"],
            "criticality": "high",
            "environment": "production",
        },
        {
            "name": "Inventory Management",
            "type": "backend_service",
            "technology_stack": ["Python", "Django", "MySQL"],
            "criticality": "medium",
            "environment": "production",
        },
        {
            "name": "Analytics Dashboard",
            "type": "web_application",
            "technology_stack": ["React", "Node.js", "MongoDB"],
            "criticality": "low",
            "environment": "development",
        },
    ]

    # Sample servers
    SERVERS = [
        {
            "name": "PROD-WEB-01",
            "type": "virtual_machine",
            "os": "Ubuntu 20.04",
            "cpu_cores": 8,
            "memory_gb": 16,
            "storage_gb": 500,
        },
        {
            "name": "PROD-DB-01",
            "type": "physical_server",
            "os": "RHEL 8",
            "cpu_cores": 16,
            "memory_gb": 64,
            "storage_gb": 2000,
        },
    ]


class SeedDataManager:
    """Manager for creating consistent seed data"""

    @staticmethod
    def get_platform_admin_data() -> Dict[str, Any]:
        """Get platform admin configuration"""
        return {
            "email": PlatformAdminConfig.EMAIL,
            "password": PlatformAdminConfig.PASSWORD,
            "first_name": PlatformAdminConfig.FIRST_NAME,
            "last_name": PlatformAdminConfig.LAST_NAME,
            "organization": PlatformAdminConfig.ORGANIZATION,
            "is_platform_admin": True,
        }

    @staticmethod
    def get_demo_client_data() -> Dict[str, Any]:
        """Get demo client configuration"""
        return {
            "id": DemoDataConfig.create_demo_uuid(),
            "name": DemoClientConfig.NAME,
            "slug": DemoClientConfig.SLUG,
            "description": DemoClientConfig.DESCRIPTION,
            "industry": DemoClientConfig.INDUSTRY,
            "company_size": DemoClientConfig.COMPANY_SIZE,
            "headquarters_location": DemoClientConfig.HEADQUARTERS,
            "primary_contact_name": DemoClientConfig.PRIMARY_CONTACT_NAME,
            "primary_contact_email": DemoClientConfig.PRIMARY_CONTACT_EMAIL,
            "contact_phone": DemoClientConfig.CONTACT_PHONE,
            "metadata": DemoClientConfig.METADATA,
        }

    @staticmethod
    def get_demo_engagement_data(client_id: uuid.UUID) -> Dict[str, Any]:
        """Get demo engagement configuration"""
        return {
            "id": DemoDataConfig.create_demo_uuid(),
            "client_account_id": client_id,
            "name": DemoEngagementConfig.NAME,
            "slug": DemoEngagementConfig.SLUG,
            "description": DemoEngagementConfig.DESCRIPTION,
            "status": DemoEngagementConfig.STATUS,
            "engagement_type": DemoEngagementConfig.ENGAGEMENT_TYPE,
            "start_date": DemoEngagementConfig.START_DATE,
            "target_completion_date": DemoEngagementConfig.TARGET_COMPLETION_DATE,
            "metadata": DemoEngagementConfig.METADATA,
        }

    @staticmethod
    def get_demo_users_data(
        client_id: uuid.UUID, engagement_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Get demo users configuration"""
        users = []

        for user_config in DemoUserConfig.USERS:
            users.append(
                {
                    "id": DemoDataConfig.create_demo_uuid(),
                    "email": user_config["email"],
                    "password": DemoUserConfig.PASSWORD,
                    "first_name": user_config["first_name"],
                    "last_name": user_config["last_name"],
                    "role": user_config["role"],
                    "role_display": user_config["role_display"],
                    "description": user_config["description"],
                    "permissions": user_config["permissions"],
                    "default_client_id": client_id,
                    "default_engagement_id": engagement_id,
                    "is_demo_user": True,
                }
            )

        return users

    @staticmethod
    def validate_no_demo_admins(users: List[Dict[str, Any]]) -> bool:
        """Ensure no demo admin accounts are being created"""
        for user in users:
            if user.get("role") in DemoUserConfig.FORBIDDEN_ROLES:
                raise ValueError(
                    f"Demo {user['role']} accounts are forbidden! "
                    f"Only platform admin can create client admins."
                )
        return True


# Export configurations for easy access
__all__ = [
    "DemoDataConfig",
    "PlatformAdminConfig",
    "DemoClientConfig",
    "DemoEngagementConfig",
    "DemoUserConfig",
    "DemoAssetConfig",
    "SeedDataManager",
]
