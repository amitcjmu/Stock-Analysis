#!/usr/bin/env python3
"""
Railway Connection Test Script
Tests connection to Railway database and compares schema with local environment
"""

import asyncio
import logging
import os
import sys

# Add backend to path
sys.path.append("/app")

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def get_railway_db_url():
    """Get Railway database URL from environment"""
    # Check for Railway environment variables
    railway_vars = [
        "DATABASE_URL",
        "RAILWAY_DATABASE_URL",
        "POSTGRES_URL",
        "PGDATABASE_URL",
    ]

    for var in railway_vars:
        url = os.getenv(var)
        if url and "railway" in url.lower():
            return url

    # If no Railway-specific URL, check if we have a general DATABASE_URL
    # that might be pointing to Railway
    general_url = os.getenv("DATABASE_URL")
    if general_url:
        logger.info(
            f"Using DATABASE_URL: {general_url.split('@')[1] if '@' in general_url else 'hidden'}"
        )
        return general_url

    return None


async def test_database_connection(db_url: str, label: str):
    """Test database connection and get schema info"""
    try:
        from sqlalchemy import create_engine, text

        # Convert to sync URL for connection test
        sync_url = db_url.replace("+asyncpg", "")
        logger.info(f"🔍 Testing {label} connection...")

        engine = create_engine(sync_url)

        with engine.connect() as conn:
            # Test basic connection
            result = conn.execute(text("SELECT 1;"))
            logger.info(f"✅ {label} connection successful")

            # Get migration version
            try:
                result = conn.execute(text("SELECT version_num FROM alembic_version;"))
                version = result.scalar()
                logger.info(f"✅ {label} migration version: {version}")
            except Exception as e:
                logger.error(f"❌ {label} migration version error: {e}")
                version = None

            # Check workflow_states table
            try:
                result = conn.execute(
                    text(
                        """
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'migration' 
                    AND table_name = 'workflow_states'
                    ORDER BY ordinal_position;
                """
                    )
                )
                columns = [row[0] for row in result.fetchall()]
                logger.info(f"✅ {label} workflow_states columns: {len(columns)}")

                # Check for key unified discovery flow columns
                key_columns = [
                    "flow_id",
                    "user_id",
                    "progress_percentage",
                    "field_mappings",
                ]
                missing = [col for col in key_columns if col not in columns]

                if missing:
                    logger.error(f"❌ {label} missing key columns: {missing}")
                else:
                    logger.info(
                        f"✅ {label} has all key unified discovery flow columns"
                    )

            except Exception as e:
                logger.error(f"❌ {label} table check error: {e}")
                columns = []

            # Check constraint
            try:
                result = conn.execute(
                    text(
                        """
                    SELECT conname 
                    FROM pg_constraint 
                    WHERE conname = 'sixr_analysis_parameters_analysis_id_fkey';
                """
                    )
                )
                constraint_exists = bool(result.fetchall())

                if constraint_exists:
                    logger.info(f"✅ {label} sixr constraint exists")
                else:
                    logger.error(f"❌ {label} sixr constraint missing")

            except Exception as e:
                logger.error(f"❌ {label} constraint check error: {e}")
                constraint_exists = False

            return {
                "connected": True,
                "version": version,
                "columns": len(columns),
                "has_key_columns": (
                    len(missing) == 0 if "missing" in locals() else False
                ),
                "has_constraint": constraint_exists,
            }

    except Exception as e:
        logger.error(f"❌ {label} connection failed: {e}")
        return {"connected": False, "error": str(e)}


async def main():
    """Main test function"""
    logger.info("🚀 Railway Connection Test")
    logger.info("=" * 60)

    # Get local Docker database URL
    from app.core.config import settings

    local_db_url = settings.DATABASE_URL

    # Get Railway database URL
    railway_db_url = get_railway_db_url()

    if not railway_db_url:
        logger.error("❌ No Railway database URL found in environment")
        logger.info("💡 Set RAILWAY_DATABASE_URL or DATABASE_URL environment variable")
        return False

    # Test local database
    logger.info("📍 Testing LOCAL Docker database...")
    local_result = await test_database_connection(local_db_url, "LOCAL")

    # Test Railway database
    logger.info("\n📍 Testing RAILWAY database...")
    railway_result = await test_database_connection(railway_db_url, "RAILWAY")

    # Compare results
    logger.info("\n" + "=" * 60)
    logger.info("📊 COMPARISON SUMMARY")
    logger.info("=" * 60)

    if local_result.get("connected") and railway_result.get("connected"):
        logger.info("✅ Both databases connected successfully")

        # Compare versions
        local_version = local_result.get("version")
        railway_version = railway_result.get("version")

        if local_version == railway_version:
            logger.info(f"✅ Migration versions match: {local_version}")
        else:
            logger.error("❌ Migration version mismatch!")
            logger.error(f"   Local: {local_version}")
            logger.error(f"   Railway: {railway_version}")

        # Compare schema
        local_columns = local_result.get("columns", 0)
        railway_columns = railway_result.get("columns", 0)

        if local_columns == railway_columns:
            logger.info(f"✅ Column counts match: {local_columns}")
        else:
            logger.error("❌ Column count mismatch!")
            logger.error(f"   Local: {local_columns}")
            logger.error(f"   Railway: {railway_columns}")

        # Check key columns
        local_keys = local_result.get("has_key_columns", False)
        railway_keys = railway_result.get("has_key_columns", False)

        if local_keys and railway_keys:
            logger.info("✅ Both have key unified discovery flow columns")
        elif local_keys and not railway_keys:
            logger.error("❌ Railway missing key columns (needs migration)")
        elif not local_keys and railway_keys:
            logger.warning("⚠️ Local missing key columns (unexpected)")
        else:
            logger.error("❌ Both missing key columns")

        # Check constraints
        local_constraint = local_result.get("has_constraint", False)
        railway_constraint = railway_result.get("has_constraint", False)

        if local_constraint and railway_constraint:
            logger.info("✅ Both have required constraints")
        elif local_constraint and not railway_constraint:
            logger.error("❌ Railway missing constraints")
        else:
            logger.warning("⚠️ Constraint issues detected")

        # Final assessment
        railway_issues = []
        if local_version != railway_version:
            railway_issues.append("Migration version mismatch")
        if local_columns != railway_columns:
            railway_issues.append("Schema structure mismatch")
        if local_keys and not railway_keys:
            railway_issues.append("Missing unified discovery flow columns")
        if local_constraint and not railway_constraint:
            railway_issues.append("Missing database constraints")

        if railway_issues:
            logger.error("\n❌ RAILWAY DEPLOYMENT ISSUES:")
            for i, issue in enumerate(railway_issues, 1):
                logger.error(f"   {i}. {issue}")

            logger.info("\n💡 RAILWAY FIX ACTIONS:")
            logger.info("   1. Connect to Railway console: railway shell")
            logger.info("   2. Run migrations: alembic upgrade head")
            logger.info("   3. Restart Railway service")
            logger.info("   4. Check deployment logs for errors")

            return False
        else:
            logger.info("\n✅ Railway database matches local - deployment should work")
            return True

    else:
        if not local_result.get("connected"):
            logger.error("❌ Local database connection failed")
        if not railway_result.get("connected"):
            logger.error("❌ Railway database connection failed")
            logger.info("💡 Check Railway database credentials and network access")

        return False


if __name__ == "__main__":
    # Set Railway database URL for testing (you can set this environment variable)
    # os.environ['RAILWAY_DATABASE_URL'] = 'postgresql://...'

    asyncio.run(main())
