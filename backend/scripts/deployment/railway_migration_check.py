#!/usr/bin/env python3
"""
Railway Migration Validation Script

This script validates that our database migrations will work safely on Railway
by checking the actual schema state vs expected migration state.
"""

import asyncio
import os
from typing import Any, Dict

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine

# Use Railway DATABASE_URL if available, otherwise local
raw_db_url = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/migration_db"
)
# Convert to async URL if needed
if raw_db_url.startswith("postgresql://"):
    DATABASE_URL = raw_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = raw_db_url


async def check_database_schema_state() -> Dict[str, Any]:
    """Check the actual database schema state."""

    engine = create_async_engine(DATABASE_URL)

    try:
        async with engine.begin() as conn:
            results = {}

            # 1. Check alembic version state
            try:
                alembic_versions = await conn.execute(
                    sa.text(
                        "SELECT version_num FROM alembic_version ORDER BY version_num"
                    )
                )
                results["alembic_versions"] = [
                    row.version_num for row in alembic_versions.fetchall()
                ]
            except Exception as e:
                results["alembic_versions"] = f"ERROR: {e}"

            # 2. Check crewai_flow_state_extensions table structure
            try:
                crewai_columns = await conn.execute(
                    sa.text(
                        """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'crewai_flow_state_extensions'
                    ORDER BY ordinal_position
                """
                    )
                )
                results["crewai_flow_state_extensions"] = [
                    {
                        "column_name": row.column_name,
                        "data_type": row.data_type,
                        "is_nullable": row.is_nullable,
                        "column_default": row.column_default,
                    }
                    for row in crewai_columns.fetchall()
                ]
            except Exception as e:
                results["crewai_flow_state_extensions"] = f"ERROR: {e}"

            # 3. Check discovery_flows table structure
            try:
                discovery_columns = await conn.execute(
                    sa.text(
                        """
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'discovery_flows'
                    ORDER BY ordinal_position
                """
                    )
                )
                results["discovery_flows"] = [
                    {
                        "column_name": row.column_name,
                        "data_type": row.data_type,
                        "is_nullable": row.is_nullable,
                    }
                    for row in discovery_columns.fetchall()
                ]
            except Exception as e:
                results["discovery_flows"] = f"ERROR: {e}"

            # 4. Check assets table for flow_id column
            try:
                assets_flow_id = await conn.execute(
                    sa.text(
                        """
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'assets' AND column_name = 'flow_id'
                """
                    )
                )
                assets_result = assets_flow_id.fetchone()
                results["assets_flow_id"] = {
                    "exists": assets_result is not None,
                    "details": (
                        {
                            "column_name": assets_result.column_name,
                            "data_type": assets_result.data_type,
                            "is_nullable": assets_result.is_nullable,
                        }
                        if assets_result
                        else None
                    ),
                }
            except Exception as e:
                results["assets_flow_id"] = f"ERROR: {e}"

            # 5. Check indexes and constraints
            try:
                indexes = await conn.execute(
                    sa.text(
                        """
                    SELECT tablename, indexname, indexdef
                    FROM pg_indexes
                    WHERE tablename IN ('crewai_flow_state_extensions', 'discovery_flows', 'assets')
                    AND indexname LIKE '%flow_id%'
                    ORDER BY tablename, indexname
                """
                    )
                )
                results["flow_id_indexes"] = [
                    {
                        "table": row.tablename,
                        "index_name": row.indexname,
                        "definition": row.indexdef,
                    }
                    for row in indexes.fetchall()
                ]
            except Exception as e:
                results["flow_id_indexes"] = f"ERROR: {e}"

            # 6. Check foreign key constraints
            try:
                constraints = await conn.execute(
                    sa.text(
                        """
                    SELECT
                        tc.table_name,
                        tc.constraint_name,
                        tc.constraint_type,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND (kcu.column_name = 'flow_id'
                         OR tc.table_name IN ('crewai_flow_state_extensions', 'discovery_flows'))
                    ORDER BY tc.table_name, tc.constraint_name
                """
                    )
                )
                results["foreign_key_constraints"] = [
                    {
                        "table": row.table_name,
                        "constraint_name": row.constraint_name,
                        "constraint_type": row.constraint_type,
                        "column": row.column_name,
                        "foreign_table": row.foreign_table_name,
                        "foreign_column": row.foreign_column_name,
                    }
                    for row in constraints.fetchall()
                ]
            except Exception as e:
                results["foreign_key_constraints"] = f"ERROR: {e}"

            # 7. Check data counts
            try:
                # Count records in key tables
                crewai_count = await conn.execute(
                    sa.text(
                        "SELECT COUNT(*) as count FROM crewai_flow_state_extensions"
                    )
                )
                discovery_count = await conn.execute(
                    sa.text("SELECT COUNT(*) as count FROM discovery_flows")
                )
                results["data_counts"] = {
                    "crewai_flow_state_extensions": crewai_count.fetchone().count,
                    "discovery_flows": discovery_count.fetchone().count,
                }
            except Exception as e:
                results["data_counts"] = f"ERROR: {e}"

            return results

    except Exception as e:
        return {"error": f"Database connection failed: {e}"}
    finally:
        await engine.dispose()


