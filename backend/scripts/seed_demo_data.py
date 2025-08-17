#!/usr/bin/env python3
"""
Seed demo data script for production deployment.
Run this after deploying to Railway/Vercel to populate the database with demo data.

Usage:
    python scripts/seed_demo_data.py
"""
import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import our modules
from seeding.deployment_seeding_script import DeploymentSeeder  # noqa: E402


async def main():
    """Run the demo data seeding"""
    print("=" * 60)
    print("🌱 DEMO DATA SEEDING SCRIPT")
    print("=" * 60)

    # Check environment
    env = (
        "PRODUCTION"
        if (os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("DATABASE_URL"))
        else "LOCAL"
    )
    print(f"\n📍 Environment: {env}")

    if env == "PRODUCTION":
        print("\n⚠️  WARNING: This will create demo data in the production database!")
        print("   This is intended for initial deployment setup only.")

        # In production, we'll auto-proceed after a delay
        print("\n⏳ Starting in 5 seconds... (Ctrl+C to cancel)")
        await asyncio.sleep(5)

    # Run the seeding
    seeder = DeploymentSeeder()
    success = await seeder.seed_complete_demo_data()

    if success:
        print("\n✅ Demo data seeding completed successfully!")
        print("\n🔐 Demo Accounts Created:")
        print("   Main Demo Account:")
        print("   - Email: demo@democorp.com")
        print("   - Password: Demo123!")
        print("\n   Additional Demo Accounts:")
        print("   - admin@demo.techcorp.com (Demo123!)")
        print("   - admin@demo.retailplus.com (Demo123!)")
        print("   - manager@demo.manufacturing.com (Demo123!)")
        print("\n   All demo accounts are clearly marked with:")
        print("   - 'Demo' prefix in names")
        print("   - @demo.company.com email pattern")
        print("   - UUID pattern: XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX")
    else:
        print("\n❌ Demo data seeding failed!")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Seeding cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        sys.exit(1)
