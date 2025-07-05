# Comprehensive Test Suite: Discovery → Assessment Flows

This test suite provides comprehensive validation of the complete user journey from CMDB file upload through discovery processing to assessment completion and 6R treatment recommendations.

## Overview

The test suite includes:

1. **Complete User Journey E2E Tests** - Full workflow simulation
2. **Real Agent Processing Tests** - Actual CrewAI agent execution
3. **Cross-Flow Data Persistence Tests** - Data flow validation
4. **Performance and Load Tests** - System performance validation
5. **Multi-Tenant Isolation Tests** - Data security validation

## Quick Start

### Prerequisites

1. **Development Environment Running**:
   ```bash
   docker-compose up -d
   ```

2. **Services Health Check**:
   - Backend: http://localhost:8000/health
   - Frontend: http://localhost:8081

3. **Required Tools**:
   - Python 3.8+
   - Node.js 16+
   - Playwright
   - pytest

### Run Complete Test Suite

```bash
# Run all comprehensive tests
./scripts/run_comprehensive_tests.sh

# Or run specific test categories
npm run test:complete
```

### Individual Test Categories

```bash
# Backend real agent processing tests
npm run test:backend:agents

# Cross-flow data persistence tests  
npm run test:backend:persistence

# Complete user journey E2E test
npm run test:e2e:journey

# All E2E tests
npm run test:e2e:all
```

## Test Categories

### 1. Complete User Journey E2E Tests

**File**: `tests/e2e/complete-user-journey.spec.ts`

**What it tests**:
- User authentication and login
- CMDB file upload with realistic enterprise data
- Discovery flow processing with real CrewAI agents
- Asset inventory population and navigation
- Application selection for assessment
- Assessment flow execution with real agent analysis
- 6R treatment recommendation generation
- Data persistence validation across flows
- Multi-tenant isolation with parallel sessions

**Expected Duration**: 10-15 minutes

**Success Criteria**:
- ✅ User can login and upload CMDB file
- ✅ Discovery flow processes real data with CrewAI agents
- ✅ Asset inventory populated with accurate field mappings
- ✅ User can select application and initiate assessment
- ✅ Assessment flow executes with real agent analysis
- ✅ 6R treatment recommendation generated with rationale
- ✅ Data persistence works correctly across flow transitions

### 2. Real Agent Processing Tests

**File**: `tests/backend/integration/test_real_agent_processing.py`

**What it tests**:
- UnifiedDiscoveryFlow execution with real CrewAI agents
- Field mapping crew processing with actual AI analysis
- Data cleansing crew execution with real data transformation
- Asset inventory crew creation with proper asset relationships
- Assessment flow integration with real agent recommendations
- Master flow orchestration system coordination
- Agent error handling and recovery mechanisms
- Performance characteristics under realistic loads

**Expected Duration**: 5-10 minutes

**Key Validations**:
- Real CrewAI agents execute (not mocked responses)
- Assets are actually created and persisted
- Agent processing produces meaningful results
- Error handling works gracefully
- Performance meets acceptable thresholds

### 3. Cross-Flow Data Persistence Tests

**File**: `tests/backend/integration/test_cross_flow_persistence.py`

**What it tests**:
- Data flow integrity between Discovery and Assessment flows
- Flow state consistency across different services
- Multi-tenant isolation across all flow types
- State recovery mechanisms after system failures
- Data integrity preservation during flow transitions
- Cross-flow query performance optimization

**Expected Duration**: 3-5 minutes

**Key Validations**:
- Discovery flow data correctly transfers to Assessment flow
- Flow state remains consistent across service boundaries
- Multi-tenant boundaries are never crossed
- Failed flows can be recovered without data loss
- Flow transitions preserve all critical metadata

### 4. Performance and Load Tests

**What it tests**:
- System performance with realistic data volumes (100+ assets)
- Concurrent user session handling
- Agent processing time optimization
- Database query performance across flows
- Memory usage and resource optimization
- Large file upload and processing capabilities

**Expected Duration**: 15-30 minutes

**Performance Targets**:
- Discovery flow completion: < 3 minutes for 50 assets
- Assessment flow completion: < 5 minutes per application
- API response time: < 2 seconds
- Concurrent user support: 10+ simultaneous users

## Test Data

### Realistic CMDB Data

**File**: `tests/fixtures/enterprise-cmdb-data.csv`

Contains enterprise-grade test data representing actual customer scenarios:
- 20 diverse assets (servers, applications, databases, networks)
- Realistic dependencies and relationships
- Proper metadata and technical details
- Multiple environments and criticality levels

