# Task Brief: devsecops-linting-engineer

## Mission
Ensure the Redis caching implementation meets all security, code quality, and operational standards through comprehensive linting rules, security hardening, and DevOps best practices.

## Context
The caching solution must handle sensitive data securely, maintain code quality standards, and operate reliably in production. Your role is critical for ensuring security compliance and operational excellence.

## Primary Objectives

### 1. Security Hardening (Week 1)
- Configure Redis for production security
- Implement encryption for sensitive cached data
- Set up security scanning for cache-related code
- Create security policies and procedures

### 2. Code Quality Standards (Week 1-2)
- Create linting rules for cache patterns
- Implement pre-commit hooks
- Set up automated code reviews
- Ensure consistent error handling

### 3. Infrastructure Configuration (Week 1)
- Docker configuration for Redis
- Environment variable management
- Monitoring and alerting setup
- Backup and recovery procedures

### 4. CI/CD Integration (Week 2-3)
- Cache testing in CI pipeline
- Security scanning automation
- Performance regression tests
- Deployment procedures

## Specific Deliverables

### Week 1: Security and Infrastructure

```yaml
# File: docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    container_name: migration_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./redis/redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    environment:
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    healthcheck:
      test: ["CMD", "redis-cli", "--pass", "${REDIS_PASSWORD}", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - migration_network
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M

volumes:
  redis_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/redis
```

```conf
# File: redis/redis.conf
# Security Configuration
requirepass ${REDIS_PASSWORD}
bind 127.0.0.1 ::1
protected-mode yes
port 6379

# Persistence
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes

# Memory Management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Security Limits
timeout 300
tcp-keepalive 300
tcp-backlog 511

# Disable Dangerous Commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""
rename-command CONFIG ""

# Logging
loglevel notice
logfile /var/log/redis/redis.log
syslog-enabled yes

# Slow Log
slowlog-log-slower-than 10000
slowlog-max-len 128
```

### Week 1-2: Linting and Code Quality

```python
# File: .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: cache-security-check
        name: Cache Security Check
        entry: python scripts/check_cache_security.py
        language: python
        files: '.*\.(py|ts|tsx)$'
        additional_dependencies: [ast, regex]
      
      - id: cache-key-validation
        name: Cache Key Validation
        entry: python scripts/validate_cache_keys.py
        language: python
        files: '.*cache.*\.(py|ts)$'
      
      - id: sensitive-data-check
        name: Sensitive Data in Cache Check
        entry: python scripts/check_sensitive_cache.py
        language: python
        files: '.*\.(py|ts|tsx)$'

  - repo: https://github.com/python-poetry/poetry
    rev: 1.5.1
    hooks:
      - id: poetry-check
      - id: poetry-lock

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-r', 'backend/', '--skip', 'B101']
        files: '.*cache.*\.py$'
```

```python
# File: scripts/check_cache_security.py
import ast
import sys
from pathlib import Path

class CacheSecurityChecker(ast.NodeVisitor):
    """Check for security issues in cache-related code"""
    
    def __init__(self):
        self.errors = []
        self.current_file = None
    
    def visit_Call(self, node):
        # Check for unencrypted sensitive data in cache
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ['set', 'setex'] and 'cache' in ast.unparse(node.func.value):
                # Check if sensitive data is being cached without encryption
                for arg in node.args:
                    if self._contains_sensitive_field(arg):
                        self.errors.append({
                            'file': self.current_file,
                            'line': node.lineno,
                            'error': 'Sensitive data must be encrypted before caching'
                        })
        
        self.generic_visit(node)
    
    def _contains_sensitive_field(self, node):
        """Check if node contains sensitive fields"""
        sensitive_fields = ['password', 'token', 'secret', 'ssn', 'credit_card']
        node_str = ast.unparse(node).lower()
        return any(field in node_str for field in sensitive_fields)

def main():
    checker = CacheSecurityChecker()
    
    for file_path in Path('backend').rglob('*.py'):
        with open(file_path, 'r') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
            checker.current_file = str(file_path)
            checker.visit(tree)
    
    if checker.errors:
        for error in checker.errors:
            print(f"{error['file']}:{error['line']}: {error['error']}")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

### Week 2-3: Monitoring and CI/CD

```yaml
# File: .github/workflows/cache-security.yml
name: Cache Security Checks

on:
  pull_request:
    paths:
      - '**/*cache*'
      - 'backend/app/services/caching/**'
      - 'src/hooks/**/*cache*'

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install bandit safety semgrep
          
      - name: Run Bandit Security Scan
        run: |
          bandit -r backend/ -f json -o bandit-report.json || true
          python scripts/analyze_bandit_cache.py bandit-report.json
      
      - name: Run Semgrep Cache Rules
        run: |
          semgrep --config=scripts/semgrep/cache-rules.yml backend/
      
      - name: Check for hardcoded secrets
        run: |
          pip install detect-secrets
          detect-secrets scan --all-files --force-use-all-plugins

  performance-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Cache Performance Tests
        run: |
          docker compose up -d
          npm run test:cache:performance
          
      - name: Check Performance Regression
        run: |
          python scripts/check_performance_regression.py
