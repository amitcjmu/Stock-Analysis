# API Testing Guide

**Last Updated: August 18, 2025**

## Overview

This guide provides comprehensive documentation for testing APIs in the AI Modernize Migration Platform. It covers authentication patterns, test fixtures, example test cases, and both manual and automated testing approaches.

## Testing Framework Setup

### Test Dependencies

**Backend Testing Stack:**
```python
# requirements-test.txt
pytest==8.4.1
pytest-asyncio==1.0.0
httpx==0.24.1
pytest-mock==3.11.1
factory-boy==3.3.0
freezegun==1.2.2
respx==0.20.2
```

**Test Configuration:**
```python
# conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from tests.fixtures.database import get_test_db

# Override database dependency for testing
app.dependency_overrides[get_db] = get_test_db

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def async_client():
    """Create async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def sync_client():
    """Create synchronous test client."""
    return TestClient(app)
```

## Authentication Testing Patterns

### 1. JWT Token Testing

**Token Generation for Tests:**
```python
# tests/fixtures/auth.py
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.config import settings

class TestAuthHelper:
    """Helper class for authentication in tests."""
    
    @staticmethod
    def create_test_token(
        user_id: str = "test-user-id",
        client_account_id: str = "11111111-1111-1111-1111-111111111111",
        engagement_id: str = "22222222-2222-2222-2222-222222222222",
        expires_in_minutes: int = 30
    ) -> str:
        """Create JWT token for testing."""
        payload = {
            "sub": user_id,
            "client_account_id": client_account_id,
            "engagement_id": engagement_id,
            "exp": datetime.utcnow() + timedelta(minutes=expires_in_minutes),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(
            payload, 
            settings.SECRET_KEY, 
            algorithm="HS256"
        )
    
    @staticmethod
    def create_expired_token(user_id: str = "test-user-id") -> str:
        """Create expired JWT token for testing."""
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() - timedelta(minutes=1),  # Expired 1 minute ago
            "iat": datetime.utcnow() - timedelta(minutes=31),
            "type": "access"
        }
        
        return jwt.encode(
            payload, 
            settings.SECRET_KEY, 
            algorithm="HS256"
        )
    
    @staticmethod
    def create_invalid_token() -> str:
        """Create invalid JWT token for testing."""
        return "invalid.jwt.token"

    @staticmethod
    def get_auth_headers(token: str = None) -> Dict[str, str]:
        """Get authentication headers for requests."""
        if token is None:
            token = TestAuthHelper.create_test_token()
        
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    @staticmethod
    def get_tenant_headers(
        client_account_id: str = "11111111-1111-1111-1111-111111111111",
        engagement_id: str = "22222222-2222-2222-2222-222222222222",
        user_id: str = "test-user"
    ) -> Dict[str, str]:
        """Get tenant context headers for requests."""
        return {
            "X-Client-Account-Id": client_account_id,
            "X-Engagement-Id": engagement_id,
            "X-User-Id": user_id,
            "Content-Type": "application/json"
        }

    @staticmethod
    def get_complete_headers(
        token: str = None,
        client_account_id: str = "11111111-1111-1111-1111-111111111111",
        engagement_id: str = "22222222-2222-2222-2222-222222222222",
        user_id: str = "test-user"
    ) -> Dict[str, str]:
        """Get both auth and tenant headers."""
        headers = TestAuthHelper.get_auth_headers(token)
        headers.update(TestAuthHelper.get_tenant_headers(
            client_account_id, engagement_id, user_id
        ))
        return headers
```

**Authentication Test Cases:**
```python
# tests/integration/api/test_authentication.py
import pytest
from httpx import AsyncClient

from tests.fixtures.auth import TestAuthHelper

class TestAuthentication:
    """Test authentication and authorization."""

    @pytest.mark.asyncio
    async def test_valid_token_access(self, async_client: AsyncClient):
        """Test API access with valid JWT token."""
        # Arrange
        token = TestAuthHelper.create_test_token()
        headers = TestAuthHelper.get_complete_headers(token)

        # Act
        response = await async_client.get("/api/v1/assets/", headers=headers)

        # Assert
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_token_denied(self, async_client: AsyncClient):
        """Test API access denied without token."""
        # Arrange
        headers = TestAuthHelper.get_tenant_headers()  # No auth token

        # Act
        response = await async_client.get("/api/v1/assets/", headers=headers)

        # Assert
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_expired_token_denied(self, async_client: AsyncClient):
        """Test API access denied with expired token."""
        # Arrange
        expired_token = TestAuthHelper.create_expired_token()
        headers = TestAuthHelper.get_complete_headers(expired_token)

        # Act
        response = await async_client.get("/api/v1/assets/", headers=headers)

        # Assert
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_token_denied(self, async_client: AsyncClient):
        """Test API access denied with invalid token."""
        # Arrange
        invalid_token = TestAuthHelper.create_invalid_token()
        headers = TestAuthHelper.get_complete_headers(invalid_token)

        # Act
        response = await async_client.get("/api/v1/assets/", headers=headers)

        # Assert
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_tenant_context_required(self, async_client: AsyncClient):
        """Test that tenant context headers are required."""
        # Arrange
        token = TestAuthHelper.create_test_token()
        headers = TestAuthHelper.get_auth_headers(token)
        # Missing tenant context headers

        # Act
        response = await async_client.get("/api/v1/assets/", headers=headers)

        # Assert - Should fail due to missing tenant context
        assert response.status_code in [400, 403]  # Bad request or forbidden
```

