# Enhanced Asset Inventory Test Suite

This comprehensive test suite validates the enhanced Asset Inventory functionality with intelligent agentic classification, device type support, and 6R migration readiness assessment. All tests use Docker containers to ensure consistent testing environments and prevent interference with localhost daemons.

## 🏗️ Test Architecture

### Test Organization
```
tests/
├── backend/                 # Python backend tests
│   ├── test_asset_classification.py    # Asset type classification tests
│   └── test_api_integration.py         # API integration tests
├── frontend/                # JavaScript frontend tests
│   ├── AssetInventory.test.js          # React component tests
│   ├── setup.js                        # Test environment setup
│   └── vitest.config.js                # Vitest configuration
├── docker/                  # Docker container validation
│   └── test_docker_containers.py       # Container integration tests
├── coverage/                # Test coverage reports
├── results/                 # Test result artifacts
├── pytest.ini              # Pytest configuration
├── run_tests_docker.py      # Docker test runner
└── README.md               # This file
```

### Key Testing Principles

#### 🚀 Docker-First Testing
- **No Localhost Daemons**: All tests use Docker containers exclusively
- **Isolated Environments**: Each test run starts with clean containers
- **Consistent State**: Containers are rebuilt and reset between test suites
- **Real Integration**: Tests validate actual Docker deployment scenarios

#### 🤖 Agentic Workflow Preservation
- **No Hard-Coded Heuristics**: Tests ensure agentic intelligence is not overridden
- **Extensible Classifications**: Support for learned asset types from CrewAI
- **Intelligent Analysis**: Validate that agentic analysis takes precedence
- **Learning Integration**: Test feedback loops and pattern recognition

#### 🎯 Enhanced Asset Classification
- **Device Type Support**: Network, Storage, Security, Infrastructure, Virtualization
- **6R Readiness Assessment**: Migration readiness evaluation
- **Migration Complexity**: Intelligent complexity scoring
- **Dynamic Headers**: AI-generated table headers based on data

## 🧪 Test Categories

### Backend Tests (`tests/backend/`)

#### Asset Classification Tests
- **Device Type Detection**: Network devices, storage arrays, security appliances
- **Server vs Application**: Intelligent distinction based on infrastructure specs
- **Database Recognition**: Pattern-based database identification
- **Virtualization Platforms**: VMware, Hyper-V, Kubernetes detection
- **Classification Precedence**: Proper ordering (Security → Network → Storage)

#### 6R Readiness Assessment
- **Application Readiness**: Business owner, environment, criticality validation
- **Server Readiness**: Infrastructure data requirements
- **Database Readiness**: Version and configuration requirements
- **Device Exclusions**: Proper "Not Applicable" marking for devices
- **Complex Analysis**: Virtualization platform special handling

#### API Integration Tests
- **CMDB Analysis**: Enhanced analysis with device classification
- **Asset Processing**: Intelligent asset transformation and enrichment
- **Error Handling**: Graceful degradation and error responses
- **Performance**: Large dataset processing validation
- **End-to-End Workflows**: Complete analysis → process → inventory flow

### Frontend Tests (`tests/frontend/`)

#### Component Rendering
- **Enhanced Summary**: Device breakdown statistics
- **Asset Table**: Dynamic headers and type-specific icons
- **Filter Controls**: Device type filter options
- **6R Indicators**: Readiness badges and complexity indicators

#### User Interactions
- **Filtering**: Asset type and department filtering
- **Refresh**: Manual data refresh functionality
- **Export**: CSV export with enhanced data
- **Responsive Design**: Mobile and desktop layouts

#### Agentic Integration
- **Custom Asset Types**: Support for agentic classifications
- **Extensible UI**: Graceful handling of unknown asset types
- **Dynamic Content**: AI-generated headers and descriptions

### Docker Tests (`tests/docker/`)

#### Container Lifecycle
- **Startup Validation**: Container health and readiness checks
- **Service Communication**: Frontend-backend connectivity
- **Resource Usage**: Memory and CPU consumption monitoring
- **Cleanup**: Proper container and volume cleanup

