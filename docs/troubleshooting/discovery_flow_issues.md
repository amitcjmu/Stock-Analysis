# Discovery Flow Troubleshooting Guide

## 📋 **Overview**

This guide provides comprehensive troubleshooting information for common Discovery Flow issues, covering crew execution failures, memory problems, performance issues, and agent collaboration problems.

## 🔍 **Diagnostic Tools**

### **Health Check Endpoints**
```bash
# Check overall flow health
curl -H "Authorization: Bearer $JWT_TOKEN" \
     -H "X-Client-Account-ID: $CLIENT_ID" \
     GET http://localhost:8000/api/v1/discovery/flow/health

# Check specific crew status
curl -H "Authorization: Bearer $JWT_TOKEN" \
     -H "X-Client-Account-ID: $CLIENT_ID" \
     GET http://localhost:8000/api/v1/discovery/flow/crews/field-mapping/status/$SESSION_ID

# Check agent performance
curl -H "Authorization: Bearer $JWT_TOKEN" \
     -H "X-Client-Account-ID: $CLIENT_ID" \
     GET http://localhost:8000/api/v1/discovery/flow/agents/performance/$SESSION_ID
```

### **Memory System Diagnostics**
```bash
# Check shared memory status
curl -H "Authorization: Bearer $JWT_TOKEN" \
     -H "X-Client-Account-ID: $CLIENT_ID" \
     GET http://localhost:8000/api/v1/discovery/flow/memory/status/$SESSION_ID

# Memory analytics
curl -H "Authorization: Bearer $JWT_TOKEN" \
     -H "X-Client-Account-ID: $CLIENT_ID" \
     GET http://localhost:8000/api/v1/discovery/flow/memory/analytics/$SESSION_ID
```

### **Container Debugging**
```bash
# Check container status
docker-compose ps

# View backend logs
docker-compose logs -f backend

# Access backend container for debugging
docker exec -it migration_backend bash

# Check agent memory usage inside container
docker exec -it migration_backend python -c "
import psutil
print(f'Memory usage: {psutil.virtual_memory().percent}%')
print(f'Available memory: {psutil.virtual_memory().available / 1024**3:.2f} GB')
"
```

---

## 🚨 **Common Issues and Solutions**

### **1. Flow Initialization Failures**

#### **Issue**: Flow fails to initialize
**Error Message**: `Flow initialization failed: insufficient memory`
**Symptoms**:
- Flow doesn't start
- Memory allocation errors
- Container resource limits exceeded

**Solutions**:
```bash
# Increase container memory limits
# Edit docker-compose.yml:
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

# Restart containers with new limits
docker-compose down
docker-compose up -d --build
```

**Prevention**:
- Monitor memory usage regularly
- Set appropriate container resource limits
- Use memory-efficient data processing

#### **Issue**: Knowledge base loading failures
**Error Message**: `Knowledge base initialization failed: file not found`
**Symptoms**:
- Missing knowledge base files
- Crew initialization errors
- Reduced agent accuracy

**Solutions**:
```bash
# Check knowledge base files
ls -la backend/app/knowledge_bases/

# Verify file permissions
chmod 644 backend/app/knowledge_bases/*.json
chmod 644 backend/app/knowledge_bases/*.yaml

# Recreate missing knowledge base files
python backend/scripts/setup_knowledge_bases.py
```

### **2. Crew Execution Failures**

#### **Issue**: Field Mapping Crew execution timeout
**Error Message**: `Field mapping crew execution timeout after 1800 seconds`
**Symptoms**:
- Crew execution hangs
- No progress updates
- High CPU usage

**Solutions**:
```python
# Adjust timeout in configuration
# backend/app/core/config.py
class DiscoveryFlowSettings(BaseSettings):
    crew_timeout_seconds: int = 3600  # Increase to 60 minutes
    agent_response_timeout: int = 300  # 5 minutes per agent response
```

**Debug Steps**:
```bash
# Check crew execution status
docker exec -it migration_backend python -c "
from backend.app.services.crewai_service import CrewAIService
service = CrewAIService()
status = service.get_crew_status('field_mapping')
print(f'Crew status: {status}')
"

# Monitor agent activities
curl -H "Authorization: Bearer $JWT_TOKEN" \
     GET http://localhost:8000/api/v1/discovery/flow/crews/field-mapping/details/$SESSION_ID
```

#### **Issue**: Agent collaboration failures
**Error Message**: `Agent collaboration error: memory access denied`
**Symptoms**:
- Agents not sharing insights
- Poor cross-crew coordination
- Reduced accuracy

