import asyncio

from app.core.database import AsyncSessionLocal
from app.services.rbac_service import create_rbac_service


async def test_rbac_modular():
    print("Testing modular RBAC service...")

    async with AsyncSessionLocal() as db:
        rbac = create_rbac_service(db)

        # Test service status
        status = rbac.get_service_status()
        print(f"Service Status: {status}")

        # Test health check
        health = await rbac.health_check()
        print(f"Health Check: {health}")

        # Test user creation with UUID fix
        user_data = {
            "email": "test.modular@example.com",
            "full_name": "Test Modular User",
            "organization": "Test Organization",
            "role_description": "Test Role",
            "access_level": "analyst",
        }

        result = await rbac.admin_create_user(user_data, "admin_user")
        print(f"User Creation Result: {result}")


if __name__ == "__main__":
    asyncio.run(test_rbac_modular())
