#!/usr/bin/env python3
"""
Docker Database Diagnosis Script
Runs inside the Docker backend container to diagnose database and dependency issues
"""

import asyncio
import logging
import sys

# Add backend to path
sys.path.append("/app")

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def check_database_connection():
    """Check database connection and migration state"""
    try:
        from sqlalchemy import create_engine, text

        from app.core.config import settings

        # Use the Docker internal database URL
        db_url = settings.DATABASE_URL.replace("+asyncpg", "")
        logger.info(
            f"🔍 Connecting to database: {db_url.split('@')[1] if '@' in db_url else 'hidden'}"
        )

        engine = create_engine(db_url)

        with engine.connect() as conn:
            # Check current migration version
            try:
                result = conn.execute(text("SELECT version_num FROM alembic_version;"))
                current_version = result.scalar()
                logger.info(f"✅ Current migration version: {current_version}")
                return current_version
            except Exception as e:
                logger.error(f"❌ Failed to get migration version: {e}")
                return None

    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return None


async def check_table_structure():
    """Check critical table structure"""
    try:
        from sqlalchemy import create_engine, text

        from app.core.config import settings

        db_url = settings.DATABASE_URL.replace("+asyncpg", "")
        engine = create_engine(db_url)

        with engine.connect() as conn:
            # Check workflow_states columns
            result = conn.execute(
                text(
                    """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'migration'
                AND table_name = 'workflow_states'
                ORDER BY ordinal_position;
            """
                )
            )
            columns = result.fetchall()

            logger.info(f"✅ workflow_states has {len(columns)} columns")

            # Check for unified discovery flow columns
            column_names = [col[0] for col in columns]
            expected_columns = [
                "flow_id",
                "user_id",
                "progress_percentage",
                "phase_completion",
                "crew_status",
                "field_mappings",
                "cleaned_data",
                "asset_inventory",
                "dependencies",
                "technical_debt",
                "data_quality_metrics",
                "agent_insights",
                "success_criteria",
                "errors",
                "warnings",
                "workflow_log",
                "discovery_summary",
                "assessment_flow_package",
                "database_assets_created",
                "database_integration_status",
                "learning_scope",
                "memory_isolation_level",
                "shared_memory_id",
                "started_at",
                "completed_at",
            ]

            missing_columns = [
                col for col in expected_columns if col not in column_names
            ]

            if missing_columns:
                logger.error(f"❌ Missing workflow_states columns: {missing_columns}")
                return False
            else:
                logger.info("✅ workflow_states has all unified discovery flow columns")
                return True

    except Exception as e:
        logger.error(f"❌ Error checking table structure: {e}")
        return False


def check_crewai_installation():
    """Check if CrewAI is properly installed and importable"""
    try:
        import crewai

        logger.info(f"✅ CrewAI version: {crewai.__version__}")

        from crewai import Agent, Crew, Process, Task

        logger.info("✅ CrewAI core classes imported successfully")

        try:
            from crewai.knowledge.knowledge import Knowledge
            from crewai.memory import LongTermMemory

            logger.info("✅ CrewAI advanced features available")
        except ImportError as e:
            logger.warning(f"⚠️ CrewAI advanced features not available: {e}")

        return True

    except ImportError as e:
        logger.error(f"❌ CrewAI not installed: {e}")
        return False


def check_discovery_flow_imports():
    """Check if discovery flow modules can be imported"""
    try:
        from app.services.crewai_flows.discovery_flow import (
            DiscoveryFlow,
            create_discovery_flow,
        )

        logger.info("✅ DiscoveryFlow imported successfully")

        from app.services.crewai_flows.crews.inventory_building_crew import (
            create_inventory_building_crew,
        )

        logger.info("✅ inventory_building_crew imported successfully")

        from app.services.crewai_flow_service import CrewAIFlowService

        logger.info("✅ CrewAIFlowService imported successfully")

        return True

    except ImportError as e:
        logger.error(f"❌ Discovery flow import failed: {e}")
        import traceback

        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False


