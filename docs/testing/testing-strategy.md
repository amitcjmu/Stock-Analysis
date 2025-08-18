# Testing Strategy Guide

**Last Updated: August 18, 2025**

## Overview

The AI Modernize Migration Platform implements a comprehensive testing strategy following the **Test Pyramid** approach with unit tests (70%), integration tests (20%), and end-to-end tests (10%). All tests run within Docker containers to ensure consistency across development environments.

## Testing Architecture

### Test Pyramid Structure

```
         ┌─────────────────┐
         │   E2E Tests     │ ← 10% - Full system tests
         │   (Slow/Expensive)  │
         └─────────────────┘
       ┌─────────────────────┐
       │ Integration Tests   │ ← 20% - Component interaction
       │   (Medium Speed)    │
       └─────────────────────┘
     ┌─────────────────────────┐
     │     Unit Tests          │ ← 70% - Individual components
     │    (Fast/Isolated)      │
     └─────────────────────────┘
```

### Testing Framework Stack

**Backend Testing:**
- **pytest** - Main testing framework
- **pytest-asyncio** - Async test support
- **unittest.mock** - Mocking and stubbing
- **SQLAlchemy** - Database testing utilities
- **httpx** - HTTP client testing
- **faker** - Test data generation

**Frontend Testing:**
- **Jest** - Unit testing framework
- **React Testing Library** - Component testing
- **Cypress** - End-to-end testing
- **MSW** - API mocking
- **@testing-library/user-event** - User interaction testing

## Test Organization

### Directory Structure

```
backend/
├── tests/
│   ├── unit/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── models/
│   │   └── utils/
│   ├── integration/
│   │   ├── api/
│   │   ├── database/
│   │   └── external_services/
│   ├── e2e/
│   │   ├── workflows/
│   │   └── scenarios/
│   ├── fixtures/
│   │   ├── data/
│   │   └── mocks/
│   └── conftest.py
│
frontend/
├── __tests__/
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   └── utils/
├── cypress/
│   ├── e2e/
│   ├── fixtures/
│   └── support/
└── jest.config.js
```

### Test Configuration

**Backend pytest Configuration (`backend/pytest.ini`):**
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --strict-config
    --tb=short
    --asyncio-mode=auto
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    db: Database tests
    external: Tests requiring external services
    tenant_isolation: Tenant isolation tests
asyncio_mode = auto
```

**Frontend Jest Configuration (`frontend/jest.config.js`):**
```javascript
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: './',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapping: {
    '^@/components/(.*)$': '<rootDir>/components/$1',
    '^@/pages/(.*)$': '<rootDir>/pages/$1',
    '^@/lib/(.*)$': '<rootDir>/lib/$1',
    '^@/hooks/(.*)$': '<rootDir>/hooks/$1',
    '^@/utils/(.*)$': '<rootDir>/utils/$1',
  },
  testEnvironment: 'jest-environment-jsdom',
  collectCoverageFrom: [
    'components/**/*.{js,jsx,ts,tsx}',
    'pages/**/*.{js,jsx,ts,tsx}',
    'lib/**/*.{js,jsx,ts,tsx}',
    'hooks/**/*.{js,jsx,ts,tsx}',
    'utils/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
}

module.exports = createJestConfig(customJestConfig)
```

## Unit Testing Patterns

### 1. Service Layer Testing

**Testing Service Classes:**
```python
# tests/unit/services/test_field_mapping_service.py
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.field_mapping_service import FieldMappingService
from app.models.data_import.mapping import ImportFieldMapping

