"""Add 6R analysis tables for migration strategy analysis

Revision ID: 030_add_sixr_analysis_tables
Revises: 029_complete_assessment_flows_schema
Create Date: 2025-08-21 12:00:00.000000

This migration creates all tables required for 6R analysis functionality:
- sixr_analyses: Main analysis records
- sixr_iterations: Analysis refinement cycles
- sixr_recommendations: Analysis results and recommendations
- sixr_questions: Qualifying questions for analysis
- sixr_analysis_parameters: Analysis parameter sets
- sixr_parameters: Global configuration parameters
- sixr_question_responses: User responses to questions
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "030_add_sixr_analysis_tables"
down_revision = "029_complete_assessment_flows_schema"
branch_labels = None
depends_on = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the 'migration' schema."""
    bind = op.get_bind()
    try:
        stmt = sa.text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'migration'
                  AND table_name = :table_name
            )
            """
        )
        result = bind.execute(stmt, {"table_name": table_name}).scalar()
        return bool(result)
    except Exception as e:
        print(f"Error checking if table {table_name} exists: {e}")
        # Fail safe: indicate table does not exist so creation proceeds
        return False


def create_table_if_not_exists(table_name, *columns, **kwargs):
    """Create a table only if it doesn't already exist"""
    if not table_exists(table_name):
        op.create_table(table_name, *columns, **kwargs)
        return True
    else:
        print(f"Table {table_name} already exists, skipping creation")
        return False