def check_deepinfra_config():
    """Check DeepInfra configuration"""
    try:
        from app.core.config import settings

        if settings.DEEPINFRA_API_KEY:
            logger.info("✅ DEEPINFRA_API_KEY is configured")
        else:
            logger.warning("⚠️ DEEPINFRA_API_KEY is missing")

        logger.info(f"✅ DEEPINFRA_MODEL: {settings.DEEPINFRA_MODEL}")
        logger.info(f"✅ CREWAI_MODEL: {settings.CREWAI_MODEL}")

        return True

    except Exception as e:
        logger.error(f"❌ Config check failed: {e}")
        return False


def test_crewai_llm():
    """Test CrewAI LLM configuration"""
    try:
        from app.services.llm_config import get_crewai_llm

        llm = get_crewai_llm()
        logger.info(
            f"✅ CrewAI LLM configured: {llm.model if hasattr(llm, 'model') else 'Unknown model'}"
        )

        return True

    except Exception as e:
        logger.error(f"❌ CrewAI LLM test failed: {e}")
        return False


async def main():
    """Main diagnosis function"""
    logger.info("🚀 Starting Docker Database Diagnosis...")
    logger.info("=" * 60)

    # Check CrewAI installation
    logger.info("🔍 Checking CrewAI installation...")
    crewai_ok = check_crewai_installation()

    # Check discovery flow imports
    logger.info("\n🔍 Checking discovery flow imports...")
    imports_ok = check_discovery_flow_imports()

    # Check DeepInfra configuration
    logger.info("\n🔍 Checking DeepInfra configuration...")
    config_ok = check_deepinfra_config()

    # Test LLM configuration
    logger.info("\n🔍 Testing LLM configuration...")
    llm_ok = test_crewai_llm()

    # Check database connection
    logger.info("\n🔍 Checking database connection...")
    db_version = await check_database_connection()

    # Check table structure
    logger.info("\n🔍 Checking table structure...")
    tables_ok = await check_table_structure()

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 DOCKER DIAGNOSIS SUMMARY")
    logger.info("=" * 60)

    logger.info(f"CrewAI Installation: {'✅ OK' if crewai_ok else '❌ FAILED'}")
    logger.info(f"Discovery Flow Imports: {'✅ OK' if imports_ok else '❌ FAILED'}")
    logger.info(f"DeepInfra Config: {'✅ OK' if config_ok else '❌ FAILED'}")
    logger.info(f"LLM Configuration: {'✅ OK' if llm_ok else '❌ FAILED'}")
    logger.info(f"Database Connection: {'✅ OK' if db_version else '❌ FAILED'}")
    logger.info(f"Table Structure: {'✅ OK' if tables_ok else '❌ FAILED'}")

    if db_version:
        logger.info(f"Migration Version: {db_version}")

    # Identify Railway-specific issues
    issues = []
    if not crewai_ok:
        issues.append("CrewAI not installed in Railway environment")
    if not imports_ok:
        issues.append("Discovery flow modules missing or broken")
    if not config_ok:
        issues.append("Configuration issues")
    if not llm_ok:
        issues.append("LLM configuration problems")
    if not db_version:
        issues.append("Database connection failed")
    if not tables_ok:
        issues.append("Database schema incomplete")

    if issues:
        logger.error("\n❌ ISSUES THAT WOULD AFFECT RAILWAY:")
        for i, issue in enumerate(issues, 1):
            logger.error(f"   {i}. {issue}")

        logger.info("\n💡 RAILWAY DEPLOYMENT RECOMMENDATIONS:")
        logger.info("   1. Ensure requirements.txt includes all dependencies")
        logger.info("   2. Run 'alembic upgrade head' in Railway console")
        logger.info("   3. Check Railway environment variables")
        logger.info("   4. Verify build process includes all Python packages")

        return False
    else:
        logger.info("\n✅ All checks passed - should work on Railway")
        return True


if __name__ == "__main__":
    asyncio.run(main())