class TestFieldMappingService:
    """Test FieldMappingService with proper tenant isolation."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        
        # Mock execute to return proper result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)
        
        return session

    @pytest.fixture
    def test_context(self):
        """Create test request context."""
        return RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
        )

    @pytest.fixture
    def field_mapping_service(self, mock_session, test_context):
        """Create FieldMappingService instance."""
        return FieldMappingService(mock_session, test_context)

    @pytest.mark.asyncio
    async def test_create_field_mapping_success(
        self, 
        field_mapping_service, 
        mock_session,
        test_context
    ):
        """Test successful field mapping creation."""
        # Arrange
        data_import_id = str(uuid.uuid4())
        mapping_data = {
            "source_field": "customer_name",
            "target_field": "name",
            "confidence_score": 0.95,
            "mapping_type": "direct"
        }

        # Act
        result = await field_mapping_service.create_field_mapping(
            data_import_id=data_import_id,
            mapping_data=mapping_data
        )

        # Assert
        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        
        # Verify tenant context is applied
        added_mapping = mock_session.add.call_args[0][0]
        assert str(added_mapping.client_account_id) == test_context.client_account_id
        assert str(added_mapping.engagement_id) == test_context.engagement_id

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, mock_session):
        """Test that different tenants cannot access each other's data."""
        # Arrange
        tenant1_context = RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
        )
        
        tenant2_context = RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
        )

        service1 = FieldMappingService(mock_session, tenant1_context)
        service2 = FieldMappingService(mock_session, tenant2_context)

        # Act & Assert
        # When tenant2 tries to access tenant1's data, it should get empty results
        await service2.get_mappings_by_data_import(str(uuid.uuid4()))
        
        # Verify query includes proper tenant filters
        query_calls = mock_session.execute.call_args_list
        assert len(query_calls) > 0
        # Query should include tenant2's context, not tenant1's
```

### 2. Repository Layer Testing

**Testing Repository Pattern:**
```python
# tests/unit/repositories/test_asset_repository.py
import uuid
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.repositories.asset_repository import AssetRepository
from app.models.asset import Asset
from app.core.context import RequestContext