**Solutions**:
```python
# Verify shared memory configuration
# Check backend/app/services/crewai_flows/discovery_flow_redesigned.py

def _setup_shared_memory(self):
    try:
        self.shared_memory = LongTermMemory(
            storage_type="vector",
            embedder_config={
                "provider": "openai",
                "model": "text-embedding-3-small"
            }
        )
        logger.info("Shared memory initialized successfully")
    except Exception as e:
        logger.error(f"Shared memory initialization failed: {e}")
        # Fallback to basic memory
        self.shared_memory = BasicMemory()
```

**Debug Memory Access**:
```bash
# Test memory operations
docker exec -it migration_backend python -c "
from backend.app.services.crewai_service import CrewAIService
service = CrewAIService()
memory = service.shared_memory

# Test memory write
memory.add('test_key', {'test': 'data'})
print('Memory write successful')

# Test memory read
result = memory.get('test_key')
print(f'Memory read result: {result}')
"
```

### **3. Performance Issues**

#### **Issue**: Slow crew execution
**Error Message**: `Crew execution exceeding performance thresholds`
**Symptoms**:
- Long execution times (>30 minutes)
- High resource usage
- Poor throughput

**Performance Analysis**:
```bash
# Check crew performance metrics
curl -H "Authorization: Bearer $JWT_TOKEN" \
     GET http://localhost:8000/api/v1/discovery/flow/crews/performance/$SESSION_ID

# Monitor resource usage
docker stats migration_backend

# Profile agent execution
docker exec -it migration_backend python -c "
import cProfile
import pstats
from backend.app.services.crewai_flows.crews.field_mapping_crew import FieldMappingCrew

# Profile crew execution
profiler = cProfile.Profile()
profiler.enable()

# Execute crew (replace with actual execution)
crew = FieldMappingCrew()
# crew.execute()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
"
```

**Optimization Solutions**:
```python
# Enable parallel execution
# backend/app/services/crewai_flows/discovery_flow_redesigned.py

@listen(initialize_discovery_flow)
def execute_field_mapping_crew(self, previous_result):
    # Enable parallel agent execution
    crew_config = {
        "parallel_execution": True,
        "max_concurrent_agents": 3,
        "agent_timeout": 300
    }
    
    crew = FieldMappingCrew(self.crewai_service, **crew_config)
    return crew.execute(previous_result)
```

#### **Issue**: Memory system performance degradation
**Error Message**: `Memory retrieval timeout: search took >10 seconds`
**Symptoms**:
- Slow memory operations
- Agent waiting for memory access
- Increasing memory usage

**Memory Optimization**:
```python
# Memory cleanup and optimization
class MemoryOptimizer:
    def optimize_memory_system(self, shared_memory):
        # Clean old insights
        cutoff_date = datetime.now() - timedelta(days=7)
        shared_memory.cleanup_old_insights(cutoff_date)
        
        # Compress large insights
        shared_memory.compress_insights(size_threshold_mb=10)
        
        # Defragment vector storage
        shared_memory.defragment_storage()
        
        # Update indexes
        shared_memory.rebuild_indexes()
```

**Manual Memory Cleanup**:
```bash
# Clean memory system
docker exec -it migration_backend python -c "
from backend.app.services.crewai_service import CrewAIService
from backend.app.utils.memory_optimizer import MemoryOptimizer

service = CrewAIService()
optimizer = MemoryOptimizer()
optimizer.optimize_memory_system(service.shared_memory)
print('Memory optimization complete')
"
```

### **4. Data Quality Issues**

#### **Issue**: Low field mapping confidence
**Error Message**: `Field mapping confidence below threshold: 0.65 < 0.8`
**Symptoms**:
- Many unmapped fields
- Low confidence scores
- Poor data quality

**Data Quality Analysis**:
```bash
# Analyze input data quality
docker exec -it migration_backend python -c "
import pandas as pd
from backend.app.services.data_quality_analyzer import DataQualityAnalyzer

# Load and analyze data
analyzer = DataQualityAnalyzer()
data = pd.read_csv('uploaded_data.csv')
quality_report = analyzer.analyze_data_quality(data)
print(quality_report)
"
```

**Improvement Strategies**:
```python
# Improve field mapping with data preprocessing
class DataPreprocessor:
    def preprocess_for_field_mapping(self, data):
        # Clean field names
        data.columns = data.columns.str.strip().str.lower()
        
        # Standardize common field patterns
        field_mapping = {
            'host_name': 'hostname',
            'server_name': 'hostname',
            'ip_addr': 'ip_address',
            'app_name': 'application'
        }
        data.rename(columns=field_mapping, inplace=True)
        
        # Add field descriptions
        field_descriptions = self._generate_field_descriptions(data)
        
        return data, field_descriptions
```