```

```python
# File: scripts/monitoring/cache_monitor.py
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge
import logging
import asyncio
from typing import Dict, Any

# Metrics
cache_operations = Counter(
    'redis_cache_operations_total',
    'Total cache operations',
    ['operation', 'status', 'cache_type']
)

cache_latency = Histogram(
    'redis_cache_latency_seconds',
    'Cache operation latency',
    ['operation', 'cache_type']
)

cache_size = Gauge(
    'redis_cache_size_bytes',
    'Current cache size in bytes',
    ['cache_type']
)

cache_hit_rate = Gauge(
    'redis_cache_hit_rate',
    'Cache hit rate percentage',
    ['endpoint', 'cache_type']
)

security_violations = Counter(
    'redis_cache_security_violations_total',
    'Security violations detected',
    ['violation_type', 'severity']
)

class CacheMonitor:
    """Monitor cache operations for security and performance"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.logger = logging.getLogger(__name__)
    
    async def monitor_cache_operation(self, operation: str, cache_key: str, 
                                    data: Any = None) -> Dict[str, Any]:
        """Monitor and validate cache operations"""
        
        # Security checks
        if not self._validate_cache_key(cache_key):
            security_violations.labels(
                violation_type='invalid_key_format',
                severity='high'
            ).inc()
            raise ValueError(f"Invalid cache key format: {cache_key}")
        
        if data and not self._validate_data_security(data):
            security_violations.labels(
                violation_type='unencrypted_sensitive_data',
                severity='critical'
            ).inc()
            raise ValueError("Sensitive data must be encrypted")
        
        # Monitor operation
        with cache_latency.labels(
            operation=operation,
            cache_type='redis'
        ).time():
            result = await self._execute_operation(operation, cache_key, data)
        
        # Update metrics
        cache_operations.labels(
            operation=operation,
            status='success' if result['success'] else 'failure',
            cache_type='redis'
        ).inc()
        
        return result
    
    def _validate_cache_key(self, key: str) -> bool:
        """Validate cache key format and security"""
        # Must include version
        if not key.startswith('v'):
            return False
        
        # Must include tenant context for user data
        if 'user:' in key and 'tenant:' not in key:
            return False
        
        # No dangerous characters
        if any(char in key for char in ['*', '?', '[', ']']):
            return False
        
        return True
    
    def _validate_data_security(self, data: Any) -> bool:
        """Check if sensitive data is properly encrypted"""
        if isinstance(data, dict):
            sensitive_fields = ['password', 'token', 'secret', 'ssn']
            for field in sensitive_fields:
                if field in str(data).lower() and not self._is_encrypted(data):
                    return False
        return True
    
    def _is_encrypted(self, data: Any) -> bool:
        """Check if data appears to be encrypted"""
        # Simple check - in production, verify actual encryption
        return isinstance(data, dict) and 'encrypted' in data
```

### Environment Configuration

```bash
# File: .env.production
# Redis Configuration
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_MAX_RETRIES=3
REDIS_RETRY_DELAY=1000
REDIS_CONNECTION_TIMEOUT=5000
REDIS_ENABLE_TLS=true
REDIS_TLS_CERT_PATH=/certs/redis.crt
REDIS_TLS_KEY_PATH=/certs/redis.key

# Cache Configuration
CACHE_DEFAULT_TTL=300
CACHE_MAX_TTL=3600
CACHE_VERSION=v1
CACHE_ENABLE_ENCRYPTION=true
CACHE_ENCRYPTION_KEY=${CACHE_ENCRYPTION_KEY}

# Monitoring
ENABLE_CACHE_METRICS=true
PROMETHEUS_METRICS_PORT=9090
CACHE_SLOW_LOG_THRESHOLD=50
```

## Security Policies

### 1. Data Classification
- **Public**: Can be cached without encryption (e.g., public configurations)
- **Internal**: Must be cached with tenant isolation
- **Confidential**: Must be encrypted before caching
- **Restricted**: Must never be cached

### 2. Key Management
- Encryption keys rotated monthly
- Keys stored in secure vault (not in code)
- Separate keys per environment
- Key access audited

### 3. Access Control
- Redis ACL configured per service
- Least privilege principle
- Regular access reviews
- Audit logging enabled

## Success Criteria
- Zero security vulnerabilities in scans
- 100% compliance with linting rules
- All sensitive data encrypted
- Monitoring alerts configured
- Backup/recovery tested

## Communication
- Daily security scan results
- Weekly security posture review
- Immediate escalation of vulnerabilities
- Monthly security metrics report

## Timeline
- Week 1: Infrastructure and security setup
- Week 2: Linting rules and pre-commit hooks
- Week 3: CI/CD and monitoring
- Ongoing: Security monitoring and updates

---
**Assigned by**: Claude Code (Orchestrator)
**Start Date**: Immediate
**Priority**: Critical for security