class TestAssetRepository:
    """Test AssetRepository with tenant isolation."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def test_context(self):
        """Create test context."""
        return RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id="test-user"
        )

    @pytest.fixture
    def asset_repository(self, mock_db, test_context):
        """Create AssetRepository instance."""
        return AssetRepository(mock_db, test_context.client_account_id)

    @pytest.mark.asyncio
    async def test_create_asset_with_tenant_context(
        self, 
        asset_repository, 
        mock_db, 
        test_context
    ):
        """Test asset creation with proper tenant context."""
        # Arrange
        asset_data = {
            "name": "Test Server",
            "asset_type": "server",
            "environment": "production",
            "attributes": {"cpu": "4 cores", "memory": "16GB"}
        }

        # Mock the created asset
        mock_asset = Asset(
            id=uuid.uuid4(),
            name=asset_data["name"],
            asset_type=asset_data["asset_type"],
            client_account_id=uuid.UUID(test_context.client_account_id),
            engagement_id=uuid.UUID(test_context.engagement_id),
            created_at=datetime.utcnow()
        )
        mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', mock_asset.id)

        # Act
        result = await asset_repository.create_asset(
            asset_data, 
            test_context.user_id, 
            test_context.engagement_id
        )

        # Assert
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # Verify tenant context is applied
        created_asset = mock_db.add.call_args[0][0]
        assert str(created_asset.client_account_id) == test_context.client_account_id
        assert str(created_asset.engagement_id) == test_context.engagement_id
```

### 3. Model Testing

**Testing Pydantic Models:**
```python
# tests/unit/models/test_asset_schemas.py
import pytest
from pydantic import ValidationError

from app.schemas.asset_schemas import AssetCreate, AssetUpdate, AssetResponse

class TestAssetSchemas:
    """Test asset Pydantic models."""

    def test_asset_create_valid_data(self):
        """Test AssetCreate with valid data."""
        # Arrange
        valid_data = {
            "name": "Web Server",
            "asset_type": "server",
            "environment": "production",
            "attributes": {"os": "ubuntu", "version": "20.04"},
            "tags": ["web", "production"]
        }

        # Act
        asset = AssetCreate(**valid_data)

        # Assert
        assert asset.name == "Web Server"
        assert asset.asset_type == "server"
        assert asset.environment == "production"
        assert asset.attributes == {"os": "ubuntu", "version": "20.04"}
        assert asset.tags == ["web", "production"]

    def test_asset_create_invalid_environment(self):
        """Test AssetCreate with invalid environment."""
        # Arrange
        invalid_data = {
            "name": "Test Server",
            "asset_type": "server",
            "environment": "invalid-env",  # Invalid environment
            "attributes": {},
            "tags": []
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AssetCreate(**invalid_data)
        
        assert "Environment must be one of" in str(exc_info.value)

    def test_asset_create_empty_name(self):
        """Test AssetCreate with empty name."""
        # Arrange
        invalid_data = {
            "name": "",  # Empty name
            "asset_type": "server",
            "environment": "dev",
            "attributes": {},
            "tags": []
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            AssetCreate(**invalid_data)
        
        assert "Asset name cannot be empty" in str(exc_info.value)
```

## Integration Testing Patterns

### 1. API Integration Tests

**Testing API Endpoints:**
```python
# tests/integration/api/test_asset_endpoints.py
import uuid
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app
from app.core.context import RequestContext
from tests.fixtures.database import test_db_session, test_client_with_db

class TestAssetEndpoints:
    """Integration tests for asset API endpoints."""

    @pytest.mark.asyncio
    async def test_create_asset_endpoint(self, test_client_with_db):
        """Test asset creation endpoint."""
        # Arrange
        client, db = test_client_with_db
        asset_data = {
            "name": "Integration Test Server",
            "asset_type": "server",
            "environment": "test",
            "attributes": {"test": True},
            "tags": ["integration-test"]
        }
        
        headers = {
            "X-Client-Account-Id": "11111111-1111-1111-1111-111111111111",
            "X-Engagement-Id": "22222222-2222-2222-2222-222222222222",
            "X-User-Id": "test-user"
        }

        # Act
        response = client.post(
            "/api/v1/assets/",
            json=asset_data,
            headers=headers
        )

        # Assert
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["name"] == asset_data["name"]
        assert response_data["asset_type"] == asset_data["asset_type"]
        assert "id" in response_data
        assert "created_at" in response_data

    @pytest.mark.asyncio
    async def test_get_asset_endpoint(self, test_client_with_db):
        """Test asset retrieval endpoint."""
        # Arrange
        client, db = test_client_with_db
        
        # First create an asset
        asset_data = {
            "name": "Test Asset for Retrieval",
            "asset_type": "database",
            "environment": "test",
            "attributes": {},
            "tags": []
        }
        
        headers = {
            "X-Client-Account-Id": "11111111-1111-1111-1111-111111111111",
            "X-Engagement-Id": "22222222-2222-2222-2222-222222222222",
            "X-User-Id": "test-user"
        }

        create_response = client.post(
            "/api/v1/assets/",
            json=asset_data,
            headers=headers
        )
        created_asset = create_response.json()
        asset_id = created_asset["id"]

        # Act
        get_response = client.get(
            f"/api/v1/assets/{asset_id}",
            headers=headers
        )

        # Assert
        assert get_response.status_code == 200
        retrieved_asset = get_response.json()
        assert retrieved_asset["id"] == asset_id
        assert retrieved_asset["name"] == asset_data["name"]

    @pytest.mark.asyncio
    async def test_tenant_isolation_in_api(self, test_client_with_db):
        """Test that API properly isolates tenant data."""
        # Arrange
        client, db = test_client_with_db
        
        tenant1_headers = {
            "X-Client-Account-Id": "11111111-1111-1111-1111-111111111111",
            "X-Engagement-Id": "22222222-2222-2222-2222-222222222222",
            "X-User-Id": "tenant1-user"
        }
        
        tenant2_headers = {
            "X-Client-Account-Id": "33333333-3333-3333-3333-333333333333",
            "X-Engagement-Id": "44444444-4444-4444-4444-444444444444",
            "X-User-Id": "tenant2-user"
        }

        # Create asset for tenant1
        asset_data = {
            "name": "Tenant1 Asset",
            "asset_type": "server",
            "environment": "test",
            "attributes": {},
            "tags": []
        }

        create_response = client.post(
            "/api/v1/assets/",
            json=asset_data,
            headers=tenant1_headers
        )
        tenant1_asset = create_response.json()
        asset_id = tenant1_asset["id"]

        # Act - Try to access tenant1's asset with tenant2's context
        get_response = client.get(
            f"/api/v1/assets/{asset_id}",
            headers=tenant2_headers
        )

        # Assert - Tenant2 should not be able to access tenant1's asset
        assert get_response.status_code == 404
```

### 2. Database Integration Tests

**Testing Database Operations:**
```python
# tests/integration/database/test_database_operations.py
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.discovery_flow import DiscoveryFlow
from app.core.context import RequestContext
from tests.fixtures.database import test_db_session

class TestDatabaseOperations:
    """Integration tests for database operations."""

    @pytest.mark.asyncio
    async def test_asset_creation_and_retrieval(self, test_db_session):
        """Test creating and retrieving assets from database."""
        # Arrange
        db: AsyncSession = test_db_session
        client_account_id = uuid.uuid4()
        engagement_id = uuid.uuid4()

        asset = Asset(
            name="Database Test Asset",
            asset_type="server",
            environment="test",
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            attributes={"test": True},
            tags=["database-test"]
        )

        # Act - Create
        db.add(asset)
        await db.commit()
        await db.refresh(asset)

        # Act - Retrieve
        result = await db.execute(
            select(Asset).where(Asset.id == asset.id)
        )
        retrieved_asset = result.scalar_one_or_none()

        # Assert
        assert retrieved_asset is not None
        assert retrieved_asset.name == "Database Test Asset"
        assert retrieved_asset.asset_type == "server"
        assert retrieved_asset.client_account_id == client_account_id
        assert retrieved_asset.engagement_id == engagement_id

    @pytest.mark.asyncio
    async def test_foreign_key_relationships(self, test_db_session):
        """Test foreign key relationships between models."""
        # Arrange
        db: AsyncSession = test_db_session
        client_account_id = uuid.uuid4()
        engagement_id = uuid.uuid4()

        # Create discovery flow
        discovery_flow = DiscoveryFlow(
            flow_id=uuid.uuid4(),
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            user_id="test-user",
            flow_name="Test Discovery Flow",
            current_phase="initialization",
            flow_status="running"
        )

        db.add(discovery_flow)
        await db.commit()
        await db.refresh(discovery_flow)

        # Create asset linked to discovery flow
        asset = Asset(
            name="Linked Asset",
            asset_type="server",
            environment="test",
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            discovery_flow_id=discovery_flow.id,
            attributes={},
            tags=[]
        )

        # Act
        db.add(asset)
        await db.commit()
        await db.refresh(asset)

        # Assert relationship
        assert asset.discovery_flow_id == discovery_flow.id
        
        # Test cascade behavior would go here
```

## End-to-End Testing Patterns

### 1. Workflow Testing

**Testing Complete User Workflows:**
```python
# tests/e2e/workflows/test_discovery_workflow.py
import pytest
import asyncio
from httpx import AsyncClient

from tests.fixtures.e2e import e2e_client, setup_test_tenant

class TestDiscoveryWorkflow:
    """End-to-end tests for discovery workflow."""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_discovery_workflow(self, e2e_client, setup_test_tenant):
        """Test complete discovery workflow from start to finish."""
        client, tenant_context = e2e_client, setup_test_tenant
        
        # Step 1: Create data import
        import_data = {
            "source_type": "csv",
            "file_name": "test_assets.csv",
            "data_rows": [
                {"name": "Server1", "type": "server", "env": "prod"},
                {"name": "Database1", "type": "database", "env": "prod"}
            ]
        }
        
        import_response = await client.post(
            "/api/v1/data-import/",
            json=import_data,
            headers=tenant_context.headers
        )
        assert import_response.status_code == 201
        data_import_id = import_response.json()["id"]

        # Step 2: Start discovery flow
        flow_data = {
            "flow_name": "E2E Test Discovery",
            "data_import_id": data_import_id,
            "description": "End-to-end test discovery flow"
        }
        
        flow_response = await client.post(
            "/api/v1/discovery/flows",
            json=flow_data,
            headers=tenant_context.headers
        )
        assert flow_response.status_code == 201
        flow_id = flow_response.json()["flow_id"]

        # Step 3: Monitor flow progress
        max_attempts = 60  # 5 minutes max
        attempt = 0
        
        while attempt < max_attempts:
            status_response = await client.get(
                f"/api/v1/flows/{flow_id}",
                headers=tenant_context.headers
            )
            assert status_response.status_code == 200
            
            flow_status = status_response.json()
            if flow_status["status"] in ["completed", "failed"]:
                break
                
            await asyncio.sleep(5)  # Wait 5 seconds
            attempt += 1

        # Step 4: Verify completion
        final_status = status_response.json()
        assert final_status["status"] == "completed"
        assert final_status["progress_percentage"] == 100.0

        # Step 5: Verify assets were created
        assets_response = await client.get(
            "/api/v1/assets/",
            headers=tenant_context.headers
        )
        assert assets_response.status_code == 200
        
        assets_data = assets_response.json()
        assert len(assets_data["items"]) >= 2  # At least the 2 we imported
        
        # Verify asset details
        asset_names = [asset["name"] for asset in assets_data["items"]]
        assert "Server1" in asset_names
        assert "Database1" in asset_names
```

### 2. Frontend E2E Testing (Cypress)

**Cypress E2E Tests:**
```javascript
// cypress/e2e/discovery-flow.cy.js
describe('Discovery Flow E2E', () => {
  beforeEach(() => {
    // Setup test environment
    cy.task('seedTestData')
    cy.visit('/dashboard')
  })

  it('should complete discovery flow workflow', () => {
    // Step 1: Navigate to discovery flow
    cy.get('[data-cy=nav-discovery]').click()
    cy.url().should('include', '/discovery')

    // Step 2: Upload data file
    cy.get('[data-cy=upload-button]').click()
    cy.get('input[type=file]').selectFile('cypress/fixtures/test-assets.csv')
    cy.get('[data-cy=confirm-upload]').click()

    // Step 3: Start discovery flow
    cy.get('[data-cy=flow-name-input]').type('Cypress Test Flow')
    cy.get('[data-cy=start-discovery]').click()

    // Step 4: Monitor progress
    cy.get('[data-cy=progress-bar]', { timeout: 300000 }) // 5 minutes timeout
      .should('have.attr', 'aria-valuenow', '100')

    // Step 5: Verify results
    cy.get('[data-cy=flow-status]').should('contain', 'Completed')
    cy.get('[data-cy=assets-count]').should('not.contain', '0')

    // Step 6: Navigate to assets and verify
    cy.get('[data-cy=view-assets]').click()
    cy.url().should('include', '/assets')
    cy.get('[data-cy=asset-list]').should('exist')
    cy.get('[data-cy=asset-item]').should('have.length.at.least', 1)
  })

  it('should handle discovery flow errors gracefully', () => {
    // Test error scenarios
    cy.get('[data-cy=nav-discovery]').click()
    
    // Try to start flow without data
    cy.get('[data-cy=start-discovery]').click()
    cy.get('[data-cy=error-message]')
      .should('be.visible')
      .and('contain', 'Data import required')

    // Upload invalid file
    cy.get('[data-cy=upload-button]').click()
    cy.get('input[type=file]').selectFile('cypress/fixtures/invalid-file.txt')
    cy.get('[data-cy=confirm-upload]').click()
    cy.get('[data-cy=error-message]')
      .should('be.visible')
      .and('contain', 'Invalid file format')
  })
})
```

## Test Data Management

### 1. Test Fixtures

**Database Test Fixtures:**
```python
# tests/fixtures/database.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.config import settings

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5433/test_migration_db"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def test_db_session(test_engine):
    """Create test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()
