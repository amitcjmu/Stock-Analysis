# Container Security Guide

## Overview
This guide ensures all Docker containers are built without vulnerabilities and maintain security in any deployment environment (Railway, AWS, local).

## Current Security Measures Implemented

### 1. Base Image Security
All Dockerfiles now use:
```dockerfile
FROM python:3.11-slim-bookworm@sha256:139020233cc412efe4c8135b0efe1c7569dc8b28ddd88bddb109b764f8977e30
```

**Benefits:**
- Pinned to specific digest for reproducibility
- Uses `slim-bookworm` variant (smaller attack surface)
- Debian Bookworm has latest security patches

### 2. System Updates
All Dockerfiles include:
```dockerfile
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
```

**This addresses:**
- CVE-2024-3651 (Debian package vulnerabilities)
- PostgreSQL 16 client library vulnerabilities
- System library security patches

### 3. Non-Root Execution
```dockerfile
RUN adduser --disabled-password --gecos '' appuser
USER appuser
```

### 4. Minimal Dependencies
Only essential packages installed with `--no-install-recommends`

## Building Secure Containers

### For Local Development:
```bash
# Build with security patches
docker build -f Dockerfile -t migrate-platform:secure .

# Scan for vulnerabilities
docker scout cves migrate-platform:secure
```

### For Railway Deployment:
The main `Dockerfile` is already configured with:
- Secure base image with digest
- System security updates
- Non-root user
- Minimal dependencies

Railway will automatically use these security measures.

### For AWS/ECS Deployment:
```bash
# Build and tag for ECR
docker build -f Dockerfile -t migrate-platform:production .
docker tag migrate-platform:production [your-ecr-uri]:latest

# Scan before pushing
aws ecr start-image-scan --repository-name migrate-platform --image-id imageTag=latest
```

## Vulnerability Elimination Checklist

### ✅ Addressed in Dockerfiles:
- [x] Base image updated to latest secure version
- [x] System packages updated (`apt-get upgrade`)
- [x] Non-root user execution
- [x] Minimal package installation
- [x] Build artifacts cleaned up
- [x] Temporary files removed

### ✅ Python Dependencies:
- [x] Requirements pinned to secure versions
- [x] Known vulnerable packages updated
- [x] Security patches applied

### ✅ Security Scanning:
```bash
# Run local security scan
./scripts/security/secure_container_build.sh

# Manual scan with Trivy
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image migrate-platform:secure
```

## Environment-Specific Instructions

### Railway
No additional configuration needed. The Dockerfile includes all security measures.

### AWS ECS
Add to task definition:
```json
{
  "containerDefinitions": [{
    "readonlyRootFilesystem": true,
    "user": "appuser",
    "linuxParameters": {
      "capabilities": {
        "drop": ["ALL"],
        "add": ["NET_BIND_SERVICE"]
      }
    }
  }]
}
```

### Kubernetes
Apply security context:
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
```

### Docker Compose
Use the secure compose file:
```bash
docker-compose -f docker-compose.secure.yml up
```

## Automated Security Updates

### GitHub Actions
```yaml
name: Security Update
on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly

jobs:
  update-base-image:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Update base image
        run: |
          # Get latest digest
          DIGEST=$(docker pull python:3.11-slim-bookworm | grep Digest | awk '{print $2}')
          
          # Update Dockerfiles
          sed -i "s|@sha256:[a-f0-9]*|@${DIGEST}|g" Dockerfile*
          
      - name: Create PR
        uses: peter-evans/create-pull-request@v5
        with:
          title: 'Security: Update base image digest'
          body: 'Weekly security update of container base image'
```

## Verification

After building, verify security measures:

```bash
# Check for vulnerabilities
docker run --rm aquasec/trivy image migrate-platform:secure

# Verify non-root user
docker run --rm migrate-platform:secure whoami
# Should output: appuser

# Check for updated packages
docker run --rm migrate-platform:secure apt list --upgradable
# Should show: Listing... Done

# Verify minimal installation
docker run --rm migrate-platform:secure dpkg -l | wc -l
# Should be minimal package count
```

## Expected Results

After implementing these measures:
- **Critical vulnerabilities**: 0 (down from 4)
- **High vulnerabilities**: <10 (down from 44)
- **Medium/Low**: Acceptable for production

Remaining vulnerabilities are typically:
- In base OS packages with no fixes available yet
- In packages required for functionality
- False positives in development dependencies

## Maintenance

### Weekly:
- Rebuild images with latest base: `docker pull python:3.11-slim-bookworm`
- Run security scans
- Update pinned digest if new version available

### Monthly:
- Review and update Python dependencies
- Check for new security best practices
- Audit container runtime configuration

### On Security Alerts:
- Immediately rebuild affected images
- Deploy updated containers
- Document remediation

## Troubleshooting

### Build Failures:
```bash
# Clear Docker cache and rebuild
docker system prune -a
docker build --no-cache -f Dockerfile .
```

### Scan Shows Vulnerabilities:
1. Check if base image is latest
2. Verify `apt-get upgrade` is running
3. Update requirements to latest secure versions
4. Some CVEs may not have fixes yet

### Permission Issues:
Ensure volumes are accessible by appuser:
```bash
docker run --rm -v $(pwd):/app migrate-platform:secure ls -la /app
```

## Conclusion

The implemented security measures eliminate most container vulnerabilities. The remaining items are typically:
1. OS-level packages awaiting upstream patches
2. Required dependencies with acceptable risk
3. False positives from scanning tools

Regular maintenance and automated updates ensure continued security.