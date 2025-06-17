# Discovery Flow Production Deployment Guide

## 📋 **Overview**

This guide provides comprehensive instructions for deploying the Discovery Flow to production environments, covering infrastructure requirements, security considerations, monitoring setup, and operational procedures.

## 🏗️ **Infrastructure Requirements**

### **Minimum System Requirements**

#### **Backend Services**
```yaml
# Production specifications
Backend Service:
  CPU: 4 cores minimum, 8 cores recommended
  Memory: 8GB minimum, 16GB recommended
  Storage: 100GB SSD minimum
  Network: 1Gbps minimum

Database:
  CPU: 2 cores minimum, 4 cores recommended  
  Memory: 4GB minimum, 8GB recommended
  Storage: 200GB SSD with backup capability
  IOPS: 3000 minimum for optimal performance

Frontend Service:
  CPU: 2 cores minimum
  Memory: 2GB minimum, 4GB recommended
  Storage: 20GB SSD
  CDN: Recommended for global distribution
```

#### **Scalability Considerations**
```yaml
# Enterprise scale requirements
High Volume (10,000+ assets):
  Backend CPU: 16 cores
  Backend Memory: 32GB
  Database: Dedicated cluster
  Load Balancer: Required
  Caching: Redis cluster

Very High Volume (50,000+ assets):
  Backend: Multi-instance cluster
  Database: Sharded PostgreSQL cluster
  Message Queue: RabbitMQ/Apache Kafka
  Storage: Distributed file system
  Monitoring: Full observability stack
```

### **Cloud Provider Specifications**

#### **AWS Deployment**
```yaml
# AWS infrastructure template
EC2 Instances:
  Backend: c5.2xlarge (8 vCPU, 16GB RAM)
  Database: r5.xlarge (4 vCPU, 32GB RAM)
  Frontend: t3.medium (2 vCPU, 4GB RAM)

Storage:
  Backend: 100GB gp3 SSD
  Database: 200GB io2 SSD (3000 IOPS)
  Backup: S3 with lifecycle policies

Networking:
  VPC: Dedicated VPC with private subnets
  Load Balancer: Application Load Balancer
  Security Groups: Restrictive access rules
  DNS: Route 53 for custom domains
```

#### **Azure Deployment**
```yaml
# Azure infrastructure template  
Virtual Machines:
  Backend: Standard_D4s_v3 (4 vCPU, 16GB RAM)
  Database: Standard_E4s_v3 (4 vCPU, 32GB RAM)
  Frontend: Standard_B2s (2 vCPU, 4GB RAM)

Storage:
  Backend: Premium SSD 128GB
  Database: Premium SSD 256GB
  Backup: Azure Blob Storage

Networking:
  Virtual Network: Dedicated VNet
  Load Balancer: Azure Load Balancer
  NSG: Network Security Groups
  DNS: Azure DNS
```

#### **Railway + Vercel Deployment (Current)**
```yaml
# Current deployment architecture
Railway (Backend):
  Service: Pro plan minimum
  Memory: 8GB limit
  CPU: Shared compute
  Storage: 100GB volume
  Networking: Custom domains

Vercel (Frontend):
  Plan: Pro plan for production
  Build Time: 45 minutes
  Functions: 30 second timeout
  Bandwidth: Generous limits
  CDN: Global edge network

Database:
  Provider: Railway PostgreSQL
  Plan: Pro plan minimum
  Storage: 100GB with automatic backups
  Connections: 100 concurrent maximum
```

---

## 🔧 **Deployment Process**

### **Environment Setup**

