# Production Deployment Runbook for Master Flow Orchestrator
**Phase 6: Day 9-10 - Production Migration and Cleanup (MFO-102)**

## Overview
This runbook provides comprehensive procedures for deploying the Master Flow Orchestrator to production, including pre-deployment validation, deployment steps, post-deployment verification, and rollback procedures.

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Production Environment Setup](#production-environment-setup)
3. [Database Backup Procedures](#database-backup-procedures)
4. [Deployment Procedures](#deployment-procedures)
5. [Post-Deployment Validation](#post-deployment-validation)
6. [Monitoring and Alerting](#monitoring-and-alerting)
7. [Rollback Procedures](#rollback-procedures)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Contact Information](#contact-information)

---

## Pre-Deployment Checklist

### ✅ Staging Validation Complete
- [ ] Staging deployment successful (MFO-093)
- [ ] Comprehensive test suite passed (MFO-095)
- [ ] Load testing passed (MFO-096)
- [ ] Security vulnerability scan passed (MFO-097)
- [ ] Data integrity validation passed (MFO-098)
- [ ] Rollback procedures tested (MFO-099)

### ✅ Production Environment Ready
- [ ] Production infrastructure provisioned
- [ ] DNS records configured
- [ ] SSL certificates installed and validated
- [ ] Load balancer configured
- [ ] Database cluster ready
- [ ] Redis cluster ready
- [ ] Monitoring systems configured
- [ ] Alerting rules configured

### ✅ Code and Configuration
- [ ] Code reviewed and approved
- [ ] All tests passing in CI/CD
- [ ] Environment variables configured
- [ ] Secrets properly managed
- [ ] Docker images built and pushed to registry
- [ ] Deployment scripts validated

### ✅ Team Readiness
- [ ] Deployment team assembled
- [ ] On-call engineers notified
- [ ] Stakeholders informed of deployment window
- [ ] Communication channels established
- [ ] Rollback decision makers identified

---

## Production Environment Setup

### Infrastructure Requirements
```bash
# Minimum Production Requirements
CPU: 8 cores per service
Memory: 16GB per service
Storage: 100GB SSD for applications, 500GB for database
Network: 1Gbps bandwidth
Load Balancer: High availability with SSL termination
Database: PostgreSQL 16 with pgvector extension
Cache: Redis 7 cluster
```

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@db-cluster/migration_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_CONNECTIONS=100

# Application
SECRET_KEY=<production-secret-key>
JWT_SECRET=<production-jwt-secret>
DEEPINFRA_API_KEY=<production-api-key>
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Master Flow Orchestrator
ENABLE_MASTER_FLOW_ORCHESTRATOR=true
MASTER_FLOW_ORCHESTRATOR_LOGGING=true
ENABLE_FLOW_PERFORMANCE_TRACKING=true
ENABLE_FLOW_AUDIT_LOGGING=true

# URLs
FRONTEND_URL=https://app.yourdomain.com
BACKEND_URL=https://api.yourdomain.com
ALLOWED_ORIGINS=https://app.yourdomain.com

# Redis
REDIS_URL=redis://redis-cluster:6379
REDIS_PASSWORD=<production-redis-password>

# Monitoring
SENTRY_DSN=<production-sentry-dsn>
ENABLE_METRICS=true
ENABLE_TRACING=true

# Performance
WORKERS=4
MAX_CONNECTIONS=20
POOL_SIZE=10
```

---

## Database Backup Procedures

### Pre-Deployment Backup
```bash
#!/bin/bash
# Create comprehensive production backup

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/production"
DB_NAME="migration_db"

echo "🗄️ Creating production database backup..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Full database dump
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
  --verbose --clean --create --if-exists \
  --format=custom \
  --file="$BACKUP_DIR/migration_db_backup_$BACKUP_DATE.dump"

# Schema-only backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
  --schema-only --verbose \
  --file="$BACKUP_DIR/migration_db_schema_$BACKUP_DATE.sql"

# Data-only backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
  --data-only --verbose \
  --file="$BACKUP_DIR/migration_db_data_$BACKUP_DATE.sql"

# Compress backups
gzip "$BACKUP_DIR/migration_db_schema_$BACKUP_DATE.sql"
gzip "$BACKUP_DIR/migration_db_data_$BACKUP_DATE.sql"

# Verify backup integrity
pg_restore --list "$BACKUP_DIR/migration_db_backup_$BACKUP_DATE.dump" > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Backup created successfully: migration_db_backup_$BACKUP_DATE.dump"
    echo "📊 Backup size: $(du -h $BACKUP_DIR/migration_db_backup_$BACKUP_DATE.dump)"
else
    echo "❌ Backup verification failed!"
    exit 1
fi

# Store backup metadata
cat > "$BACKUP_DIR/backup_metadata_$BACKUP_DATE.json" << EOF
{
  "backup_date": "$BACKUP_DATE",
  "database_name": "$DB_NAME",
  "backup_type": "pre_deployment",
  "master_flow_orchestrator_version": "1.0.0",
  "files": [
    "migration_db_backup_$BACKUP_DATE.dump",
    "migration_db_schema_$BACKUP_DATE.sql.gz",
    "migration_db_data_$BACKUP_DATE.sql.gz"
  ]
}
EOF

echo "✅ Pre-deployment backup completed"
```

### Backup Verification Script
```bash
#!/bin/bash
# Verify backup integrity and restore capability

BACKUP_FILE="$1"
TEST_DB="migration_db_test_restore"

echo "🔍 Verifying backup integrity..."

# Create test database
createdb -h $DB_HOST -U $DB_USER $TEST_DB

# Restore backup to test database
pg_restore -h $DB_HOST -U $DB_USER -d $TEST_DB \
  --verbose --clean --if-exists \
  "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Backup restore test successful"

    # Verify data integrity
    RECORD_COUNT=$(psql -h $DB_HOST -U $DB_USER -d $TEST_DB -t -c "
        SELECT COUNT(*) FROM crewai_flow_state_extensions;
    ")

    echo "📊 Restored records: $RECORD_COUNT"

    # Clean up test database
    dropdb -h $DB_HOST -U $DB_USER $TEST_DB

    echo "✅ Backup verification completed successfully"
else
    echo "❌ Backup restore test failed!"
    dropdb -h $DB_HOST -U $DB_USER $TEST_DB 2>/dev/null
    exit 1
fi
```

---

## Deployment Procedures

### Blue-Green Deployment Strategy

#### Phase 1: Pre-Deployment
```bash
#!/bin/bash
# Pre-deployment validation

echo "🚀 Starting Master Flow Orchestrator production deployment..."

# 1. Verify staging environment
echo "📋 Verifying staging environment..."
./scripts/deployment/staging_deployment.py --verify-only

# 2. Create production backup
echo "💾 Creating production backup..."
./scripts/deployment/create_production_backup.sh

# 3. Verify backup integrity
echo "🔍 Verifying backup integrity..."
./scripts/deployment/verify_backup.sh "/backups/production/migration_db_backup_$(date +%Y%m%d)*.dump"

echo "✅ Pre-deployment phase completed"
```

#### Phase 2: Green Environment Deployment
```bash
#!/bin/bash
# Deploy to green environment (new version)

echo "🟢 Deploying to green environment..."

# 1. Deploy backend services
docker-compose -f docker-compose.prod.yml --profile green up -d backend_green

# 2. Wait for health checks
echo "⏳ Waiting for backend health checks..."
for i in {1..30}; do
    if curl -f http://backend_green:8000/health > /dev/null 2>&1; then
        echo "✅ Backend green environment healthy"
        break
    fi
    echo "⏳ Waiting for backend... ($i/30)"
    sleep 10
done

# 3. Run database migrations
echo "🔄 Running database migrations..."
docker exec backend_green alembic upgrade head

# 4. Deploy frontend
docker-compose -f docker-compose.prod.yml --profile green up -d frontend_green

# 5. Verify green environment
echo "🔍 Verifying green environment..."
./scripts/deployment/verify_green_environment.sh

echo "✅ Green environment deployment completed"
```

#### Phase 3: Traffic Switch
```bash
#!/bin/bash
# Switch traffic from blue to green

echo "🔄 Switching traffic to green environment..."

# 1. Update load balancer configuration
./scripts/deployment/update_load_balancer.sh --target=green

# 2. Gradual traffic shift (10% increments)
for PERCENTAGE in 10 25 50 75 100; do
    echo "📊 Shifting ${PERCENTAGE}% traffic to green environment..."
    ./scripts/deployment/update_traffic_split.sh --green=${PERCENTAGE}

    # Monitor for 2 minutes
    echo "⏳ Monitoring for 2 minutes..."
    sleep 120

    # Check error rates
    ERROR_RATE=$(./scripts/monitoring/check_error_rate.sh)
    if (( $(echo "$ERROR_RATE > 0.05" | bc -l) )); then
        echo "❌ Error rate too high ($ERROR_RATE), rolling back..."
        ./scripts/deployment/rollback_traffic.sh
        exit 1
    fi

    echo "✅ ${PERCENTAGE}% traffic shift successful"
done

echo "✅ Traffic switch completed"
```

#### Phase 4: Blue Environment Cleanup
```bash
#!/bin/bash
# Clean up blue environment after successful deployment

echo "🔵 Cleaning up blue environment..."

# Wait for 30 minutes to ensure stability
echo "⏳ Waiting 30 minutes for stability verification..."
sleep 1800

# Check system health
HEALTH_CHECK=$(./scripts/monitoring/comprehensive_health_check.sh)
if [ "$HEALTH_CHECK" != "healthy" ]; then
    echo "❌ System not healthy, keeping blue environment as backup"
    exit 1
fi

# Stop blue environment services
docker-compose -f docker-compose.prod.yml --profile blue down

# Update monitoring to point to green environment
./scripts/monitoring/update_monitoring_targets.sh --target=green

echo "✅ Blue environment cleanup completed"
```

### Single-Step Deployment (Alternative)
```bash
#!/bin/bash
# Single-step deployment for smaller environments

echo "🚀 Starting single-step production deployment..."

# 1. Enable maintenance mode
./scripts/deployment/enable_maintenance_mode.sh

# 2. Stop services
docker-compose -f docker-compose.prod.yml down

# 3. Pull latest images
docker-compose -f docker-compose.prod.yml pull

# 4. Start services
docker-compose -f docker-compose.prod.yml up -d

# 5. Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 6. Verify deployment
./scripts/deployment/verify_production_deployment.sh

# 7. Disable maintenance mode
./scripts/deployment/disable_maintenance_mode.sh

echo "✅ Single-step deployment completed"
```

---

## Post-Deployment Validation

### Automated Validation Script
```bash
#!/bin/bash
# Comprehensive post-deployment validation

echo "🔍 Starting post-deployment validation..."

VALIDATION_RESULTS="/tmp/validation_results_$(date +%Y%m%d_%H%M%S).json"

# 1. Health check validation
echo "📋 Running health checks..."
HEALTH_STATUS=$(curl -s https://api.yourdomain.com/health | jq -r '.status')
if [ "$HEALTH_STATUS" != "healthy" ]; then
    echo "❌ Health check failed: $HEALTH_STATUS"
    exit 1
fi

# 2. Master Flow Orchestrator validation
echo "🔍 Validating Master Flow Orchestrator..."
python3 scripts/deployment/validate_master_flow_orchestrator.py \
    --production-url="https://api.yourdomain.com" \
    --output="$VALIDATION_RESULTS"

# 3. Database connectivity
echo "🗄️ Validating database connectivity..."
python3 scripts/deployment/validate_database_connectivity.py

# 4. API endpoint validation
echo "🌐 Validating API endpoints..."
./scripts/deployment/validate_api_endpoints.sh

# 5. Frontend accessibility
echo "🖥️ Validating frontend accessibility..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://app.yourdomain.com)
if [ "$FRONTEND_STATUS" != "200" ]; then
    echo "❌ Frontend not accessible: HTTP $FRONTEND_STATUS"
    exit 1
fi

# 6. Performance validation
echo "📊 Running performance validation..."
./scripts/deployment/validate_performance.sh

# 7. Security validation
echo "🔒 Running security validation..."
./scripts/deployment/validate_security.sh

echo "✅ Post-deployment validation completed successfully"
echo "📊 Validation results saved to: $VALIDATION_RESULTS"
```

### Key Metrics to Monitor
```bash
# Application Metrics
- Response time percentiles (p50, p95, p99)
- Error rates (< 0.1%)
- Throughput (requests per second)
- Active flows count
- Database connection pool usage

# Infrastructure Metrics
- CPU utilization (< 80%)
- Memory utilization (< 85%)
- Disk usage (< 80%)
- Network I/O
- Database query performance

# Business Metrics
- Flow creation rate
- Flow completion rate
- User activity
- Asset processing rate
- System availability (> 99.9%)
```

---

## Monitoring and Alerting

### Critical Alerts
```yaml
# Prometheus Alert Rules
groups:
  - name: master_flow_orchestrator_critical
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} requests/second"

      - alert: DatabaseConnectionFailure
        expr: up{job="postgresql"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failure"
          description: "PostgreSQL database is not responding"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time"
          description: "95th percentile response time is {{ $value }} seconds"

      - alert: FlowProcessingFailure
        expr: rate(flow_operations_total{status="failed"}[10m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High flow processing failure rate"
          description: "Flow failure rate is {{ $value }} failures/second"
```

### Monitoring Dashboard
```bash
# Grafana Dashboard Components
1. System Overview
   - Total requests per minute
   - Error rate percentage
   - Response time percentiles
   - Active connections

2. Master Flow Orchestrator
   - Active flows by type
   - Flow completion rates
   - Phase execution times
   - Agent performance metrics

3. Database Performance
   - Query execution time
   - Connection pool usage
   - Slow queries
   - Database size growth

4. Infrastructure
   - CPU and memory usage
   - Disk I/O and space
   - Network throughput
   - Container health
```

---

## Rollback Procedures

### Automatic Rollback Triggers
```bash
# Conditions that trigger automatic rollback
- Error rate > 5% for 5 minutes
- Response time p95 > 5 seconds for 10 minutes
- Database connection failures > 50% for 2 minutes
- Critical application errors > 10 per minute
- Health check failures for 3 consecutive checks
```

### Manual Rollback Procedure
```bash
#!/bin/bash
# Manual rollback to previous version

echo "🔄 Starting rollback procedure..."

ROLLBACK_VERSION="$1"
if [ -z "$ROLLBACK_VERSION" ]; then
    echo "❌ Rollback version not specified"
    echo "Usage: $0 <rollback_version>"
    exit 1
fi

# 1. Enable maintenance mode
echo "🔧 Enabling maintenance mode..."
./scripts/deployment/enable_maintenance_mode.sh

# 2. Switch traffic to blue environment (if available)
echo "🔄 Switching traffic to stable environment..."
./scripts/deployment/update_load_balancer.sh --target=blue

# 3. Restore database if needed
read -p "Do you need to restore database? (y/N): " RESTORE_DB
if [ "$RESTORE_DB" = "y" ] || [ "$RESTORE_DB" = "Y" ]; then
    echo "🗄️ Restoring database..."
    ./scripts/deployment/restore_database.sh "$ROLLBACK_VERSION"
fi

# 4. Deploy previous version
echo "📦 Deploying previous version: $ROLLBACK_VERSION"
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml pull
docker tag yourregistry/app:$ROLLBACK_VERSION yourregistry/app:latest
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify rollback
echo "🔍 Verifying rollback..."
./scripts/deployment/verify_production_deployment.sh

# 6. Disable maintenance mode
echo "✅ Disabling maintenance mode..."
./scripts/deployment/disable_maintenance_mode.sh

echo "✅ Rollback completed successfully"
```

### Database Rollback
```bash
#!/bin/bash
# Database rollback procedure

BACKUP_FILE="$1"
if [ -z "$BACKUP_FILE" ]; then
    echo "❌ Backup file not specified"
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "🗄️ Starting database rollback..."

# 1. Create current state backup
echo "💾 Creating current state backup..."
CURRENT_BACKUP="/backups/emergency/before_rollback_$(date +%Y%m%d_%H%M%S).dump"
pg_dump -h $DB_HOST -U $DB_USER -d migration_db \
  --format=custom --file="$CURRENT_BACKUP"

# 2. Stop application services
echo "⏹️ Stopping application services..."
docker-compose -f docker-compose.prod.yml stop backend frontend

# 3. Restore database
echo "🔄 Restoring database from backup..."
pg_restore -h $DB_HOST -U $DB_USER -d migration_db \
  --clean --if-exists --verbose "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Database rollback successful"
else
    echo "❌ Database rollback failed!"
    exit 1
fi

# 4. Restart services
echo "🚀 Restarting services..."
docker-compose -f docker-compose.prod.yml start backend frontend

echo "✅ Database rollback completed"
```

---

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Database Migration Failures
```bash
# Symptoms
- Alembic migration errors
- Schema inconsistencies
- Foreign key constraint failures

# Diagnosis
docker logs migration_backend_prod | grep "alembic"
psql -h $DB_HOST -U $DB_USER -d migration_db -c "\dt"

# Resolution
1. Check migration dependencies
2. Verify database state
3. Run migrations manually with --sql flag first
4. Apply fixes and retry

# Emergency Resolution
./scripts/deployment/rollback_database.sh <last_known_good_backup>
```

#### 2. High Error Rates
```bash
# Symptoms
- 5xx HTTP status codes
- Application exceptions
- Database connection errors

# Diagnosis
curl -s https://api.yourdomain.com/health | jq '.'
docker logs migration_backend_prod --tail=100
./scripts/monitoring/check_error_logs.sh

# Resolution
1. Check application logs for specific errors
2. Verify database connectivity
3. Check resource utilization
4. Scale services if needed
5. Rollback if errors persist
```

#### 3. Performance Degradation
```bash
# Symptoms
- Slow response times
- High CPU/memory usage
- Database slow queries

# Diagnosis
./scripts/monitoring/performance_analysis.sh
docker stats migration_backend_prod
psql -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# Resolution
1. Identify bottleneck (CPU, memory, I/O, database)
2. Scale horizontally if needed
3. Optimize database queries
4. Increase resource allocation
5. Consider rollback if performance is critical
```

#### 4. Master Flow Orchestrator Issues
```bash
# Symptoms
- Flows not starting
- Flow state inconsistencies
- Agent communication failures

# Diagnosis
python3 scripts/deployment/diagnose_master_flow_orchestrator.py
docker exec migration_backend_prod python -c "
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
# Check orchestrator status
"

# Resolution
1. Verify flow registry configuration
2. Check agent service availability
3. Validate flow state database records
4. Restart flow services if needed
5. Check CrewAI integration
```

### Emergency Contact Procedures
```bash
# Severity Levels and Response

Critical (System Down):
- Response Time: 15 minutes
- Contacts: On-call engineer, DevOps lead, CTO
- Actions: Immediate rollback, incident declaration

High (Major Degradation):
- Response Time: 30 minutes
- Contacts: On-call engineer, DevOps lead
- Actions: Investigate and fix, prepare rollback

Medium (Minor Issues):
- Response Time: 2 hours
- Contacts: On-call engineer
- Actions: Schedule fix, monitor closely

Low (Non-Critical):
- Response Time: Next business day
- Contacts: Development team
- Actions: Create bug report, schedule fix
```

### Log Analysis Commands
```bash
# Application Logs
docker logs migration_backend_prod --since=10m | grep ERROR
docker logs migration_frontend_prod --since=10m | grep -i error

# Database Logs
sudo tail -f /var/log/postgresql/postgresql-16-main.log

# System Logs
journalctl -u docker --since="10 minutes ago"
dmesg | tail -20

# Performance Logs
docker stats --no-stream migration_backend_prod
iostat -x 1 5
top -bn1 | head -20
```

---

## Contact Information

### Emergency Contacts
```
On-Call Engineer: +1-XXX-XXX-XXXX
DevOps Lead: devops-lead@company.com
CTO: cto@company.com
Platform Admin: admin@company.com
```

### Escalation Matrix
```
Level 1: On-Call Engineer (0-30 minutes)
Level 2: DevOps Lead (30-60 minutes)
Level 3: Engineering Director (1-2 hours)
Level 4: CTO (2+ hours or business critical)
```

### Communication Channels
```
Slack: #production-alerts
PagerDuty: Production Incidents
Email: production-alerts@company.com
Status Page: status.company.com
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] All staging validations passed
- [ ] Production backup created and verified
- [ ] Team assembled and briefed
- [ ] Communication plan activated
- [ ] Rollback procedures reviewed

### During Deployment
- [ ] Blue-green deployment initiated
- [ ] Health checks monitored
- [ ] Database migration completed
- [ ] Traffic gradually shifted
- [ ] Error rates monitored
- [ ] Performance metrics validated

### Post-Deployment
- [ ] Comprehensive validation completed
- [ ] Monitoring dashboards updated
- [ ] Alert rules activated
- [ ] Documentation updated
- [ ] Team debriefing scheduled
- [ ] Success communicated to stakeholders

---

**Document Version**: 1.0
**Last Updated**: 2025-07-05
**Next Review**: 2025-07-20
**Owner**: DevOps Team
**Approval**: Engineering Director
