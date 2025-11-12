import sys
import types
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from sqlalchemy.types import Float, TypeDecorator

pgvector_module = types.ModuleType("pgvector")
pgvector_sqlalchemy_module = types.ModuleType("pgvector.sqlalchemy")


class Vector(TypeDecorator):  # pragma: no cover - runtime stub
    impl = Float

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


pgvector_sqlalchemy_module.Vector = Vector
pgvector_module.sqlalchemy = pgvector_sqlalchemy_module
sys.modules.setdefault("pgvector", pgvector_module)
sys.modules.setdefault("pgvector.sqlalchemy", pgvector_sqlalchemy_module)

from app.models.asset import Asset
from app.services.unified_discovery_handlers.asset_list_handler import (
    INTERNAL_FIELDS,
    AssetListHandler,
)


def test_asset_transform_includes_all_model_columns():
    asset_columns = {column.name for column in Asset.__table__.columns}
    public_asset_columns = asset_columns - INTERNAL_FIELDS

    asset = Asset(
        id=uuid4(),
        client_account_id=uuid4(),
        engagement_id=uuid4(),
        name="Test Asset",
        asset_type="application",
        status="active",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    asset.discovery_timestamp = datetime(2024, 1, 3, tzinfo=timezone.utc)
    asset.asset_tags = ["tag1", "tag2"]
    asset.dependencies = []
    asset.dependents = []

    context_mock = MagicMock()
    context_mock.client_account_id = uuid4()
    context_mock.engagement_id = uuid4()
    handler = AssetListHandler(db=MagicMock(), context=context_mock)

    transformed = handler._transform_asset_to_dict(asset)

    missing = public_asset_columns - transformed.keys()
    assert not missing, (
        "AssetListHandler._transform_asset_to_dict is missing columns: "
        f"{', '.join(sorted(missing))}"
    )

    internal_present = INTERNAL_FIELDS & transformed.keys()
    assert not internal_present, (
        "Internal fields should not be exposed: "
        f"{', '.join(sorted(internal_present))}"
    )