### 2. Permission Testing

**Role-Based Access Control Tests:**
```python
# tests/integration/api/test_permissions.py
import pytest
from httpx import AsyncClient

from tests.fixtures.auth import TestAuthHelper
from tests.fixtures.users import create_test_user_with_role

class TestPermissions:
    """Test role-based permissions."""

    @pytest.mark.asyncio
    async def test_admin_can_delete_assets(self, async_client: AsyncClient):
        """Test that admin users can delete assets."""
        # Arrange
        admin_user = await create_test_user_with_role("admin")
        token = TestAuthHelper.create_test_token(user_id=str(admin_user.id))
        headers = TestAuthHelper.get_complete_headers(token)

        # Create asset first
        asset_data = {
            "name": "Test Asset for Deletion",
            "asset_type": "server",
            "environment": "test",
            "attributes": {},
            "tags": []
        }
        
        create_response = await async_client.post(
            "/api/v1/assets/",
            json=asset_data,
            headers=headers
        )
        assert create_response.status_code == 201
        asset_id = create_response.json()["id"]

        # Act - Delete the asset
        delete_response = await async_client.delete(
            f"/api/v1/assets/{asset_id}",
            headers=headers
        )

        # Assert
        assert delete_response.status_code == 204

    @pytest.mark.asyncio
    async def test_viewer_cannot_delete_assets(self, async_client: AsyncClient):
        """Test that viewer users cannot delete assets."""
        # Arrange
        viewer_user = await create_test_user_with_role("viewer")
        token = TestAuthHelper.create_test_token(user_id=str(viewer_user.id))
        headers = TestAuthHelper.get_complete_headers(token)

        # Create asset with admin user first
        admin_user = await create_test_user_with_role("admin")
        admin_token = TestAuthHelper.create_test_token(user_id=str(admin_user.id))
        admin_headers = TestAuthHelper.get_complete_headers(admin_token)

        asset_data = {
            "name": "Test Asset for Permission Test",
            "asset_type": "server",
            "environment": "test",
            "attributes": {},
            "tags": []
        }
        
        create_response = await async_client.post(
            "/api/v1/assets/",
            json=asset_data,
            headers=admin_headers
        )
        assert create_response.status_code == 201
        asset_id = create_response.json()["id"]

        # Act - Try to delete with viewer permissions
        delete_response = await async_client.delete(
            f"/api/v1/assets/{asset_id}",
            headers=headers
        )

        # Assert
        assert delete_response.status_code == 403
        assert "Insufficient permissions" in delete_response.json()["detail"]

    @pytest.mark.asyncio
    async def test_contributor_can_create_and_update(self, async_client: AsyncClient):
        """Test that contributor users can create and update assets."""
        # Arrange
        contributor_user = await create_test_user_with_role("contributor")
        token = TestAuthHelper.create_test_token(user_id=str(contributor_user.id))
        headers = TestAuthHelper.get_complete_headers(token)

        # Act - Create asset
        asset_data = {
            "name": "Contributor Asset",
            "asset_type": "database",
            "environment": "staging",
            "attributes": {"contributor_test": True},
            "tags": ["contributor"]
        }
        
        create_response = await async_client.post(
            "/api/v1/assets/",
            json=asset_data,
            headers=headers
        )

        # Assert creation
        assert create_response.status_code == 201
        asset_id = create_response.json()["id"]

        # Act - Update asset
        update_data = {
            "name": "Updated Contributor Asset",
            "attributes": {"updated": True}
        }
        
        update_response = await async_client.put(
            f"/api/v1/assets/{asset_id}",
            json=update_data,
            headers=headers
        )

        # Assert update
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated Contributor Asset"
```

## Test Fixtures and Data Management

### 1. Data Factories

