#!/usr/bin/env python3
"""
Unified Model Planning Script

This script analyzes the differences between the `assets` and `cmdb_assets` models
and plans the data unification strategy for the Data Model Consolidation project.
"""

import asyncio
import os
import sys

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import AsyncSessionLocal
from sqlalchemy import text


async def analyze_model_differences():
    """Compare assets vs cmdb_assets table schemas and plan unification."""

    async with AsyncSessionLocal() as session:
        print("🔍 **UNIFIED MODEL ANALYSIS**")
        print("=" * 50)

        # Get table schemas
        inspector_query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_schema = 'migration' AND table_name IN ('assets', 'cmdb_assets')
        ORDER BY table_name, ordinal_position;
        """

        result = await session.execute(text(inspector_query))
        columns_info = result.fetchall()

        # Organize by table
        assets_columns = {}
        cmdb_assets_columns = {}

        for row in columns_info:
            col_name, data_type, nullable, default = row
            col_info = {
                "data_type": data_type,
                "nullable": nullable,
                "default": default,
            }

            # Determine which table this column belongs to
            table_check = await session.execute(
                text(
                    f"""
                SELECT table_name FROM information_schema.columns 
                WHERE table_schema = 'migration' 
                AND column_name = '{col_name}' 
                AND table_name IN ('assets', 'cmdb_assets')
            """
                )
            )

            tables = [r[0] for r in table_check.fetchall()]

            if "assets" in tables:
                assets_columns[col_name] = col_info
            if "cmdb_assets" in tables:
                cmdb_assets_columns[col_name] = col_info

        print("\n📊 **SCHEMA COMPARISON**")
        print(f"Assets table columns: {len(assets_columns)}")
        print(f"CMDB Assets table columns: {len(cmdb_assets_columns)}")

        # Find common columns
        common_columns = set(assets_columns.keys()) & set(cmdb_assets_columns.keys())
        assets_only = set(assets_columns.keys()) - set(cmdb_assets_columns.keys())
        cmdb_only = set(cmdb_assets_columns.keys()) - set(assets_columns.keys())

        print("\n🔗 **COLUMN OVERLAP ANALYSIS**")
        print(f"Common columns: {len(common_columns)}")
        print(f"Assets-only columns: {len(assets_only)}")
        print(f"CMDB-only columns: {len(cmdb_only)}")

        # Show common columns (these can be directly migrated)
        print(f"\n✅ **DIRECT MIGRATION COLUMNS** ({len(common_columns)})")
        for col in sorted(common_columns):
            print(f"  - {col}")

        # Show assets-only columns (enhanced capabilities)
        print(f"\n🚀 **ENHANCED CAPABILITIES** (Assets-only: {len(assets_only)})")
        ai_fields = [
            col
            for col in assets_only
            if "ai" in col.lower()
            or "intelligent" in col.lower()
            or "confidence" in col.lower()
        ]
        app_fields = [
            col
            for col in assets_only
            if "application" in col.lower()
            or "programming" in col.lower()
            or "framework" in col.lower()
        ]
        business_fields = [
            col
            for col in assets_only
            if "business" in col.lower()
            or "department" in col.lower()
            or "owner" in col.lower()
        ]

        if ai_fields:
            print(f"  📱 AI/Intelligence fields ({len(ai_fields)}):")
            for col in ai_fields:
                print(f"    - {col}")

        if app_fields:
            print(f"  💻 Application fields ({len(app_fields)}):")
            for col in app_fields:
                print(f"    - {col}")

        if business_fields:
            print(f"  🏢 Business fields ({len(business_fields)}):")
            for col in business_fields:
                print(f"    - {col}")

        other_assets_only = (
            set(assets_only) - set(ai_fields) - set(app_fields) - set(business_fields)
        )
        if other_assets_only:
            print(f"  🔧 Other enhanced fields ({len(other_assets_only)}):")
            for col in sorted(other_assets_only):
                print(f"    - {col}")

        # Show cmdb-only columns (need mapping or can be dropped)
        print(f"\n⚠️  **CMDB-ONLY COLUMNS** (Need mapping: {len(cmdb_only)})")
        for col in sorted(cmdb_only):
            print(f"  - {col}")

        # Check data distribution
        print("\n📈 **DATA DISTRIBUTION**")

        assets_count = await session.execute(
            text("SELECT COUNT(*) FROM migration.assets")
        )
        cmdb_count = await session.execute(
            text("SELECT COUNT(*) FROM migration.cmdb_assets")
        )

        assets_total = assets_count.scalar()
        cmdb_total = cmdb_count.scalar()

        print(f"Assets table: {assets_total} records")
        print(f"CMDB Assets table: {cmdb_total} records")

        if cmdb_total > 0:
            # Sample data analysis
            sample_query = """
            SELECT name, asset_type, application_name, technology_stack, 
                   business_owner, migration_priority, six_r_strategy
            FROM migration.cmdb_assets 
            LIMIT 5
            """
            samples = await session.execute(text(sample_query))

            print("\n📋 **SAMPLE CMDB DATA** (First 5 records)")
            for row in samples.fetchall():
                print(f"  - {row[0]} | {row[1]} | App: {row[2]} | Tech: {row[3]}")

        # Plan the migration mapping
        print("\n🗺️  **MIGRATION PLAN**")
        print(f"1. **Direct Migration**: {len(common_columns)} fields map directly")
        print(
            f"2. **Enhanced Fields**: {len(assets_only)} new capabilities from Assets model"
        )
        print(
            f"3. **Data Preservation**: {cmdb_total} records to migrate to unified model"
        )
        print("4. **Table Consolidation**: Drop cmdb_assets after successful migration")

        # Critical fields mapping
        critical_fields = ["name", "asset_type", "client_account_id", "engagement_id"]
        missing_critical = [
            field for field in critical_fields if field not in common_columns
        ]

        if missing_critical:
            print(f"\n❌ **CRITICAL FIELDS MISSING**: {missing_critical}")
            print("   Migration cannot proceed without these fields!")
        else:
            print("\n✅ **CRITICAL FIELDS VERIFIED**: All essential fields present")

        # Heuristic population opportunities
        print("\n🧠 **HEURISTIC POPULATION OPPORTUNITIES**")
        print("During migration, we can intelligently populate enhanced fields:")
        print("  - intelligent_asset_type: Detect applications vs infrastructure")
        print("  - application_type: Parse application patterns from names")
        print("  - framework: Extract from technology_stack field")
        print("  - discovery_method: Set to 'data_import' for migrated records")

        return {
            "common_columns": len(common_columns),
            "assets_only": len(assets_only),
            "cmdb_only": len(cmdb_only),
            "migration_ready": len(missing_critical) == 0,
            "data_to_migrate": cmdb_total,
        }


async def plan_foreign_key_updates():
    """Plan the foreign key constraint updates needed."""

    async with AsyncSessionLocal() as session:
        print("\n🔗 **FOREIGN KEY ANALYSIS**")
        print("=" * 50)

        # Find all foreign keys pointing to cmdb_assets
        fk_query = """
        SELECT 
            tc.table_name,
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'migration'
            AND ccu.table_name = 'cmdb_assets';
        """

        result = await session.execute(text(fk_query))
        foreign_keys = result.fetchall()

        if foreign_keys:
            print(f"Found {len(foreign_keys)} foreign key constraints to update:")
            for fk in foreign_keys:
                table, constraint, column, ref_table, ref_column = fk
                print(
                    f"  - {table}.{column} → {ref_table}.{ref_column} (constraint: {constraint})"
                )
        else:
            print("No foreign key constraints found pointing to cmdb_assets")

        return foreign_keys


if __name__ == "__main__":

    async def main():
        print("🚀 **UNIFIED MODEL PLANNING ANALYSIS**")
        print("This script analyzes the consolidation requirements\n")

        try:
            # Analyze model differences
            analysis = await analyze_model_differences()

            # Plan foreign key updates
            foreign_keys = await plan_foreign_key_updates()

            print("\n📊 **SUMMARY**")
            print("=" * 50)
            print(f"✅ Common fields: {analysis['common_columns']}")
            print(f"🚀 Enhanced capabilities: {analysis['assets_only']}")
            print(f"⚠️  Fields needing review: {analysis['cmdb_only']}")
            print(f"📦 Records to migrate: {analysis['data_to_migrate']}")
            print(f"🔗 Foreign keys to update: {len(foreign_keys)}")
            print(
                f"🎯 Migration ready: {'Yes' if analysis['migration_ready'] else 'No'}"
            )

            if analysis["migration_ready"]:
                print("\n✅ **READY TO PROCEED**")
                print("All critical fields verified. Migration can proceed safely.")
            else:
                print("\n❌ **MIGRATION BLOCKED**")
                print("Critical fields missing. Review schema before proceeding.")

        except Exception as e:
            print(f"❌ **ERROR**: {str(e)}")
            print("Make sure database is running and accessible.")

    asyncio.run(main())
