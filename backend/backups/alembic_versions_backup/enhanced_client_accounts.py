"""Add enhanced client account and engagement fields

Revision ID: enhanced_client_accounts
Revises: 078ab506c9da
Create Date: 2025-06-27 17:30:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "enhanced_client_accounts"
down_revision = "078ab506c9da"
branch_labels = None
depends_on = None


def upgrade():
    """Add enhanced fields to client_accounts and engagements tables."""

    # =============================================================================
    # ENHANCE CLIENT_ACCOUNTS TABLE
    # =============================================================================

    # Add essential client account fields
    op.add_column(
        "client_accounts", sa.Column("slug", sa.String(100), unique=True, nullable=True)
    )
    op.add_column(
        "client_accounts", sa.Column("industry", sa.String(100), nullable=True)
    )
    op.add_column(
        "client_accounts", sa.Column("company_size", sa.String(50), nullable=True)
    )
    op.add_column(
        "client_accounts",
        sa.Column("headquarters_location", sa.String(255), nullable=True),
    )
    op.add_column(
        "client_accounts",
        sa.Column("primary_contact_name", sa.String(255), nullable=True),
    )
    op.add_column(
        "client_accounts",
        sa.Column("primary_contact_email", sa.String(255), nullable=True),
    )
    op.add_column(
        "client_accounts",
        sa.Column("primary_contact_phone", sa.String(50), nullable=True),
    )
    op.add_column(
        "client_accounts",
        sa.Column(
            "subscription_tier", sa.String(50), default="standard", nullable=True
        ),
    )
    op.add_column(
        "client_accounts",
        sa.Column("billing_contact_email", sa.String(255), nullable=True),
    )

    # Add JSON fields for complex data
    op.add_column(
        "client_accounts",
        sa.Column("settings", sa.JSON(), default=lambda: {}, nullable=True),
    )
    op.add_column(
        "client_accounts",
        sa.Column("branding", sa.JSON(), default=lambda: {}, nullable=True),
    )
    op.add_column(
        "client_accounts",
        sa.Column(
            "business_objectives",
            sa.JSON(),
            default=lambda: {
                "primary_goals": [],
                "timeframe": "",
                "success_metrics": [],
                "budget_constraints": "",
                "compliance_requirements": [],
            },
            nullable=True,
        ),
    )
    op.add_column(
        "client_accounts",
        sa.Column(
            "it_guidelines",
            sa.JSON(),
            default=lambda: {
                "architecture_patterns": [],
                "security_requirements": [],
                "compliance_standards": [],
                "technology_preferences": [],
                "cloud_strategy": "",
                "data_governance": {},
            },
            nullable=True,
        ),
    )
    op.add_column(
        "client_accounts",
        sa.Column(
            "decision_criteria",
            sa.JSON(),
            default=lambda: {
                "risk_tolerance": "medium",
                "cost_sensitivity": "medium",
                "innovation_appetite": "moderate",
                "timeline_pressure": "medium",
                "quality_vs_speed": "balanced",
                "technical_debt_tolerance": "low",
            },
            nullable=True,
        ),
    )
    op.add_column(
        "client_accounts",
        sa.Column(
            "agent_preferences",
            sa.JSON(),
            default=lambda: {
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
            nullable=True,
        ),
    )

    # Add audit fields - first as nullable, then populate and make not null
    op.add_column("client_accounts", sa.Column("is_mock", sa.Boolean(), nullable=True))
    op.add_column(
        "client_accounts",
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Populate is_mock with default value for existing records
    op.execute("UPDATE client_accounts SET is_mock = false WHERE is_mock IS NULL")

    # Now make it not null
    op.alter_column(
        "client_accounts", "is_mock", nullable=False, server_default=sa.text("false")
    )

    # Ensure is_active has proper default
    op.alter_column(
        "client_accounts", "is_active", nullable=False, server_default=sa.text("true")
    )

    # Create indexes
    op.create_index("ix_client_accounts_slug", "client_accounts", ["slug"], unique=True)
    op.create_index("ix_client_accounts_is_active", "client_accounts", ["is_active"])
    op.create_index("ix_client_accounts_is_mock", "client_accounts", ["is_mock"])

    # Create foreign key for created_by
    op.create_foreign_key(
        "client_accounts_created_by_fkey",
        "client_accounts",
        "users",
        ["created_by"],
        ["id"],
    )

    # Update existing client accounts to have slugs
    op.execute(
        """
        UPDATE client_accounts 
        SET slug = LOWER(REPLACE(REPLACE(name, ' ', '-'), '&', 'and'))
        WHERE slug IS NULL
    """
    )

    # =============================================================================
    # ENHANCE ENGAGEMENTS TABLE
    # =============================================================================

    # Add essential engagement fields
    op.add_column("engagements", sa.Column("slug", sa.String(100), nullable=True))
    op.add_column(
        "engagements",
        sa.Column("engagement_type", sa.String(50), default="migration", nullable=True),
    )
    op.add_column(
        "engagements",
        sa.Column("status", sa.String(50), default="active", nullable=True),
    )
    op.add_column(
        "engagements",
        sa.Column("priority", sa.String(20), default="medium", nullable=True),
    )

    # Add timeline fields
    op.add_column(
        "engagements",
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "engagements",
        sa.Column("target_completion_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "engagements",
        sa.Column("actual_completion_date", sa.DateTime(timezone=True), nullable=True),
    )

    # Add team and contact fields
    op.add_column(
        "engagements",
        sa.Column("engagement_lead_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "engagements", sa.Column("client_contact_name", sa.String(255), nullable=True)
    )
    op.add_column(
        "engagements", sa.Column("client_contact_email", sa.String(255), nullable=True)
    )

    # Add JSON fields for complex data
    op.add_column(
        "engagements",
        sa.Column("settings", sa.JSON(), default=lambda: {}, nullable=True),
    )
    op.add_column(
        "engagements",
        sa.Column(
            "migration_scope",
            sa.JSON(),
            default=lambda: {
                "target_clouds": [],
                "migration_strategies": [],
                "excluded_systems": [],
                "included_environments": [],
                "business_units": [],
                "geographic_scope": [],
                "timeline_constraints": {},
            },
            nullable=True,
        ),
    )
    op.add_column(
        "engagements",
        sa.Column(
            "team_preferences",
            sa.JSON(),
            default=lambda: {
                "stakeholders": [],
                "decision_makers": [],
                "technical_leads": [],
                "communication_style": "formal",
                "reporting_frequency": "weekly",
                "preferred_meeting_times": [],
                "escalation_contacts": [],
                "project_methodology": "agile",
            },
            nullable=True,
        ),
    )

    # Add audit fields - first as nullable, then populate and make not null
    op.add_column("engagements", sa.Column("is_mock", sa.Boolean(), nullable=True))
    op.add_column(
        "engagements",
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Populate is_mock with default value for existing records
    op.execute("UPDATE engagements SET is_mock = false WHERE is_mock IS NULL")

    # Now make it not null
    op.alter_column(
        "engagements", "is_mock", nullable=False, server_default=sa.text("false")
    )

    # Ensure is_active has proper default
    op.alter_column(
        "engagements", "is_active", nullable=False, server_default=sa.text("true")
    )

    # Create indexes
    op.create_index("ix_engagements_status", "engagements", ["status"])
    op.create_index("ix_engagements_is_active", "engagements", ["is_active"])
    op.create_index("ix_engagements_is_mock", "engagements", ["is_mock"])

    # Create foreign keys
    op.create_foreign_key(
        "engagements_engagement_lead_id_fkey",
        "engagements",
        "users",
        ["engagement_lead_id"],
        ["id"],
    )
    op.create_foreign_key(
        "engagements_created_by_fkey", "engagements", "users", ["created_by"], ["id"]
    )

    # Update existing engagements to have slugs
    op.execute(
        """
        UPDATE engagements 
        SET slug = LOWER(REPLACE(REPLACE(name, ' ', '-'), '&', 'and'))
        WHERE slug IS NULL
    """
    )

    print("✅ Enhanced client accounts and engagements tables")
    print("✅ Added sophisticated fields for admin functionality")
    print("✅ Ready for enhanced admin operations")


def downgrade():
    """Remove enhanced fields from client_accounts and engagements tables."""

    # Drop engagements enhancements
    op.drop_constraint("engagements_created_by_fkey", "engagements", type_="foreignkey")
    op.drop_constraint(
        "engagements_engagement_lead_id_fkey", "engagements", type_="foreignkey"
    )
    op.drop_index("ix_engagements_is_mock", table_name="engagements")
    op.drop_index("ix_engagements_is_active", table_name="engagements")
    op.drop_index("ix_engagements_status", table_name="engagements")

    op.drop_column("engagements", "created_by")
    op.drop_column("engagements", "is_mock")
    op.drop_column("engagements", "team_preferences")
    op.drop_column("engagements", "migration_scope")
    op.drop_column("engagements", "settings")
    op.drop_column("engagements", "client_contact_email")
    op.drop_column("engagements", "client_contact_name")
    op.drop_column("engagements", "engagement_lead_id")
    op.drop_column("engagements", "actual_completion_date")
    op.drop_column("engagements", "target_completion_date")
    op.drop_column("engagements", "start_date")
    op.drop_column("engagements", "priority")
    op.drop_column("engagements", "status")
    op.drop_column("engagements", "engagement_type")
    op.drop_column("engagements", "slug")

    # Drop client_accounts enhancements
    op.drop_constraint(
        "client_accounts_created_by_fkey", "client_accounts", type_="foreignkey"
    )
    op.drop_index("ix_client_accounts_is_mock", table_name="client_accounts")
    op.drop_index("ix_client_accounts_is_active", table_name="client_accounts")
    op.drop_index("ix_client_accounts_slug", table_name="client_accounts")

    op.drop_column("client_accounts", "created_by")
    op.drop_column("client_accounts", "is_mock")
    op.drop_column("client_accounts", "agent_preferences")
    op.drop_column("client_accounts", "decision_criteria")
    op.drop_column("client_accounts", "it_guidelines")
    op.drop_column("client_accounts", "business_objectives")
    op.drop_column("client_accounts", "branding")
    op.drop_column("client_accounts", "settings")
    op.drop_column("client_accounts", "billing_contact_email")
    op.drop_column("client_accounts", "subscription_tier")
    op.drop_column("client_accounts", "primary_contact_phone")
    op.drop_column("client_accounts", "primary_contact_email")
    op.drop_column("client_accounts", "primary_contact_name")
    op.drop_column("client_accounts", "headquarters_location")
    op.drop_column("client_accounts", "company_size")
    op.drop_column("client_accounts", "industry")
    op.drop_column("client_accounts", "slug")