**Model Factories:**
```python
# tests/fixtures/factories.py
import factory
import uuid
from datetime import datetime
from factory import fuzzy

from app.models.asset import Asset
from app.models.discovery_flow import DiscoveryFlow
from app.models.client_account import User, ClientAccount, Engagement

class ClientAccountFactory(factory.Factory):
    """Factory for ClientAccount model."""
    
    class Meta:
        model = ClientAccount
    
    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Faker("company")
    created_at = factory.LazyFunction(datetime.utcnow)
    is_active = True

class EngagementFactory(factory.Factory):
    """Factory for Engagement model."""
    
    class Meta:
        model = Engagement
    
    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Faker("bs")
    client_account_id = factory.SubFactory(ClientAccountFactory)
    created_at = factory.LazyFunction(datetime.utcnow)
    is_active = True

class UserFactory(factory.Factory):
    """Factory for User model."""
    
    class Meta:
        model = User
    
    id = factory.LazyFunction(uuid.uuid4)
    email = factory.Faker("email")
    full_name = factory.Faker("name")
    is_active = True
    created_at = factory.LazyFunction(datetime.utcnow)

class AssetFactory(factory.Factory):
    """Factory for Asset model."""
    
    class Meta:
        model = Asset
    
    id = factory.LazyFunction(uuid.uuid4)
    name = factory.Faker("word")
    asset_type = fuzzy.FuzzyChoice(["server", "database", "application", "network"])
    environment = fuzzy.FuzzyChoice(["dev", "staging", "prod", "test"])
    client_account_id = factory.LazyFunction(uuid.uuid4)
    engagement_id = factory.LazyFunction(uuid.uuid4)
    attributes = factory.LazyFunction(dict)
    tags = factory.LazyFunction(list)
    created_at = factory.LazyFunction(datetime.utcnow)

class DiscoveryFlowFactory(factory.Factory):
    """Factory for DiscoveryFlow model."""
    
    class Meta:
        model = DiscoveryFlow
    
    id = factory.LazyFunction(uuid.uuid4)
    flow_id = factory.LazyFunction(uuid.uuid4)
    client_account_id = factory.LazyFunction(uuid.uuid4)
    engagement_id = factory.LazyFunction(uuid.uuid4)
    user_id = factory.Faker("uuid4")
    flow_name = factory.Faker("sentence", nb_words=3)
    current_phase = fuzzy.FuzzyChoice([
        "initialization", "data_import", "field_mapping", 
        "asset_creation", "dependency_analysis", "completed"
    ])
    flow_status = fuzzy.FuzzyChoice([
        "running", "completed", "failed", "paused"
    ])
    created_at = factory.LazyFunction(datetime.utcnow)
```

**Test Data Builder Pattern:**
```python
# tests/fixtures/builders.py
from typing import Dict, Any, Optional
import uuid

class AssetTestDataBuilder:
    """Builder pattern for creating test asset data."""
    
    def __init__(self):
        self._data = {
            "name": "Test Asset",
            "asset_type": "server",
            "environment": "test",
            "attributes": {},
            "tags": []
        }
    
    def with_name(self, name: str) -> "AssetTestDataBuilder":
        """Set asset name."""
        self._data["name"] = name
        return self
    
    def with_type(self, asset_type: str) -> "AssetTestDataBuilder":
        """Set asset type."""
        self._data["asset_type"] = asset_type
        return self
    
    def with_environment(self, environment: str) -> "AssetTestDataBuilder":
        """Set environment."""
        self._data["environment"] = environment
        return self
    
    def with_attributes(self, attributes: Dict[str, Any]) -> "AssetTestDataBuilder":
        """Set attributes."""
        self._data["attributes"] = attributes
        return self
    
    def with_tags(self, tags: list) -> "AssetTestDataBuilder":
        """Set tags."""
        self._data["tags"] = tags
        return self
    
    def server(self) -> "AssetTestDataBuilder":
        """Configure as server asset."""
        return self.with_type("server").with_attributes({
            "cpu": "4 cores",
            "memory": "16GB",
            "os": "Ubuntu 20.04"
        })
    
    def database(self) -> "AssetTestDataBuilder":
        """Configure as database asset."""
        return self.with_type("database").with_attributes({
            "engine": "PostgreSQL",
            "version": "13.0",
            "size": "100GB"
        })
    
    def production(self) -> "AssetTestDataBuilder":
        """Configure for production environment."""
        return self.with_environment("prod").with_tags(["production", "critical"])
    
    def development(self) -> "AssetTestDataBuilder":
        """Configure for development environment."""
        return self.with_environment("dev").with_tags(["development"])
    
    def build(self) -> Dict[str, Any]:
        """Build the test data."""
        return self._data.copy()

# Usage examples:
def test_asset_builder_usage():
    # Create production server
    prod_server = (AssetTestDataBuilder()
                   .with_name("Production Web Server")
                   .server()
                   .production()
                   .build())
    
    # Create development database
    dev_db = (AssetTestDataBuilder()
              .with_name("Dev Database")
              .database()
              .development()
              .build())
```

### 2. Mock Services

