#!/usr/bin/env python3
"""
COMPREHENSIVE CMDB Backfill Script

Backfills ALL CMDB-related fields (not just the 24 new ones) from cleansed_data.
Covers ~60+ CMDB fields across the entire assets table schema.

Usage: python backfill_all_cmdb_fields.py <discovery_flow_id> [--dry-run]
"""
import asyncio
import os
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/migration_db"
)


def safe_bool_convert(value):
    """Convert value to boolean."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("true", "1", "yes", "t", "y")


def safe_int_convert(value, default=None):
    """Convert value to integer."""
    if value is None or value == "":
        return default
    try:
        return int(float(str(value)))
    except (ValueError, TypeError):
        return default


def safe_float_convert(value, default=None):
    """Convert value to float."""
    if value is None or value == "":
        return default
    try:
        return float(str(value))
    except (ValueError, TypeError):
        return default


def extract_all_cmdb_fields(cleansed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract ALL CMDB fields from cleansed_data.
    Covers existing fields + 24 new fields from PR #833.
    """
    return {
        # ===== CORE TECHNICAL SPECS =====
        "description": cleansed.get("description") or cleansed.get("asset_description"),
        "ip_address": cleansed.get("ip_address") or cleansed.get("ip_primary"),
        "fqdn": cleansed.get("fqdn") or cleansed.get("fully_qualified_domain_name"),
        "mac_address": cleansed.get("mac_address"),
        # ===== INFRASTRUCTURE =====
        "environment": cleansed.get("environment"),
        "location": cleansed.get("location"),
        "datacenter": cleansed.get("datacenter") or cleansed.get("data_center"),
        "rack_location": cleansed.get("rack_location"),
        "availability_zone": cleansed.get("availability_zone"),
        # ===== OPERATING SYSTEM =====
        "operating_system": cleansed.get("operating_system")
        or cleansed.get("os_family"),
        "os_version": cleansed.get("os_version"),
        # ===== COMPUTE RESOURCES =====
        "cpu_cores": safe_int_convert(
            cleansed.get("cpu_cores") or cleansed.get("vcpu_cores")
        ),
        "memory_gb": safe_float_convert(cleansed.get("memory_gb")),
        "storage_gb": safe_float_convert(
            cleansed.get("storage_gb") or cleansed.get("storage_total_gb")
        ),
        "storage_used_gb": safe_float_convert(cleansed.get("storage_used_gb")),
        "storage_free_gb": safe_float_convert(cleansed.get("storage_free_gb")),
        # ===== BUSINESS CONTEXT =====
        "business_owner": cleansed.get("business_owner")
        or cleansed.get("business_owner_name"),
        "technical_owner": cleansed.get("technical_owner")
        or cleansed.get("technical_owner_name"),
        "department": cleansed.get("department"),
        "application_name": cleansed.get("application_name"),
        "technology_stack": cleansed.get("technology_stack")
        or cleansed.get("tech_stack"),
        "criticality": cleansed.get("criticality"),
        "business_criticality": cleansed.get("business_criticality"),
        # ===== MIGRATION PLANNING =====
        "six_r_strategy": cleansed.get("six_r_strategy") or cleansed.get("proposed_6r"),
        "migration_priority": safe_int_convert(cleansed.get("migration_priority")),
        "migration_complexity": cleansed.get("migration_complexity"),
        "migration_wave": safe_int_convert(cleansed.get("migration_wave")),
        # ===== PERFORMANCE METRICS =====
        "cpu_utilization_percent": safe_float_convert(
            cleansed.get("cpu_utilization_percent") or cleansed.get("avg_cpu_percent")
        ),
        "memory_utilization_percent": safe_float_convert(
            cleansed.get("memory_utilization_percent")
            or cleansed.get("memory_avg_percent")
        ),
        "cpu_utilization_percent_max": safe_float_convert(
            cleansed.get("cpu_utilization_percent_max")
            or cleansed.get("cpu_max_percent")
        ),
        "memory_utilization_percent_max": safe_float_convert(
            cleansed.get("memory_utilization_percent_max")
            or cleansed.get("memory_max_percent")
        ),
        "disk_iops": safe_float_convert(
            cleansed.get("disk_iops") or cleansed.get("iops_peak")
        ),
        "network_throughput_mbps": safe_float_convert(
            cleansed.get("network_throughput_mbps") or cleansed.get("network_peak_mbps")
        ),
        # ===== FINANCIAL =====
        "current_monthly_cost": safe_float_convert(
            cleansed.get("current_monthly_cost")
        ),
        "estimated_cloud_cost": safe_float_convert(
            cleansed.get("estimated_cloud_cost")
        ),
        "annual_cost_estimate": safe_float_convert(
            cleansed.get("annual_cost_estimate")
        ),
        # ===== PR #833 NEW FIELDS - Business/Org =====
        "business_unit": cleansed.get("business_unit"),
        "vendor": cleansed.get("vendor"),
        # ===== PR #833 NEW FIELDS - Application =====
        "application_type": cleansed.get("application_type")
        or cleansed.get("cots_or_custom"),
        "lifecycle": cleansed.get("lifecycle"),
        "hosting_model": cleansed.get("hosting_model"),
        # ===== PR #833 NEW FIELDS - Server =====
        "server_role": cleansed.get("server_role") or cleansed.get("role"),
        "security_zone": cleansed.get("security_zone"),
        # ===== PR #833 NEW FIELDS - Database =====
        "database_type": cleansed.get("database_type")
        or cleansed.get("primary_database_type"),
        "database_version": cleansed.get("database_version")
        or cleansed.get("primary_database_version"),
        "database_size_gb": safe_float_convert(cleansed.get("database_size_gb")),
        # ===== PR #833 NEW FIELDS - Compliance =====
        "pii_flag": safe_bool_convert(cleansed.get("pii_flag")),
        "application_data_classification": cleansed.get(
            "application_data_classification"
        )
        or cleansed.get("data_classification"),
        # ===== PR #833 NEW FIELDS - Migration =====
        "has_saas_replacement": safe_bool_convert(cleansed.get("has_saas_replacement")),
        "risk_level": cleansed.get("risk_level"),
        "tshirt_size": cleansed.get("tshirt_size"),
        "proposed_treatmentplan_rationale": cleansed.get(
            "proposed_treatmentplan_rationale"
        )
        or cleansed.get("proposed_rationale"),
        # ===== OTHER CMDB FIELDS =====
        "backup_policy": cleansed.get("backup_policy"),
        "tech_debt_flags": cleansed.get("tech_debt_flags"),
        "completeness_score": safe_float_convert(cleansed.get("completeness_score")),
        "quality_score": safe_float_convert(cleansed.get("quality_score")),
        "confidence_score": safe_float_convert(cleansed.get("confidence_score")),
        "assessment_readiness_score": safe_float_convert(
            cleansed.get("assessment_readiness_score")
        ),
        "complexity_score": safe_float_convert(cleansed.get("complexity_score")),
    }


