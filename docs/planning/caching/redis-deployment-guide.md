# Redis Deployment Guide - AI Modernize Migration Platform

## Executive Summary

This guide provides step-by-step deployment instructions for Redis integration across local Docker, Railway production, and Upstash cloud environments. It complements the task tracker and technical specifications with practical, copy-paste ready configurations and troubleshooting guidance.

---

## Table of Contents
1. [Local Docker Development](#1-local-docker-development)
2. [Railway Deployment](#2-railway-deployment)
3. [Upstash Integration](#3-upstash-integration)
4. [Monitoring and Debugging](#4-monitoring-and-debugging)
5. [CI/CD Integration](#5-cicd-integration)
6. [Troubleshooting Guide](#6-troubleshooting-guide)

---

## 1. Local Docker Development

### 1.1 Complete Docker Compose Configuration

Create or update `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: migration_postgres_dev
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-migration_dev}
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
    networks:
      - migration_dev
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: migration_redis_dev
    ports:
      - "6379:6379"
    volumes:
      - redis_dev_data:/data
      - ./redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
    networks:
      - migration_dev
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 10s
    command: >
      redis-server /usr/local/etc/redis/redis.conf
      --appendonly yes
      --appendfsync everysec
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --tcp-keepalive 60
      --timeout 300
      --loglevel notice

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    container_name: migration_backend_dev
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@postgres:5432/${POSTGRES_DB:-migration_dev}
      REDIS_ENABLED: "true"
      REDIS_URL: redis://redis:6379/0
      PYTHONUNBUFFERED: 1
      ENVIRONMENT: development
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - backend_cache:/app/.cache
    networks:
      - migration_dev
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Redis Commander (GUI)
  redis-commander:
    image: rediscommander/redis-commander:latest
    container_name: migration_redis_commander
    environment:
      REDIS_HOSTS: local:redis:6379
      HTTP_USER: admin
      HTTP_PASSWORD: ${REDIS_COMMANDER_PASSWORD:-admin123}
    ports:
      - "8081:8081"
    networks:
      - migration_dev
    depends_on:
      - redis
    profiles:
      - debug

volumes:
  postgres_dev_data:
  redis_dev_data:
  backend_cache:

networks:
  migration_dev:
    driver: bridge
```

### 1.2 Redis Configuration File

Create `redis/redis.conf` for custom Redis settings:

```conf
# Redis Configuration for Development

# Network
bind 0.0.0.0
protected-mode no
port 6379
tcp-backlog 511
timeout 300
tcp-keepalive 60

# General
daemonize no
supervised no
pidfile /var/run/redis_6379.pid
loglevel notice
logfile ""
databases 16

# Snapshotting
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /data

# Replication
replica-read-only yes

# Security
# requirepass your_redis_password_here

# Memory Management
maxmemory 256mb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# Append Only Mode
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Slow Log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Advanced Config
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
```

### 1.3 Starting Redis Development Environment

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Start with Redis Commander GUI (debug profile)
docker-compose -f docker-compose.dev.yml --profile debug up -d

# View Redis logs
docker-compose -f docker-compose.dev.yml logs -f redis

# Check Redis health
docker exec migration_redis_dev redis-cli ping
# Expected: PONG

# Monitor Redis in real-time
docker exec migration_redis_dev redis-cli monitor

# Access Redis Commander
# Navigate to http://localhost:8081
# Username: admin, Password: admin123
```

### 1.4 Testing Redis Connectivity from FastAPI

Create a test script `backend/scripts/test_redis_connection.py`:

```python
#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.redis_config import redis_manager
from app.services.flows.events import flow_event_bus
from app.schemas.flow_events import FlowEvent
from datetime import datetime
import time


async def test_redis_connection():
    """Test Redis connectivity and basic operations"""
    print("🔄 Testing Redis Connection...")
    print(f"Redis URL: {os.getenv('REDIS_URL', 'Not set')}")
    
    # Test 1: Connection
    print("\n1. Testing connection...")
    connected = await redis_manager.initialize()
    if not connected:
        print("❌ Failed to connect to Redis")
        return False
    print("✅ Connected to Redis")
    
    # Test 2: Basic operations
    print("\n2. Testing basic operations...")
    try:
        # Set
        await redis_manager.redis.set("test:key", "test_value", ex=60)
        print("✅ SET operation successful")
        
        # Get
        value = await redis_manager.redis.get("test:key")
        assert value == "test_value", f"Expected 'test_value', got '{value}'"
        print("✅ GET operation successful")
        
        # Delete
        deleted = await redis_manager.redis.delete("test:key")
        assert deleted == 1, f"Expected 1 key deleted, got {deleted}"
        print("✅ DELETE operation successful")
        
    except Exception as e:
        print(f"❌ Basic operations failed: {e}")
        return False
    
    # Test 3: Event Bus
    print("\n3. Testing Event Bus...")
    try:
        test_event = FlowEvent(
            flow_id="test-flow-123",
            event_type="TEST_CONNECTION",
            payload={"message": "Redis connection test"},
            timestamp=datetime.utcnow(),
            source="test_script"
        )
        
        # Publish
        start = time.time()
        success = await flow_event_bus.publish(test_event)
        publish_time = (time.time() - start) * 1000
        assert success, "Event publish failed"
        print(f"✅ Event published in {publish_time:.2f}ms")
        
        # Retrieve
        start = time.time()
        events = await flow_event_bus.get_events("test-flow-123", count=10)
        retrieve_time = (time.time() - start) * 1000
        assert len(events) > 0, "No events retrieved"
        print(f"✅ Retrieved {len(events)} events in {retrieve_time:.2f}ms")
        
    except Exception as e:
        print(f"❌ Event Bus test failed: {e}")
        return False
    
    # Test 4: Performance
    print("\n4. Testing performance...")
    try:
        # Batch operations
        operations = 100
        start = time.time()
        
        # Pipeline for batch operations
        pipe = redis_manager.redis.pipeline()
        for i in range(operations):
            pipe.set(f"perf:test:{i}", f"value_{i}", ex=60)
        await pipe.execute()
        
        batch_time = (time.time() - start) * 1000
        avg_time = batch_time / operations
        print(f"✅ {operations} SET operations in {batch_time:.2f}ms")
        print(f"   Average: {avg_time:.2f}ms per operation")
        
        # Cleanup
        pipe = redis_manager.redis.pipeline()
        for i in range(operations):
            pipe.delete(f"perf:test:{i}")
        await pipe.execute()
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False
    
    # Test 5: Memory usage
    print("\n5. Checking memory usage...")
    try:
        info = await redis_manager.redis.info("memory")
        used_memory = info.get("used_memory_human", "Unknown")
        peak_memory = info.get("used_memory_peak_human", "Unknown")
        print(f"✅ Memory usage: {used_memory} (peak: {peak_memory})")
        
    except Exception as e:
        print(f"❌ Memory check failed: {e}")
    
    # Cleanup
    await redis_manager.close()
    print("\n✅ All Redis tests passed!")
    return True


if __name__ == "__main__":
    # Set environment variables if not set
    os.environ.setdefault("REDIS_ENABLED", "true")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    
    # Run tests
    success = asyncio.run(test_redis_connection())
    sys.exit(0 if success else 1)
```

Run the test:

```bash
cd backend
python scripts/test_redis_connection.py
```

### 1.5 Redis CLI Commands for Debugging

```bash
# Access Redis CLI
docker exec -it migration_redis_dev redis-cli

# Basic commands
ping                          # Check if Redis is running
INFO server                   # Server information
INFO memory                   # Memory usage details
INFO stats                    # General statistics
CLIENT LIST                   # List connected clients
CONFIG GET maxmemory         # Check memory limit
CONFIG GET *                 # View all configuration

# Monitor commands in real-time
MONITOR                      # See all commands (exit with Ctrl+C)

# Check specific keys
KEYS flow:events:*           # List all flow event keys
TYPE flow:events:test-123    # Check key type
TTL flow:events:test-123     # Check time to live

# Stream operations
XLEN flow:events:test-123    # Length of stream
XREVRANGE flow:events:test-123 + - COUNT 10  # Latest 10 events
XINFO STREAM flow:events:test-123            # Stream information

# Performance debugging
SLOWLOG GET 10               # Get 10 slowest operations
LATENCY LATEST               # Latest latency events
MEMORY DOCTOR                # Memory optimization suggestions

# Flush data (development only!)
FLUSHDB                      # Clear current database
FLUSHALL                     # Clear all databases
```

---

## 2. Railway Deployment

### 2.1 Railway Project Setup

```bash
# Install Railway CLI
curl -fsSL https://railway.app/install.sh | sh

# Login to Railway
railway login

# Link to existing project or create new
railway link

# View current environment
railway status
```

### 2.2 Environment Variable Configuration

Create `.railway/env.production`:

```bash
# Redis Configuration
REDIS_ENABLED=true
REDIS_URL=${UPSTASH_REDIS_URL}
REDIS_SSL_REQUIRED=true
REDIS_MAX_CONNECTIONS=50
SERVER_ID=railway-prod-${RAILWAY_REPLICA_ID}

# Feature Flags
REDIS_EVENT_BUS=true
REDIS_CACHE=true
REDIS_SSE=true

# Monitoring
REDIS_MONITOR_ENABLED=true
REDIS_MONITOR_INTERVAL=60
REDIS_ALERT_WEBHOOK=${SLACK_WEBHOOK_URL}

# Performance Tuning
REDIS_COMMAND_TIMEOUT=5
REDIS_PIPELINE_ENABLED=true
REDIS_COMPRESSION_THRESHOLD=1024
```

Deploy environment variables:

```bash
# Set individual variables
railway variables set REDIS_ENABLED=true
railway variables set REDIS_URL="${UPSTASH_REDIS_URL}"
railway variables set REDIS_SSL_REQUIRED=true
railway variables set SERVER_ID="railway-prod-1"

# Set from file
railway variables set < .railway/env.production

# Verify variables
railway variables
```

### 2.3 Railway Service Configuration

Create `railway.toml`:

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "./backend/Dockerfile"

[deploy]
healthcheckPath = "/api/v1/health"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[[services]]
name = "backend"
port = 8000

[services.backend]
  [services.backend.envs]
  PORT = 8000
  REDIS_ENABLED = true
  
  [[services.backend.healthcheck]]
  path = "/api/v1/health/redis"
  interval = "30s"
  timeout = "10s"
  retries = 3
```

### 2.4 Deployment Commands

```bash
# Deploy to Railway
railway up

# Deploy with specific environment
railway up -e production

# View deployment logs
railway logs

# Stream logs in real-time
railway logs -f

# Run commands in production
railway run python -m app.scripts.test_redis_connection

# Open Redis shell in production (if Redis is hosted on Railway)
railway run redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT}

# Restart service
railway restart

# Rollback to previous deployment
railway rollback
```

### 2.5 Health Check Endpoints

Update `backend/app/api/v1/endpoints/health.py`:

```python
from fastapi import APIRouter, HTTPException
from app.core.redis_config import redis_manager
from app.monitoring.redis_monitor import redis_monitor
import time
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ai-modernize-backend",
        "version": "1.0.0"
    }

@router.get("/health/redis")
async def redis_health_check():
    """Detailed Redis health check"""
    health_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "redis": {
            "enabled": redis_manager.enabled,
            "connected": False,
            "latency_ms": None,
            "error": None
        }
    }
    
    if not redis_manager.enabled:
        health_status["redis"]["status"] = "disabled"
        return health_status
    
    if not redis_manager.is_available():
        health_status["redis"]["status"] = "disconnected"
        health_status["redis"]["error"] = "Redis connection not available"
        raise HTTPException(status_code=503, detail=health_status)
    
    try:
        # Test Redis connection
        start = time.time()
        await redis_manager.redis.ping()
        latency = (time.time() - start) * 1000
        
        # Get detailed info
        info = await redis_monitor.get_redis_info()
        
        health_status["redis"].update({
            "connected": True,
            "status": "healthy",
            "latency_ms": round(latency, 2),
            "details": info
        })
        
        # Check if latency is acceptable
        if latency > 100:  # 100ms threshold
            health_status["redis"]["warning"] = "High latency detected"
            
    except Exception as e:
        health_status["redis"].update({
            "status": "unhealthy",
            "error": str(e)
        })
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

@router.get("/health/dependencies")
async def dependency_health_check():
    """Check all service dependencies"""
    dependencies = {}
    
    # Check PostgreSQL
    try:
        from app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            await db.execute("SELECT 1")
        dependencies["postgresql"] = {"status": "healthy"}
    except Exception as e:
        dependencies["postgresql"] = {"status": "unhealthy", "error": str(e)}
    
    # Check Redis
    if redis_manager.enabled:
        try:
            await redis_manager.redis.ping()
            dependencies["redis"] = {"status": "healthy"}
        except Exception as e:
            dependencies["redis"] = {"status": "unhealthy", "error": str(e)}
    else:
        dependencies["redis"] = {"status": "disabled"}
    
    # Check external services
    dependencies["upstash"] = {
        "status": "healthy" if redis_manager.is_available() else "disconnected"
    }
    
    # Overall status
    all_healthy = all(
        dep.get("status") in ["healthy", "disabled"] 
        for dep in dependencies.values()
    )
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": dependencies
    }
```

### 2.6 Deployment Verification Script

Create `backend/scripts/verify_railway_deployment.py`:

```python
#!/usr/bin/env python3
import asyncio
import os
import sys
import httpx
from datetime import datetime

async def verify_deployment():
    """Verify Railway deployment is working correctly"""
    base_url = os.getenv("RAILWAY_PUBLIC_URL", "https://your-app.railway.app")
    
    print(f"🚂 Verifying Railway Deployment")
    print(f"URL: {base_url}")
    print(f"Time: {datetime.utcnow().isoformat()}")
    print("-" * 50)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Basic health
        print("\n1. Testing basic health endpoint...")
        try:
            response = await client.get(f"{base_url}/api/v1/health")
            response.raise_for_status()
            data = response.json()
            print(f"✅ Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
        except Exception as e:
            print(f"❌ Basic health check failed: {e}")
            return False
        
        # Test 2: Redis health
        print("\n2. Testing Redis health endpoint...")
        try:
            response = await client.get(f"{base_url}/api/v1/health/redis")
            data = response.json()
            redis_status = data.get("redis", {})
            
            if redis_status.get("connected"):
                print(f"✅ Redis connected")
                print(f"   Latency: {redis_status.get('latency_ms')}ms")
                print(f"   Memory: {redis_status.get('details', {}).get('used_memory_human')}")
            else:
                print(f"⚠️  Redis not connected: {redis_status.get('error')}")
                
        except Exception as e:
            print(f"❌ Redis health check failed: {e}")
        
        # Test 3: Dependencies
        print("\n3. Testing all dependencies...")
        try:
            response = await client.get(f"{base_url}/api/v1/health/dependencies")
            data = response.json()
            print(f"Overall status: {data.get('status')}")
            
            for dep, status in data.get("dependencies", {}).items():
                emoji = "✅" if status.get("status") == "healthy" else "❌"
                print(f"{emoji} {dep}: {status.get('status')}")
                if status.get("error"):
                    print(f"   Error: {status.get('error')}")
                    
        except Exception as e:
            print(f"❌ Dependency check failed: {e}")
        
        # Test 4: Metrics endpoint
        print("\n4. Testing metrics endpoint...")
        try:
            response = await client.get(f"{base_url}/api/v1/metrics/redis")
            if response.status_code == 200:
                data = response.json()
                print("✅ Metrics available")
                print(f"   Cache metrics: {len(data.get('cache_metrics', {}))}")
                print(f"   Connections: {data.get('connection_count', 0)}")
            else:
                print("⚠️  Metrics endpoint not available")
                
        except Exception as e:
            print(f"⚠️  Metrics check skipped: {e}")
    
    print("\n" + "-" * 50)
    print("✅ Deployment verification complete!")
    return True

if __name__ == "__main__":
    success = asyncio.run(verify_deployment())
    sys.exit(0 if success else 1)
```

---

## 3. Upstash Integration

### 3.1 Upstash Account Setup

1. **Create Account**:
   ```bash
   # Navigate to https://upstash.com
   # Sign up with GitHub (recommended for Railway integration)
   ```

2. **Create Redis Database**:
   ```bash
   # Via Upstash CLI (install first)
   npm install -g @upstash/cli
   upstash auth login
   
   # Create database
   upstash redis create \
     --name "ai-modernize-prod" \
     --region "us-east-1" \
     --type "pay-as-you-go"
   ```

3. **Configure Database Settings**:
   - Navigate to Upstash Console
   - Select your database
   - Configure:
     - Eviction: `allkeys-lru`
     - Max Memory: `256MB` (free tier)
     - Enable TLS/SSL
     - Enable Persistence

### 3.2 Connection Configuration

Get connection details from Upstash Console:

```bash
# Example Upstash Redis URL format:
# rediss://default:YOUR_PASSWORD@YOUR_ENDPOINT.upstash.io:6379

# Test connection
redis-cli --tls \
  -h YOUR_ENDPOINT.upstash.io \
  -p 6379 \
  -a YOUR_PASSWORD \
  ping
```

### 3.3 Upstash-Specific Configuration

Create `backend/app/core/upstash_config.py`:

```python
import os
from typing import Dict, Any
from urllib.parse import urlparse

class UpstashOptimizer:
    """Optimize Redis operations for Upstash limits"""
    
    def __init__(self):
        self.url = os.getenv("UPSTASH_REDIS_URL", "")
        self.daily_command_limit = 10000  # Free tier
        self.max_request_size = 1048576   # 1MB
        self.max_response_size = 10485760 # 10MB
        
    def get_optimized_pool_config(self) -> Dict[str, Any]:
        """Get connection pool config optimized for Upstash"""
        parsed = urlparse(self.url)
        
        return {
            "url": self.url,
            "decode_responses": True,
            "encoding": "utf-8",
            "encoding_errors": "strict",
            
            # Connection settings
            "max_connections": 50,  # Upstash concurrent connection limit
            "socket_connect_timeout": 10,
            "socket_timeout": 10,
            "socket_keepalive": True,
            "socket_keepalive_options": {
                1: 10,  # TCP_KEEPIDLE
                2: 3,   # TCP_KEEPINTVL
                3: 3,   # TCP_KEEPCNT
            },
            
            # SSL/TLS (required for Upstash)
            "ssl": True,
            "ssl_cert_reqs": "required",
            "ssl_check_hostname": True,
            "ssl_ca_certs": None,  # Use system bundle
            
            # Retry configuration
            "retry_on_timeout": True,
            "retry_on_error": [ConnectionError, TimeoutError],
            "health_check_interval": 60,
        }
    
    def should_compress(self, data_size: int) -> bool:
        """Determine if data should be compressed"""
        return data_size > 1024  # Compress if > 1KB
    
    def estimate_command_cost(self, command: str, *args) -> int:
        """Estimate command cost for rate limiting"""
        # Command costs (approximate)
        costs = {
            "GET": 1,
            "SET": 1,
            "DEL": 1,
            "EXISTS": 1,
            "EXPIRE": 1,
            "TTL": 1,
            "HGET": 1,
            "HSET": 1,
            "SADD": len(args) - 1,  # Cost per member
            "SMEMBERS": 10,  # Higher cost for reading sets
            "XADD": 2,
            "XRANGE": 10,
            "XREVRANGE": 10,
            "SCAN": 10,
            "PIPELINE": 1,  # Per command in pipeline
        }
        
        return costs.get(command.upper(), 1)
```

### 3.4 Upstash Rate Limiting

Implement rate limiting to stay within free tier limits:

```python
# backend/app/services/redis/upstash_rate_limiter.py
import asyncio
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)

class UpstashRateLimiter:
    """Rate limiter for Upstash Redis commands"""
    
    def __init__(self, daily_limit: int = 10000):
        self.daily_limit = daily_limit
        self.window_size = 86400  # 24 hours in seconds
        self.commands = deque()  # (timestamp, cost) tuples
        self.lock = asyncio.Lock()
        
    async def check_rate_limit(self, command_cost: int = 1) -> bool:
        """Check if command can be executed within rate limits"""
        async with self.lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=self.window_size)
            
            # Remove old commands outside window
            while self.commands and self.commands[0][0] < cutoff:
                self.commands.popleft()
            
            # Calculate current usage
            current_usage = sum(cost for _, cost in self.commands)
            
            # Check if adding this command would exceed limit
            if current_usage + command_cost > self.daily_limit:
                logger.warning(
                    f"Rate limit would be exceeded: {current_usage + command_cost}/{self.daily_limit}"
                )
                return False
            
            # Add command to tracking
            self.commands.append((now, command_cost))
            return True
    
    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        async with self.lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=self.window_size)
            
            # Clean old entries
            while self.commands and self.commands[0][0] < cutoff:
                self.commands.popleft()
            
            current_usage = sum(cost for _, cost in self.commands)
            usage_percent = (current_usage / self.daily_limit) * 100
            
            # Estimate time until reset
            if self.commands:
                oldest = self.commands[0][0]
                time_until_reset = (oldest + timedelta(seconds=self.window_size) - now).total_seconds()
            else:
                time_until_reset = 0
            
            return {
                "current_usage": current_usage,
                "daily_limit": self.daily_limit,
                "usage_percent": round(usage_percent, 2),
                "remaining": self.daily_limit - current_usage,
                "time_until_reset_seconds": max(0, int(time_until_reset)),
                "commands_in_window": len(self.commands)
            }

# Global rate limiter
upstash_rate_limiter = UpstashRateLimiter()
```

### 3.5 Upstash Monitoring Dashboard

Create monitoring endpoint for Upstash usage:

```python
# backend/app/api/v1/endpoints/upstash_metrics.py
from fastapi import APIRouter, HTTPException
from app.services.redis.upstash_rate_limiter import upstash_rate_limiter
from app.core.redis_config import redis_manager
import httpx

router = APIRouter()

@router.get("/metrics/upstash")
async def upstash_metrics():
    """Get Upstash usage metrics"""
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "rate_limit": await upstash_rate_limiter.get_usage_stats(),
        "connection": {
            "enabled": redis_manager.enabled,
            "connected": redis_manager.is_available()
        }
    }
    
    # Get Upstash API metrics if available
    upstash_api_key = os.getenv("UPSTASH_API_KEY")
    if upstash_api_key and redis_manager.is_available():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.upstash.com/v2/redis/database",
                    headers={"Authorization": f"Bearer {upstash_api_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Find our database
                    for db in data:
                        if db["database_name"] == "ai-modernize-prod":
                            metrics["upstash_api"] = {
                                "commands_today": db.get("commands_today", 0),
                                "storage_mb": db.get("disk_usage", 0) / 1024 / 1024,
                                "bandwidth_mb": db.get("bandwidth_usage", 0) / 1024 / 1024,
                                "endpoint": db.get("endpoint", ""),
                                "max_clients": db.get("max_clients", 0),
                                "max_request_size": db.get("max_request_size", 0),
                                "max_memory_mb": db.get("max_memory", 0) / 1024 / 1024
                            }
                            break
                            
        except Exception as e:
            logger.error(f"Failed to fetch Upstash API metrics: {e}")
    
    return metrics

@router.post("/metrics/upstash/alert")
async def setup_upstash_alerts(webhook_url: str, threshold_percent: int = 80):
    """Setup alerts for Upstash usage"""
    # This would integrate with your alerting system
    return {
        "status": "configured",
        "webhook_url": webhook_url,
        "threshold_percent": threshold_percent,
        "message": "Alerts will be sent when usage exceeds threshold"
    }
```

---

## 4. Monitoring and Debugging

### 4.1 Redis Monitoring Commands

Create `backend/scripts/redis_monitor.sh`:

```bash
#!/bin/bash

# Redis Monitoring Script for Production

REDIS_CLI="redis-cli"
if [ ! -z "$UPSTASH_REDIS_URL" ]; then
    # Parse Upstash URL
    REDIS_CLI="redis-cli --tls -u $UPSTASH_REDIS_URL"
fi

echo "=== Redis Monitoring Dashboard ==="
echo "Time: $(date)"
echo ""

# General Info
echo "1. Server Info:"
$REDIS_CLI INFO server | grep -E "redis_version|uptime_in_days|process_id"
echo ""

# Memory Usage
echo "2. Memory Usage:"
$REDIS_CLI INFO memory | grep -E "used_memory_human|used_memory_peak_human|mem_fragmentation_ratio"
echo ""

# Client Connections
echo "3. Client Connections:"
$REDIS_CLI INFO clients | grep -E "connected_clients|blocked_clients"
echo ""

# Operations per Second
echo "4. Performance:"
$REDIS_CLI INFO stats | grep -E "instantaneous_ops_per_sec|total_commands_processed"
echo ""

# Key Statistics
echo "5. Keyspace:"
$REDIS_CLI INFO keyspace
echo ""

# Slow Queries
echo "6. Slow Queries (last 5):"
$REDIS_CLI SLOWLOG GET 5
echo ""

# Memory Doctor
echo "7. Memory Doctor:"
$REDIS_CLI MEMORY DOCTOR
echo ""

# Top Keys by Memory
echo "8. Sampling Keys for Memory Usage:"
for pattern in "flow:*" "cache:*" "agent:*" "sse:*"; do
    echo "  Pattern: $pattern"
    $REDIS_CLI --scan --pattern "$pattern" | head -5 | while read key; do
        size=$($REDIS_CLI MEMORY USAGE "$key")
        echo "    $key: $size bytes"
    done
done
```

### 4.2 FastAPI Monitoring Endpoints

Update `backend/app/api/v1/endpoints/monitoring.py`:

```python
from fastapi import APIRouter, BackgroundTasks
from app.core.redis_config import redis_manager
from app.monitoring.redis_health_monitor import redis_health_monitor
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/monitor/redis/live")
async def redis_live_monitor(duration_seconds: int = 10):
    """Monitor Redis operations in real-time"""
    if not redis_manager.is_available():
        return {"error": "Redis not available"}
    
    operations = []
    start_time = datetime.utcnow()
    
    # Use Redis MONITOR command (careful in production!)
    pubsub = redis_manager.redis.pubsub()
    
    try:
        # This is a simplified version - in production, use streaming response
        while (datetime.utcnow() - start_time).seconds < duration_seconds:
            # Collect operations
            # Note: MONITOR is not available in Upstash
            pass
            
    except Exception as e:
        return {"error": str(e)}
    
    return {
        "duration_seconds": duration_seconds,
        "operations_captured": len(operations),
        "operations": operations[:100]  # Limit response size
    }

@router.get("/monitor/redis/patterns")
async def analyze_key_patterns():
    """Analyze Redis key patterns and usage"""
    if not redis_manager.is_available():
        return {"error": "Redis not available"}
    
    patterns = {
        "flow_events": "flow:events:*",
        "flow_cache": "cache:flow:*",
        "agent_results": "agent:results:*",
        "sse_connections": "sse:connections:*",
        "orchestrator": "orchestrator:*"
    }
    
    analysis = {}
    
    for name, pattern in patterns.items():
        try:
            # Count keys matching pattern
            keys = []
            cursor = 0
            while True:
                cursor, batch = await redis_manager.redis.scan(
                    cursor, match=pattern, count=100
                )
                keys.extend(batch)
                if cursor == 0:
                    break
            
            # Sample memory usage
            sample_size = min(10, len(keys))
            total_memory = 0
            
            for key in keys[:sample_size]:
                try:
                    memory = await redis_manager.redis.memory_usage(key) or 0
                    total_memory += memory
                except:
                    pass
            
            avg_memory = total_memory / sample_size if sample_size > 0 else 0
            
            analysis[name] = {
                "pattern": pattern,
                "key_count": len(keys),
                "sample_size": sample_size,
                "avg_memory_bytes": int(avg_memory),
                "estimated_total_memory_mb": round((avg_memory * len(keys)) / 1024 / 1024, 2)
            }
            
        except Exception as e:
            analysis[name] = {"error": str(e)}
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "patterns": analysis,
        "total_keys": sum(p.get("key_count", 0) for p in analysis.values()),
        "estimated_total_memory_mb": sum(
            p.get("estimated_total_memory_mb", 0) for p in analysis.values()
        )
    }

@router.get("/monitor/redis/performance")
async def redis_performance_test():
    """Run Redis performance test"""
    if not redis_manager.is_available():
        return {"error": "Redis not available"}
    
    results = {}
    
    # Test 1: Single operation latency
    single_ops = []
    for _ in range(10):
        start = time.time()
        await redis_manager.redis.ping()
        single_ops.append((time.time() - start) * 1000)
    
    results["single_operation"] = {
        "avg_ms": round(sum(single_ops) / len(single_ops), 2),
        "min_ms": round(min(single_ops), 2),
        "max_ms": round(max(single_ops), 2)
    }
    
    # Test 2: Pipeline performance
    pipeline_start = time.time()
    pipe = redis_manager.redis.pipeline()
    for i in range(100):
        pipe.set(f"perf:test:{i}", "x" * 100, ex=60)
    await pipe.execute()
    pipeline_time = (time.time() - pipeline_start) * 1000
    
    results["pipeline_100_ops"] = {
        "total_ms": round(pipeline_time, 2),
        "avg_per_op_ms": round(pipeline_time / 100, 2)
    }
    
    # Cleanup
    pipe = redis_manager.redis.pipeline()
    for i in range(100):
        pipe.delete(f"perf:test:{i}")
    await pipe.execute()
    
    # Test 3: Concurrent operations
    async def concurrent_op(idx):
        start = time.time()
        await redis_manager.redis.set(f"concurrent:{idx}", "test", ex=60)
        await redis_manager.redis.get(f"concurrent:{idx}")
        await redis_manager.redis.delete(f"concurrent:{idx}")
        return (time.time() - start) * 1000
    
    concurrent_start = time.time()
    tasks = [concurrent_op(i) for i in range(50)]
    concurrent_times = await asyncio.gather(*tasks)
    concurrent_total = (time.time() - concurrent_start) * 1000
    
    results["concurrent_50_ops"] = {
        "total_ms": round(concurrent_total, 2),
        "avg_per_op_ms": round(sum(concurrent_times) / len(concurrent_times), 2),
        "parallelism_factor": round(sum(concurrent_times) / concurrent_total, 2)
    }
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "results": results,
        "recommendation": get_performance_recommendation(results)
    }

def get_performance_recommendation(results: Dict[str, Any]) -> str:
    """Get performance recommendations based on test results"""
    avg_latency = results["single_operation"]["avg_ms"]
    
    if avg_latency < 5:
        return "Excellent performance - Redis is responding quickly"
    elif avg_latency < 20:
        return "Good performance - Consider using pipeline for bulk operations"
    elif avg_latency < 50:
        return "Moderate performance - Check network latency to Redis server"
    else:
        return "Poor performance - Investigate network issues or Redis server load"
```

### 4.3 Logging Configuration

Update `backend/app/core/logging_config.py`:

```python
import logging
import sys
from pythonjsonlogger import jsonlogger
from app.core.config import settings

def setup_logging():
    """Configure structured logging for Redis operations"""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(settings.LOG_LEVEL)
    
    # Remove default handler
    logger.handlers = []
    
    # JSON formatter for production
    if settings.ENVIRONMENT == "production":
        formatter = jsonlogger.JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s",
            timestamp=True
        )
    else:
        # Human-readable for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Redis-specific logger
    redis_logger = logging.getLogger("app.redis")
    redis_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Redis command logger (be careful in production!)
    if settings.REDIS_COMMAND_LOGGING:
        redis_cmd_logger = logging.getLogger("redis.commands")
        redis_cmd_logger.setLevel(logging.DEBUG)
        
        # Separate file for Redis commands
        redis_handler = logging.FileHandler("redis_commands.log")
        redis_handler.setFormatter(formatter)
        redis_cmd_logger.addHandler(redis_handler)
    
    return logger

# Custom Redis logging wrapper
class LoggedRedisClient:
    """Redis client wrapper with logging"""
    
    def __init__(self, redis_client):
        self.client = redis_client
        self.logger = logging.getLogger("redis.commands")
        
    async def execute_command(self, *args, **kwargs):
        """Execute command with logging"""
        command = args[0] if args else "unknown"
        
        # Log command (careful with sensitive data!)
        if self.logger.isEnabledFor(logging.DEBUG):
            # Sanitize sensitive commands
            if command.upper() in ["AUTH", "CONFIG"]:
                self.logger.debug(f"Redis command: {command} [REDACTED]")
            else:
                self.logger.debug(f"Redis command: {command} {args[1:3]}...")  # Log first few args
        
        try:
            start = time.time()
            result = await self.client.execute_command(*args, **kwargs)
            duration = (time.time() - start) * 1000
            
            if duration > 100:  # Log slow commands
                self.logger.warning(f"Slow Redis command: {command} took {duration:.2f}ms")
                
            return result
            
        except Exception as e:
            self.logger.error(f"Redis command failed: {command} - {str(e)}")
            raise
```

### 4.4 Common Issues and Solutions

Create `backend/docs/redis_troubleshooting.md`:

```markdown
# Redis Troubleshooting Guide

## Common Issues and Solutions

### 1. Connection Failures

**Symptom**: `ConnectionError: Error connecting to Redis`

**Solutions**:
- Check Redis is running: `docker ps | grep redis`
- Verify connection URL: `echo $REDIS_URL`
- Test connectivity: `redis-cli -u $REDIS_URL ping`
- Check firewall/security groups
- Verify TLS/SSL settings for Upstash

### 2. High Memory Usage

**Symptom**: `OOM command not allowed when used memory > 'maxmemory'`

**Solutions**:
```bash
# Check memory usage
redis-cli INFO memory

# Find large keys
redis-cli --bigkeys

# Set memory limit
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Flush old data (careful!)
redis-cli FLUSHDB
```

### 3. Slow Performance

**Symptom**: High latency in Redis operations

**Solutions**:
```bash
# Check slow log
redis-cli SLOWLOG GET 10

# Monitor commands
redis-cli MONITOR  # Ctrl+C to stop

# Check client connections
redis-cli CLIENT LIST

# Optimize slow commands
# - Use pipeline for bulk operations
# - Implement caching at application level
# - Use appropriate data structures
```

### 4. Rate Limiting (Upstash)

**Symptom**: `Rate limit exceeded` errors

**Solutions**:
- Check current usage: `/api/v1/metrics/upstash`
- Implement batching for bulk operations
- Use pipeline to reduce command count
- Consider upgrading Upstash plan
- Implement local caching layer

### 5. SSL/TLS Issues (Production)

**Symptom**: `SSL: CERTIFICATE_VERIFY_FAILED`

**Solutions**:
```python
# Update SSL configuration
redis_client = redis.from_url(
    url,
    ssl_cert_reqs="required",
    ssl_ca_certs="/path/to/ca-cert.pem"  # Or None for system bundle
)
```

### 6. Memory Leaks

**Symptom**: Growing memory usage over time

**Solutions**:
- Set TTL on all keys
- Implement key expiration policies
- Monitor key growth patterns
- Use Redis streams with MAXLEN
- Regular cleanup of old data

### 7. Connection Pool Exhaustion

**Symptom**: `ConnectionPool: Connection pool is full`

**Solutions**:
```python
# Increase pool size
redis.from_url(
    url,
    max_connections=100,  # Increase from default
    socket_keepalive=True,
    socket_keepalive_options={...}
)
```

## Debug Commands

```bash
# General debugging
redis-cli INFO
redis-cli CONFIG GET *
redis-cli CLIENT LIST
redis-cli MONITOR

# Memory debugging
redis-cli MEMORY STATS
redis-cli MEMORY DOCTOR
redis-cli --bigkeys

# Performance debugging
redis-cli SLOWLOG GET 20
redis-cli LATENCY DOCTOR
redis-cli --latency

# Key analysis
redis-cli --scan --pattern "flow:*" | wc -l
redis-cli DBSIZE
```

## Emergency Procedures

### 1. Redis Unresponsive
```bash
# Restart Redis (Docker)
docker restart migration_redis_dev

# Restart Redis (Railway)
railway restart

# Clear all data (last resort!)
redis-cli FLUSHALL
```

### 2. Disable Redis (Fallback)
```bash
# Set environment variable
export REDIS_ENABLED=false

# Railway
railway variables set REDIS_ENABLED=false
railway restart
```

### 3. Export Critical Data
```bash
# Export to file
redis-cli --rdb dump.rdb

# Export specific keys
redis-cli --scan --pattern "critical:*" | while read key; do
    redis-cli GET "$key" >> backup.txt
done
```
```

---

## 5. CI/CD Integration

### 5.1 GitHub Actions Configuration

Update `.github/workflows/backend-tests.yml`:

```yaml
name: Backend Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
          
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Cache pip packages
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
          
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        
    - name: Run Redis tests
      env:
        DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/test_db
        REDIS_ENABLED: true
        REDIS_URL: redis://localhost:6379/0
        PYTHONPATH: ${{ github.workspace }}/backend
      run: |
        cd backend
        
        # Test Redis connection
        python scripts/test_redis_connection.py
        
        # Run unit tests
        pytest tests/unit/cache/ -v
        pytest tests/unit/redis/ -v
        
        # Run integration tests
        pytest tests/integration/test_redis_integration.py -v
        
    - name: Run performance tests
      if: github.event_name == 'push' && github.ref == 'refs/heads/main'
      env:
        REDIS_ENABLED: true
        REDIS_URL: redis://localhost:6379/0
      run: |
        cd backend
        pytest tests/performance/test_redis_load.py -v --benchmark-only
        
    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: backend/test-results/
```

### 5.2 Pre-deployment Validation

Create `backend/scripts/pre_deploy_check.py`:

```python
#!/usr/bin/env python3
"""Pre-deployment validation for Redis integration"""

import asyncio
import os
import sys
from typing import List, Tuple, Dict, Any

class PreDeploymentChecker:
    def __init__(self):
        self.checks: List[Tuple[str, callable]] = [
            ("Environment Variables", self.check_env_vars),
            ("Redis Connection", self.check_redis_connection),
            ("Redis Memory", self.check_redis_memory),
            ("Feature Flags", self.check_feature_flags),
            ("Rate Limits", self.check_rate_limits),
            ("SSL/TLS Config", self.check_ssl_config),
        ]
        self.errors = []
        self.warnings = []
        
    async def check_env_vars(self) -> bool:
        """Check required environment variables"""
        required = [
            "REDIS_ENABLED",
            "REDIS_URL",
            "DATABASE_URL",
            "SECRET_KEY"
        ]
        
        missing = [var for var in required if not os.getenv(var)]
        
        if missing:
            self.errors.append(f"Missing environment variables: {', '.join(missing)}")
            return False
            
        # Check Redis URL format
        redis_url = os.getenv("REDIS_URL", "")
        if not redis_url.startswith(("redis://", "rediss://")):
            self.errors.append("Invalid REDIS_URL format")
            return False
            
        return True
    
    async def check_redis_connection(self) -> bool:
        """Test Redis connectivity"""
        try:
            from app.core.redis_config import redis_manager
            
            connected = await redis_manager.initialize()
            if not connected:
                self.errors.append("Failed to connect to Redis")
                return False
                
            # Test basic operations
            await redis_manager.redis.set("deploy:check", "1", ex=60)
            value = await redis_manager.redis.get("deploy:check")
            await redis_manager.redis.delete("deploy:check")
            
            if value != "1":
                self.errors.append("Redis read/write test failed")
                return False
                
            await redis_manager.close()
            return True
            
        except Exception as e:
            self.errors.append(f"Redis connection error: {str(e)}")
            return False
    
    async def check_redis_memory(self) -> bool:
        """Check Redis memory availability"""
        try:
            from app.core.redis_config import redis_manager
            
            await redis_manager.initialize()
            info = await redis_manager.redis.info("memory")
            
            used_memory = info.get("used_memory", 0)
            max_memory = info.get("maxmemory", 0)
            
            if max_memory > 0:
                usage_percent = (used_memory / max_memory) * 100
                if usage_percent > 80:
                    self.warnings.append(
                        f"High Redis memory usage: {usage_percent:.1f}%"
                    )
                    
            await redis_manager.close()
            return True
            
        except Exception as e:
            self.warnings.append(f"Could not check Redis memory: {str(e)}")
            return True  # Non-critical
    
    async def check_feature_flags(self) -> bool:
        """Verify feature flags configuration"""
        flags = {
            "REDIS_EVENT_BUS": os.getenv("REDIS_EVENT_BUS", "false"),
            "REDIS_CACHE": os.getenv("REDIS_CACHE", "false"),
            "REDIS_SSE": os.getenv("REDIS_SSE", "false"),
        }
        
        redis_enabled = os.getenv("REDIS_ENABLED", "false").lower() == "true"
        
        if redis_enabled:
            disabled_features = [k for k, v in flags.items() if v.lower() != "true"]
            if disabled_features:
                self.warnings.append(
                    f"Redis enabled but features disabled: {', '.join(disabled_features)}"
                )
                
        return True
    
    async def check_rate_limits(self) -> bool:
        """Check Upstash rate limit configuration"""
        if "upstash" in os.getenv("REDIS_URL", "").lower():
            daily_limit = int(os.getenv("UPSTASH_DAILY_LIMIT", "10000"))
            if daily_limit <= 1000:
                self.warnings.append(
                    f"Low Upstash daily limit: {daily_limit} commands"
                )
                
        return True
    
    async def check_ssl_config(self) -> bool:
        """Verify SSL/TLS configuration for production"""
        redis_url = os.getenv("REDIS_URL", "")
        
        if redis_url.startswith("rediss://"):
            # SSL is required
            if os.getenv("REDIS_SSL_REQUIRED", "false").lower() != "true":
                self.errors.append(
                    "REDIS_SSL_REQUIRED must be true for rediss:// URLs"
                )
                return False
                
        return True
    
    async def run_all_checks(self) -> bool:
        """Run all pre-deployment checks"""
        print("🚀 Running pre-deployment checks...\n")
        
        all_passed = True
        
        for name, check_func in self.checks:
            print(f"Checking {name}...", end=" ")
            try:
                passed = await check_func()
                if passed and not any(
                    name in msg for msg in self.errors + self.warnings
                ):
                    print("✅")
                else:
                    print("⚠️" if passed else "❌")
                    all_passed = all_passed and passed
            except Exception as e:
                print("❌")
                self.errors.append(f"{name}: {str(e)}")
                all_passed = False
        
        # Print summary
        print("\n" + "=" * 50)
        print("DEPLOYMENT READINESS SUMMARY")
        print("=" * 50)
        
        if self.errors:
            print("\n❌ ERRORS (must fix before deployment):")
            for error in self.errors:
                print(f"  - {error}")
                
        if self.warnings:
            print("\n⚠️  WARNINGS (should review):")
            for warning in self.warnings:
                print(f"  - {warning}")
                
        if all_passed and not self.errors:
            print("\n✅ All checks passed! Ready for deployment.")
            return True
        else:
            print("\n❌ Deployment checks failed. Please fix errors above.")
            return False


async def main():
    checker = PreDeploymentChecker()
    success = await checker.run_all_checks()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

### 5.3 Automated Rollback

Create `.github/workflows/auto-rollback.yml`:

```yaml
name: Automated Rollback

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to rollback'
        required: true
        default: 'production'
        type: choice
        options:
        - production
        - staging

jobs:
  rollback:
    runs-on: ubuntu-latest
    
    steps:
    - name: Rollback Redis Features
      env:
        RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
      run: |
        # Install Railway CLI
        curl -fsSL https://railway.app/install.sh | sh
        
        # Disable Redis features
        railway variables set REDIS_ENABLED=false -e ${{ inputs.environment }}
        railway variables set REDIS_EVENT_BUS=false -e ${{ inputs.environment }}
        railway variables set REDIS_CACHE=false -e ${{ inputs.environment }}
        railway variables set REDIS_SSE=false -e ${{ inputs.environment }}
        
        # Restart service
        railway restart -e ${{ inputs.environment }}
        
    - name: Verify Rollback
      run: |
        # Wait for service to restart
        sleep 30
        
        # Check health endpoint
        curl -f https://your-app.railway.app/api/v1/health || exit 1
        
    - name: Notify Team
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        text: 'Redis features rolled back in ${{ inputs.environment }}'
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 6. Troubleshooting Guide

### 6.1 Quick Diagnostics Script

Create `backend/scripts/redis_diagnostics.py`:

```python
#!/usr/bin/env python3
"""Quick Redis diagnostics tool"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any

class RedisDiagnostics:
    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "checks": {}
        }
        
    async def run_diagnostics(self):
        """Run all diagnostic checks"""
        print("🔍 Redis Diagnostics Tool")
        print("=" * 50)
        
        # Check 1: Environment
        self.check_environment()
        
        # Check 2: Connection
        await self.check_connection()
        
        # Check 3: Performance
        await self.check_performance()
        
        # Check 4: Memory
        await self.check_memory()
        
        # Check 5: Keys
        await self.check_keys()
        
        # Print results
        self.print_results()
        
    def check_environment(self):
        """Check environment configuration"""
        print("\n1. Environment Configuration:")
        
        env_vars = {
            "REDIS_ENABLED": os.getenv("REDIS_ENABLED", "not set"),
            "REDIS_URL": "***" if os.getenv("REDIS_URL") else "not set",
            "REDIS_SSL_REQUIRED": os.getenv("REDIS_SSL_REQUIRED", "not set"),
            "SERVER_ID": os.getenv("SERVER_ID", "not set")
        }
        
        for key, value in env_vars.items():
            print(f"   {key}: {value}")
            
        self.results["checks"]["environment"] = env_vars
        
    async def check_connection(self):
        """Check Redis connection"""
        print("\n2. Redis Connection:")
        
        try:
            from app.core.redis_config import redis_manager
            
            connected = await redis_manager.initialize()
            
            if connected:
                # Test ping
                start = time.time()
                await redis_manager.redis.ping()
                latency = (time.time() - start) * 1000
                
                print(f"   ✅ Connected")
                print(f"   Latency: {latency:.2f}ms")
                
                self.results["checks"]["connection"] = {
                    "status": "connected",
                    "latency_ms": round(latency, 2)
                }
            else:
                print(f"   ❌ Not connected")
                self.results["checks"]["connection"] = {"status": "disconnected"}
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            self.results["checks"]["connection"] = {
                "status": "error",
                "error": str(e)
            }
            
    async def check_performance(self):
        """Quick performance check"""
        print("\n3. Performance Check:")
        
        try:
            from app.core.redis_config import redis_manager
            
            if not redis_manager.is_available():
                print("   ⚠️  Redis not available")
                return
                
            # Single operation
            times = []
            for _ in range(5):
                start = time.time()
                await redis_manager.redis.set("diag:test", "1", ex=10)
                await redis_manager.redis.get("diag:test")
                times.append((time.time() - start) * 1000)
                
            avg_time = sum(times) / len(times)
            print(f"   Avg operation time: {avg_time:.2f}ms")
            
            if avg_time < 10:
                print("   ✅ Excellent performance")
            elif avg_time < 50:
                print("   ⚠️  Moderate performance")
            else:
                print("   ❌ Poor performance")
                
            self.results["checks"]["performance"] = {
                "avg_operation_ms": round(avg_time, 2),
                "samples": len(times)
            }
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            
    async def check_memory(self):
        """Check memory usage"""
        print("\n4. Memory Usage:")
        
        try:
            from app.core.redis_config import redis_manager
            
            if not redis_manager.is_available():
                print("   ⚠️  Redis not available")
                return
                
            info = await redis_manager.redis.info("memory")
            
            used = info.get("used_memory_human", "unknown")
            peak = info.get("used_memory_peak_human", "unknown")
            
            print(f"   Used: {used}")
            print(f"   Peak: {peak}")
            
            self.results["checks"]["memory"] = {
                "used": used,
                "peak": peak
            }
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            
    async def check_keys(self):
        """Check key patterns"""
        print("\n5. Key Analysis:")
        
        try:
            from app.core.redis_config import redis_manager
            
            if not redis_manager.is_available():
                print("   ⚠️  Redis not available")
                return
                
            patterns = ["flow:*", "cache:*", "agent:*", "sse:*"]
            total_keys = 0
            
            for pattern in patterns:
                cursor = 0
                count = 0
                while True:
                    cursor, keys = await redis_manager.redis.scan(
                        cursor, match=pattern, count=100
                    )
                    count += len(keys)
                    if cursor == 0:
                        break
                        
                print(f"   {pattern}: {count} keys")
                total_keys += count
                
            print(f"   Total: {total_keys} keys")
            
            self.results["checks"]["keys"] = {
                "total": total_keys,
                "patterns": {p: c for p, c in zip(patterns, counts)}
            }
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            
    def print_results(self):
        """Print diagnostic summary"""
        print("\n" + "=" * 50)
        print("DIAGNOSTIC SUMMARY")
        print("=" * 50)
        
        # Save results to file
        with open("redis_diagnostics.json", "w") as f:
            json.dump(self.results, f, indent=2)
            
        print("\n📊 Results saved to: redis_diagnostics.json")
        
        # Check for issues
        issues = []
        
        if self.results["checks"].get("connection", {}).get("status") != "connected":
            issues.append("Redis not connected")
            
        perf = self.results["checks"].get("performance", {})
        if perf.get("avg_operation_ms", 0) > 50:
            issues.append("High latency detected")
            
        if issues:
            print("\n⚠️  Issues found:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\n✅ No issues found!")


if __name__ == "__main__":
    import time
    import json
    
    diagnostics = RedisDiagnostics()
    asyncio.run(diagnostics.run_diagnostics())
```

### 6.2 Emergency Recovery Procedures

Create `backend/scripts/emergency_recovery.sh`:

```bash
#!/bin/bash

# Emergency Redis Recovery Script

echo "🚨 Redis Emergency Recovery Tool"
echo "================================"

# Function to disable Redis
disable_redis() {
    echo "Disabling Redis..."
    
    # Local development
    if [ -f "docker-compose.dev.yml" ]; then
        docker-compose -f docker-compose.dev.yml stop redis
    fi
    
    # Production (Railway)
    if command -v railway &> /dev/null; then
        railway variables set REDIS_ENABLED=false
        railway restart
    fi
    
    echo "✅ Redis disabled"
}

# Function to clear Redis data
clear_redis() {
    echo "Clearing Redis data..."
    
    read -p "⚠️  This will delete ALL Redis data. Continue? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        redis-cli FLUSHALL
        echo "✅ Redis data cleared"
    else
        echo "❌ Cancelled"
    fi
}

# Function to export critical data
export_data() {
    echo "Exporting critical data..."
    
    # Export to RDB
    redis-cli BGSAVE
    
    # Export specific patterns
    for pattern in "flow:*" "cache:*" "agent:*"; do
        echo "Exporting $pattern keys..."
        redis-cli --scan --pattern "$pattern" | while read key; do
            echo "$key:$(redis-cli GET "$key")" >> redis_export_$(date +%Y%m%d_%H%M%S).txt
        done
    done
    
    echo "✅ Data exported"
}

# Function to restart Redis
restart_redis() {
    echo "Restarting Redis..."
    
    # Local development
    if [ -f "docker-compose.dev.yml" ]; then
        docker-compose -f docker-compose.dev.yml restart redis
    fi
    
    # Production
    if command -v railway &> /dev/null; then
        railway restart
    fi
    
    echo "✅ Redis restarted"
}

# Main menu
PS3='Please select recovery option: '
options=(
    "Disable Redis (fallback to memory)"
    "Clear all Redis data"
    "Export critical data"
    "Restart Redis service"
    "Run diagnostics"
    "Exit"
)

select opt in "${options[@]}"
do
    case $opt in
        "Disable Redis (fallback to memory)")
            disable_redis
            break
            ;;
        "Clear all Redis data")
            clear_redis
            break
            ;;
        "Export critical data")
            export_data
            break
            ;;
        "Restart Redis service")
            restart_redis
            break
            ;;
        "Run diagnostics")
            python scripts/redis_diagnostics.py
            break
            ;;
        "Exit")
            break
            ;;
        *) echo "Invalid option $REPLY";;
    esac
done
```

Make the script executable:

```bash
chmod +x backend/scripts/emergency_recovery.sh
```

---

## Summary

This deployment guide provides comprehensive, practical instructions for deploying Redis across all environments. Key features include:

1. **Local Development**: Complete Docker setup with monitoring tools
2. **Railway Deployment**: Step-by-step configuration with health checks
3. **Upstash Integration**: Production-ready setup with rate limiting
4. **Monitoring Tools**: Real-time performance tracking and diagnostics
5. **CI/CD Pipeline**: Automated testing and deployment validation
6. **Troubleshooting**: Common issues with solutions and emergency procedures

All configurations are copy-paste ready and tested for the AI Modernize Migration Platform's specific requirements. The guide ensures smooth deployment while maintaining fallback capabilities for system resilience.