**External Service Mocking:**
```python
# tests/fixtures/mock_services.py
from unittest.mock import AsyncMock, MagicMock
import respx
import httpx

class MockCrewAIService:
    """Mock CrewAI service for testing."""
    
    def __init__(self):
        self.mock_crew = MagicMock()
        self.mock_crew.kickoff = AsyncMock()
        
    async def mock_successful_discovery(self, *args, **kwargs):
        """Mock successful discovery flow."""
        return {
            "status": "completed",
            "results": {
                "assets_discovered": 10,
                "dependencies_mapped": 5,
                "field_mappings_created": 15,
                "confidence_score": 0.92
            },
            "execution_time": 120.5,
            "agent_insights": [
                {
                    "agent": "asset_discovery_agent",
                    "insight": "Discovered 10 server assets with high confidence",
                    "confidence": 0.95
                }
            ]
        }
    
    async def mock_failed_discovery(self, *args, **kwargs):
        """Mock failed discovery flow."""
        raise Exception("Mock CrewAI execution failure")

class MockDeepInfraAPI:
    """Mock DeepInfra API for testing."""
    
    @staticmethod
    def setup_mock_responses():
        """Setup mock HTTP responses for DeepInfra API."""
        
        @respx.mock
        async def mock_chat_completion():
            return httpx.Response(
                200,
                json={
                    "choices": [
                        {
                            "message": {
                                "content": "Mock AI response for testing",
                                "role": "assistant"
                            },
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 100,
                        "completion_tokens": 50,
                        "total_tokens": 150
                    }
                }
            )
        
        respx.post("https://api.deepinfra.com/v1/openai/chat/completions").mock(
            return_value=httpx.Response(200, json={
                "choices": [{"message": {"content": "Mock response"}}],
                "usage": {"total_tokens": 150}
            })
        )

class MockRedisCache:
    """Mock Redis cache for testing."""
    
    def __init__(self):
        self._data = {}
        self._ttl = {}
    
    async def get(self, key: str):
        """Get value from mock cache."""
        return self._data.get(key)
    
    async def set(self, key: str, value: str):
        """Set value in mock cache."""
        self._data[key] = value
    
    async def setex(self, key: str, ttl: int, value: str):
        """Set value with TTL in mock cache."""
        self._data[key] = value
        self._ttl[key] = ttl
    
    async def delete(self, key: str):
        """Delete value from mock cache."""
        self._data.pop(key, None)
        self._ttl.pop(key, None)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in mock cache."""
        return key in self._data
```

## API Endpoint Testing Examples

### 1. CRUD Operations Testing

**Asset CRUD Tests:**
```python
# tests/integration/api/test_asset_crud.py
import pytest
import uuid
from httpx import AsyncClient

from tests.fixtures.auth import TestAuthHelper
from tests.fixtures.builders import AssetTestDataBuilder

class TestAssetCRUD:
    """Test Asset CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_asset(self, async_client: AsyncClient):
        """Test asset creation."""
        # Arrange
        headers = TestAuthHelper.get_complete_headers()
        asset_data = (AssetTestDataBuilder()
                      .with_name("Test Web Server")
                      .server()
                      .production()
                      .build())

        # Act
        response = await async_client.post(
            "/api/v1/assets/",
            json=asset_data,
            headers=headers
        )

        # Assert
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["name"] == asset_data["name"]
        assert response_data["asset_type"] == asset_data["asset_type"]
        assert response_data["environment"] == asset_data["environment"]
        assert "id" in response_data
        assert "created_at" in response_data

    @pytest.mark.asyncio
    async def test_get_asset(self, async_client: AsyncClient):
        """Test asset retrieval."""
        # Arrange
        headers = TestAuthHelper.get_complete_headers()
        
        # Create asset first
        create_data = (AssetTestDataBuilder()
                       .with_name("Test Database")
                       .database()
                       .development()
                       .build())
        
        create_response = await async_client.post(
            "/api/v1/assets/",
            json=create_data,
            headers=headers
        )
        assert create_response.status_code == 201
        asset_id = create_response.json()["id"]

        # Act
        get_response = await async_client.get(
            f"/api/v1/assets/{asset_id}",
            headers=headers
        )

        # Assert
        assert get_response.status_code == 200
        asset_data = get_response.json()
        assert asset_data["id"] == asset_id
        assert asset_data["name"] == create_data["name"]
        assert asset_data["asset_type"] == create_data["asset_type"]

    @pytest.mark.asyncio
    async def test_update_asset(self, async_client: AsyncClient):
        """Test asset update."""
        # Arrange
        headers = TestAuthHelper.get_complete_headers()
        
        # Create asset first
        create_data = (AssetTestDataBuilder()
                       .with_name("Original Name")
                       .server()
                       .development()
                       .build())
        
        create_response = await async_client.post(
            "/api/v1/assets/",
            json=create_data,
            headers=headers
        )
        asset_id = create_response.json()["id"]

        # Act
        update_data = {
            "name": "Updated Asset Name",
            "environment": "staging",
            "attributes": {"updated": True, "version": "2.0"}
        }
        
        update_response = await async_client.put(
            f"/api/v1/assets/{asset_id}",
            json=update_data,
            headers=headers
        )

        # Assert
        assert update_response.status_code == 200
        updated_asset = update_response.json()
        assert updated_asset["name"] == update_data["name"]
        assert updated_asset["environment"] == update_data["environment"]
        assert updated_asset["attributes"]["updated"] is True

    @pytest.mark.asyncio
    async def test_delete_asset(self, async_client: AsyncClient):
        """Test asset deletion."""
        # Arrange
        admin_token = TestAuthHelper.create_test_token()  # Admin permissions needed
        headers = TestAuthHelper.get_complete_headers(admin_token)
        
        # Create asset first
        create_data = (AssetTestDataBuilder()
                       .with_name("Asset to Delete")
                       .server()
                       .development()
                       .build())
        
        create_response = await async_client.post(
            "/api/v1/assets/",
            json=create_data,
            headers=headers
        )
        asset_id = create_response.json()["id"]

        # Act
        delete_response = await async_client.delete(
            f"/api/v1/assets/{asset_id}",
            headers=headers
        )

        # Assert deletion
        assert delete_response.status_code == 204

        # Verify asset is gone
        get_response = await async_client.get(
            f"/api/v1/assets/{asset_id}",
            headers=headers
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_assets_with_pagination(self, async_client: AsyncClient):
        """Test asset listing with pagination."""
        # Arrange
        headers = TestAuthHelper.get_complete_headers()
        
        # Create multiple assets
        for i in range(15):
            asset_data = (AssetTestDataBuilder()
                          .with_name(f"Test Asset {i}")
                          .server()
                          .development()
                          .build())
            
            await async_client.post(
                "/api/v1/assets/",
                json=asset_data,
                headers=headers
            )

        # Act
        list_response = await async_client.get(
            "/api/v1/assets/?page=1&page_size=10",
            headers=headers
        )

        # Assert
        assert list_response.status_code == 200
        response_data = list_response.json()
        assert "items" in response_data
        assert "total" in response_data
        assert "page" in response_data
        assert "page_size" in response_data
        assert len(response_data["items"]) <= 10
        assert response_data["total"] >= 15
```