#### **Issue**: Asset classification errors
**Error Message**: `Asset classification accuracy below threshold: 0.82 < 0.9`
**Symptoms**:
- Incorrect asset types
- Misclassified servers/applications
- Poor inventory quality

**Classification Improvement**:
```python
# Enhance classification with additional context
class AssetClassificationEnhancer:
    def enhance_classification_context(self, assets):
        for asset in assets:
            # Add naming pattern analysis
            asset['naming_pattern'] = self._analyze_naming_pattern(asset['name'])
            
            # Add context clues
            asset['context_clues'] = self._extract_context_clues(asset)
            
            # Cross-reference with knowledge base
            asset['kb_matches'] = self._get_kb_matches(asset)
        
        return assets
```

### **5. Integration Issues**

#### **Issue**: API authentication failures
**Error Message**: `Authentication failed: invalid JWT token`
**Symptoms**:
- API calls rejected
- 401 Unauthorized errors
- Flow initialization blocked

**Authentication Debug**:
```bash
# Verify JWT token
docker exec -it migration_backend python -c "
import jwt
from backend.app.core.auth import verify_token

token = 'your_jwt_token_here'
try:
    payload = verify_token(token)
    print(f'Token valid: {payload}')
except Exception as e:
    print(f'Token validation failed: {e}')
"

# Check token expiration
docker exec -it migration_backend python -c "
import jwt
from datetime import datetime

token = 'your_jwt_token_here'
try:
    payload = jwt.decode(token, options={'verify_signature': False})
    exp = payload.get('exp')
    if exp:
        exp_time = datetime.fromtimestamp(exp)
        print(f'Token expires: {exp_time}')
        if exp_time < datetime.now():
            print('Token has expired')
    else:
        print('No expiration in token')
except Exception as e:
    print(f'Token decode failed: {e}')
"
```

#### **Issue**: Database connection failures
**Error Message**: `Database connection failed: connection timeout`
**Symptoms**:
- Cannot save flow state
- Data persistence errors
- Session management issues

**Database Debug**:
```bash
# Test database connection
docker exec -it migration_backend python -c "
from backend.app.core.database import get_db
from sqlalchemy import text

try:
    db = next(get_db())
    result = db.execute(text('SELECT 1'))
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
"

# Check database tables
docker exec -it migration_db psql -U user -d migration_db -c "\dt"
```

---

## 🔧 **Advanced Debugging Techniques**

### **Agent Debugging**

#### **Enable Verbose Agent Logging**
```python
# Add to crew configuration
agent = Agent(
    role="Debug Agent",
    verbose=True,
    step_callback=self._debug_step_callback,
    # ... other configuration
)

def _debug_step_callback(self, step):
    logger.debug(f"Agent step: {step}")
    # Log to file for analysis
    with open("agent_debug.log", "a") as f:
        f.write(f"{datetime.now()}: {step}\n")
```

#### **Memory State Inspection**
```python
# Debug memory state
class MemoryDebugger:
    def inspect_memory_state(self, shared_memory, session_id):
        # Get all insights for session
        session_insights = shared_memory.search(
            query=f"session_id:{session_id}",
            top_k=100
        )
        
        # Analyze insight types
        insight_types = {}
        for insight in session_insights:
            insight_type = insight.get('type', 'unknown')
            insight_types[insight_type] = insight_types.get(insight_type, 0) + 1
        
        return {
            "total_insights": len(session_insights),
            "insight_types": insight_types,
            "memory_size": shared_memory.size_mb(),
            "last_update": max([i.get('timestamp', '') for i in session_insights])
        }
```

### **Performance Profiling**

#### **Crew Execution Profiling**
```python
import time
import tracemalloc
from functools import wraps

def profile_crew_execution(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Start memory tracing
        tracemalloc.start()
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            # Get memory usage
            current, peak = tracemalloc.get_traced_memory()
            execution_time = time.time() - start_time
            
            # Log performance metrics
            logger.info(f"Crew execution completed:")
            logger.info(f"  Execution time: {execution_time:.2f}s")
            logger.info(f"  Current memory: {current / 1024**2:.2f} MB")
            logger.info(f"  Peak memory: {peak / 1024**2:.2f} MB")
            
            return result
            
        finally:
            tracemalloc.stop()
    
    return wrapper

# Apply to crew execution methods
@profile_crew_execution
def execute_field_mapping_crew(self, previous_result):
    # Crew execution logic
    pass
```

### **Log Analysis Tools**