#### Integration Testing
- **API Functionality**: Full API testing within containers
- **Data Persistence**: Database persistence across restarts
- **Environment Configuration**: Environment variable validation
- **Network Configuration**: CORS and port configuration

## 🚀 Running Tests

### Quick Start (Docker-Based)
```bash
# Run all tests with Docker containers
python tests/run_tests_docker.py

# Run specific test suites
python tests/run_tests_docker.py --suites backend frontend
python tests/run_tests_docker.py --suites docker

# Keep containers running for debugging
python tests/run_tests_docker.py --keep-running
```

### Individual Test Suites

#### Backend Tests Only
```bash
# With Docker containers running
python tests/run_tests_docker.py --suites backend

# Direct pytest (requires containers to be running)
export DOCKER_API_BASE=http://localhost:8000
python -m pytest tests/backend/ -v
```

#### Frontend Tests Only
```bash
# With Docker containers running
python tests/run_tests_docker.py --suites frontend

# Direct npm test (requires containers to be running)
npm test -- --run
```

#### Docker Integration Tests
```bash
# Quick tests (no slow integration)
python -m pytest tests/docker/ -v -m "not slow"

# Full integration tests (slow)
python -m pytest tests/docker/ -v -m "slow"
```

### Test Markers

Use pytest markers to run specific test categories. See `docs/testing/QA_GUIDE.md` and `docs/testing/SUITE_MATRIX.md` for the full taxonomy and suite matrix.

```bash
# Device classification tests only
python -m pytest -m device_classification

# 6R readiness tests only
python -m pytest -m sixr_readiness

# Agentic workflow tests only
python -m pytest -m agentic

# Unit tests only (fast)
python -m pytest -m unit

# Integration tests only (requires services)
python -m pytest -m integration
```

## 📊 Test Coverage

### Coverage Requirements
- **Backend**: Minimum 80% line coverage for enhanced functionality
- **Frontend**: Minimum 60% coverage for React components
- **Critical Paths**: 95% coverage for agentic workflows and device classification

### Coverage Reports
```bash
# Generate coverage reports
python tests/run_tests_docker.py --suites all

# View HTML coverage reports
open tests/coverage/html/index.html          # Backend coverage
open tests/coverage/frontend/index.html      # Frontend coverage
```

## 🐛 Debugging Tests

### Container Logs
```bash
# View container logs during test failures
docker-compose -p migrate-ui-orchestrator-test logs backend
docker-compose -p migrate-ui-orchestrator-test logs frontend

# Follow logs in real-time
docker-compose -p migrate-ui-orchestrator-test logs -f
```

### Interactive Debugging
```bash
# Keep containers running after tests
python tests/run_tests_docker.py --keep-running

# Connect to running backend container
docker exec -it $(docker ps -qf "name=backend") /bin/bash

# Run specific tests with verbose output
python -m pytest tests/backend/test_asset_classification.py::TestAssetTypeClassification::test_database_detection_patterns -v -s
```

### Test Data Inspection
```bash
# Access test database
docker exec -it $(docker ps -qf "name=postgres") psql -U postgres -d test_db

# View API responses
curl http://localhost:8000/api/v1/discovery/assets | jq .
```

## 🔧 Configuration

### Environment Variables
```bash
# Docker endpoints (automatically set by test runner)
DOCKER_API_BASE=http://localhost:8000
DOCKER_FRONTEND_BASE=http://localhost:8081

# Test mode flags
TESTING=true
NODE_ENV=test

# Coverage and reporting
PYTHONPATH=backend:tests/backend
```

### Test Configuration Files
- `tests/pytest.ini`: Pytest configuration and markers
- `tests/frontend/vitest.config.js`: Frontend test configuration
- `tests/frontend/setup.js`: React testing environment setup
- `docker-compose.yml`: Container definitions for testing

## 🚨 Test Requirements

