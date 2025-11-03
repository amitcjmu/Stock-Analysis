#!/usr/bin/env python3
"""
Backfill CMDB fields and child tables for existing assets.

Updates assets table and creates child table records from cleansed_data
without requiring re-import or re-mapping.

Usage: python backfill_cmdb_fields.py <discovery_flow_id>
"""
import asyncio
import os
from datetime import datetime
from typing import Dict, Any
from uuid import UUID
from sqlalchemy import text, select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/migration_db"
)


def safe_bool_convert(value):
    """Convert string to boolean."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("true", "1", "yes")


def safe_int_convert(value, default=None):
    """Convert value to integer with safe error handling."""
    if value is None or value == "":
        return default
    try:
        return int(float(str(value)))
    except (ValueError, TypeError):
        return default


def safe_float_convert(value, default=None):
    """Convert value to float with safe error handling."""
    if value is None or value == "":
        return default
    try:
        return float(str(value))
    except (ValueError, TypeError):
        return default


def check_environment_safety():
    """
    Safety check to prevent accidental production runs.

    Checks database URL for production indicators and requires
    explicit confirmation before proceeding with data modifications.
    """
    import sys

    db_url = os.getenv("DATABASE_URL", "")

    # Check if production-like environment
    is_production = any(
        [
            "prod" in db_url.lower(),
            "production" in db_url.lower(),
            ".rds." in db_url.lower(),  # AWS RDS
            "railway.app" in db_url.lower(),  # Railway
        ]
    )

    if is_production:
        print("\n" + "⚠️  " + "=" * 76)
        print("⚠️  WARNING: PRODUCTION DATABASE DETECTED!")
        print("⚠️  " + "=" * 76)
        print(f"⚠️  Database: {db_url[:50]}...")
        print("⚠️  ")
        print("⚠️  This script will UPDATE EXISTING DATA in the database.")
        print("⚠️  Make sure you have a recent backup!")
        print("⚠️  " + "=" * 76 + "\n")

        # Require explicit confirmation
        confirmation = input("Type 'CONFIRM' to proceed (or anything else to abort): ")
        if confirmation != "CONFIRM":
            print("❌ Aborted by user - no changes made\n")
            sys.exit(1)
        print()


async def backfill_cmdb_data(flow_id: str, dry_run: bool = False):
    """Backfill CMDB fields and child tables for a discovery flow."""

    # Safety check for production environments (only if not dry-run)
    if not dry_run:
        check_environment_safety()

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print(f"\n{'='*80}")
        print(f"CMDB BACKFILL FOR FLOW: {flow_id}")
        print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE UPDATE'}")
        print(f"{'='*80}\n")

        # 1. Get all assets with their raw import records
        result = await session.execute(
            text(
                """
                SELECT
                    a.id as asset_id,
                    a.name as asset_name,
                    a.client_account_id,
                    a.engagement_id,
                    r.cleansed_data
                FROM migration.assets a
                JOIN migration.raw_import_records r ON a.raw_import_records_id = r.id
                WHERE a.discovery_flow_id = :flow_id
                ORDER BY a.name
            """
            ),
            {"flow_id": flow_id},
        )

        assets = result.fetchall()
        print(f"📊 Found {len(assets)} assets to process\n")

        if len(assets) == 0:
            print("❌ No assets found for this flow!")
            return

        updated_assets = 0
        eol_records_created = 0
        contact_records_created = 0

        for asset in assets:
            cleansed = asset.cleansed_data or {}

            # Extract CMDB fields from cleansed_data
            cmdb_fields = {
                # Business/Org
                "business_unit": cleansed.get("business_unit"),
                "vendor": cleansed.get("vendor"),
                # Application
                "application_type": cleansed.get("application_type"),
                "lifecycle": cleansed.get("lifecycle"),
                "hosting_model": cleansed.get("hosting_model"),
                # Server
                "server_role": cleansed.get("server_role"),
                "security_zone": cleansed.get("security_zone"),
                # Database
                "database_type": cleansed.get("database_type")
                or cleansed.get("primary_database_type"),
                "database_version": cleansed.get("database_version")
                or cleansed.get("primary_database_version"),
                "database_size_gb": safe_float_convert(
                    cleansed.get("database_size_gb")
                ),
                # Compliance
                "pii_flag": safe_bool_convert(cleansed.get("pii_flag")),
                "application_data_classification": cleansed.get(
                    "application_data_classification"
                )
                or cleansed.get("data_classification"),
                # Performance
                "cpu_utilization_percent_max": safe_float_convert(
                    cleansed.get("cpu_utilization_percent_max")
                    or cleansed.get("cpu_max_percent")
                ),
                "memory_utilization_percent_max": safe_float_convert(
                    cleansed.get("memory_utilization_percent_max")
                    or cleansed.get("memory_max_percent")
                ),
                "storage_free_gb": safe_float_convert(cleansed.get("storage_free_gb")),
                # Migration
                "has_saas_replacement": safe_bool_convert(
                    cleansed.get("has_saas_replacement")
                ),
                "risk_level": cleansed.get("risk_level"),
                "tshirt_size": cleansed.get("tshirt_size"),
                "proposed_treatmentplan_rationale": cleansed.get(
                    "proposed_treatmentplan_rationale"
                )
                or cleansed.get("proposed_rationale"),
                "annual_cost_estimate": safe_float_convert(
                    cleansed.get("annual_cost_estimate")
                ),
            }

            # Check if any CMDB fields have data
            has_cmdb_data = any(v is not None for v in cmdb_fields.values())

            if has_cmdb_data:
                if not dry_run:
                    # Update asset with CMDB fields
                    await session.execute(
                        text(
                            """
                            UPDATE migration.assets
                            SET
                                business_unit = :business_unit,
                                vendor = :vendor,
                                application_type = :application_type,
                                lifecycle = :lifecycle,
                                hosting_model = :hosting_model,
                                server_role = :server_role,
                                security_zone = :security_zone,
                                database_type = :database_type,
                                database_version = :database_version,
                                database_size_gb = :database_size_gb,
                                pii_flag = :pii_flag,
                                application_data_classification = :application_data_classification,
                                cpu_utilization_percent_max = :cpu_utilization_percent_max,
                                memory_utilization_percent_max = :memory_utilization_percent_max,
                                storage_free_gb = :storage_free_gb,
                                has_saas_replacement = :has_saas_replacement,
                                risk_level = :risk_level,
                                tshirt_size = :tshirt_size,
                                proposed_treatmentplan_rationale = :proposed_treatmentplan_rationale,
                                annual_cost_estimate = :annual_cost_estimate,
                                updated_at = NOW()
                            WHERE id = :asset_id
                        """
                        ),
                        {"asset_id": asset.asset_id, **cmdb_fields},
                    )
                updated_assets += 1

            # Create EOL assessment if data exists
            eol_date = cleansed.get("eol_date") or cleansed.get("end_of_life_date")
            eol_risk = cleansed.get("eol_risk_level")

            if eol_date or eol_risk:
                # Validate risk level
                valid_risk_levels = ("low", "medium", "high", "critical")
                if eol_risk and eol_risk.lower() not in valid_risk_levels:
                    print(
                        f"⚠️ Invalid EOL risk level '{eol_risk}' for {asset.asset_name}, setting to None"
                    )
                    eol_risk = None
                elif eol_risk:
                    eol_risk = eol_risk.lower()

                if not dry_run:
                    # Check if EOL record already exists
                    existing_eol = await session.execute(
                        text(
                            """
                            SELECT id FROM migration.asset_eol_assessments
                            WHERE asset_id = :asset_id
                        """
                        ),
                        {"asset_id": asset.asset_id},
                    )

                    if not existing_eol.fetchone():
                        await session.execute(
                            text(
                                """
                                INSERT INTO migration.asset_eol_assessments
                                (id, asset_id, client_account_id, engagement_id, eol_date, eol_risk_level,
                                 extended_support_available, extended_support_cost, notes, created_at, updated_at)
                                VALUES
                                (gen_random_uuid(), :asset_id, :client_id, :engagement_id, :eol_date, :eol_risk,
                                 :ext_support, :ext_cost, :notes, NOW(), NOW())
                            """
                            ),
                            {
                                "asset_id": asset.asset_id,
                                "client_id": asset.client_account_id,
                                "engagement_id": asset.engagement_id,
                                "eol_date": eol_date,
                                "eol_risk": eol_risk,
                                "ext_support": safe_bool_convert(
                                    cleansed.get("extended_support_available")
                                ),
                                "ext_cost": safe_float_convert(
                                    cleansed.get("extended_support_cost")
                                ),
                                "notes": cleansed.get("eol_notes"),
                            },
                        )
                        eol_records_created += 1

            # Create contact records if data exists
            contacts_to_create = []

            # Business owner
            if cleansed.get("business_owner_email"):
                contacts_to_create.append(
                    {
                        "type": "business_owner",
                        "name": cleansed.get("business_owner_name"),
                        "email": cleansed.get("business_owner_email"),
                    }
                )

            # Technical owner
            if cleansed.get("technical_owner_email"):
                contacts_to_create.append(
                    {
                        "type": "technical_owner",
                        "name": cleansed.get("technical_owner_name"),
                        "email": cleansed.get("technical_owner_email"),
                    }
                )

            for contact in contacts_to_create:
                if not dry_run:
                    # Check if contact already exists
                    existing_contact = await session.execute(
                        text(
                            """
                            SELECT id FROM migration.asset_contacts
                            WHERE asset_id = :asset_id AND contact_type = :contact_type
                        """
                        ),
                        {"asset_id": asset.asset_id, "contact_type": contact["type"]},
                    )

                    if not existing_contact.fetchone():
                        await session.execute(
                            text(
                                """
                                INSERT INTO migration.asset_contacts
                                (id, asset_id, client_account_id, engagement_id, contact_type,
                                 contact_name, contact_email, created_at, updated_at)
                                VALUES
                                (gen_random_uuid(), :asset_id, :client_id, :engagement_id, :contact_type,
                                 :contact_name, :contact_email, NOW(), NOW())
                            """
                            ),
                            {
                                "asset_id": asset.asset_id,
                                "client_id": asset.client_account_id,
                                "engagement_id": asset.engagement_id,
                                "contact_type": contact["type"],
                                "contact_name": contact["name"],
                                "contact_email": contact["email"],
                            },
                        )
                        contact_records_created += 1

        if not dry_run:
            await session.commit()
            print(f"\n✅ BACKFILL COMPLETE!")
        else:
            print(f"\n🔍 DRY RUN COMPLETE (no changes made)")

        print(f"\n📊 Summary:")
        print(f"   Assets updated: {updated_assets}")
        print(f"   EOL records created: {eol_records_created}")
        print(f"   Contact records created: {contact_records_created}")
        print(f"\n{'='*80}\n")

    await engine.dispose()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python backfill_cmdb_fields.py <flow_id> [--dry-run]")
        print(
            "Example: python backfill_cmdb_fields.py 0a10e113-e471-470b-8b2a-a76af88882fd"
        )
        print(
            "         python backfill_cmdb_fields.py 0a10e113-e471-470b-8b2a-a76af88882fd --dry-run"
        )
        sys.exit(1)

    flow_id = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    asyncio.run(backfill_cmdb_data(flow_id, dry_run))
