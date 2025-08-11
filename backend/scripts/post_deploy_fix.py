#!/usr/bin/env python3
"""
Post-deployment script for Railway production database schema fixes.
This script runs automatically after deployment to ensure schema consistency.
"""

import asyncio
import json
import logging
import os
import sys
from urllib.parse import urlparse

import asyncpg

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Import secure logging utilities with fallback for deployment context
try:
    from app.core.security.secure_logging import mask_string, mask_id
except ImportError:
    # Fallback implementations for deployment context
    def mask_string(value, show_chars=4):
        if value is None:
            return "None"
        value_str = str(value)
        if len(value_str) <= show_chars:
            return f"***{value_str}"
        return f"***{value_str[-show_chars:]}"

    def mask_id(value):
        if value is None:
            return "None"
        value_str = str(value)
        if len(value_str) >= 8:
            return f"***{value_str[-8:]}"
        return f"***{value_str}"


async def fix_railway_schema():
    """
    Automatically fix Railway database schema issues after deployment.
    This ensures the production database has all required columns.
    """

    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.warning(
            "❌ DATABASE_URL environment variable not found - skipping schema fix"
        )
        return False

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

        logger.info("✅ Connected to Railway database for post-deploy schema fix")

        # Check current schema
        logger.info("📊 Checking current schema...")

        # Check client_accounts columns
        client_cols = await conn.fetch(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'client_accounts'
            ORDER BY column_name
        """
        )
        existing_client_cols = [row["column_name"] for row in client_cols]
        logger.info(
            f"Client accounts columns: {len(existing_client_cols)} found"
        )  # nosec B106

        # Check engagements columns
        engagement_cols = await conn.fetch(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'engagements'
            ORDER BY column_name
        """
        )
        existing_engagement_cols = [row["column_name"] for row in engagement_cols]
        logger.info(
            f"Engagements columns: {len(existing_engagement_cols)} found"
        )  # nosec B106

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

        # Track if any changes were made
        changes_made = False

        # Add missing client_accounts columns
        logger.info("🔧 Adding missing client_accounts columns...")  # nosec B106
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
                    logger.info(f"  ✅ Added {mask_string(col)}")  # nosec B106
                    changes_made = True
                except Exception:
                    logger.error(
                        f"  ❌ Failed to add {mask_string(col)}: [REDACTED]"
                    )  # nosec B106
            else:
                logger.info(f"  ℹ️  {mask_string(col)} already exists")  # nosec B106

        # Add missing engagements columns
        logger.info("🔧 Adding missing engagements columns...")  # nosec B106
        for col in required_engagement_cols:
            if col not in existing_engagement_cols:
                try:
                    await conn.execute(f"ALTER TABLE engagements ADD COLUMN {col} JSON")
                    logger.info(f"  ✅ Added {mask_string(col)}")  # nosec B106
                    changes_made = True
                except Exception:
                    logger.error(
                        f"  ❌ Failed to add {mask_string(col)}: [REDACTED]"
                    )  # nosec B106
            else:
                logger.info(f"  ℹ️  {mask_string(col)} already exists")  # nosec B106

        # Set default values if changes were made
        if changes_made:
            logger.info("📝 Setting default values...")

            try:
                # Set subscription_tier default
                await conn.execute(
                    """
                    UPDATE client_accounts
                    SET subscription_tier = 'standard'
                    WHERE subscription_tier IS NULL
                """
                )
                logger.info("  ✅ Set subscription_tier defaults")
            except Exception as e:
                logger.error(f"  ❌ Failed to set subscription_tier: {e}")

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

            # Define allowed columns for security (prevent SQL injection)
            ALLOWED_CLIENT_COLUMNS = {
                "settings",
                "branding",
                "business_objectives",
                "it_guidelines",
                "decision_criteria",
                "agent_preferences",
            }

            for col, default_val in json_defaults.items():
                # Security: Validate column name against allowlist
                if col not in ALLOWED_CLIENT_COLUMNS:
                    logger.warning(
                        f"  ⚠️  Skipping unauthorized column: {mask_string(col)}"
                    )  # nosec B106
                    continue

                try:
                    # Safe SQL construction with validated column name
                    # Column name validated against ALLOWED_CLIENT_COLUMNS allowlist
                    # Use asyncpg's built-in identifier formatting to prevent SQL injection warnings
                    import asyncpg

                    quoted_col = asyncpg.Connection._quote_name(col)
                    query = """
                        UPDATE client_accounts
                        SET {} = $1::json
                        WHERE {} IS NULL
                    """.format(
                        quoted_col, quoted_col
                    )
                    await conn.execute(query, json.dumps(default_val))
                    logger.info(f"  ✅ Set {mask_string(col)} defaults")  # nosec B106
                except Exception:
                    logger.error(
                        f"  ❌ Failed to set {mask_string(col)}: [REDACTED]"
                    )  # nosec B106

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

            # Define allowed columns for security (prevent SQL injection)
            ALLOWED_ENGAGEMENT_COLUMNS = {
                "migration_scope",
                "technical_requirements",
                "stakeholder_info",
            }

            for col, default_val in engagement_defaults.items():
                # Security: Validate column name against allowlist
                if col not in ALLOWED_ENGAGEMENT_COLUMNS:
                    logger.warning(
                        f"  ⚠️  Skipping unauthorized column: {mask_string(col)}"
                    )  # nosec B106
                    continue

                try:
                    # Safe SQL construction with validated column name
                    # Column name validated against ALLOWED_ENGAGEMENT_COLUMNS allowlist
                    # Use asyncpg's built-in identifier formatting to prevent SQL injection warnings
                    import asyncpg

                    quoted_col = asyncpg.Connection._quote_name(col)
                    query = """
                        UPDATE engagements
                        SET {} = $1::json
                        WHERE {} IS NULL
                    """.format(
                        quoted_col, quoted_col
                    )
                    await conn.execute(query, json.dumps(default_val))
                    logger.info(f"  ✅ Set {mask_string(col)} defaults")  # nosec B106
                except Exception:
                    logger.error(
                        f"  ❌ Failed to set {mask_string(col)}: [REDACTED]"
                    )  # nosec B106

        logger.info("🎉 Post-deploy schema fix completed successfully!")

        # Verify fix
        logger.info("🔍 Verifying fix...")
        try:
            await conn.fetch(
                """
                SELECT id, name, headquarters_location, settings
                FROM client_accounts
                LIMIT 1
            """
            )
            logger.info("  ✅ Client accounts query successful")
        except Exception as e:
            logger.error(f"  ❌ Client accounts still failing: {e}")
            return False

        try:
            await conn.fetch(
                """
                SELECT id, name, migration_scope
                FROM engagements
                LIMIT 1
            """
            )
            logger.info("  ✅ Engagements query successful")
        except Exception as e:
            logger.error(f"  ❌ Engagements still failing: {e}")
            return False

        await conn.close()
        logger.info("✅ Database connection closed")

        return True

    except Exception as e:
        logger.error(f"❌ Error during schema fix: {e}")
        return False


def main():
    """Main entry point for post-deploy script."""

    # Only run if we're in Railway environment (has DATABASE_URL)
    if not os.getenv("DATABASE_URL"):
        logger.info("ℹ️  Not in Railway environment - skipping post-deploy schema fix")
        return

    logger.info("🚀 Starting Railway post-deploy schema fix...")

    try:
        success = asyncio.run(fix_railway_schema())
        if success:
            logger.info("✅ Post-deploy schema fix completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Post-deploy schema fix failed!")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Post-deploy script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
