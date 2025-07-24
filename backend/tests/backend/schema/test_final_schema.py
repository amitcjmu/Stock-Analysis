#!/usr/bin/env python
"""
Final schema validation test.
"""

import asyncio

from app.core.database import AsyncSessionLocal
from sqlalchemy import text


async def test_final_schema():
    """Test that all required tables exist with correct columns."""

    print("=== FINAL SCHEMA VALIDATION ===\n")

    async with AsyncSessionLocal() as session:
        # Count total tables
        result = await session.execute(
            text(
                """
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """
            )
        )
        table_count = result.scalar()
        print(f"✅ Total tables in database: {table_count}")

        # Check critical tables exist
        critical_tables = [
            "client_accounts",
            "users",
            "engagements",
            "user_account_associations",
            "discovery_flows",
            "assets",
            "data_imports",
            "crewai_flow_state_extensions",
            "user_profiles",
            "user_roles",
            "client_access",
            "engagement_access",
            "workflow_progress",
            "enhanced_user_profiles",
            "role_permissions",
            "soft_deleted_items",
        ]

        print("\n=== CRITICAL TABLES CHECK ===")
        for table in critical_tables:
            result = await session.execute(
                f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = '{table}'
                )
            """
            )
            exists = result.scalar()
            print(f"{'✅' if exists else '❌'} {table}")

        # Check critical fields in key tables
        print("\n=== CRITICAL FIELDS CHECK ===")

        # Check Asset table has all required fields
        print("\nAsset table fields:")
        result = await session.execute(
            """
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'assets'
        """
        )
        asset_field_count = result.scalar()
        print(f"  Total fields: {asset_field_count} (should be 70+)")

        critical_asset_fields = [
            "flow_id",
            "session_id",
            "master_flow_id",
            "discovery_flow_id",
            "name",
            "description",
            "business_owner",
            "technical_owner",
            "six_r_strategy",
            "migration_status",
            "dependencies",
        ]

        for field in critical_asset_fields:
            result = await session.execute(
                f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'assets' AND column_name = '{field}'
                )
            """
            )
            exists = result.scalar()
            print(f"  {'✅' if exists else '❌'} {field}")

        # Check DiscoveryFlow fields
        print("\nDiscoveryFlow table fields:")
        critical_flow_fields = [
            "learning_scope",
            "memory_isolation_level",
            "assessment_ready",
            "phase_state",
            "agent_state",
        ]

        for field in critical_flow_fields:
            result = await session.execute(
                f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'discovery_flows' AND column_name = '{field}'
                )
            """
            )
            exists = result.scalar()
            print(f"  {'✅' if exists else '❌'} {field}")

        # Check DataImport fields
        print("\nDataImport table fields:")
        critical_import_fields = [
            "source_system",
            "error_message",
            "error_details",
            "failed_records",
        ]

        for field in critical_import_fields:
            result = await session.execute(
                f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'data_imports' AND column_name = '{field}'
                )
            """
            )
            exists = result.scalar()
            print(f"  {'✅' if exists else '❌'} {field}")

        # Check ClientAccount fields
        print("\nClientAccount table fields:")
        result = await session.execute(
            """
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'client_accounts' AND column_name = 'agent_preferences'
            )
        """
        )
        exists = result.scalar()
        print(f"  {'✅' if exists else '❌'} agent_preferences")

        # Check UserRole fields
        print("\nUserRole table fields:")
        user_role_fields = [
            "role_name",
            "description",
            "scope_type",
            "scope_client_id",
            "scope_engagement_id",
            "assigned_at",
            "assigned_by",
        ]

        for field in user_role_fields:
            result = await session.execute(
                f"""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'user_roles' AND column_name = '{field}'
                )
            """
            )
            exists = result.scalar()
            print(f"  {'✅' if exists else '❌'} {field}")

        # Check for is_mock fields (should be none)
        print("\n=== NO is_mock FIELDS CHECK ===")
        result = await session.execute(
            """
            SELECT table_name, column_name 
            FROM information_schema.columns 
            WHERE column_name = 'is_mock'
        """
        )
        is_mock_fields = result.fetchall()
        if is_mock_fields:
            print(f"❌ Found {len(is_mock_fields)} is_mock fields:")
            for table, column in is_mock_fields:
                print(f"   - {table}.{column}")
        else:
            print("✅ No is_mock fields found (correct)")

        # Check indexes
        print("\n=== KEY INDEXES CHECK ===")
        key_indexes = [
            ("assets", "ix_assets_master_flow_id"),
            ("assets", "ix_assets_name"),
            ("assets", "ix_assets_status"),
            ("user_roles", "ix_user_roles_user_id"),
            ("user_roles", "ix_user_roles_is_active"),
        ]

        for table, index in key_indexes:
            result = await session.execute(
                f"""
                SELECT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE tablename = '{table}' AND indexname = '{index}'
                )
            """
            )
            exists = result.scalar()
            print(f"{'✅' if exists else '❌'} {table}.{index}")

        print("\n=== SCHEMA VALIDATION COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(test_final_schema())