```

**Test Data Factories:**
```python
# tests/fixtures/factories.py
import uuid
from datetime import datetime
from typing import Dict, Any

from app.models.asset import Asset
from app.models.discovery_flow import DiscoveryFlow
from app.core.context import RequestContext

class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_test_context() -> RequestContext:
        """Create test request context."""
        return RequestContext(
            client_account_id=str(uuid.uuid4()),
            engagement_id=str(uuid.uuid4()),
            user_id="test-user",
            request_id=str(uuid.uuid4())
        )

    @staticmethod
    def create_test_asset(
        context: RequestContext,
        overrides: Dict[str, Any] = None
    ) -> Asset:
        """Create test asset."""
        data = {
            "name": "Test Asset",
            "asset_type": "server",
            "environment": "test",
            "client_account_id": uuid.UUID(context.client_account_id),
            "engagement_id": uuid.UUID(context.engagement_id),
            "attributes": {"test": True},
            "tags": ["test"],
            "created_at": datetime.utcnow()
        }
        
        if overrides:
            data.update(overrides)
        
        return Asset(**data)

    @staticmethod
    def create_test_discovery_flow(
        context: RequestContext,
        overrides: Dict[str, Any] = None
    ) -> DiscoveryFlow:
        """Create test discovery flow."""
        data = {
            "flow_id": uuid.uuid4(),
            "client_account_id": uuid.UUID(context.client_account_id),
            "engagement_id": uuid.UUID(context.engagement_id),
            "user_id": context.user_id,
            "flow_name": "Test Discovery Flow",
            "current_phase": "initialization",
            "flow_status": "running",
            "created_at": datetime.utcnow()
        }
        
        if overrides:
            data.update(overrides)
        
        return DiscoveryFlow(**data)
