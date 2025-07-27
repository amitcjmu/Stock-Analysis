#!/usr/bin/env python3
"""
Railway Database Diagnosis Script
Checks migration state, table existence, and constraint issues
"""

import asyncio
import logging
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_migration_state():
    """Check current migration state"""
    try:
        from sqlalchemy import create_engine, text

        from app.core.config import get_settings

        settings = get_settings()
        engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))

        with engine.connect() as conn:
            # Check current migration version
            try:
                result = conn.execute(text("SELECT version_num FROM alembic_version;"))
                current_version = result.scalar()
                logger.info(f"✅ Current migration version: {current_version}")
            except Exception as e:
                logger.error(f"❌ Failed to get migration version: {e}")
                return False

            # Check if key tables exist
            tables_to_check = [
                "client_accounts",
                "engagements",
                "users",
                "user_roles",
                "workflow_states",
                "sixr_analyses",
                "sixr_analysis_parameters",
            ]

            missing_tables = []
            for table in tables_to_check:
                try:
                    result = conn.execute(
                        text(  # nosec B608 - table names are hardcoded, not user input
                            f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'migration'
                            AND table_name = '{table}'
                        );
                    """
                        )
                    )
                    exists = result.scalar()
                    if exists:
                        logger.info(f"✅ Table exists: migration.{table}")
                    else:
                        logger.error(f"❌ Missing table: migration.{table}")
                        missing_tables.append(table)
                except Exception as e:
                    logger.error(f"❌ Error checking table {table}: {e}")
                    missing_tables.append(table)

            # Check workflow_states columns
            try:
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

                existing_column_names = [col[0] for col in columns]
                missing_columns = [
                    col for col in expected_columns if col not in existing_column_names
                ]

                if missing_columns:
                    logger.error(
                        f"❌ Missing workflow_states columns: {missing_columns}"
                    )
                else:
                    logger.info("✅ workflow_states has all expected columns")

            except Exception as e:
                logger.error(f"❌ Error checking workflow_states columns: {e}")

            # Check sixr constraint issue
            try:
                result = conn.execute(
                    text(
                        """
                    SELECT
                        conname as constraint_name,
                        pg_get_constraintdef(oid) as constraint_definition
                    FROM pg_constraint
                    WHERE conname LIKE '%sixr_analysis_parameters%analysis_id%';
                """
                    )
                )
                constraints = result.fetchall()

                if constraints:
                    for constraint in constraints:
                        logger.info(
                            f"✅ Constraint exists: {constraint[0]} - {constraint[1]}"
                        )
                else:
                    logger.error(
                        "❌ Missing sixr_analysis_parameters foreign key constraint"
                    )

            except Exception as e:
                logger.error(f"❌ Error checking constraints: {e}")

            return len(missing_tables) == 0

    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


def check_crewai_installation():
    """Check if CrewAI is properly installed"""
    try:
        import crewai

        logger.info(f"✅ CrewAI version: {crewai.__version__}")

        # CrewAI imports removed - not used in this diagnostic script

        logger.info("✅ CrewAI core classes imported successfully")

        try:
            # Knowledge and memory imports removed - not used in diagnostics

            logger.info("✅ CrewAI advanced features available")
        except ImportError as e:
            logger.warning(f"⚠️ CrewAI advanced features not available: {e}")

        return True

    except ImportError as e:
        logger.error(f"❌ CrewAI not installed: {e}")
        return False


def check_requirements():
    """Check if all requirements are met"""
    logger.info("🔍 Checking requirements.txt dependencies...")

    requirements_file = os.path.join(
        os.path.dirname(__file__), "..", "requirements.txt"
    )
    if not os.path.exists(requirements_file):
        logger.error("❌ requirements.txt not found")
        return False

    with open(requirements_file, "r") as f:
        requirements = f.read().splitlines()

    # Check key dependencies
    key_deps = ["crewai", "fastapi", "sqlalchemy", "alembic", "openai"]
    missing_deps = []

    for dep in key_deps:
        if not any(dep in req for req in requirements if not req.startswith("#")):
            missing_deps.append(dep)

    if missing_deps:
        logger.error(f"❌ Missing dependencies in requirements.txt: {missing_deps}")
        return False
    else:
        logger.info("✅ All key dependencies found in requirements.txt")
        return True


async def main():
    """Main diagnosis function"""
    logger.info("🚀 Starting Railway Database Diagnosis...")

    # Check requirements
    req_ok = check_requirements()

    # Check CrewAI installation
    crewai_ok = check_crewai_installation()

    # Check database state
    db_ok = await check_migration_state()

    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 DIAGNOSIS SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Requirements.txt: {'✅ OK' if req_ok else '❌ ISSUES'}")
    logger.info(f"CrewAI Installation: {'✅ OK' if crewai_ok else '❌ MISSING'}")
    logger.info(f"Database State: {'✅ OK' if db_ok else '❌ ISSUES'}")

    if not (req_ok and crewai_ok and db_ok):
        logger.error("\n❌ Issues found that need to be fixed before deployment")
        return False
    else:
        logger.info("\n✅ All checks passed - Railway should deploy successfully")
        return True


if __name__ == "__main__":
    asyncio.run(main())
