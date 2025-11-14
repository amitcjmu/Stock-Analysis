#!/usr/bin/env python3
"""
Script to check CMDB fields population in assets table and child tables.
"""
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Database URL (modify if needed)
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/migration_db"
)


async def check_cmdb_data(flow_id: str):
    """Check CMDB fields and child table data for a specific flow."""

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print(f"\n{'='*80}")
        print(f"CMDB DATA CHECK FOR FLOW: {flow_id}")
        print(f"{'='*80}\n")

        # 1. Check total assets for this flow
        result = await session.execute(
            text(
                """
                SELECT COUNT(*) as total_assets
                FROM migration.assets
                WHERE discovery_flow_id = :flow_id
            """
            ),
            {"flow_id": flow_id},
        )
        total_assets = result.scalar()
        print(f"📊 Total Assets: {total_assets}\n")

        if total_assets == 0:
            print("❌ No assets found for this flow!")
            return

        # 2. Check CMDB fields population (sample 5 assets)
        print("=" * 80)
        print("CMDB FIELDS CHECK (First 5 Assets)")
        print("=" * 80)

        result = await session.execute(
            text(
                """
                SELECT
                    id, name, asset_type,
                    -- CMDB Business/Org fields
                    business_unit, vendor,
                    -- CMDB Application fields
                    application_type, lifecycle, hosting_model,
                    -- CMDB Server fields
                    server_role, security_zone,
                    -- CMDB Database fields
                    database_type, database_version, database_size_gb,
                    -- CMDB Compliance fields
                    pii_flag, application_data_classification,
                    -- CMDB Performance fields
                    cpu_utilization_percent_max, memory_utilization_percent_max, storage_free_gb,
                    -- CMDB Migration fields
                    has_saas_replacement, risk_level, tshirt_size,
                    proposed_treatmentplan_rationale, annual_cost_estimate
                FROM migration.assets
                WHERE discovery_flow_id = :flow_id
                LIMIT 5
            """
            ),
            {"flow_id": flow_id},
        )

        assets = result.fetchall()
        for asset in assets:
            print(f"\n📦 Asset: {asset.name} (Type: {asset.asset_type})")
            print(f"   Business Unit: {asset.business_unit}")
            print(f"   Vendor: {asset.vendor}")
            print(f"   Application Type: {asset.application_type}")
            print(f"   Lifecycle: {asset.lifecycle}")
            print(f"   Hosting Model: {asset.hosting_model}")
            print(f"   Server Role: {asset.server_role}")
            print(f"   Security Zone: {asset.security_zone}")
            print(f"   Database Type: {asset.database_type}")
            print(f"   PII Flag: {asset.pii_flag}")
            print(f"   Data Classification: {asset.application_data_classification}")
            print(f"   Risk Level: {asset.risk_level}")
            print(f"   T-Shirt Size: {asset.tshirt_size}")
            print(f"   Annual Cost: {asset.annual_cost_estimate}")

        # 3. Check how many assets have at least one CMDB field populated
        print(f"\n{'='*80}")
        print("CMDB FIELD POPULATION SUMMARY")
        print("=" * 80)

        result = await session.execute(
            text(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(business_unit) as has_business_unit,
                    COUNT(vendor) as has_vendor,
                    COUNT(application_type) as has_app_type,
                    COUNT(lifecycle) as has_lifecycle,
                    COUNT(hosting_model) as has_hosting,
                    COUNT(server_role) as has_server_role,
                    COUNT(security_zone) as has_security_zone,
                    COUNT(database_type) as has_db_type,
                    COUNT(pii_flag) as has_pii_flag,
                    COUNT(application_data_classification) as has_data_class,
                    COUNT(risk_level) as has_risk_level,
                    COUNT(tshirt_size) as has_tshirt,
                    COUNT(annual_cost_estimate) as has_cost
                FROM migration.assets
                WHERE discovery_flow_id = :flow_id
            """
            ),
            {"flow_id": flow_id},
        )

        summary = result.fetchone()
        print(f"\n📊 Assets with CMDB fields populated (out of {summary.total}):")
        print(f"   Business Unit: {summary.has_business_unit}")
        print(f"   Vendor: {summary.has_vendor}")
        print(f"   Application Type: {summary.has_app_type}")
        print(f"   Lifecycle: {summary.has_lifecycle}")
        print(f"   Hosting Model: {summary.has_hosting}")
        print(f"   Server Role: {summary.has_server_role}")
        print(f"   Security Zone: {summary.has_security_zone}")
        print(f"   Database Type: {summary.has_db_type}")
        print(f"   PII Flag: {summary.has_pii_flag}")
        print(f"   Data Classification: {summary.has_data_class}")
        print(f"   Risk Level: {summary.has_risk_level}")
        print(f"   T-Shirt Size: {summary.has_tshirt}")
        print(f"   Annual Cost: {summary.has_cost}")

        # 4. Check asset_eol_assessments table
        print(f"\n{'='*80}")
        print("CHILD TABLE: asset_eol_assessments")
        print("=" * 80)

        result = await session.execute(
            text(
                """
                SELECT COUNT(*) as total
                FROM migration.asset_eol_assessments ae
                JOIN migration.assets a ON ae.asset_id = a.id
                WHERE a.discovery_flow_id = :flow_id
            """
            ),
            {"flow_id": flow_id},
        )
        eol_count = result.scalar()
        print(f"\n📊 Total EOL Assessment Records: {eol_count}")

        if eol_count > 0:
            result = await session.execute(
                text(
                    """
                    SELECT
                        a.name as asset_name,
                        ae.eol_date,
                        ae.eol_risk_level,
                        ae.extended_support_available,
                        ae.notes
                    FROM migration.asset_eol_assessments ae
                    JOIN migration.assets a ON ae.asset_id = a.id
                    WHERE a.discovery_flow_id = :flow_id
                    LIMIT 5
                """
                ),
                {"flow_id": flow_id},
            )
            for row in result.fetchall():
                print(f"\n   Asset: {row.asset_name}")
                print(f"   EOL Date: {row.eol_date}")
                print(f"   Risk Level: {row.eol_risk_level}")
                print(f"   Extended Support: {row.extended_support_available}")
        else:
            print("❌ No EOL assessment records found!")

        # 5. Check asset_contacts table
        print(f"\n{'='*80}")
        print("CHILD TABLE: asset_contacts")
        print("=" * 80)

        result = await session.execute(
            text(
                """
                SELECT COUNT(*) as total
                FROM migration.asset_contacts ac
                JOIN migration.assets a ON ac.asset_id = a.id
                WHERE a.discovery_flow_id = :flow_id
            """
            ),
            {"flow_id": flow_id},
        )
        contact_count = result.scalar()
        print(f"\n📊 Total Asset Contact Records: {contact_count}")

        if contact_count > 0:
            result = await session.execute(
                text(
                    """
                    SELECT
                        a.name as asset_name,
                        ac.contact_type,
                        ac.contact_name,
                        ac.contact_email
                    FROM migration.asset_contacts ac
                    JOIN migration.assets a ON ac.asset_id = a.id
                    WHERE a.discovery_flow_id = :flow_id
                    LIMIT 10
                """
                ),
                {"flow_id": flow_id},
            )
            for row in result.fetchall():
                print(f"\n   Asset: {row.asset_name}")
                print(f"   Type: {row.contact_type}")
                print(f"   Name: {row.contact_name}")
                print(f"   Email: {row.contact_email}")
        else:
            print("❌ No contact records found!")

        # 6. Check raw_import_records for EOL/contact data
        print(f"\n{'='*80}")
        print("RAW DATA CHECK (EOL & Contact Fields)")
        print("=" * 80)

        result = await session.execute(
            text(
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(raw_data->>'eol_date') as has_eol_date,
                    COUNT(raw_data->>'eol_risk_level') as has_eol_risk,
                    COUNT(raw_data->>'business_owner_name') as has_owner_name,
                    COUNT(raw_data->>'business_owner_email') as has_owner_email,
                    COUNT(raw_data->>'technical_owner_name') as has_tech_name,
                    COUNT(raw_data->>'technical_owner_email') as has_tech_email
                FROM migration.raw_import_records
                WHERE discovery_flow_id = :flow_id
            """
            ),
            {"flow_id": flow_id},
        )

        raw_summary = result.fetchone()
        print(f"\n📊 Raw records with EOL/Contact data (out of {raw_summary.total}):")
        print(f"   EOL Date: {raw_summary.has_eol_date}")
        print(f"   EOL Risk Level: {raw_summary.has_eol_risk}")
        print(f"   Business Owner Name: {raw_summary.has_owner_name}")
        print(f"   Business Owner Email: {raw_summary.has_owner_email}")
        print(f"   Technical Owner Name: {raw_summary.has_tech_name}")
        print(f"   Technical Owner Email: {raw_summary.has_tech_email}")

        print(f"\n{'='*80}")
        print("CHECK COMPLETE")
        print(f"{'='*80}\n")

    await engine.dispose()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python check_cmdb_data.py <flow_id>")
        print("Example: python check_cmdb_data.py 0a10e113-e471-470b-8b2a-a76af88882fd")
        sys.exit(1)

    flow_id = sys.argv[1]
    asyncio.run(check_cmdb_data(flow_id))