### 2. Discovery Flow Testing

**Discovery Flow API Tests:**
```python
# tests/integration/api/test_discovery_flow.py
import pytest
import asyncio
from httpx import AsyncClient

from tests.fixtures.auth import TestAuthHelper
from tests.fixtures.mock_services import MockCrewAIService

class TestDiscoveryFlowAPI:
    """Test Discovery Flow API endpoints."""

    @pytest.mark.asyncio
    async def test_create_discovery_flow(self, async_client: AsyncClient):
        """Test discovery flow creation."""
        # Arrange
        headers = TestAuthHelper.get_complete_headers()
        
        # Create data import first
        import_data = {
            "source_type": "csv",
            "file_name": "test_assets.csv",
            "data_rows": [
                {"name": "Server1", "type": "server", "env": "prod"},
                {"name": "Database1", "type": "database", "env": "prod"}
            ]
        }
        
        import_response = await async_client.post(
            "/api/v1/data-import/",
            json=import_data,
            headers=headers
        )
        assert import_response.status_code == 201
        data_import_id = import_response.json()["id"]

        # Act
        flow_data = {
            "flow_name": "Test Discovery Flow",
            "data_import_id": data_import_id,
            "description": "Testing discovery flow creation"
        }
        
        response = await async_client.post(
            "/api/v1/discovery/flows",
            json=flow_data,
            headers=headers
        )

        # Assert
        assert response.status_code == 201
        flow_response = response.json()
        assert "flow_id" in flow_response
        assert flow_response["flow_name"] == flow_data["flow_name"]
        assert flow_response["status"] == "running"

    @pytest.mark.asyncio
    async def test_get_flow_status(self, async_client: AsyncClient):
        """Test getting flow status."""
        # Arrange
        headers = TestAuthHelper.get_complete_headers()
        
        # Create flow first (simplified for test)
        flow_data = {
            "flow_name": "Status Test Flow",
            "description": "Testing flow status retrieval"
        }
        
        create_response = await async_client.post(
            "/api/v1/discovery/flows",
            json=flow_data,
            headers=headers
        )
        flow_id = create_response.json()["flow_id"]

        # Act
        status_response = await async_client.get(
            f"/api/v1/flows/{flow_id}",
            headers=headers
        )

        # Assert
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["flow_id"] == flow_id
        assert "status" in status_data
        assert "current_phase" in status_data
        assert "progress_percentage" in status_data

    @pytest.mark.asyncio
    async def test_flow_execution_monitoring(self, async_client: AsyncClient):
        """Test monitoring flow execution progress."""
        # Arrange
        headers = TestAuthHelper.get_complete_headers()
        mock_service = MockCrewAIService()
        
        # Create and start flow
        flow_data = {
            "flow_name": "Monitoring Test Flow",
            "description": "Testing flow monitoring"
        }
        
        create_response = await async_client.post(
            "/api/v1/discovery/flows",
            json=flow_data,
            headers=headers
        )
        flow_id = create_response.json()["flow_id"]

        # Act - Monitor flow for completion
        max_attempts = 30  # 5 minutes max
        attempt = 0
        
        while attempt < max_attempts:
            status_response = await async_client.get(
                f"/api/v1/flows/{flow_id}",
                headers=headers
            )
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            if status_data["status"] in ["completed", "failed"]:
                break
            
            await asyncio.sleep(10)  # Wait 10 seconds
            attempt += 1

        # Assert
        final_status = status_response.json()
        assert final_status["status"] in ["completed", "failed"]
        
        if final_status["status"] == "completed":
            assert final_status["progress_percentage"] == 100.0
            assert "results" in final_status

    @pytest.mark.asyncio
    async def test_flow_error_handling(self, async_client: AsyncClient):
        """Test flow error handling and status reporting."""
        # Arrange
        headers = TestAuthHelper.get_complete_headers()
        
        # Create flow with invalid data to trigger error
        flow_data = {
            "flow_name": "Error Test Flow",
            "data_import_id": str(uuid.uuid4()),  # Non-existent import
            "description": "Testing error handling"
        }

        # Act
        response = await async_client.post(
            "/api/v1/discovery/flows",
            json=flow_data,
            headers=headers
        )

        # Assert
        # Should either fail immediately or create flow that fails during execution
        if response.status_code == 400:
            # Immediate validation failure
            error_data = response.json()
            assert "error" in error_data
        elif response.status_code == 201:
            # Flow created but should fail during execution
            flow_id = response.json()["flow_id"]
            
            # Monitor for failure
            for _ in range(10):  # Wait up to 100 seconds
                status_response = await async_client.get(
                    f"/api/v1/flows/{flow_id}",
                    headers=headers
                )
                
                status_data = status_response.json()
                if status_data["status"] == "failed":
                    assert "error" in status_data or "errors" in status_data
                    break
                
                await asyncio.sleep(10)
```