def analyze_migration_safety(schema_state: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze if migrations are safe to run on Railway."""

    analysis = {"safe_to_migrate": True, "issues": [], "recommendations": []}

    # Check if critical columns exist
    if isinstance(schema_state.get("crewai_flow_state_extensions"), list):
        crewai_columns = [
            col["column_name"] for col in schema_state["crewai_flow_state_extensions"]
        ]
        required_columns = [
            "client_account_id",
            "engagement_id",
            "user_id",
            "flow_type",
            "flow_status",
        ]

        missing_columns = [col for col in required_columns if col not in crewai_columns]
        if missing_columns:
            analysis["issues"].append(
                f"crewai_flow_state_extensions missing columns: {missing_columns}"
            )
            analysis["safe_to_migrate"] = False

    # Check assets flow_id column
    if not schema_state.get("assets_flow_id", {}).get("exists", False):
        analysis["issues"].append("assets table missing flow_id column")
        analysis["safe_to_migrate"] = False

    # Check alembic version
    versions = schema_state.get("alembic_versions", [])
    if "a1409a6c4f88" not in versions:
        analysis["issues"].append("Missing critical migration a1409a6c4f88")
        analysis["recommendations"].append("Run migration a1409a6c4f88 first")

    # Check data consistency
    data_counts = schema_state.get("data_counts", {})
    if isinstance(data_counts, dict):
        crewai_count = data_counts.get("crewai_flow_state_extensions", 0)
        discovery_count = data_counts.get("discovery_flows", 0)

        if discovery_count > 0 and crewai_count == 0:
            analysis["issues"].append(
                f"Data inconsistency: {discovery_count} discovery flows but 0 crewai extensions"
            )
            analysis["recommendations"].append(
                "Run orphan flow migration to fix missing extensions"
            )

    return analysis


async def main():
    """Main function to check database state and provide Railway migration guidance."""

    print("🔍 Checking database schema state for Railway migration safety...")
    print("=" * 80)

    # Check current schema state
    schema_state = await check_database_schema_state()

    # Analyze migration safety
    analysis = analyze_migration_safety(schema_state)

    # Output results
    print("\n📊 DATABASE SCHEMA STATE:")
    print("-" * 40)

    if "error" in schema_state:
        print(f"❌ Database Error: {schema_state['error']}")
        return

    # Alembic versions
    print(
        f"📋 Alembic Versions Applied: {schema_state.get('alembic_versions', 'ERROR')}"
    )

    # Data counts
    data_counts = schema_state.get("data_counts", {})
    if isinstance(data_counts, dict):
        print("📊 Data Counts:")
        for table, count in data_counts.items():
            print(f"   - {table}: {count} records")

    # Critical columns check
    crewai_cols = schema_state.get("crewai_flow_state_extensions", [])
    if isinstance(crewai_cols, list):
        print(f"📋 crewai_flow_state_extensions columns: {len(crewai_cols)} total")
        required_cols = [
            "client_account_id",
            "engagement_id",
            "user_id",
            "flow_type",
            "flow_status",
        ]
        existing_cols = [col["column_name"] for col in crewai_cols]
        for req_col in required_cols:
            status = "✅" if req_col in existing_cols else "❌"
            print(f"   {status} {req_col}")

    # Assets flow_id check
    assets_flow_id = schema_state.get("assets_flow_id", {})
    if isinstance(assets_flow_id, dict):
        status = "✅" if assets_flow_id.get("exists") else "❌"
        print(f"{status} assets.flow_id column exists")

    # Migration safety analysis
    print("\n🚨 RAILWAY MIGRATION SAFETY ANALYSIS:")
    print("-" * 40)

    if analysis["safe_to_migrate"]:
        print("✅ SAFE: Database schema is ready for Railway deployment")
    else:
        print("❌ UNSAFE: Issues detected that could cause Railway deployment failures")

    if analysis["issues"]:
        print("\n🔥 CRITICAL ISSUES:")
        for issue in analysis["issues"]:
            print(f"   - {issue}")

    if analysis["recommendations"]:
        print("\n💡 RECOMMENDATIONS:")
        for rec in analysis["recommendations"]:
            print(f"   - {rec}")

    print("\n" + "=" * 80)

    # Generate Railway deployment script
    if analysis["safe_to_migrate"]:
        print("🚀 RAILWAY DEPLOYMENT READY")
        print("Your database schema matches the expected migration state.")
        print("Safe to deploy to Railway with current migrations.")
    else:
        print("⚠️  RAILWAY DEPLOYMENT BLOCKED")
        print("Fix the issues above before deploying to Railway.")
        print("Consider creating a Railway-specific migration script.")


if __name__ == "__main__":
    asyncio.run(main())