#### **Environment Variables Configuration**
```bash
# Production environment variables template
# Copy to .env.production and customize

# Database Configuration
DATABASE_URL=postgresql://user:password@host:5432/migration_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_CONNECTIONS=100

# CrewAI Configuration  
DEEPINFRA_API_KEY=your_deepinfra_api_key
OPENAI_API_KEY=your_openai_api_key_fallback
CREWAI_ENABLED=true
CREWAI_MAX_CONCURRENT_CREWS=10
CREWAI_CREW_TIMEOUT=3600

# Memory Configuration
MEMORY_STORAGE_TYPE=vector
MEMORY_MAX_SIZE_MB=2000
MEMORY_CLEANUP_INTERVAL=7200

# Security Configuration
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key
JWT_EXPIRATION_HOURS=24
ALLOWED_ORIGINS=https://your-domain.com

# Performance Configuration
MAX_CONCURRENT_SESSIONS=50
SESSION_TIMEOUT_MINUTES=180
BACKGROUND_TASK_WORKERS=5

# Monitoring Configuration
ENABLE_METRICS=true
PROMETHEUS_PORT=9090
LOG_LEVEL=INFO
SENTRY_DSN=your_sentry_dsn

# Email Configuration (for alerts)
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password
```

#### **Frontend Environment Configuration**
```bash
# Frontend environment variables (.env.production)
NEXT_PUBLIC_API_URL=https://your-backend-api.com/api/v1
NEXT_PUBLIC_WS_URL=wss://your-backend-api.com/ws
NEXT_PUBLIC_ENVIRONMENT=production
NEXT_PUBLIC_ANALYTICS_ID=your_analytics_id
NEXT_PUBLIC_SENTRY_DSN=your_frontend_sentry_dsn
```

### **Database Setup**

#### **Production Database Configuration**
```sql
-- Production database setup script
-- File: deployment/production_db_setup.sql

-- Create production database
CREATE DATABASE migration_db_prod WITH
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Create database user with limited privileges
CREATE USER migration_app WITH PASSWORD 'secure_password_here';

-- Grant necessary permissions
GRANT CONNECT ON DATABASE migration_db_prod TO migration_app;
GRANT USAGE ON SCHEMA public TO migration_app;
GRANT CREATE ON SCHEMA public TO migration_app;

-- Grant table permissions (after migrations)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO migration_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO migration_app;

-- Set default permissions for new tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO migration_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO migration_app;
```

#### **Database Optimization for Production**
```sql
-- Production PostgreSQL optimization
-- File: deployment/postgresql_optimization.sql

-- Connection settings
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '6GB';
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';

-- Performance settings
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET seq_page_cost = 1.0;
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Logging for production monitoring
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log slow queries
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_lock_waits = on;

-- Reload configuration
SELECT pg_reload_conf();
```

### **Backend Deployment**

#### **Railway Deployment**
```bash
# Railway deployment script
# File: deployment/deploy_railway.sh

#!/bin/bash

echo "Starting Railway backend deployment..."

# Install Railway CLI if not installed
if ! command -v railway &> /dev/null; then
    npm install -g @railway/cli
fi

# Login to Railway (interactive)
railway login

# Set up Railway project
railway link your-project-id

# Set environment variables
railway variables set DATABASE_URL="$DATABASE_URL"
railway variables set DEEPINFRA_API_KEY="$DEEPINFRA_API_KEY"
railway variables set SECRET_KEY="$SECRET_KEY"
railway variables set ALLOWED_ORIGINS="$ALLOWED_ORIGINS"

# Add all production environment variables
while IFS='=' read -r key value; do
    if [[ ! $key =~ ^# ]] && [[ $key ]]; then
        railway variables set "$key" "$value"
    fi
done < .env.production

# Deploy backend
railway up

echo "Railway deployment completed"
```

#### **Docker Production Configuration**
```dockerfile
# Production Dockerfile
# File: backend/Dockerfile.production

FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create app user for security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appgroup . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### **Frontend Deployment**

#### **Vercel Deployment**
```bash
# Vercel deployment script
# File: deployment/deploy_vercel.sh

#!/bin/bash

echo "Starting Vercel frontend deployment..."

# Install Vercel CLI if not installed
if ! command -v vercel &> /dev/null; then
    npm install -g vercel
fi

# Build frontend
npm run build

