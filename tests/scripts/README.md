# Phase 3: CrewAI Flow Migration Validation Scripts

This directory contains comprehensive validation scripts for the CrewAI Flow migration from legacy handlers to native CrewAI Flow patterns.

## 🎯 **Validation Scripts Overview**

### **1. validate_crewai_flow_migration.py**
Comprehensive Python validation script that tests the entire CrewAI Flow system.

**Features:**
- Container health checks
- Service initialization validation
- Discovery workflow functionality testing
- Backward compatibility verification
- Fallback behavior validation
- Performance testing
- Error handling validation

**Usage:**
```bash
# Basic validation
python tests/scripts/validate_crewai_flow_migration.py

# Verbose output
python tests/scripts/validate_crewai_flow_migration.py --verbose

# Quick validation (skip performance tests)
python tests/scripts/validate_crewai_flow_migration.py --quick

# Save results to file
python tests/scripts/validate_crewai_flow_migration.py --output validation_results.json
```

### **2. run_docker_validation.sh**
Bash script that manages Docker containers and runs comprehensive validation.

**Features:**
- Automatic Docker container startup
- Health check monitoring
- Comprehensive validation execution
- Container cleanup
- Colored output and logging

**Usage:**
```bash
# Full validation with container management
./tests/scripts/run_docker_validation.sh

# Verbose output
./tests/scripts/run_docker_validation.sh --verbose

# Quick validation
./tests/scripts/run_docker_validation.sh --quick

# Keep containers running after validation
./tests/scripts/run_docker_validation.sh --no-cleanup

# Health check only (for existing containers)
./tests/scripts/run_docker_validation.sh --health-only
```

### **3. run_backend_tests.py**
Python script for running backend-specific tests.

**Features:**
- Import validation
- Service health checks
- Database connectivity tests
- Migration-specific tests
- Docker and local execution support

**Usage:**
```bash
# Run all backend tests
python tests/scripts/run_backend_tests.py

# Verbose output
python tests/scripts/run_backend_tests.py --verbose

# Run without Docker
python tests/scripts/run_backend_tests.py --no-docker

# Run specific test
python tests/scripts/run_backend_tests.py --test imports
```

## 🚀 **Quick Start Guide**

### **Option 1: Full Docker Validation (Recommended)**
```bash
# Start containers and run full validation
./tests/scripts/run_docker_validation.sh --verbose
```

### **Option 2: Manual Container Management**
```bash
# Start containers manually
docker-compose up -d --build

# Wait for containers to be ready (check logs)
docker-compose logs -f backend

# Run validation against running containers
python tests/scripts/validate_crewai_flow_migration.py --verbose

# Cleanup
docker-compose down
```

### **Option 3: Backend Tests Only**
```bash
# Run backend tests in Docker
python tests/scripts/run_backend_tests.py --verbose

# Or run locally (requires local setup)
python tests/scripts/run_backend_tests.py --no-docker
```

## 📊 **Test Categories**

### **Core Functionality Tests**
- ✅ Container health and connectivity
- ✅ Service initialization and health checks
- ✅ Discovery workflow initiation
- ✅ Workflow state management
- ✅ Active flows monitoring

### **Migration Validation Tests**
- ✅ Legacy API compatibility
- ✅ New CrewAI Flow patterns
- ✅ State format conversion
- ✅ Fallback behavior
- ✅ Error handling

### **Performance Tests**
- ✅ Basic performance with moderate datasets
- ✅ Concurrent workflow handling
- ✅ Large dataset processing
- ✅ Response time validation

### **Integration Tests**
- ✅ Docker container integration
- ✅ Database connectivity
- ✅ API endpoint functionality
- ✅ Service dependencies

## 🎪 **Expected Results**

### **Successful Migration Indicators**
- All containers start and become healthy
- CrewAI Flow service responds correctly
- Discovery workflows can be initiated
- Legacy API contracts are preserved
- Fallback execution works when CrewAI Flow unavailable
- Performance meets acceptable thresholds

### **Success Metrics**
- **100% test pass rate** for core functionality
- **< 15 seconds** for 50-record dataset processing
- **Graceful degradation** when dependencies unavailable
- **Backward compatibility** with all existing APIs

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Container Startup Issues**
```bash
# Check Docker status
docker info

# Check container logs
docker-compose logs backend
docker-compose logs db

# Rebuild containers
docker-compose down --volumes
docker-compose up -d --build
```

#### **Service Health Issues**
```bash
# Check backend health directly
curl http://localhost:8000/health

# Check CrewAI Flow service health
curl http://localhost:8000/api/v1/discovery/flow/health

# Check container status
docker-compose ps
```

#### **Test Failures**
```bash
# Run with verbose output for debugging
python tests/scripts/validate_crewai_flow_migration.py --verbose

# Check specific test categories
python tests/scripts/run_backend_tests.py --test health
python tests/scripts/run_backend_tests.py --test imports
```

#### **Import Errors**
```bash
# Verify Python path in container
docker exec -it migration_backend python -c "import sys; print(sys.path)"

# Test imports manually
docker exec -it migration_backend python -c "from app.services.crewai_flow_service import CrewAIFlowService"
```

## 📋 **Validation Checklist**

### **Pre-Validation Setup**
- [ ] Docker is running and accessible
- [ ] Project dependencies are installed
- [ ] No conflicting services on ports 8000, 3000, 5432
- [ ] Sufficient disk space for containers

### **Core Validation Steps**
- [ ] Container health checks pass
- [ ] Service initialization successful
- [ ] Discovery workflow initiation works
- [ ] State retrieval and management functional
- [ ] Error handling graceful

### **Migration-Specific Validation**
- [ ] Legacy API compatibility maintained
- [ ] New CrewAI Flow patterns working
- [ ] Fallback execution functional
- [ ] Performance acceptable
- [ ] No regression in existing functionality

### **Post-Validation Cleanup**
- [ ] Containers stopped (if cleanup enabled)
- [ ] Validation results saved
- [ ] Any issues documented
- [ ] Success metrics recorded

## 🎯 **Success Criteria**

The CrewAI Flow migration is considered successful when:

1. **All validation tests pass** (100% success rate)
2. **Performance meets requirements** (< 15s for moderate datasets)
3. **Backward compatibility preserved** (all legacy APIs work)
4. **Fallback behavior functional** (works without CrewAI Flow)
5. **Error handling robust** (graceful degradation)
6. **Docker integration seamless** (containers start and run correctly)

## 📈 **Continuous Validation**

These scripts can be integrated into CI/CD pipelines for continuous validation:

```bash
# CI/CD pipeline example
./tests/scripts/run_docker_validation.sh --quick --output ci_results.json
```

The validation results can be used to:
- Monitor migration health over time
- Detect regressions in functionality
- Validate new features don't break existing workflows
- Ensure performance remains acceptable

---

## 🌟 **Phase 3 Completion**

When all validation scripts pass consistently, **Phase 3: Validation and Cleanup** is complete, and the CrewAI Flow migration from legacy handlers to native patterns is successfully validated and ready for production use.