def upgrade() -> None:
    """Create all 6R analysis tables"""

    print("🔄 Creating 6R analysis tables...")
    created_count = 0

    # Define ENUM types for reuse across columns
    analysis_status_enum = postgresql.ENUM(
        "pending",
        "in_progress",
        "completed",
        "failed",
        "requires_input",
        name="analysis_status",
        create_type=False,
    )
    
    question_type_enum = postgresql.ENUM(
        "text",
        "select",
        "multiselect",
        "file_upload",
        "boolean",
        "numeric",
        name="question_type",
        create_type=False,
    )
    
    sixr_strategy_enum = postgresql.ENUM(
        "rehost",
        "replatform",
        "refactor",
        "rearchitect",
        "replace",
        "rewrite",
        name="sixr_strategy",
        create_type=False,
    )

    # Create enums if they don't exist
    for enum_obj, enum_name in [
        (analysis_status_enum, "analysis_status"),
        (question_type_enum, "question_type"),
        (sixr_strategy_enum, "sixr_strategy"),
    ]:
        try:
            enum_obj.create(op.get_bind(), checkfirst=True)
            print(f"  ✅ Created {enum_name} enum")
        except Exception as e:
            print(f"  ℹ️  {enum_name} enum might already exist: {e}")

    # 1. sixr_analyses table (main analysis records)
    if create_table_if_not_exists(
        "sixr_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("migration_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Multi-tenant isolation
        sa.Column(
            "client_account_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "engagement_id", postgresql.UUID(as_uuid=True), nullable=False, index=True
        ),
        # Analysis metadata
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("description", sa.Text),
        sa.Column(
            "status",
            analysis_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("priority", sa.Integer, server_default="3"),
        # Application data
        sa.Column("application_ids", postgresql.JSONB),
        sa.Column("application_data", postgresql.JSONB),
        # Analysis progress
        sa.Column("current_iteration", sa.Integer, server_default="1"),
        sa.Column("progress_percentage", sa.Float, server_default="0.0"),
        sa.Column("estimated_completion", sa.DateTime(timezone=True)),
        # Results
        sa.Column("final_recommendation", sixr_strategy_enum),
        sa.Column("confidence_score", sa.Float),
        # Metadata
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        # Analysis configuration
        sa.Column("analysis_config", postgresql.JSONB),
        # Foreign key constraints
        sa.ForeignKeyConstraint(["migration_id"], ["migration.migrations.id"]),
        sa.ForeignKeyConstraint(
            ["client_account_id"], ["migration.client_accounts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["engagement_id"], ["migration.engagements.id"], ondelete="CASCADE"
        ),
        schema="migration",
    ):
        created_count += 1
        print("  ✅ Created sixr_analyses table")

    # 2. sixr_iterations table (analysis refinement cycles)
    if create_table_if_not_exists(
        "sixr_iterations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("iteration_number", sa.Integer, nullable=False),
        # Iteration metadata
        sa.Column("iteration_name", sa.String(255)),
        sa.Column("iteration_reason", sa.Text),
        sa.Column("stakeholder_feedback", sa.Text),
        # Parameter changes
        sa.Column("parameter_changes", postgresql.JSONB),
        # Question responses
        sa.Column("question_responses", postgresql.JSONB),
        # Iteration results
        sa.Column("recommendation_data", postgresql.JSONB),
        sa.Column("confidence_score", sa.Float),
        # Analysis metadata
        sa.Column("analysis_duration", sa.Float),
        sa.Column("agent_insights", postgresql.JSONB),
        # Status tracking
        sa.Column("status", analysis_status_enum, server_default="pending"),
        sa.Column("error_details", postgresql.JSONB),
        # Audit fields
        sa.Column("created_by", sa.String(100)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        # Foreign key constraints
        sa.ForeignKeyConstraint(
            ["analysis_id"], ["migration.sixr_analyses.id"], ondelete="CASCADE"
        ),
        schema="migration",
    ):
        created_count += 1
        print("  ✅ Created sixr_iterations table")

    # 3. sixr_recommendations table (analysis results)
    if create_table_if_not_exists(
        "sixr_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("iteration_number", sa.Integer, server_default="1"),
        # Core recommendation
        sa.Column(
            "recommended_strategy",
            sixr_strategy_enum,
            nullable=False,
        ),
        sa.Column("confidence_score", sa.Float, nullable=False),
        # Strategy scores
        sa.Column("strategy_scores", postgresql.JSONB),
        # Analysis insights
        sa.Column("key_factors", postgresql.JSONB),
        sa.Column("assumptions", postgresql.JSONB),
        sa.Column("next_steps", postgresql.JSONB),
        # Estimates
        sa.Column("estimated_effort", sa.String(50)),
        sa.Column("estimated_timeline", sa.String(100)),
        sa.Column("estimated_cost_impact", sa.String(50)),
        # Additional details
        sa.Column("risk_factors", postgresql.JSONB),
        sa.Column("business_benefits", postgresql.JSONB),
        sa.Column("technical_benefits", postgresql.JSONB),
        # Metadata
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column("created_by", sa.String(100)),
        # Foreign key constraints
        sa.ForeignKeyConstraint(
            ["analysis_id"], ["migration.sixr_analyses.id"], ondelete="CASCADE"
        ),
        schema="migration",
    ):
        created_count += 1
        print("  ✅ Created sixr_recommendations table")

    # 4. sixr_questions table (qualifying questions)
    if create_table_if_not_exists(
        "sixr_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        # Question definition
        sa.Column(
            "question_id", sa.String(100), unique=True, nullable=False, index=True
        ),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column(
            "question_type", question_type_enum, nullable=False
        ),
        sa.Column("category", sa.String(100), nullable=False),
        # Question metadata
        sa.Column("priority", sa.Integer, server_default="1"),
        sa.Column("required", sa.Boolean, server_default="false"),
        sa.Column("active", sa.Boolean, server_default="true"),
        # Question configuration
        sa.Column("options", postgresql.JSONB),
        sa.Column("validation_rules", postgresql.JSONB),
        sa.Column("help_text", sa.Text),
        sa.Column("depends_on", sa.String(100)),
        # Conditional logic
        sa.Column("show_conditions", postgresql.JSONB),
        sa.Column("skip_conditions", postgresql.JSONB),
        # Audit fields
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        # Version control
        sa.Column("version", sa.String(20), server_default="1.0"),
        sa.Column("parent_question_id", sa.String(100)),
        schema="migration",
    ):
        created_count += 1
        print("  ✅ Created sixr_questions table")

    # 5. sixr_analysis_parameters table (analysis parameter sets)
    if create_table_if_not_exists(
        "sixr_analysis_parameters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("iteration_number", sa.Integer, nullable=False),
        # Dynamic parameters
        sa.Column("business_value", sa.Float, nullable=False, server_default="3"),
        sa.Column("technical_complexity", sa.Float, nullable=False, server_default="3"),
        sa.Column("migration_urgency", sa.Float, nullable=False, server_default="3"),
        sa.Column(
            "compliance_requirements", sa.Float, nullable=False, server_default="3"
        ),
        sa.Column("cost_sensitivity", sa.Float, nullable=False, server_default="3"),
        sa.Column("risk_tolerance", sa.Float, nullable=False, server_default="3"),
        sa.Column("innovation_priority", sa.Float, nullable=False, server_default="3"),
        # Contextual parameters
        sa.Column("application_type", sa.String(20), server_default="custom"),
        sa.Column("parameter_source", sa.String(50), server_default="initial"),
        sa.Column("confidence_level", sa.Float, server_default="1.0"),
        # Metadata
        sa.Column("created_by", sa.String(100)),
        sa.Column("updated_by", sa.String(100)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column("parameter_notes", sa.Text),
        sa.Column("validation_status", sa.String(20), server_default="valid"),
        # Foreign key constraints
        sa.ForeignKeyConstraint(
            ["analysis_id"], ["migration.sixr_analyses.id"], ondelete="CASCADE"
        ),
        schema="migration",
    ):
        created_count += 1
        print("  ✅ Created sixr_analysis_parameters table")

    # 6. sixr_parameters table (global configuration)
    if create_table_if_not_exists(
        "sixr_parameters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "parameter_key", sa.String(255), unique=True, nullable=False, index=True
        ),
        sa.Column("value", postgresql.JSONB, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        schema="migration",
    ):
        created_count += 1
        print("  ✅ Created sixr_parameters table")

    # 7. sixr_question_responses table (user responses)
    if create_table_if_not_exists(
        "sixr_question_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, index=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("iteration_number", sa.Integer, nullable=False),
        sa.Column("question_id", sa.String(100), nullable=False),
        # Response data
        sa.Column("response_value", postgresql.JSONB),
        sa.Column("response_text", sa.Text),
        sa.Column("confidence", sa.Float, server_default="1.0"),
        sa.Column("source", sa.String(50), server_default="user"),
        # Response metadata
        sa.Column("response_time", sa.Float),
        sa.Column("validation_status", sa.String(20), server_default="pending"),
        sa.Column("validation_errors", postgresql.JSONB),
        # Audit fields
        sa.Column("created_by", sa.String(100)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        # Foreign key constraints
        sa.ForeignKeyConstraint(
            ["analysis_id"], ["migration.sixr_analyses.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["question_id"], ["migration.sixr_questions.question_id"]
        ),
        schema="migration",
    ):
        created_count += 1
        print("  ✅ Created sixr_question_responses table")

    # Create indexes for better performance
    indexes_to_create = [
        ("ix_sixr_analyses_client_account_id", "sixr_analyses", ["client_account_id"]),
        ("ix_sixr_analyses_engagement_id", "sixr_analyses", ["engagement_id"]),
        ("ix_sixr_analyses_status", "sixr_analyses", ["status"]),
        ("ix_sixr_analyses_name", "sixr_analyses", ["name"]),
        ("ix_sixr_iterations_analysis_id", "sixr_iterations", ["analysis_id"]),
        (
            "ix_sixr_recommendations_analysis_id",
            "sixr_recommendations",
            ["analysis_id"],
        ),
        ("ix_sixr_questions_question_id", "sixr_questions", ["question_id"]),
        ("ix_sixr_questions_category", "sixr_questions", ["category"]),
        (
            "ix_sixr_analysis_parameters_analysis_id",
            "sixr_analysis_parameters",
            ["analysis_id"],
        ),
        ("ix_sixr_parameters_parameter_key", "sixr_parameters", ["parameter_key"]),
        (
            "ix_sixr_question_responses_analysis_id",
            "sixr_question_responses",
            ["analysis_id"],
        ),
    ]

    for index_name, table_name, columns in indexes_to_create:
        try:
            # Check if table exists before creating index
            if table_exists(table_name):
                # Check if index already exists
                bind = op.get_bind()
                result = bind.execute(
                    sa.text(
                        """
                        SELECT indexname
                        FROM pg_indexes
                        WHERE schemaname = 'migration'
                        AND tablename = :table_name
                        AND indexname = :index_name
                    """
                    ),
                    {"table_name": table_name, "index_name": index_name},
                )

                if not result.fetchone():
                    op.create_index(index_name, table_name, columns, schema="migration")
                    print(f"  ✅ Created index {index_name}")
                else:
                    print(f"  ℹ️  Index {index_name} already exists")
            else:
                print(
                    f"  ⚠️  Table {table_name} does not exist, skipping index {index_name}"
                )
        except Exception as e:
            print(f"  ⚠️  Could not create index {index_name}: {str(e)}")

    print(
        f"\n✅ 6R analysis tables migration completed - created {created_count} tables"
    )


def downgrade() -> None:
    """Drop all 6R analysis tables"""

    print("🔄 Dropping 6R analysis tables...")

    # Drop indexes first
    indexes_to_drop = [
        "ix_sixr_question_responses_analysis_id",
        "ix_sixr_parameters_parameter_key",
        "ix_sixr_analysis_parameters_analysis_id",
        "ix_sixr_questions_category",
        "ix_sixr_questions_question_id",
        "ix_sixr_recommendations_analysis_id",
        "ix_sixr_iterations_analysis_id",
        "ix_sixr_analyses_name",
        "ix_sixr_analyses_status",
        "ix_sixr_analyses_engagement_id",
        "ix_sixr_analyses_client_account_id",
    ]

    for index_name in indexes_to_drop:
        try:
            op.drop_index(index_name, schema="migration")
            print(f"  ✅ Dropped index {index_name}")
        except Exception:
            pass  # Index might not exist

    # Drop tables in reverse dependency order
    tables_to_drop = [
        "sixr_question_responses",
        "sixr_parameters",
        "sixr_analysis_parameters",
        "sixr_questions",
        "sixr_recommendations",
        "sixr_iterations",
        "sixr_analyses",
    ]

    for table_name in tables_to_drop:
        try:
            op.drop_table(table_name, schema="migration")
            print(f"  ✅ Dropped table {table_name}")
        except Exception as e:
            print(f"  ⚠️  Could not drop table {table_name}: {str(e)}")

    # Drop enums
    enums_to_drop = [
        "sixr_strategy",
        "question_type",
        "analysis_status",
    ]

    for enum_name in enums_to_drop:
        try:
            enum_type = postgresql.ENUM(name=enum_name)
            enum_type.drop(op.get_bind())
            print(f"  ✅ Dropped enum {enum_name}")
        except Exception as e:
            print(f"  ⚠️  Could not drop enum {enum_name}: {str(e)}")

    print("✅ 6R analysis tables downgrade completed")