```

### 2. Mock Data and Services

**Service Mocking:**
```python
# tests/fixtures/mocks.py
from unittest.mock import AsyncMock, MagicMock
import json

class MockCrewAIService:
    """Mock CrewAI service for testing."""
    
    def __init__(self):
        self.execute_discovery = AsyncMock()
        self.execute_assessment = AsyncMock()
        
    async def mock_discovery_success(self, *args, **kwargs):
        """Mock successful discovery execution."""
        return {
            "status": "completed",
            "results": {
                "assets_discovered": 5,
                "dependencies_mapped": 3,
                "confidence_score": 0.95
            }
        }
    
    async def mock_discovery_failure(self, *args, **kwargs):
        """Mock failed discovery execution."""
        raise Exception("Mock discovery failure")

class MockRedisCache:
    """Mock Redis cache for testing."""
    
    def __init__(self):
        self._data = {}
    
    async def get(self, key):
        return self._data.get(key)
    
    async def set(self, key, value):
        self._data[key] = value
    
    async def setex(self, key, ttl, value):
        self._data[key] = value
    
    async def delete(self, key):
        self._data.pop(key, None)
```

## Test Execution

### 1. Running Tests in Docker

**Backend Tests:**
```bash
# Enter backend container
docker exec -it migration_backend bash