async def backfill_comprehensive_cmdb(flow_id: str, dry_run: bool = False):
    """Backfill ALL CMDB fields and child tables comprehensively."""

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print(f"\n{'='*80}")
        print(f"COMPREHENSIVE CMDB BACKFILL FOR FLOW: {flow_id}")
        print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE UPDATE'}")
        print(f"Covers: ALL ~60+ CMDB fields (not just 24 new ones)")
        print(f"{'='*80}\n")

        # Get all assets with both cleansed_data AND raw_data (for emails/EOL)
        result = await session.execute(
            text(
                """
                SELECT
                    a.id as asset_id,
                    a.name as asset_name,
                    a.asset_type,
                    a.client_account_id,
                    a.engagement_id,
                    r.cleansed_data,
                    r.raw_data
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

        # Statistics
        assets_updated = 0
        eol_records = 0
        contact_records = 0
        fields_populated_count = {}

        for idx, asset in enumerate(assets, 1):
            cleansed = asset.cleansed_data or {}
            raw = asset.raw_data or {}

            if idx <= 3:  # Show first 3 for debugging
                print(f"🔍 Asset {idx}: {asset.asset_name} (Type: {asset.asset_type})")
                print(f"   Cleansed data keys: {list(cleansed.keys())[:10]}...")
                print(
                    f"   Raw data has emails: BO={bool(raw.get('business_owner_email'))}, TO={bool(raw.get('technical_owner_email'))}"
                )

            # Extract ALL CMDB fields
            cmdb_fields = extract_all_cmdb_fields(cleansed)

            # Track which fields have data
            for field, value in cmdb_fields.items():
                if value is not None:
                    fields_populated_count[field] = (
                        fields_populated_count.get(field, 0) + 1
                    )

            # Update asset
            if not dry_run:
                await session.execute(
                    text(
                        """
                        UPDATE migration.assets
                        SET
                            description = :description,
                            ip_address = :ip_address,
                            fqdn = :fqdn,
                            mac_address = :mac_address,
                            environment = :environment,
                            location = :location,
                            datacenter = :datacenter,
                            rack_location = :rack_location,
                            availability_zone = :availability_zone,
                            operating_system = :operating_system,
                            os_version = :os_version,
                            cpu_cores = :cpu_cores,
                            memory_gb = :memory_gb,
                            storage_gb = :storage_gb,
                            storage_used_gb = :storage_used_gb,
                            storage_free_gb = :storage_free_gb,
                            business_owner = :business_owner,
                            technical_owner = :technical_owner,
                            department = :department,
                            application_name = :application_name,
                            technology_stack = :technology_stack,
                            criticality = :criticality,
                            business_criticality = :business_criticality,
                            six_r_strategy = :six_r_strategy,
                            migration_priority = :migration_priority,
                            migration_complexity = :migration_complexity,
                            migration_wave = :migration_wave,
                            cpu_utilization_percent = :cpu_utilization_percent,
                            memory_utilization_percent = :memory_utilization_percent,
                            cpu_utilization_percent_max = :cpu_utilization_percent_max,
                            memory_utilization_percent_max = :memory_utilization_percent_max,
                            disk_iops = :disk_iops,
                            network_throughput_mbps = :network_throughput_mbps,
                            current_monthly_cost = :current_monthly_cost,
                            estimated_cloud_cost = :estimated_cloud_cost,
                            annual_cost_estimate = :annual_cost_estimate,
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
                            has_saas_replacement = :has_saas_replacement,
                            risk_level = :risk_level,
                            tshirt_size = :tshirt_size,
                            proposed_treatmentplan_rationale = :proposed_treatmentplan_rationale,
                            backup_policy = :backup_policy,
                            tech_debt_flags = :tech_debt_flags,
                            completeness_score = :completeness_score,
                            quality_score = :quality_score,
                            confidence_score = :confidence_score,
                            assessment_readiness_score = :assessment_readiness_score,
                            complexity_score = :complexity_score,
                            updated_at = NOW()
                        WHERE id = :asset_id
                    """
                    ),
                    {"asset_id": asset.asset_id, **cmdb_fields},
                )
            assets_updated += 1

            # ===== CREATE EOL ASSESSMENT RECORDS =====
            # Check both cleansed and raw data for EOL info
            eol_date = (
                cleansed.get("eol_date")
                or cleansed.get("end_of_life_date")
                or raw.get("eol_date")
                or raw.get("end_of_life_date")
            )
            eol_risk = cleansed.get("eol_risk_level") or raw.get("eol_risk_level")

            if eol_date or eol_risk:
                # Validate risk level
                valid_risk = ("low", "medium", "high", "critical")
                if eol_risk and eol_risk.lower() not in valid_risk:
                    eol_risk = None
                elif eol_risk:
                    eol_risk = eol_risk.lower()

                if not dry_run:
                    existing = await session.execute(
                        text(
                            "SELECT id FROM migration.asset_eol_assessments WHERE asset_id = :aid"
                        ),
                        {"aid": asset.asset_id},
                    )

                    if not existing.fetchone():
                        await session.execute(
                            text(
                                """
                                INSERT INTO migration.asset_eol_assessments
                                (id, asset_id, client_account_id, engagement_id, eol_date, eol_risk_level,
                                 extended_support_available, extended_support_cost, notes, created_at, updated_at)
                                VALUES
                                (gen_random_uuid(), :asset_id, :client_id, :eng_id, :eol_date, :eol_risk,
                                 :ext_support, :ext_cost, :notes, NOW(), NOW())
                            """
                            ),
                            {
                                "asset_id": asset.asset_id,
                                "client_id": asset.client_account_id,
                                "eng_id": asset.engagement_id,
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
                        eol_records += 1

            # ===== CREATE CONTACT RECORDS =====
            # CRITICAL: Email fields are in raw_data, not cleansed_data (data cleansing drops them)
            contacts = []

            # Business owner - check raw_data for email
            bo_email = raw.get("business_owner_email")
            if bo_email and bo_email.strip():
                contacts.append(
                    {
                        "type": "business_owner",
                        "name": raw.get("business_owner_name")
                        or cleansed.get("business_owner"),
                        "email": bo_email,
                        "phone": raw.get("business_owner_phone"),
                    }
                )

            # Technical owner - check raw_data for email
            to_email = raw.get("technical_owner_email")
            if to_email and to_email.strip():
                contacts.append(
                    {
                        "type": "technical_owner",
                        "name": raw.get("technical_owner_name")
                        or cleansed.get("technical_owner"),
                        "email": to_email,
                        "phone": raw.get("technical_owner_phone"),
                    }
                )

            for contact in contacts:
                if not dry_run:
                    existing = await session.execute(
                        text(
                            "SELECT id FROM migration.asset_contacts WHERE asset_id = :aid AND contact_type = :ctype"
                        ),
                        {"aid": asset.asset_id, "ctype": contact["type"]},
                    )

                    if not existing.fetchone():
                        await session.execute(
                            text(
                                """
                                INSERT INTO migration.asset_contacts
                                (id, asset_id, client_account_id, engagement_id, contact_type,
                                 contact_name, contact_email, contact_phone, created_at, updated_at)
                                VALUES
                                (gen_random_uuid(), :asset_id, :client_id, :eng_id, :ctype,
                                 :cname, :cemail, :cphone, NOW(), NOW())
                            """
                            ),
                            {
                                "asset_id": asset.asset_id,
                                "client_id": asset.client_account_id,
                                "eng_id": asset.engagement_id,
                                "ctype": contact["type"],
                                "cname": contact["name"],
                                "cemail": contact["email"],
                                "cphone": contact.get("phone"),
                            },
                        )
                        contact_records += 1

        # Commit if not dry run
        if not dry_run:
            await session.commit()
            print(f"\n✅ COMPREHENSIVE BACKFILL COMPLETE!\n")
        else:
            print(f"\n🔍 DRY RUN COMPLETE (no changes made)\n")

        # Summary
        print(f"{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Assets processed: {assets_updated}")
        print(f"EOL records created: {eol_records}")
        print(f"Contact records created: {contact_records}")
        print(f"\nFields with data (coverage):")
        for field, count in sorted(fields_populated_count.items(), key=lambda x: -x[1])[
            :20
        ]:
            percentage = (count / len(assets)) * 100
            print(f"  {field:40s}: {count:4d} / {len(assets):4d} ({percentage:5.1f}%)")

        if len(fields_populated_count) > 20:
            print(f"  ... and {len(fields_populated_count) - 20} more fields")

        print(f"\n{'='*80}\n")

    await engine.dispose()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python backfill_all_cmdb_fields.py <flow_id> [--dry-run]")
        print("")
        print("Example:")
        print(
            "  python backfill_all_cmdb_fields.py 0a10e113-e471-470b-8b2a-a76af88882fd --dry-run"
        )
        print(
            "  python backfill_all_cmdb_fields.py 0a10e113-e471-470b-8b2a-a76af88882fd"
        )
        print("")
        print("Covers ALL CMDB fields (~60+), not just the 24 new ones from PR #833")
        sys.exit(1)

    flow_id = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    asyncio.run(backfill_comprehensive_cmdb(flow_id, dry_run))
