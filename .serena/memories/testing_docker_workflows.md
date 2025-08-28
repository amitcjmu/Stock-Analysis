# Testing Strategies and Docker Workflows

## Docker Environment Setup

### Critical Configuration
- **Frontend**: Runs on localhost:8081 (NOT port 3000)
- **Backend**: FastAPI on localhost:8000
- **Database**: PostgreSQL on localhost:5433 (internal 5432)
- **Redis**: localhost:6379
- **Never run**: `npm run dev` locally - use Docker only

### Docker Compose Structure
```yaml
services:
  frontend:
    build: ./frontend
    ports: ["8081:3000"]
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8000

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [db, redis]
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/migration_db

  db:
    image: postgres:15
    ports: ["5433:5432"]
    volumes: ["postgres_data:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

### Essential Docker Commands
```bash
# Start all services
docker-compose up -d

# Rebuild after changes
docker-compose build backend
docker-compose up -d backend

# View logs
docker-compose logs -f backend

# Execute commands in container
docker exec -it migration_backend bash
docker exec migration_postgres psql -U postgres -d migration_db

# Clean restart
docker-compose down -v
docker-compose up -d --build
```

## Testing Strategy Hierarchy

### 1. Pre-commit Validation (First Line)
```bash
# Never bypass on first attempt
pre-commit run --all-files

# Individual checks
flake8 backend/
black backend/ --check
mypy backend/
bandit -r backend/
```

### 2. Unit Testing (Isolated)
```bash
# Run in Docker container
docker exec migration_backend pytest tests/unit/ -v

# With coverage
docker exec migration_backend pytest tests/unit/ --cov=app --cov-report=html

# Specific test file
docker exec migration_backend pytest tests/unit/test_service.py::test_function
```

### 3. Integration Testing (Service Layer)
```bash
# Test service integrations
docker exec migration_backend pytest tests/integration/ -v

# Database integration tests
docker exec migration_backend pytest tests/integration/test_repositories.py

# Redis integration tests
docker exec migration_backend pytest tests/integration/test_cache.py
```

### 4. E2E Testing (Full Stack)
```bash
# Playwright tests
npx playwright test

# Specific test file
npx playwright test tests/e2e/discovery-flow.spec.ts

# With debugging
npx playwright test --debug

# Headed mode (see browser)
npx playwright test --headed
```

## Test Patterns and Best Practices

### Fixture Organization
```python
# conftest.py
@pytest.fixture
async def db_session():
    """Provide test database session with rollback"""
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.rollback()

@pytest.fixture
async def test_client(db_session):
    """Provide test client with database"""
    app.dependency_overrides[get_session] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
def test_flow_state():
    """Provide sample flow state"""
    return DiscoveryFlowState(
        flow_id=uuid4(),
        client_account_id=uuid4(),
        engagement_id=uuid4(),
        status="in_progress"
    )
```

### Mocking External Services
```python
# Mock Azure services
@patch('app.services.azure_adapter.AzureAdapter.discover_resources')
async def test_discovery(mock_discover):
    mock_discover.return_value = {
        "virtual_machines": [],
        "storage_accounts": []
    }
    result = await discovery_service.run_discovery()
    assert result.status == "completed"

# Mock CrewAI agents
@patch('app.services.crewai_flow_service.Crew.kickoff')
async def test_crew_execution(mock_kickoff):
    mock_kickoff.return_value = Mock(output="Success")
    result = await crew_service.execute_flow()
    assert "Success" in result.output
```

### Database Testing Patterns
```python
# Test with real database transactions
async def test_repository_save(db_session):
    repo = FlowStateRepository(db_session)
    entity = DiscoveryFlowState(...)

    saved = await repo.save(entity)
    assert saved.id is not None

    # Verify in database
    result = await db_session.get(DiscoveryFlowState, saved.id)
    assert result is not None

# Test rollback on error
async def test_transaction_rollback(db_session):
    async with db_session.begin():
        # Make changes
        await repo.save(entity)
        # Force error
        raise ValueError("Test rollback")

    # Verify rollback
    result = await db_session.get(DiscoveryFlowState, entity.id)
    assert result is None