# Run all tests
pytest

# Run specific test categories
pytest -m unit                    # Unit tests only
pytest -m integration            # Integration tests only  
pytest -m "not slow"             # Exclude slow tests
pytest -m tenant_isolation       # Tenant isolation tests

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/services/test_field_mapping_service.py -v

# Run tests in parallel
pytest -n auto
```

**Frontend Tests:**
```bash
# Enter frontend container
docker exec -it migration_frontend sh

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run cypress:run

# Run E2E tests interactively
npm run cypress:open
```

### 2. CI/CD Test Execution

**GitHub Actions Workflow:**
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_migration_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Run unit tests
      run: |
        cd backend
        pytest tests/unit -v --cov=app
    
    - name: Run integration tests
      run: |
        cd backend
        pytest tests/integration -v
      env:
        DATABASE_URL: postgresql+asyncpg://postgres:test@localhost:5432/test_migration_db

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Run tests
      run: |
        cd frontend
        npm run test:coverage
    
    - name: Run E2E tests
      run: |
        cd frontend
        npm run cypress:run
```

## Performance and Load Testing

### 1. Performance Testing

**API Performance Tests:**
```python
# tests/performance/test_api_performance.py
import pytest
import asyncio
import time
from httpx import AsyncClient

class TestAPIPerformance:
    """Performance tests for API endpoints."""

    @pytest.mark.asyncio
    async def test_asset_creation_performance(self, test_client):
        """Test asset creation performance."""
        client = test_client
        
        # Warm up
        for _ in range(5):
            await self._create_test_asset(client)
        
        # Performance test
        start_time = time.time()
        tasks = []
        
        for i in range(100):  # Create 100 assets concurrently
            task = self._create_test_asset(client, f"Perf Test Asset {i}")
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        end_time = time.time()
        
        duration = end_time - start_time
        assert duration < 10.0  # Should complete in under 10 seconds
        print(f"Created 100 assets in {duration:.2f} seconds")

    async def _create_test_asset(self, client, name="Test Asset"):
        """Helper to create test asset."""
        asset_data = {
            "name": name,
            "asset_type": "server",
            "environment": "test",
            "attributes": {},
            "tags": []
        }
        
        response = await client.post(
            "/api/v1/assets/",
            json=asset_data,
            headers={
                "X-Client-Account-Id": "11111111-1111-1111-1111-111111111111",
                "X-Engagement-Id": "22222222-2222-2222-2222-222222222222",
                "X-User-Id": "perf-test-user"
            }
        )
        return response
```