### 3. Tenant Isolation Testing

**Multi-Tenant API Tests:**
```python
# tests/integration/api/test_tenant_isolation.py
import pytest
import uuid
from httpx import AsyncClient

from tests.fixtures.auth import TestAuthHelper
from tests.fixtures.builders import AssetTestDataBuilder

class TestTenantIsolation:
    """Test tenant isolation in API endpoints."""

    @pytest.mark.asyncio
    async def test_assets_isolated_between_tenants(self, async_client: AsyncClient):
        """Test that assets are isolated between different tenants."""
        # Arrange
        tenant1_headers = TestAuthHelper.get_complete_headers(
            client_account_id="11111111-1111-1111-1111-111111111111",
            engagement_id="22222222-2222-2222-2222-222222222222"
        )
        
        tenant2_headers = TestAuthHelper.get_complete_headers(
            client_account_id="33333333-3333-3333-3333-333333333333",
            engagement_id="44444444-4444-4444-4444-444444444444"
        )

        # Create asset for tenant 1
        tenant1_asset = (AssetTestDataBuilder()
                         .with_name("Tenant 1 Asset")
                         .server()
                         .production()
                         .build())
        
        tenant1_response = await async_client.post(
            "/api/v1/assets/",
            json=tenant1_asset,
            headers=tenant1_headers
        )
        assert tenant1_response.status_code == 201
        tenant1_asset_id = tenant1_response.json()["id"]

        # Create asset for tenant 2
        tenant2_asset = (AssetTestDataBuilder()
                         .with_name("Tenant 2 Asset")
                         .database()
                         .development()
                         .build())
        
        tenant2_response = await async_client.post(
            "/api/v1/assets/",
            json=tenant2_asset,
            headers=tenant2_headers
        )
        assert tenant2_response.status_code == 201
        tenant2_asset_id = tenant2_response.json()["id"]

        # Act & Assert - Tenant 1 cannot see tenant 2's asset
        tenant1_get_tenant2_asset = await async_client.get(
            f"/api/v1/assets/{tenant2_asset_id}",
            headers=tenant1_headers
        )
        assert tenant1_get_tenant2_asset.status_code == 404

        # Act & Assert - Tenant 2 cannot see tenant 1's asset
        tenant2_get_tenant1_asset = await async_client.get(
            f"/api/v1/assets/{tenant1_asset_id}",
            headers=tenant2_headers
        )
        assert tenant2_get_tenant1_asset.status_code == 404

        # Act & Assert - Each tenant can see their own assets
        tenant1_get_own = await async_client.get(
            f"/api/v1/assets/{tenant1_asset_id}",
            headers=tenant1_headers
        )
        assert tenant1_get_own.status_code == 200

        tenant2_get_own = await async_client.get(
            f"/api/v1/assets/{tenant2_asset_id}",
            headers=tenant2_headers
        )
        assert tenant2_get_own.status_code == 200

    @pytest.mark.asyncio
    async def test_asset_list_filtered_by_tenant(self, async_client: AsyncClient):
        """Test that asset listing is filtered by tenant."""
        # Arrange
        tenant1_headers = TestAuthHelper.get_complete_headers(
            client_account_id="11111111-1111-1111-1111-111111111111"
        )
        
        tenant2_headers = TestAuthHelper.get_complete_headers(
            client_account_id="33333333-3333-3333-3333-333333333333"
        )

        # Create assets for both tenants
        for i in range(3):
            tenant1_asset = (AssetTestDataBuilder()
                             .with_name(f"Tenant 1 Asset {i}")
                             .server()
                             .build())
            
            await async_client.post(
                "/api/v1/assets/",
                json=tenant1_asset,
                headers=tenant1_headers
            )

        for i in range(2):
            tenant2_asset = (AssetTestDataBuilder()
                             .with_name(f"Tenant 2 Asset {i}")
                             .database()
                             .build())
            
            await async_client.post(
                "/api/v1/assets/",
                json=tenant2_asset,
                headers=tenant2_headers
            )

        # Act
        tenant1_list = await async_client.get(
            "/api/v1/assets/",
            headers=tenant1_headers
        )
        
        tenant2_list = await async_client.get(
            "/api/v1/assets/",
            headers=tenant2_headers
        )

        # Assert
        assert tenant1_list.status_code == 200
        assert tenant2_list.status_code == 200

        tenant1_data = tenant1_list.json()
        tenant2_data = tenant2_list.json()

        # Each tenant should only see their own assets
        assert len(tenant1_data["items"]) == 3
        assert len(tenant2_data["items"]) == 2

        # Verify asset names match tenant
        tenant1_names = [asset["name"] for asset in tenant1_data["items"]]
        tenant2_names = [asset["name"] for asset in tenant2_data["items"]]

        for name in tenant1_names:
            assert "Tenant 1" in name

        for name in tenant2_names:
            assert "Tenant 2" in name
```