# Set production environment variables
vercel env add NEXT_PUBLIC_API_URL production
vercel env add NEXT_PUBLIC_WS_URL production
vercel env add NEXT_PUBLIC_ENVIRONMENT production

# Deploy to production
vercel --prod

echo "Vercel deployment completed"
```

#### **Production Build Configuration**
```javascript
// next.config.js - Production configuration
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Production optimizations
  output: 'standalone',
  compress: true,
  poweredByHeader: false,
  
  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Content-Security-Policy',
            value: "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://your-backend-api.com wss://your-backend-api.com;",
          },
        ],
      },
    ];
  },
  
  // Environment-specific configuration
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
  
  // Performance optimizations
  experimental: {
    optimizeCss: true,
    optimizeServerReact: true,
  },
  
  // Bundle analyzer (disable in production)
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
      };
    }
    return config;
  },
};

module.exports = nextConfig;
```

---

## 🔒 **Security Configuration**

### **SSL/TLS Setup**

#### **SSL Certificate Configuration**
```nginx
# Nginx SSL configuration
# File: deployment/nginx/ssl.conf

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL certificates (use Let's Encrypt or commercial certificates)
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Proxy to backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### **Authentication and Authorization**

#### **Production JWT Configuration**
```python
# backend/app/core/security.py - Production settings

from datetime import timedelta
import secrets

class ProductionSecurityConfig:
    # Generate strong secret keys
    SECRET_KEY = secrets.token_urlsafe(32)
    JWT_SECRET_KEY = secrets.token_urlsafe(32)
    
    # JWT settings
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_DELTA = timedelta(hours=24)
    JWT_REFRESH_EXPIRATION_DELTA = timedelta(days=7)
    
    # Password requirements
    PASSWORD_MIN_LENGTH = 12
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_SPECIAL_CHARS = True
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE = 60
    RATE_LIMIT_PER_HOUR = 1000
    RATE_LIMIT_PER_DAY = 10000
    
    # Session security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"
```

### **Network Security**

#### **Firewall Rules**
```bash
# Production firewall configuration
# File: deployment/security/firewall_rules.sh

#!/bin/bash

# Reset firewall rules
ufw --force reset

# Default policies
ufw default deny incoming
ufw default allow outgoing

# SSH access (limit to specific IPs)
ufw allow from 203.0.113.0/24 to any port 22

# HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Database (only from backend servers)
ufw allow from 10.0.1.0/24 to any port 5432

# Monitoring
ufw allow from 10.0.2.0/24 to any port 9090

# Enable firewall
ufw --force enable

echo "Firewall rules configured"
```

---

## 📊 **Monitoring and Observability**

### **Prometheus Configuration**

#### **Prometheus Setup**
```yaml
# deployment/monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "discovery_flow_alerts.yml"

scrape_configs:
  - job_name: 'discovery-flow-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
    
  - job_name: 'postgresql'
    static_configs:
      - targets: ['postgres_exporter:9187']
    
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node_exporter:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

#### **Grafana Dashboards**
```json
# deployment/monitoring/grafana/discovery_flow_dashboard.json
{
  "dashboard": {
    "title": "Discovery Flow Production Dashboard",
    "panels": [
      {
        "title": "Crew Execution Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(crew_executions_total[5m])",
            "legendFormat": "{{crew_name}}"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph", 
        "targets": [
          {
            "expr": "memory_usage_mb",
            "legendFormat": "Memory Usage (MB)"
          }
        ]
      },
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

### **Logging Configuration**

#### **Structured Logging Setup**
```python
# backend/app/core/logging.py - Production logging

import logging
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger

class ProductionLoggingConfig:
    def setup_logging(self):
        # Create custom formatter
        log_formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler for errors
        error_handler = logging.FileHandler('/var/log/discovery_flow/error.log')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(log_formatter)
        root_logger.addHandler(error_handler)
        
        # Audit log handler
        audit_handler = logging.FileHandler('/var/log/discovery_flow/audit.log')
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(log_formatter)
        
        # Create audit logger
        audit_logger = logging.getLogger('audit')
        audit_logger.addHandler(audit_handler)
        audit_logger.propagate = False
        
        return root_logger, audit_logger
```

#### **Log Aggregation with ELK Stack**
```yaml
# deployment/logging/logstash.conf
input {
  file {
    path => "/var/log/discovery_flow/*.log"
    start_position => "beginning"
    codec => "json"
  }
}

filter {
  if [levelname] == "ERROR" {
    mutate {
      add_tag => ["error"]
    }
  }
  
  if [name] == "audit" {
    mutate {
      add_tag => ["audit"]
    }
  }
  
  date {
    match => [ "asctime", "yyyy-MM-dd'T'HH:mm:ss" ]
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "discovery-flow-logs-%{+YYYY.MM.dd}"
  }
}
```

---

## 🚀 **Performance Optimization**

### **Database Performance**

#### **Connection Pooling**
```python
# backend/app/core/database.py - Production database config

from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine

class ProductionDatabaseConfig:
    def create_engine(self, database_url: str):
        return create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=20,                    # Base number of connections
            max_overflow=30,                 # Additional connections under load
            pool_pre_ping=True,              # Validate connections
            pool_recycle=3600,               # Recycle connections hourly
            echo=False,                      # Disable SQL logging in production
            connect_args={
                "connect_timeout": 10,
                "command_timeout": 30,
                "application_name": "discovery_flow"
            }
        )
```

#### **Database Indexing Strategy**
```sql
-- Production database indexes
-- File: deployment/database/production_indexes.sql

-- Session performance indexes
CREATE INDEX CONCURRENTLY idx_sessions_client_account_active 
ON sessions(client_account_id) WHERE active = true;

CREATE INDEX CONCURRENTLY idx_sessions_created_at_desc 
ON sessions(created_at DESC);

-- Asset inventory indexes  
CREATE INDEX CONCURRENTLY idx_assets_client_engagement 
ON assets(client_account_id, engagement_id);

CREATE INDEX CONCURRENTLY idx_assets_classification 
ON assets(asset_type, asset_subtype) WHERE active = true;

-- Flow execution indexes
CREATE INDEX CONCURRENTLY idx_flow_executions_session_status 
ON flow_executions(session_id, status);

CREATE INDEX CONCURRENTLY idx_flow_executions_created_at 
ON flow_executions(created_at) WHERE status IN ('running', 'pending');

-- Agent insights indexes
CREATE INDEX CONCURRENTLY idx_agent_insights_session_crew 
ON agent_insights(session_id, crew_name);

CREATE INDEX CONCURRENTLY idx_agent_insights_timestamp 
ON agent_insights(created_at DESC);

-- Full-text search indexes
CREATE INDEX CONCURRENTLY idx_assets_name_search 
ON assets USING gin(to_tsvector('english', asset_name));

-- Refresh statistics
ANALYZE;
```

### **Caching Strategy**

#### **Redis Configuration**
```python
# backend/app/core/cache.py - Production Redis config

import redis
from typing import Any, Optional
import json
import pickle

class ProductionCacheConfig:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='redis-cluster.internal',
            port=6379,
            password='secure_redis_password',
            db=0,
            max_connections=50,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
    
    def cache_crew_results(self, session_id: str, crew_name: str, results: dict, ttl: int = 3600):
        """Cache crew execution results"""
        cache_key = f"crew_results:{session_id}:{crew_name}"
        serialized_results = json.dumps(results)
        self.redis_client.setex(cache_key, ttl, serialized_results)
    
    def get_cached_crew_results(self, session_id: str, crew_name: str) -> Optional[dict]:
        """Retrieve cached crew results"""
        cache_key = f"crew_results:{session_id}:{crew_name}"
        cached_data = self.redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        return None
    
    def cache_field_mappings(self, client_id: str, data_signature: str, mappings: dict):
        """Cache field mapping results for reuse"""
        cache_key = f"field_mappings:{client_id}:{data_signature}"
        self.redis_client.setex(cache_key, 86400, json.dumps(mappings))  # 24 hour TTL
```

### **CDN Configuration**

#### **CloudFlare Setup**
```javascript
// deployment/cdn/cloudflare_config.js
const cloudflareConfig = {
  // Caching rules
  cacheRules: [
    {
      pattern: "*.js",
      cacheTtl: 86400,  // 1 day
      browserTtl: 86400
    },
    {
      pattern: "*.css", 
      cacheTtl: 86400,
      browserTtl: 86400
    },
    {
      pattern: "/api/*",
      cacheTtl: 0,      // No caching for API endpoints
      browserTtl: 0
    }
  ],
  
  // Security settings
  securityLevel: "high",
  challengePassage: 30,
  
  // Performance settings
  minify: {
    javascript: true,
    css: true,
    html: true
  },
  
  // SSL settings
  ssl: "full_strict",
  httpRedirect: true,
  hsts: {
    enabled: true,
    maxAge: 63072000,
    includeSubdomains: true,
    preload: true
  }
};
```

---

## 🔄 **Backup and Recovery**

### **Database Backup Strategy**

#### **Automated Backup Script**
```bash
#!/bin/bash
# File: deployment/backup/backup_database.sh

# Configuration
DB_HOST="your-db-host"
DB_NAME="migration_db_prod"
DB_USER="backup_user"
BACKUP_DIR="/backups/database"
S3_BUCKET="your-backup-bucket"
RETENTION_DAYS=30

# Create timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="migration_db_${TIMESTAMP}.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
    --no-password \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --format=custom \
    --file="$BACKUP_DIR/$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_DIR/$BACKUP_FILE"

# Upload to S3
aws s3 cp "$BACKUP_DIR/${BACKUP_FILE}.gz" "s3://$S3_BUCKET/database/"

# Clean up local backups older than retention period
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Log completion
echo "$(date): Database backup completed: ${BACKUP_FILE}.gz" >> /var/log/backup.log
```

#### **Backup Verification**
```bash
#!/bin/bash
# File: deployment/backup/verify_backup.sh

BACKUP_FILE=$1
TEST_DB="migration_db_test"

# Create test database
createdb $TEST_DB

# Restore backup to test database
pg_restore -d $TEST_DB "$BACKUP_FILE"

# Run verification queries
psql -d $TEST_DB -c "SELECT COUNT(*) FROM sessions;"
psql -d $TEST_DB -c "SELECT COUNT(*) FROM assets;"
psql -d $TEST_DB -c "SELECT COUNT(*) FROM flow_executions;"

# Clean up test database
dropdb $TEST_DB

echo "Backup verification completed for: $BACKUP_FILE"
```

### **Disaster Recovery Plan**

#### **Recovery Procedures**
```bash
#!/bin/bash
# File: deployment/recovery/disaster_recovery.sh

echo "Starting disaster recovery procedure..."

# 1. Stop all services
docker-compose down

# 2. Restore database from latest backup
LATEST_BACKUP=$(aws s3 ls s3://your-backup-bucket/database/ | sort | tail -n 1 | awk '{print $4}')
aws s3 cp "s3://your-backup-bucket/database/$LATEST_BACKUP" ./latest_backup.sql.gz

# 3. Decompress and restore
gunzip latest_backup.sql.gz
pg_restore -d migration_db_prod latest_backup.sql

# 4. Restore application data
aws s3 sync s3://your-backup-bucket/app-data/ ./data/

# 5. Restart services
docker-compose up -d

# 6. Verify system health
sleep 30
curl -f http://localhost:8000/health

echo "Disaster recovery completed"
```

---

## 📋 **Operational Procedures**

### **Deployment Checklist**

#### **Pre-Deployment Checklist**
```markdown
# Production Deployment Checklist

## Infrastructure
- [ ] Server resources verified (CPU, Memory, Storage)
- [ ] Database cluster ready and optimized
- [ ] Load balancer configured
- [ ] SSL certificates installed and valid
- [ ] DNS records configured
- [ ] Firewall rules applied

## Security
- [ ] Environment variables secured
- [ ] API keys rotated
- [ ] Database passwords updated
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Audit logging configured

## Performance
- [ ] Database indexes created
- [ ] Connection pooling configured
- [ ] Caching layer deployed
- [ ] CDN configured
- [ ] Performance monitoring enabled

## Monitoring
- [ ] Prometheus metrics enabled
- [ ] Grafana dashboards imported
- [ ] Alerting rules configured
- [ ] Log aggregation working
- [ ] Health checks operational

## Backup & Recovery
- [ ] Automated backups configured
- [ ] Backup verification scheduled
- [ ] Recovery procedures tested
- [ ] Documentation updated
```

#### **Post-Deployment Verification**
```bash
#!/bin/bash
# File: deployment/verification/post_deploy_check.sh

echo "Starting post-deployment verification..."

# Health check
echo "Checking application health..."
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ $HEALTH -eq 200 ]; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed: $HEALTH"
    exit 1
fi

# Database connectivity
echo "Checking database connectivity..."
DB_CHECK=$(docker exec migration_backend python -c "
from app.core.database import get_db
try:
    db = next(get_db())
    result = db.execute('SELECT 1')
    print('OK')
except Exception as e:
    print(f'ERROR: {e}')
")

if [ "$DB_CHECK" = "OK" ]; then
    echo "✅ Database connectivity verified"
else
    echo "❌ Database connectivity failed: $DB_CHECK"
    exit 1
fi

# API endpoints
echo "Testing API endpoints..."
API_TEST=$(curl -s -w "%{http_code}" -H "Authorization: Bearer test_token" \
    http://localhost:8000/api/v1/discovery/flow/status)

if [[ $API_TEST == *"200"* ]]; then
    echo "✅ API endpoints responding"
else
    echo "❌ API endpoints not responding properly"
fi

# Memory system
echo "Checking memory system..."
MEMORY_TEST=$(docker exec migration_backend python -c "
from app.services.crewai_service import CrewAIService
try:
    service = CrewAIService()
    if hasattr(service, 'shared_memory'):
        print('OK')
    else:
        print('ERROR: Memory system not initialized')
except Exception as e:
    print(f'ERROR: {e}')
")

if [ "$MEMORY_TEST" = "OK" ]; then
    echo "✅ Memory system operational"
else
    echo "❌ Memory system issues: $MEMORY_TEST"
fi

echo "Post-deployment verification completed"
```

### **Maintenance Procedures**

#### **Regular Maintenance Tasks**
```bash
#!/bin/bash
# File: deployment/maintenance/weekly_maintenance.sh

echo "Starting weekly maintenance tasks..."

# 1. Database maintenance
echo "Running database maintenance..."
docker exec migration_db psql -U user -d migration_db -c "VACUUM ANALYZE;"
docker exec migration_db psql -U user -d migration_db -c "REINDEX DATABASE migration_db;"

# 2. Log rotation
echo "Rotating logs..."
logrotate /etc/logrotate.d/discovery_flow

# 3. Clear old temporary files
echo "Cleaning temporary files..."
find /tmp -name "discovery_flow_*" -mtime +7 -delete

# 4. Update system packages (if needed)
echo "Checking for security updates..."
apt list --upgradable | grep -i security

# 5. Backup verification
echo "Verifying recent backups..."
./deployment/backup/verify_backup.sh /backups/database/$(ls -t /backups/database/ | head -1)

# 6. Performance metrics check
echo "Generating performance report..."
docker exec migration_backend python scripts/generate_performance_report.py

echo "Weekly maintenance completed"
```

---

This comprehensive production deployment guide ensures reliable, secure, and performant deployment of the Discovery Flow system in enterprise environments. 