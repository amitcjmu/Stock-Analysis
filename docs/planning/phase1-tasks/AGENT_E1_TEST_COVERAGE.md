# Phase 1 - Agent E1: Test Coverage & Automation

## Context
You are part of a parallel remediation effort to fix critical architectural issues in the AI Force Migration Platform. This is Track E (Testing) of Phase 1, focusing on establishing comprehensive test coverage and automation for all Phase 1 changes.

### Required Reading Before Starting
- `docs/planning/PHASE-1-REMEDIATION-PLAN.md` - Overall Phase 1 objectives
- All other agent task files to understand what's being built
- Current test coverage report: `docker exec -it migration_backend coverage report`

### Phase 1 Goal
Achieve 80% test coverage and establish automated testing for all critical paths. Your tests will ensure the stability of Phase 1 changes and prevent regressions.

## Your Specific Tasks

### 1. Backend Unit Tests for Migration
**File to create**: `backend/tests/unit/test_session_flow_migration.py`

```python
"""
Test session to flow ID migration
"""
import pytest
from app.services.migration.session_to_flow import SessionFlowCompatibilityService
from app.models import DataImport, RawImportRecord

class TestSessionFlowMigration:
    """Test cases for session to flow migration"""
    
    @pytest.mark.asyncio
    async def test_migrate_data_import(self, db_session):
        """Test migrating data import from session to flow"""
        # Create test data with session_id
        # Run migration
        # Verify flow_id populated
        # Verify data integrity
    
    @pytest.mark.asyncio
    async def test_backward_compatibility(self, db_session):
        """Test backward compatibility layer"""
        # Test session_id lookup returns flow_id
        # Test deprecation warnings logged
    
    @pytest.mark.asyncio
    async def test_migration_rollback(self, db_session):
        """Test migration can be rolled back safely"""
        # Run migration
        # Rollback
        # Verify original state restored
```

### 2. Frontend Unit Tests
**File to create**: `src/hooks/__tests__/useAttributeMappingLogic.test.ts`

```typescript
import { renderHook, act } from '@testing-library/react-hooks';
import { useAttributeMappingLogic } from '../discovery/useAttributeMappingLogic';
import { mockFlow, mockFieldMappings } from './fixtures';

describe('useAttributeMappingLogic', () => {
  it('should load field mappings on mount', async () => {
    const { result, waitForNextUpdate } = renderHook(() => 
      useAttributeMappingLogic()
    );
    
    expect(result.current.isAgenticLoading).toBe(true);
    await waitForNextUpdate();
    expect(result.current.fieldMappings).toEqual(mockFieldMappings);
  });
  
  it('should handle approve mapping correctly', async () => {
    const { result } = renderHook(() => useAttributeMappingLogic());
    
    await act(async () => {
      await result.current.handleApproveMapping('mapping-1');
    });
    
    // Verify API called with correct params
    // Verify optimistic update
    // Verify refetch triggered
  });
  
  it('should use data_import_id not flow_id', async () => {
    // Test that ensures correct ID usage
  });
});
```

### 3. API Integration Tests
**File to create**: `backend/tests/integration/test_v3_api.py`

```python
"""
Integration tests for v3 API
"""
import pytest
from httpx import AsyncClient
from app.main import app

class TestV3DiscoveryFlowAPI:
    """Test v3 discovery flow endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_flow(self, async_client: AsyncClient, auth_headers):
        """Test creating a new flow"""
        response = await async_client.post(
            "/api/v3/discovery-flow/flows",
            json={
                "name": "Test Flow",
                "client_account_id": "test-client",
                "engagement_id": "test-engagement"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "flow_id" in data
        assert data["status"] == "initializing"
    
    @pytest.mark.asyncio
    async def test_flow_lifecycle(self, async_client: AsyncClient, auth_headers):
        """Test complete flow lifecycle"""
        # Create flow
        # Execute phases
        # Verify state transitions
        # Complete flow
        # Verify final state
```

### 4. End-to-End Tests
**File to create**: `frontend/tests/e2e/field-mapping-flow.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Field Mapping Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login and navigate to field mapping
    await page.goto('/discovery/attribute-mapping');
  });
  
  test('should complete field mapping workflow', async ({ page }) => {
    // Wait for mappings to load
    await page.waitForSelector('[data-testid="field-mapping-table"]');
    
    // Test dropdown interaction
    await page.click('[data-testid="mapping-dropdown-1"]');
    await expect(page.locator('.dropdown-menu')).toBeVisible();
    
    // Click outside to close
    await page.click('body');
    await expect(page.locator('.dropdown-menu')).not.toBeVisible();
    
    // Approve a mapping
    await page.click('[data-testid="approve-mapping-1"]');
    await expect(page.locator('[data-testid="success-toast"]')).toBeVisible();
    
    // Verify mapping removed from pending list
    await expect(page.locator('[data-testid="mapping-row-1"]')).not.toBeVisible();
  });
  
  test('should handle errors gracefully', async ({ page }) => {
    // Test network failure
    await page.route('**/api/v1/**', route => route.abort());
    
    await page.click('[data-testid="approve-mapping-1"]');
    await expect(page.locator('[data-testid="error-toast"]')).toBeVisible();
  });
});
```

