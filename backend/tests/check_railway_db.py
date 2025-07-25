#!/usr/bin/env python3
"""
Railway Database Verification Script
Checks if PostgreSQL database is properly configured and tables are created
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


async def check_database_setup():
    """Check if database is properly set up in Railway environment."""
    print("🔍 Checking Railway Database Setup...")
    print("=" * 50)

    # Check environment variables
    database_url = os.getenv("DATABASE_URL")
    environment = os.getenv("ENVIRONMENT", "unknown")
    railway_env = os.getenv("RAILWAY_ENVIRONMENT")

    print(f"🌍 Environment: {environment}")
    print(f"🚂 Railway Environment: {railway_env}")
    print(f"📊 Database URL: {'Set' if database_url else 'Not Set'}")

    if not database_url:
        print("❌ DATABASE_URL environment variable is not set")
        print("💡 In Railway.com, ensure PostgreSQL service is added and connected")
        return False

    # Test database connection
    try:
        from app.core.config import settings
        from app.core.database import engine

        print(f"🔗 Using database URL: {settings.database_url_async[:50]}...")

        # Test connection
        from sqlalchemy import text

        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print("✅ PostgreSQL Connection: SUCCESS")
            print(f"📋 Database Version: {version}")

        # Test table creation
        await check_tables()

        # Test data operations
        await test_data_operations()

        return True

    except Exception as e:
        print("❌ Database Connection: FAILED")
        print(f"💥 Error: {e}")
        print("\n🔧 Troubleshooting Steps:")
        print("1. Verify PostgreSQL service is running in Railway")
        print("2. Check DATABASE_URL environment variable")
        print("3. Ensure database permissions are correct")
        print("4. Check network connectivity")
        return False


async def check_tables():
    """Check if database tables exist."""
    print("\n📋 Checking Database Tables...")

    try:
        from app.core.database import engine
        from sqlalchemy import text

        async with engine.begin() as conn:
            # Query for table existence
            result = await conn.execute(
                text(
                    """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """
                )
            )

            tables = [row[0] for row in result.fetchall()]

            if tables:
                print(f"✅ Found {len(tables)} tables:")
                for table in tables:
                    print(f"   📁 {table}")
            else:
                print("⚠️  No tables found. Running table creation...")
                await create_tables()

    except Exception as e:
        print(f"❌ Table Check Failed: {e}")


async def create_tables():
    """Create database tables if they don't exist."""
    try:
        from app.core.database import init_db

        print("🔧 Creating database tables...")
        await init_db()
        print("✅ Database tables created successfully!")

    except Exception as e:
        print(f"❌ Table Creation Failed: {e}")
        print("💡 You may need to run Alembic migrations:")
        print("   alembic upgrade head")


async def test_data_operations():
    """Test basic data operations."""
    print("\n🧪 Testing Data Operations...")

    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            # Test a simple query
            result = await session.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]

            if test_value == 1:
                print("✅ Basic Query Test: PASSED")
            else:
                print("❌ Basic Query Test: FAILED")

        # Test table access (if tables exist)
        await test_table_access()

    except Exception as e:
        print(f"❌ Data Operations Test Failed: {e}")


async def test_table_access():
    """Test access to application tables."""
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            # Try to access feedback table (if it exists)
            try:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM feedback LIMIT 1")
                )
                count = result.fetchone()[0]
                print(f"📊 Feedback table: {count} records found")
            except Exception:
                print("⚠️  Feedback table not accessible (may not exist yet)")

            # Try to access assets table (if it exists)
            try:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM assets LIMIT 1")
                )
                count = result.fetchone()[0]
                print(f"📊 Assets table: {count} records found")
            except Exception:
                print("⚠️  Assets table not accessible (may not exist yet)")

    except Exception as e:
        print(f"❌ Table Access Test Failed: {e}")


def print_deployment_info():
    """Print deployment information and next steps."""
    print("\n🚀 Railway Deployment Information:")
    print("=" * 50)
    print("1. 🗄️  PostgreSQL Service:")
    print("   - Should be added as a separate service in Railway")
    print("   - Automatically provides DATABASE_URL environment variable")
    print("   - Supports standard PostgreSQL features")

    print("\n2. 🔧 Environment Variables Required:")
    print("   - DATABASE_URL (automatically set by Railway PostgreSQL)")
    print("   - ENVIRONMENT=production")
    print("   - DEBUG=false")
    print("   - DEEPINFRA_API_KEY (for AI features)")
    print("   - SECRET_KEY (for session management)")

    print("\n3. 🔄 Table Creation:")
    print("   - Tables are created automatically on first run")
    print("   - Or run: alembic upgrade head")

    print("\n4. 📦 Multi-Tenant Setup:")
    print("   - Client accounts and engagements supported")
    print("   - Data isolation by client_account_id")
    print("   - Mock data available for testing")


if __name__ == "__main__":
    try:
        result = asyncio.run(check_database_setup())

        print("\n" + "=" * 50)
        if result:
            print("🎉 Railway Database Setup: SUCCESSFUL")
            print("✅ Your database is ready for production use!")
        else:
            print("❌ Railway Database Setup: NEEDS ATTENTION")
            print("🔧 Please check the troubleshooting steps above")

        print_deployment_info()

    except KeyboardInterrupt:
        print("\n👋 Database check cancelled by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
