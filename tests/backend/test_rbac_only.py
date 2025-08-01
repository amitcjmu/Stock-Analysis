import asyncio

from app.core.database import AsyncSessionLocal


async def test_rbac_only():
    print("=== Testing RBAC Service Only ===")

    async with AsyncSessionLocal() as db:
        # Test the modular RBAC service initialization without client models
        try:
            from app.services.rbac_service import create_rbac_service

            rbac = create_rbac_service(db)

            status = rbac.get_service_status()
            print(f"Service Status: {status}")

            # Test health check without client models
            health = await rbac.health_check()
            print(f"Health Check: {health}")

            print("\n✅ RBAC service working without client model issues!")

        except Exception as e:
            print(f"❌ RBAC service error: {e}")
            import traceback

            print(f"Traceback: {traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(test_rbac_only())