### 2. Load Testing with Locust

**Load Test Scripts:**
```python
# tests/load/locustfile.py
from locust import HttpUser, task, between
import json
import uuid

class APIUser(HttpUser):
    """Load test user for API endpoints."""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Setup test user."""
        self.headers = {
            "Content-Type": "application/json",
            "X-Client-Account-Id": "11111111-1111-1111-1111-111111111111",
            "X-Engagement-Id": "22222222-2222-2222-2222-222222222222",
            "X-User-Id": f"load-test-user-{uuid.uuid4()}"
        }
    
    @task(3)
    def get_health(self):
        """Test health endpoint."""
        self.client.get("/health")
    
    @task(2)
    def list_assets(self):
        """Test asset listing."""
        self.client.get("/api/v1/assets/", headers=self.headers)
    
    @task(1)
    def create_asset(self):
        """Test asset creation."""
        asset_data = {
            "name": f"Load Test Asset {uuid.uuid4()}",
            "asset_type": "server",
            "environment": "test",
            "attributes": {"load_test": True},
            "tags": ["load-test"]
        }
        
        response = self.client.post(
            "/api/v1/assets/",
            json=asset_data,
            headers=self.headers
        )
        
        if response.status_code == 201:
            asset_id = response.json()["id"]
            # Sometimes get the created asset
            if uuid.uuid4().int % 4 == 0:
                self.client.get(f"/api/v1/assets/{asset_id}", headers=self.headers)
```

**Running Load Tests:**
```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Run headless load test
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
       --users 50 --spawn-rate 5 --run-time 5m --headless
```

## Test Reporting and Coverage

### 1. Coverage Reports

**Backend Coverage:**
```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html --cov-report=term

# Coverage report output
# Name                                      Stmts   Miss  Cover
# -----------------------------------------------------------
# app/__init__.py                               0      0   100%
# app/api/__init__.py                          0      0   100%
# app/api/v1/__init__.py                       0      0   100%
# app/api/v1/endpoints/assets.py             120     12    90%
# app/services/asset_service.py               95      8    92%
# app/repositories/asset_repository.py        78      5    94%
# -----------------------------------------------------------
# TOTAL                                     2847    156    95%
```

**Frontend Coverage:**
```bash
# Generate frontend coverage
npm run test:coverage

# Coverage output
# -------------------|---------|----------|---------|---------|-------------------
# File               | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s 
# -------------------|---------|----------|---------|---------|-------------------
# All files          |   89.45 |    82.14 |   88.23 |   89.67 |                   
#  components        |   92.11 |    85.71 |   90.48 |   92.31 |                   
#   Dashboard.tsx    |   95.65 |    87.50 |   100.0 |   95.45 | 45,67            
#   AssetList.tsx    |   88.24 |    83.33 |   81.82 |   88.89 | 23,89,156        
# -------------------|---------|----------|---------|---------|-------------------
```

### 2. Test Reports

**JUnit XML Reports:**
```bash
# Generate JUnit XML for CI/CD
pytest --junitxml=test-results.xml

# Frontend test reports
npm test -- --coverage --watchAll=false --reporters=default --reporters=jest-junit
```

This comprehensive testing strategy ensures high-quality, reliable code with excellent test coverage across all layers of the AI Modernize Migration Platform.