```

## Validation Workflows

### After Modularization
```bash
# 1. Check file structure
ls -la backend/app/services/module_name/

# 2. Verify imports
python -c "from app.services.module_name import OriginalClass"

# 3. Run pre-commit
pre-commit run --files backend/app/services/module_name.py

# 4. Run unit tests
docker exec migration_backend pytest tests/unit/test_module_name.py

# 5. Test in Docker
docker-compose build backend
docker-compose up -d backend
docker-compose logs backend | grep -i error

# 6. Run integration tests
docker exec migration_backend pytest tests/integration/

# 7. Run E2E tests
npx playwright test tests/e2e/
```

### Performance Testing
```python
# Load testing with locust
from locust import HttpUser, task, between

class DiscoveryUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def discover_resources(self):
        self.client.post("/api/v1/discovery/start", json={
            "client_account_id": "test-client",
            "resource_types": ["vm", "storage"]
        })

# Run: locust -f loadtest.py --host=http://localhost:8000
```

### Memory Leak Detection
```python
# Use memory_profiler
from memory_profiler import profile

@profile
def memory_intensive_operation():
    # Operation to test
    pass

# Run: python -m memory_profiler test_memory.py
```

## Common Docker Issues and Solutions

### Database Connection Issues
```bash
# Check if database is ready
docker exec migration_postgres pg_isready

# Reset database
docker exec migration_postgres psql -U postgres -c "DROP DATABASE IF EXISTS migration_db;"
docker exec migration_postgres psql -U postgres -c "CREATE DATABASE migration_db;"
docker exec migration_backend alembic upgrade head
```

### Container Not Starting
```bash
# Check logs
docker-compose logs backend

# Common fixes:
# 1. Check DATABASE_URL format
# 2. Ensure dependencies are installed
# 3. Verify Dockerfile COPY commands
# 4. Check for port conflicts
```

### Redis Connection Issues
```bash
# Test Redis connection
docker exec migration_redis redis-cli ping

# Clear Redis cache
docker exec migration_redis redis-cli FLUSHALL
```

### Volume Permission Issues
```bash
# Fix ownership
docker exec migration_backend chown -R app:app /app

# Reset volumes
docker-compose down -v
docker volume prune -f
docker-compose up -d
```

## Test Data Management

### Seed Data Creation
```python
# scripts/seed_data.py
async def create_test_data():
    async with get_session() as session:
        # Create test accounts
        accounts = [
            ClientAccount(id=uuid4(), name=f"Test Client {i}")
            for i in range(5)
        ]
        session.add_all(accounts)

        # Create test flows
        flows = [
            DiscoveryFlow(
                client_account_id=account.id,
                status="completed"
            )
            for account in accounts
        ]
        session.add_all(flows)

        await session.commit()
```

### Test Data Cleanup
```python
# Clean up after tests
@pytest.fixture(autouse=True)
async def cleanup(db_session):
    yield
    # Delete test data
    await db_session.execute(
        delete(DiscoveryFlow).where(
            DiscoveryFlow.client_account_id.like('test-%')
        )
    )
    await db_session.commit()
```

## CI/CD Testing Pipeline

### GitHub Actions Workflow
```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Docker
        run: docker-compose up -d

      - name: Run pre-commit
        run: pre-commit run --all-files

      - name: Run unit tests
        run: docker exec migration_backend pytest tests/unit/ --cov

      - name: Run integration tests
        run: docker exec migration_backend pytest tests/integration/

      - name: Run E2E tests
        run: npx playwright test

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Critical Testing Rules

1. **ALWAYS** test in Docker environment
2. **NEVER** skip pre-commit on first attempt
3. **ALWAYS** run integration tests after modularization
4. **NEVER** assume tests pass without running
5. **ALWAYS** check Docker logs for errors
6. **NEVER** use npm run dev locally
7. **ALWAYS** verify backward compatibility
8. **NEVER** merge without passing tests
