"""Add hybrid properties for normalized_data field access in CollectedDataInventory

Revision ID: 011_add_hybrid_properties
Revises: 010_add_timestamp_columns_to_collected_data_inventory
Create Date: 2025-09-01 15:30:00.000000

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "011_add_hybrid_properties"
down_revision: Union[str, None] = (
    "010_add_timestamp_columns_to_collected_data_inventory"
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add hybrid properties to CollectedDataInventory model.

    This revision does not change the database schema as hybrid properties
    are Python-level properties that provide access to existing JSONB fields.

    The hybrid properties added:
    - ip_address: Extracts IP address from normalized_data
    - server_name: Extracts server name or hostname from normalized_data
    - os: Extracts operating system info from normalized_data
    - hostname: Extracts hostname or server name from normalized_data
    - operating_system: Alias for os property

    This resolves the SQLAlchemy mapper error "Mapper has no property 'ip_address'"
    by providing direct access to JSONB fields without requiring actual columns.
    """
    # No database changes needed - hybrid properties are ORM-level only
    pass


def downgrade() -> None:
    """
    Remove hybrid properties from CollectedDataInventory model.

    This would involve removing the hybrid property methods from the model,
    but does not require any database schema changes.
    """
    # No database changes needed - hybrid properties are ORM-level only
    pass