### 5. Performance Tests
**File to create**: `backend/tests/performance/test_state_operations.py`

```python
"""
Performance tests for state operations
"""
import pytest
import time
from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore

class TestStatePerformance:
    """Ensure state operations meet performance requirements"""
    
    @pytest.mark.asyncio
    async def test_state_save_performance(self, db_session, large_state):
        """State save should complete in <50ms"""
        store = PostgresFlowStateStore(db_session, test_context)
        
        start = time.time()
        await store.save_state("test-flow", large_state, "field_mapping")
        duration = (time.time() - start) * 1000
        
        assert duration < 50, f"State save took {duration}ms"
    
    @pytest.mark.asyncio
    async def test_concurrent_state_updates(self, db_session):
        """Test optimistic locking prevents conflicts"""
        # Create multiple concurrent updates
        # Verify only one succeeds
        # Verify others get ConcurrentModificationError
```

### 6. Test Automation Setup
**File to create**: `.github/workflows/phase1-tests.yml`

```yaml
name: Phase 1 Test Suite

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main, develop]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
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
          pip install pytest-cov
      
      - name: Run unit tests with coverage
        run: |
          cd backend
          pytest tests/unit --cov=app --cov-report=xml
      
      - name: Run integration tests
        run: |
          cd backend
          pytest tests/integration
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
  
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run unit tests
        run: |
          cd frontend
          npm run test -- --coverage
      
      - name: Run type checking
        run: |
          cd frontend
          npm run type-check
  
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Start Docker Compose
        run: docker-compose up -d
      
      - name: Wait for services
        run: |
          timeout 60 bash -c 'until curl -f http://localhost:3000; do sleep 2; done'
      
      - name: Run E2E tests
        run: |
          cd frontend
          npm run test:e2e
      
      - name: Upload test artifacts
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-screenshots
          path: frontend/test-results/
```

## Success Criteria
- [ ] Backend test coverage ≥80%
- [ ] Frontend test coverage ≥80%
- [ ] All critical paths have E2E tests
- [ ] Performance tests passing
- [ ] CI/CD pipeline running all tests
- [ ] Test execution time <5 minutes
- [ ] Zero flaky tests

## Test Categories to Cover

### Unit Tests
- Session to flow migration
- API v3 endpoints
- State management operations
- Field mapping logic
- React hooks and components

### Integration Tests
- API endpoint integration
- Database operations
- Multi-tenant context validation
- State persistence
- Authentication flows

### E2E Tests
- Complete discovery flow
- Field mapping workflow
- Error scenarios
- Multi-user scenarios
- Performance under load

## Commands to Run
```bash
# Backend coverage report
docker exec -it migration_backend coverage run -m pytest
docker exec -it migration_backend coverage report
docker exec -it migration_backend coverage html

# Frontend coverage
docker exec -it migration_frontend npm run test -- --coverage

# E2E tests
docker exec -it migration_frontend npm run test:e2e

# Performance tests
docker exec -it migration_backend pytest tests/performance -v
```

## Definition of Done
- [ ] 80% test coverage achieved (both frontend and backend)
- [ ] All test files created and passing
- [ ] CI/CD pipeline configured and running
- [ ] Test documentation written
- [ ] No flaky tests
- [ ] Performance benchmarks met
- [ ] PR created with title: "test: [Phase1-E1] Comprehensive test coverage"

## Testing Best Practices
1. **Test Isolation**: Each test should be independent
2. **Clear Names**: Test names should describe what they test
3. **Arrange-Act-Assert**: Follow AAA pattern
4. **Mock External Services**: Don't call real APIs in tests
5. **Test Edge Cases**: Include error scenarios
6. **Performance Aware**: Tests should run quickly

## Coordination Notes
- Work with all agents to understand their changes
- Prioritize tests for critical paths
- Add tests as agents complete features
- Update tests if APIs change
- Share test fixtures and utilities

## Notes
- Focus on critical paths first
- Tests should be maintainable
- Avoid over-mocking
- Test behavior, not implementation
- Keep tests fast and reliable