### Assessment Test Applications

**File**: `tests/fixtures/assessment-test-applications.json`

Standardized test applications with known characteristics:
- **Legacy COBOL System**: Expected 6R = Replace
- **Modern Java Microservice**: Expected 6R = Refactor  
- **Simple Static Website**: Expected 6R = Rehost
- **Enterprise ERP**: Expected 6R = Retain
- **Analytics Platform**: Expected 6R = Replatform
- **Desktop Application**: Expected 6R = Repurchase

## Configuration

### Test Environment Setup

- **Base URL**: `http://localhost:8081`
- **API URL**: `http://localhost:8000`
- **Database**: Local PostgreSQL with test data
- **Authentication**: Real user accounts with proper permissions

### Test User Accounts

- **Platform Admin**: `chocka@gmail.com` / `Password123!`
- **Client Admin**: Demo user with client-specific permissions
- **Standard User**: Limited permissions for RBAC testing

### Multi-Tenant Test Clients

- **Complete Test Client**: `bafd5b46-aaaf-4c95-8142-573699d93171`
- **Marathon Petroleum**: `73dee5f1-6a01-43e3-b1b8-dbe6c66f2990`

## Debugging and Troubleshooting

### Common Issues

1. **Services Not Running**:
   ```bash
   docker-compose up -d
   # Wait for services to be healthy
   curl http://localhost:8000/health
   curl http://localhost:8081
   ```

2. **Test Database Issues**:
   ```bash
   # Reset database with seed data
   docker exec migration_backend python -m app.core.database_initialization
   ```

3. **Authentication Failures**:
   ```bash
   # Verify platform admin exists
   docker exec migration_backend python scripts/setup_platform_admin.py
   ```

4. **CrewAI Agent Errors**:
   - Check DEEPINFRA_API_KEY is configured
   - Verify internet connectivity for AI model access
   - Check agent configuration in backend logs

### Test Debugging

1. **Enable Verbose Logging**:
   ```bash
   # Backend tests with detailed logs
   cd tests/backend/integration && python -m pytest test_real_agent_processing.py -v -s

   # E2E tests with debugging
   npx playwright test tests/e2e/complete-user-journey.spec.ts --debug
   ```

2. **Screenshot and Video Capture**:
   - E2E tests automatically capture screenshots on failure
   - Video recordings available in `test-results/`
   - Full page screenshots for debugging

3. **Database Inspection**:
   ```bash
   # Access test database
   docker exec -it migration_db psql -U postgres -d migration_db
   
   # Check specific tables
   SELECT * FROM discovery_flows WHERE status = 'running';
   SELECT * FROM assets WHERE created_at > NOW() - INTERVAL '1 hour';
   ```

## Test Results and Reports

### Automated Reporting

- **HTML Report**: `test-results/index.html` (Playwright)
- **JSON Results**: `test-results/results.json`
- **JUnit XML**: `test-results/results.xml`
- **Coverage Report**: `tests/coverage/html/index.html`

### Key Metrics Tracked

- **Test Execution Time**: Individual and total test duration
- **Success Rate**: Pass/fail ratio across test categories
- **Performance Benchmarks**: Response times and throughput
- **Coverage**: Code coverage across backend services

## Continuous Integration

### CI/CD Integration

Add to your CI pipeline:

```yaml
# Example GitHub Actions
- name: Run Comprehensive Tests
  run: |
    docker-compose up -d
    npm install
    npx playwright install
    ./scripts/run_comprehensive_tests.sh
```

### Test Scheduling

- **Daily**: Complete test suite execution
- **Per PR**: Smoke tests and critical path validation
- **Weekly**: Performance regression testing
- **Monthly**: Full load testing with realistic data volumes

## Maintenance

### Regular Updates

1. **Test Data Refresh**: Update enterprise CMDB data quarterly
2. **Performance Baselines**: Review and update performance thresholds
3. **Browser Updates**: Keep Playwright browsers current
4. **Dependency Updates**: Regular package updates for security

### Extending Tests

1. **New Flow Types**: Add tests for Plan, Execute, Modernize flows
2. **Additional Scenarios**: Edge cases and error conditions
3. **Integration Points**: Third-party service integrations
4. **Mobile Testing**: Responsive design validation

## Support

For issues with the test suite:

1. Check the [troubleshooting guide](#debugging-and-troubleshooting)
2. Review test logs in `test-results/`
3. Verify service health and configuration
4. Check the comprehensive test plan documentation

---

**Last Updated**: July 2025  
**Test Suite Version**: 1.0  
**Platform Version**: Phase 5 (Flow-Based Architecture)