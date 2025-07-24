#!/usr/bin/env python3
"""
Force migration script for Railway production database.
This script directly applies missing schema changes to fix production issues.
"""

import asyncio
import json
import os
from urllib.parse import urlparse

import asyncpg


async def main():
    """Apply missing schema changes to Railway production database."""

    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        return

    # Parse database URL
    parsed = urlparse(database_url)

    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:],  # Remove leading slash
        )

        print("✅ Connected to Railway database")

        # Check current schema
        print("\n📊 Checking current schema...")

        # Check client_accounts columns
        client_cols = await conn.fetch(
            """
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'client_accounts' 
            ORDER BY column_name
        """
        )
        existing_client_cols = [row["column_name"] for row in client_cols]
        print(f"Client accounts columns: {len(existing_client_cols)} found")

        # Check engagements columns
        engagement_cols = await conn.fetch(
            """
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'engagements' 
            ORDER BY column_name
        """
        )
        existing_engagement_cols = [row["column_name"] for row in engagement_cols]
        print(f"Engagements columns: {len(existing_engagement_cols)} found")

        # Define required columns
        required_client_cols = [
            "headquarters_location",
            "primary_contact_name",
            "primary_contact_email",
            "primary_contact_phone",
            "subscription_tier",
            "billing_contact_email",
            "settings",
            "branding",
            "business_objectives",
            "it_guidelines",
            "decision_criteria",
            "agent_preferences",
        ]

        required_engagement_cols = ["migration_scope", "team_preferences"]

        # Add missing client_accounts columns
        print("\n🔧 Adding missing client_accounts columns...")
        for col in required_client_cols:
            if col not in existing_client_cols:
                try:
                    if col in [
                        "settings",
                        "branding",
                        "business_objectives",
                        "it_guidelines",
                        "decision_criteria",
                        "agent_preferences",
                    ]:
                        await conn.execute(
                            f"ALTER TABLE client_accounts ADD COLUMN {col} JSON"
                        )
                    else:
                        size = (
                            "50"
                            if col in ["subscription_tier", "primary_contact_phone"]
                            else "255"
                        )
                        await conn.execute(
                            f"ALTER TABLE client_accounts ADD COLUMN {col} VARCHAR({size})"
                        )
                    print(f"  ✅ Added {col}")
                except Exception as e:
                    print(f"  ❌ Failed to add {col}: {e}")
            else:
                print(f"  ℹ️  {col} already exists")

        # Add missing engagements columns
        print("\n🔧 Adding missing engagements columns...")
        for col in required_engagement_cols:
            if col not in existing_engagement_cols:
                try:
                    await conn.execute(f"ALTER TABLE engagements ADD COLUMN {col} JSON")
                    print(f"  ✅ Added {col}")
                except Exception as e:
                    print(f"  ❌ Failed to add {col}: {e}")
            else:
                print(f"  ℹ️  {col} already exists")

        # Set default values
        print("\n📝 Setting default values...")

        try:
            # Set subscription_tier default
            await conn.execute(
                """
                UPDATE client_accounts 
                SET subscription_tier = 'standard' 
                WHERE subscription_tier IS NULL
            """
            )
            print("  ✅ Set subscription_tier defaults")
        except Exception as e:
            print(f"  ❌ Failed to set subscription_tier: {e}")

        # Set JSON defaults
        json_defaults = {
            "settings": "{}",
            "branding": "{}",
            "business_objectives": {
                "primary_goals": [],
                "timeframe": "",
                "success_metrics": [],
                "budget_constraints": "",
                "compliance_requirements": [],
            },
            "it_guidelines": {
                "architecture_patterns": [],
                "security_requirements": [],
                "compliance_standards": [],
                "technology_preferences": [],
                "cloud_strategy": "",
                "data_governance": {},
            },
            "decision_criteria": {
                "risk_tolerance": "medium",
                "cost_sensitivity": "medium",
                "innovation_appetite": "moderate",
                "timeline_pressure": "medium",
                "quality_vs_speed": "balanced",
                "technical_debt_tolerance": "low",
            },
            "agent_preferences": {
                "confidence_thresholds": {
                    "field_mapping": 0.8,
                    "data_classification": 0.75,
                    "risk_assessment": 0.85,
                    "migration_strategy": 0.9,
                },
                "learning_preferences": ["conservative", "accuracy_focused"],
                "custom_prompts": {},
                "notification_preferences": {
                    "confidence_alerts": True,
                    "learning_updates": False,
                    "error_notifications": True,
                },
            },
        }

        for col, default_val in json_defaults.items():
            try:
                await conn.execute(
                    f"""
                    UPDATE client_accounts 
                    SET {col} = $1::json 
                    WHERE {col} IS NULL
                """,
                    json.dumps(default_val),
                )
                print(f"  ✅ Set {col} defaults")
            except Exception as e:
                print(f"  ❌ Failed to set {col}: {e}")

        # Set engagement defaults
        engagement_defaults = {
            "migration_scope": {
                "target_clouds": [],
                "migration_strategies": [],
                "excluded_systems": [],
                "included_environments": [],
                "business_units": [],
                "geographic_scope": [],
                "timeline_constraints": {},
            },
            "team_preferences": {
                "stakeholders": [],
                "decision_makers": [],
                "technical_leads": [],
                "communication_style": "formal",
                "reporting_frequency": "weekly",
                "preferred_meeting_times": [],
                "escalation_contacts": [],
                "project_methodology": "agile",
            },
        }

        for col, default_val in engagement_defaults.items():
            try:
                await conn.execute(
                    f"""
                    UPDATE engagements 
                    SET {col} = $1::json 
                    WHERE {col} IS NULL
                """,
                    json.dumps(default_val),
                )
                print(f"  ✅ Set {col} defaults")
            except Exception as e:
                print(f"  ❌ Failed to set {col}: {e}")

        print("\n🎉 Schema fix completed successfully!")

        # Verify fix
        print("\n🔍 Verifying fix...")
        try:
            await conn.fetch(
                """
                SELECT id, name, headquarters_location, settings 
                FROM client_accounts 
                LIMIT 1
            """
            )
            print("  ✅ Client accounts query successful")
        except Exception as e:
            print(f"  ❌ Client accounts still failing: {e}")

        try:
            await conn.fetch(
                """
                SELECT id, name, migration_scope 
                FROM engagements 
                LIMIT 1
            """
            )
            print("  ✅ Engagements query successful")
        except Exception as e:
            print(f"  ❌ Engagements still failing: {e}")

        await conn.close()
        print("\n✅ Database connection closed")

    except Exception as e:
        print(f"❌ Error connecting to database: {e}")


if __name__ == "__main__":
    asyncio.run(main())
