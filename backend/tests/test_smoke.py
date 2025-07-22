"""
Backend Smoke Test: Ensure all critical services, endpoints, and agentic components initialize and basic health checks pass.
This test should be run after every backend restart to catch initialization errors early.
"""

import pytest


@pytest.mark.smoke
def test_basic_imports():
    """Test that essential backend modules can be imported."""
    from app.core.database import get_db
    from app.core.config import settings
    assert hasattr(settings, 'DATABASE_URL')

@pytest.mark.smoke
def test_crewai_service_initialization():
    """Test that CrewAI service can be instantiated."""
    from app.services.crewai_service_modular import CrewAIService
    service = CrewAIService()
    assert hasattr(service, 'analyze_with_agents')

@pytest.mark.smoke
def test_agent_manager_initialization():
    """Test that AgentManager can be instantiated and has agents."""
    from app.core.config import settings
    from app.services.agents import AgentManager
    from app.services.deepinfra_llm import create_deepinfra_llm
    llm = create_deepinfra_llm(
        api_token=settings.DEEPINFRA_API_KEY,
        model_id=settings.DEEPINFRA_MODEL
    )
    agent_manager = AgentManager(llm)
    assert hasattr(agent_manager, 'agents')
    assert isinstance(agent_manager.agents, dict)

@pytest.mark.smoke
def test_health_endpoint(client):
    """Test that the /health endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"

@pytest.mark.smoke
def test_discovery_endpoint_available(client):
    """Test that the discovery endpoint is available and returns a valid response."""
    response = client.post("/api/v1/discovery/analyze", json={"data": {}})
    assert response.status_code in (200, 422)  # 422 if missing/invalid payload

# ---
# If not already present, ensure a pytest fixture for `client` is available in conftest.py:
#
# @pytest.fixture
# def client():
#     from app.main import app
#     from fastapi.testclient import TestClient
#     return TestClient(app)
#
# Place this in tests/conftest.py if not already present.
