"""merge heads for MFO testing

Revision ID: merge_mfo_testing_heads
Revises: 032_add_master_flow_id_to_assessment_flows, cb5aa7ecb987
Create Date: 2025-08-23 15:26:35.000000

"""

# from alembic import op  # noqa: F401 - needed for alembic
# import sqlalchemy as sa  # noqa: F401 - needed for alembic


# revision identifiers
revision = "merge_mfo_testing_heads"
down_revision = ("032_add_master_flow_id_to_assessment_flows", "cb5aa7ecb987")
branch_labels = None
depends_on = None


def upgrade():
    # Merge migration, no changes needed
    pass


def downgrade():
    # Merge migration, no changes needed
    pass