## Performance Testing

### 1. API Performance Tests

**Load Testing API Endpoints:**
```python
# tests/performance/test_api_performance.py
import pytest
import asyncio
import time
from httpx import AsyncClient
from concurrent.futures import ThreadPoolExecutor

from tests.fixtures.auth import TestAuthHelper
from tests.fixtures.builders import AssetTestDataBuilder

class TestAPIPerformance:
    """Performance tests for API endpoints."""

    @pytest.mark.asyncio
    async def test_concurrent_asset_creation(self, async_client: AsyncClient):
        """Test concurrent asset creation performance."""
        # Arrange
        headers = TestAuthHelper.get_complete_headers()
        num_assets = 50
        
        async def create_asset(index: int):
            asset_data = (AssetTestDataBuilder()
                          .with_name(f"Performance Test Asset {index}")
                          .server()
                          .development()
                          .build())
            
            start_time = time.time()
            response = await async_client.post(
                "/api/v1/assets/",
                json=asset_data,
                headers=headers
            )
            end_time = time.time()
            
            return {
                "index": index,
                "status_code": response.status_code,
                "duration": end_time - start_time
            }

        # Act
        start_time = time.time()
        tasks = [create_asset(i) for i in range(num_assets)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Assert
        total_duration = end_time - start_time
        successful_requests = [r for r in results if r["status_code"] == 201]
        
        assert len(successful_requests) == num_assets
        assert total_duration < 30.0  # Should complete in under 30 seconds
        
        # Check individual request performance
        avg_duration = sum(r["duration"] for r in results) / len(results)
        assert avg_duration < 2.0  # Average request should be under 2 seconds
        
        print(f"Created {num_assets} assets in {total_duration:.2f}s")
        print(f"Average request duration: {avg_duration:.3f}s")

    @pytest.mark.asyncio
    async def test_pagination_performance(self, async_client: AsyncClient):
        """Test pagination performance with large datasets."""
        # Arrange
        headers = TestAuthHelper.get_complete_headers()
        num_assets = 200
        
        # Create test assets
        for i in range(num_assets):
            asset_data = (AssetTestDataBuilder()
                          .with_name(f"Pagination Test Asset {i}")
                          .server()
                          .development()
                          .build())
            
            await async_client.post(
                "/api/v1/assets/",
                json=asset_data,
                headers=headers
            )

        # Act - Test different page sizes
        page_sizes = [10, 25, 50, 100]
        performance_data = {}
        
        for page_size in page_sizes:
            start_time = time.time()
            
            response = await async_client.get(
                f"/api/v1/assets/?page=1&page_size={page_size}",
                headers=headers
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == min(page_size, num_assets)
            
            performance_data[page_size] = duration

        # Assert - Larger page sizes shouldn't be significantly slower
        for page_size, duration in performance_data.items():
            assert duration < 5.0  # Should complete in under 5 seconds
            print(f"Page size {page_size}: {duration:.3f}s")

    @pytest.mark.asyncio
    async def test_discovery_flow_startup_performance(self, async_client: AsyncClient):
        """Test discovery flow startup performance."""
        # Arrange
        headers = TestAuthHelper.get_complete_headers()
        
        # Create data import
        import_data = {
            "source_type": "csv",
            "file_name": "performance_test.csv",
            "data_rows": [{"name": f"Asset {i}", "type": "server"} for i in range(100)]
        }
        
        import_response = await async_client.post(
            "/api/v1/data-import/",
            json=import_data,
            headers=headers
        )
        data_import_id = import_response.json()["id"]

        # Act
        flow_data = {
            "flow_name": "Performance Test Flow",
            "data_import_id": data_import_id,
            "description": "Testing flow startup performance"
        }
        
        start_time = time.time()
        response = await async_client.post(
            "/api/v1/discovery/flows",
            json=flow_data,
            headers=headers
        )
        end_time = time.time()

        # Assert
        assert response.status_code == 201
        startup_duration = end_time - start_time
        assert startup_duration < 10.0  # Should start in under 10 seconds
        
        print(f"Discovery flow startup took {startup_duration:.3f}s")
```

## Error Handling Testing

### 1. Validation Error Testing