#### **Automated Log Analysis**
```bash
# Script: analyze_logs.sh
#!/bin/bash

# Extract error patterns
echo "=== Error Analysis ==="
docker-compose logs backend | grep -i error | tail -20

# Extract performance metrics
echo "=== Performance Metrics ==="
docker-compose logs backend | grep "execution_time" | tail -10

# Extract memory usage patterns
echo "=== Memory Usage ==="
docker-compose logs backend | grep "memory" | tail -10

# Extract crew status changes
echo "=== Crew Status Changes ==="
docker-compose logs backend | grep "crew.*status" | tail -15
```

#### **Real-Time Monitoring**
```python
# Real-time monitoring script
import asyncio
import websockets
import json

async def monitor_discovery_flow(session_id):
    uri = f"ws://localhost:8000/ws/discovery-flow/{session_id}"
    
    async with websockets.connect(uri) as websocket:
        print(f"Monitoring session: {session_id}")
        
        async for message in websocket:
            event = json.loads(message)
            
            # Log important events
            if event.get('event_type') == 'error_occurrence':
                print(f"ERROR: {event['data']}")
            elif event.get('event_type') == 'performance_alert':
                print(f"PERFORMANCE ALERT: {event['data']}")
            elif event.get('event_type') == 'crew_status_update':
                print(f"CREW UPDATE: {event['data']}")

# Run monitoring
asyncio.run(monitor_discovery_flow("your_session_id"))
```

---

## 📊 **Monitoring and Alerts**

### **Setting Up Monitoring**

#### **Prometheus Metrics**
```python
# backend/app/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
crew_execution_counter = Counter('crew_executions_total', 'Total crew executions', ['crew_name', 'status'])
crew_execution_time = Histogram('crew_execution_duration_seconds', 'Crew execution time', ['crew_name'])
memory_usage_gauge = Gauge('memory_usage_mb', 'Memory usage in MB')
agent_collaboration_counter = Counter('agent_collaborations_total', 'Agent collaboration events', ['from_agent', 'to_agent'])

# Use in crews
def execute_crew_with_metrics(crew_name, execution_func):
    start_time = time.time()
    
    try:
        result = execution_func()
        crew_execution_counter.labels(crew_name=crew_name, status='success').inc()
        return result
    except Exception as e:
        crew_execution_counter.labels(crew_name=crew_name, status='failure').inc()
        raise
    finally:
        execution_time = time.time() - start_time
        crew_execution_time.labels(crew_name=crew_name).observe(execution_time)
```

#### **Alert Configuration**
```yaml
# observability/alerts.yaml
groups:
  - name: discovery_flow_alerts
    rules:
      - alert: CrewExecutionTimeout
        expr: crew_execution_duration_seconds > 1800
        for: 0m
        labels:
          severity: warning
        annotations:
          summary: "Crew execution timeout"
          description: "Crew {{ $labels.crew_name }} has been running for over 30 minutes"
      
      - alert: HighMemoryUsage
        expr: memory_usage_mb > 2000
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}MB, exceeding 2GB threshold"
      
      - alert: CrewExecutionFailures
        expr: rate(crew_executions_total{status="failure"}[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High crew execution failure rate"
          description: "Crew execution failure rate is {{ $value }} per second"
```

---

## 🆘 **Emergency Procedures**

### **System Recovery**

#### **Complete System Reset**
```bash
# Emergency reset procedure
echo "Starting emergency system reset..."

# Stop all containers
docker-compose down

# Clean up volumes (WARNING: This removes all data)
docker volume prune -f

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d

# Verify system health
sleep 30
curl -f http://localhost:8000/health || echo "System not ready yet"
```

#### **Memory System Recovery**
```python
# Emergency memory cleanup
class EmergencyMemoryRecovery:
    def emergency_memory_cleanup(self, shared_memory):
        try:
            # Archive all insights older than 1 hour
            cutoff = datetime.now() - timedelta(hours=1)
            shared_memory.archive_insights_older_than(cutoff)
            
            # Clear low-relevance insights
            shared_memory.clear_insights_below_relevance(threshold=0.1)
            
            # Force garbage collection
            shared_memory.force_gc()
            
            logger.info("Emergency memory cleanup completed")
            
        except Exception as e:
            logger.error(f"Emergency memory cleanup failed: {e}")
            # Fallback: restart memory system
            self._restart_memory_system()
```

### **Data Recovery**

#### **Session Recovery**
```python
# Recover session from database backup
class SessionRecovery:
    def recover_session(self, session_id):
        # Get session data from database
        session_data = self.db.get_session_data(session_id)
        
        # Restore flow state
        restored_state = self._restore_flow_state(session_data)
        
        # Resume from last successful crew
        last_crew = restored_state.get_last_completed_crew()
        self._resume_from_crew(last_crew)
        
        return restored_state
```

---

This comprehensive troubleshooting guide covers the most common issues and provides systematic approaches to diagnosing and resolving Discovery Flow problems. 