### Prerequisites
- **Docker & Docker Compose**: For container-based testing
- **Python 3.8+**: For backend tests
- **Node.js 16+**: For frontend tests
- **pytest**: Backend test framework
- **Vitest**: Frontend test framework

### Required Python Packages
```bash
pip install pytest pytest-asyncio pytest-cov pytest-timeout httpx docker pyyaml
```

### Required Node Packages
```bash
npm install --save-dev vitest jsdom @testing-library/react @testing-library/jest-dom @vitejs/plugin-react
```

## 🎯 Test Quality Standards

### Agentic Workflow Validation
- ✅ **Preserve Intelligence**: Never override CrewAI analysis with hard-coded rules
- ✅ **Support Learning**: Test extensible asset types and field mappings
- ✅ **Validate Feedback**: Ensure user feedback improves agentic accuracy
- ✅ **Graceful Fallback**: Rule-based classification only when agentic unavailable

### Device Classification Standards
- ✅ **Comprehensive Coverage**: All device types properly classified
- ✅ **Precedence Rules**: Security → Network → Storage → Infrastructure
- ✅ **6R Exclusions**: Devices marked "Not Applicable" for 6R analysis
- ✅ **Migration Complexity**: Appropriate complexity scoring for devices

### Test Reliability
- ✅ **Docker Isolation**: All tests use containers, no localhost dependencies
- ✅ **Deterministic**: Tests produce consistent results across environments
- ✅ **Fast Feedback**: Unit tests complete within seconds
- ✅ **Clear Failures**: Descriptive error messages for debugging

## 📈 Continuous Integration

### CI/CD Integration
```yaml
# Example GitHub Actions workflow
- name: Run Enhanced Asset Inventory Tests
  run: |
    python tests/run_tests_docker.py --suites all

- name: Upload Coverage Reports
  uses: codecov/codecov-action@v1
  with:
    file: tests/coverage/coverage.xml
```

### Quality Gates
- All tests must pass before deployment
- Coverage thresholds must be maintained
- Agentic workflow tests must validate intelligence preservation
- Docker integration tests must verify container functionality

---

## 🤝 Contributing to Tests

### Adding New Tests
1. **Follow Naming Conventions**: `test_*.py` for Python, `*.test.js` for JavaScript
2. **Use Appropriate Markers**: Mark tests with `@pytest.mark.device_classification`, etc.
3. **Preserve Agentic Workflows**: Ensure new tests don't break intelligent analysis
4. **Docker-First**: All new tests should use Docker containers

### Test Best Practices
- **Descriptive Names**: Test names should clearly describe what is being tested
- **Isolated Tests**: Each test should be independent and not rely on others
- **Mock External Services**: Use mocks for external APIs while preserving agentic intelligence
- **Clear Assertions**: Use descriptive assertion messages

For questions or contributions, please refer to the main project documentation.

## Port Configuration

This application uses **fixed ports** to avoid conflicts with other development projects:

- **Backend API**: `http://localhost:8000` (FastAPI)
- **Frontend**: `http://localhost:8081` (Vite React app)
- **PostgreSQL**: `localhost:5433` (mapped from container port 5432)

### Why Port 8081 for Frontend?

Port 8081 is specifically chosen to avoid conflicts with:
- Port 3000: Common default for Next.js applications
- Port 5173: Vite's default development port
- Port 8080: Common for various development servers

### CORS Configuration

The backend accepts requests from multiple frontend ports:
- `http://localhost:8081` - This application's frontend
- `http://localhost:3000` - For other Next.js apps you may run
- `http://localhost:5173` - For Vite default port compatibility

All **tests** specifically use port 8081 since that's this application's designated frontend port.

## Health Check Configuration

The Docker backend health check runs every **2 minutes** (120 seconds) to balance:
- System resource usage (not too frequent)
- Reasonable failure detection (not too slow)

You can adjust this in `docker-compose.yml` if needed:
```yaml
healthcheck:
  interval: 120s  # Adjust as needed
```
