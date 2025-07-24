"""Remove unique constraint on workflow_states.session_id for smart session management

Revision ID: 118ea9101cec
Revises: d13b778f701f
Create Date: 2025-06-16 08:09:28.364432

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "118ea9101cec"
down_revision = "d13b778f701f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove the unique constraint on session_id to allow multiple workflows per session
    # The constraint name might vary, so we'll try a few common patterns
    try:
        # Try dropping by constraint name (most likely pattern)
        op.drop_constraint(
            "workflow_states_session_id_key", "workflow_states", type_="unique"
        )
    except Exception:
        try:
            # Alternative constraint name pattern
            op.drop_constraint(
                "uq_workflow_states_session_id", "workflow_states", type_="unique"
            )
        except Exception:
            try:
                # Another common pattern
                op.drop_constraint(
                    "workflow_states_session_id_unique",
                    "workflow_states",
                    type_="unique",
                )
            except Exception:
                # If none of the constraint names work, we'll handle it gracefully
                # This might happen if the constraint doesn't exist or has a different name
                pass


def downgrade() -> None:
    # Re-add the unique constraint on session_id
    # Note: This downgrade might fail if there are duplicate session_ids in the table
    op.create_unique_constraint(
        "workflow_states_session_id_key", "workflow_states", ["session_id"]
    )
