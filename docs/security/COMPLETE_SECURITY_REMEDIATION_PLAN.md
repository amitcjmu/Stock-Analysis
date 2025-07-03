# Complete Security Remediation Plan

## Overview
This plan addresses both **application security** (code vulnerabilities) and **container security** (Docker/dependency vulnerabilities).

## 1. Container Vulnerabilities (Docker Scan Results)

### Current Issues:
- **217 vulnerabilities** in container (4 Critical, 44 High)
- Base image (Debian) has unpatched CVEs
- PostgreSQL 16 client libraries have vulnerabilities
- Python packages with known CVEs

### Remediation Steps:

#### Immediate (Day 1):
```bash
# 1. Update base image to latest patched version
docker pull python:3.11-slim-bookworm

# 2. Update Dockerfile to use specific digest
FROM python:3.11-slim-bookworm@sha256:[latest-secure-digest]

# 3. Add security updates in Dockerfile
RUN apt-get update && apt-get upgrade -y

# 4. Run the container hardening script
./scripts/security/fix_container_vulnerabilities.sh
```

#### Short-term (Week 1):
1. **Use Multi-stage builds** to reduce attack surface
2. **Pin all package versions** in requirements.txt
3. **Remove unnecessary system packages**
4. **Implement regular image rebuilds** (weekly)
5. **Enable Docker Content Trust**
   ```bash
   export DOCKER_CONTENT_TRUST=1
   ```

#### Container Security Best Practices:
```dockerfile
# Use specific base image version
FROM python:3.11-slim-bookworm@sha256:specific-digest

# Update packages immediately
RUN apt-get update && apt-get upgrade -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install only what's needed
RUN apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Run as non-root user
USER appuser

# Drop capabilities
RUN setcap -r /usr/local/bin/python3.11

# Read-only root filesystem
# Add to docker-compose.yml:
# read_only: true
# tmpfs:
#   - /tmp
```

## 2. Application Security (Code Scan Results)

### Critical Issues to Fix:

#### Day 1 - Hardcoded Secrets:
```python
# BEFORE (config.py:71)
SECRET_KEY: str = "your-secret-key-here"

# AFTER
SECRET_KEY: str = Field(default=None, env='SECRET_KEY')

# Add validation
@validator('SECRET_KEY')
def validate_secret_key(cls, v):
    if not v:
        raise ValueError("SECRET_KEY must be set")
    if len(v) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters")
    return v
```

#### Day 2 - SQL Injection:
```python
# BEFORE (VULNERABLE)
result = bind.execute(text(f"SELECT to_regclass('{table}')"))

# AFTER (SAFE)
result = bind.execute(
    text("SELECT to_regclass(:table)"),
    {"table": table}
)

# Or use SQLAlchemy properly
from sqlalchemy import select, table
result = session.execute(select(table(table_name)))
```

#### Day 3 - Authentication:
```python
# Implement proper JWT
from app.core.auth.jwt_handler import JWTHandler

jwt_handler = JWTHandler(settings.JWT_SECRET_KEY)
token = jwt_handler.create_access_token(
    data={"sub": user.email},
    expires_delta=timedelta(minutes=30)
)
```

## 3. CI/CD Security Integration

### GitHub Actions Workflow:
```yaml
name: Security Check
on: [push, pull_request]

jobs:
  code-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run security scan
        run: |
          pip install bandit safety
          bandit -r backend/
          safety check -r backend/requirements.txt
          
  container-security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build image
        run: docker build -t myapp:test .
      - name: Run Trivy scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'myapp:test'
          exit-code: '1'
          severity: 'CRITICAL,HIGH'
```

### Pre-commit Hooks:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pycqa/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-ll', '-i']
        
  - repo: local
    hooks:
      - id: no-secrets
        name: Detect secrets
        entry: ./scripts/security/check_credentials.py
        language: python
        files: \.(py|yml|yaml|json)$
```

## 4. Security Monitoring

### Container Registry Scanning:
1. **Enable Docker Hub scanning** (if using Docker Hub)
2. **Use Amazon ECR scanning** (if on AWS)
3. **Harbor with Trivy** (self-hosted option)

### Runtime Security:
```yaml
# docker-compose.yml security options
services:
  backend:
    security_opt:
      - no-new-privileges:true
      - seccomp:unconfined
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
```

## 5. Automated Remediation

### Daily Security Updates:
```bash
#!/bin/bash
# cron job: 0 2 * * * /path/to/security-update.sh

# Update base image
docker pull python:3.11-slim-bookworm

# Rebuild with latest security patches
docker build --no-cache -t myapp:latest .

# Scan for vulnerabilities
docker run --rm aquasec/trivy image myapp:latest

# Deploy if clean
if [ $? -eq 0 ]; then
    docker push myapp:latest
fi
```

## 6. Security Checklist

### Before Deployment:
- [ ] All hardcoded secrets removed
- [ ] SQL injection vulnerabilities fixed
- [ ] Container image scanned and patched
- [ ] Base image updated to latest
- [ ] Unnecessary packages removed
- [ ] Running as non-root user
- [ ] Security headers configured
- [ ] Rate limiting implemented
- [ ] JWT with expiration
- [ ] Input validation on all endpoints

### Ongoing Security:
- [ ] Weekly base image updates
- [ ] Monthly dependency updates
- [ ] Quarterly security audits
- [ ] Automated vulnerability scanning
- [ ] Security training for developers

## 7. Tools Integration

### Local Development:
```bash
# Before every commit
pre-commit run --all-files

# Weekly security check
./scripts/security/run_security_scan_local.sh
```

### CI/CD Pipeline:
- **Code scanning**: Bandit, Semgrep, SonarQube
- **Dependency scanning**: Safety, Snyk, pip-audit
- **Container scanning**: Trivy, Grype, Clair
- **Secret detection**: Gitleaks, TruffleHog

### Production Monitoring:
- **Runtime protection**: Falco, Sysdig
- **Vulnerability management**: Qualys, Rapid7
- **Compliance scanning**: OpenSCAP, InSpec

## Summary

To fix the Docker vulnerabilities shown in your screenshot:

1. **Update the base image** - Most CVEs are in the Debian base
2. **Apply security updates** - Run `apt-get upgrade` in Dockerfile
3. **Use minimal images** - Consider Alpine or distroless
4. **Pin package versions** - Avoid unexpected vulnerable updates
5. **Regular rebuilds** - Automate weekly image rebuilds with patches

The container vulnerabilities are **separate** from code vulnerabilities and require different remediation approaches. Both need to be addressed for comprehensive security.