**Input Validation Tests:**
```python
# tests/integration/api/test_validation_errors.py
import pytest
from httpx import AsyncClient

from tests.fixtures.auth import TestAuthHelper

class TestValidationErrors:
    """Test API validation error handling."""

    @pytest.mark.asyncio
    async def test_missing_required_fields(self, async_client: AsyncClient):
        """Test validation errors for missing required fields."""
        # Arrange
        headers = TestAuthHelper.get_complete_headers()
        incomplete_asset = {
            # Missing required 'name' field
            "asset_type": "server",
            "environment": "test"
        }

        # Act
        response = await async_client.post(
            "/api/v1/assets/",
            json=incomplete_asset,
            headers=headers
        )

        # Assert
        assert response.status_code == 422
        error_data = response.json()
        assert "error" in error_data
        assert "field_errors" in error_data["error"]["details"]
        
        field_errors = error_data["error"]["details"]["field_errors"]
        name_error = next((e for e in field_errors if e["field"] == "name"), None)
        assert name_error is not None
        assert "required" in name_error["message"]

    @pytest.mark.asyncio
    async def test_invalid_field_values(self, async_client: AsyncClient):
        """Test validation errors for invalid field values."""
        # Arrange
        headers = TestAuthHelper.get_complete_headers()
        invalid_asset = {
            "name": "",  # Empty name
            "asset_type": "server",
            "environment": "invalid-env"  # Invalid environment
        }

        # Act
        response = await async_client.post(
            "/api/v1/assets/",
            json=invalid_asset,
            headers=headers
        )

        # Assert
        assert response.status_code == 422
        error_data = response.json()
        field_errors = error_data["error"]["details"]["field_errors"]
        
        # Check for name validation error
        name_error = next((e for e in field_errors if e["field"] == "name"), None)
        assert name_error is not None
        assert "cannot be empty" in name_error["message"]
        
        # Check for environment validation error
        env_error = next((e for e in field_errors if e["field"] == "environment"), None)
        assert env_error is not None
        assert "must be one of" in env_error["message"]

    @pytest.mark.asyncio
    async def test_invalid_uuid_format(self, async_client: AsyncClient):
        """Test validation errors for invalid UUID formats."""
        # Arrange
        headers = TestAuthHelper.get_complete_headers()
        invalid_uuid = "not-a-uuid"

        # Act
        response = await async_client.get(
            f"/api/v1/assets/{invalid_uuid}",
            headers=headers
        )

        # Assert
        assert response.status_code == 422
        error_data = response.json()
        assert "invalid UUID format" in str(error_data).lower()
```

### 2. HTTP Error Testing

**HTTP Status Code Tests:**
```python
# tests/integration/api/test_http_errors.py
import pytest
import uuid
from httpx import AsyncClient

from tests.fixtures.auth import TestAuthHelper

class TestHTTPErrors:
    """Test HTTP error responses."""

    @pytest.mark.asyncio
    async def test_404_not_found(self, async_client: AsyncClient):
        """Test 404 error for non-existent resource."""
        # Arrange
        headers = TestAuthHelper.get_complete_headers()
        non_existent_id = str(uuid.uuid4())

        # Act
        response = await async_client.get(
            f"/api/v1/assets/{non_existent_id}",
            headers=headers
        )

        # Assert
        assert response.status_code == 404
        error_data = response.json()
        assert "not found" in error_data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_405_method_not_allowed(self, async_client: AsyncClient):
        """Test 405 error for unsupported HTTP method."""
        # Arrange
        headers = TestAuthHelper.get_complete_headers()

        # Act - PATCH method not supported on this endpoint
        response = await async_client.patch(
            "/api/v1/assets/",
            json={"test": "data"},
            headers=headers
        )

        # Assert
        assert response.status_code == 405
        error_data = response.json()
        assert "method not allowed" in error_data["error"]["message"].lower()

    @pytest.mark.asyncio
    async def test_500_internal_server_error_handling(self, async_client: AsyncClient):
        """Test 500 error handling for server errors."""
        # Note: This test would require mocking to force a server error
        # Implementation depends on specific error simulation needs
        pass

    @pytest.mark.asyncio
    async def test_429_rate_limiting(self, async_client: AsyncClient):
        """Test rate limiting responses."""
        # Arrange
        headers = TestAuthHelper.get_complete_headers()
        
        # Act - Make many requests rapidly (if rate limiting is implemented)
        responses = []
        for _ in range(100):
            response = await async_client.get("/api/v1/health", headers=headers)
            responses.append(response.status_code)
            
            # If we get rate limited, break
            if response.status_code == 429:
                break

        # Assert - Check if any requests were rate limited
        rate_limited = any(status == 429 for status in responses)
        if rate_limited:
            # If rate limiting is implemented, verify the response
            rate_limit_response = await async_client.get("/api/v1/health", headers=headers)
            if rate_limit_response.status_code == 429:
                error_data = rate_limit_response.json()
                assert "rate limit" in error_data["error"]["message"].lower()
```

This comprehensive API testing guide provides robust patterns for testing all aspects of the AI Modernize Migration Platform's API, ensuring reliability, security, and proper error handling across all endpoints.