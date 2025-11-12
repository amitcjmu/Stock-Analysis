"""Unit-level regression test for discovery phase transitions."""

from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
import sys
from types import SimpleNamespace

import pytest

# Provide a lightweight stand-in for pgvector to avoid optional dependency issues in tests
if "pgvector.sqlalchemy" not in sys.modules:  # pragma: no cover - test scaffolding
    mock_pgvector = SimpleNamespace(Vector=lambda *args, **kwargs: None)
    sys.modules["pgvector.sqlalchemy"] = mock_pgvector
    sys.modules.setdefault("pgvector", SimpleNamespace(sqlalchemy=mock_pgvector))

from app.models.discovery_flow import DiscoveryFlow
from app.services.discovery.phase_transition_service import (
    DiscoveryPhaseTransitionService,
)


@pytest.mark.asyncio
async def test_phase_transition_uses_crew_flow_id(monkeypatch):
    """Ensure the service looks up discovery flows by CrewAI flow_id rather than DB primary key."""

    crew_flow_id = uuid4()

    flow = DiscoveryFlow(
        id=uuid4(),
        flow_id=crew_flow_id,
        client_account_id=uuid4(),
        engagement_id=uuid4(),
        user_id="tester",
        flow_name="Test Flow",
        status="active",
        current_phase="field_mapping",
    )

    flow_result = MagicMock()
    flow_result.scalar_one_or_none.return_value = flow

    counts_row = MagicMock(total=1, approved=1)
    counts_result = MagicMock()
    counts_result.one.return_value = counts_row

    db_session = AsyncMock()
    db_session.execute.side_effect = [flow_result, counts_result]

    mock_phase_mgmt = AsyncMock()
    monkeypatch.setattr(
        "app.services.discovery.phase_transition_service.FlowPhaseManagementCommands",
        lambda *args, **kwargs: mock_phase_mgmt,
    )

    advance_phase_mock = AsyncMock(return_value=MagicMock(success=True, warnings=[]))
    monkeypatch.setattr(
        "app.services.discovery.phase_transition_service.advance_phase",
        advance_phase_mock,
    )

    service = DiscoveryPhaseTransitionService(db_session)
    result = await service.check_and_transition_from_attribute_mapping(
        str(crew_flow_id)
    )

    executed_statement = db_session.execute.await_args_list[0].args[0]
    where_clause = tuple(executed_statement._where_criteria)[0]
    assert getattr(where_clause.left, "key", None) == "flow_id"
    assert result == "data_cleansing"

    mock_phase_mgmt.update_phase_completion.assert_awaited()
    advance_phase_mock.assert_awaited()
