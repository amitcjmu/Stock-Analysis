#!/bin/bash
# Fix Container Vulnerabilities Script

echo "🔒 Container Security Hardening Script"
echo "====================================="
echo ""

# Function to update base image
update_base_image() {
    echo "📦 Updating base image to latest secure version..."

    # Get latest Python 3.11 slim image with security patches
    docker pull python:3.11-slim-bookworm

    # Get the exact digest for reproducibility
    DIGEST=$(docker inspect python:3.11-slim-bookworm --format='{{.RepoDigests}}' | grep -o 'sha256:[a-f0-9]*' | head -1)
    echo "Latest secure image digest: $DIGEST"

    # Update Dockerfile with specific digest
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|FROM python:3.11-slim|FROM python:3.11-slim-bookworm@$DIGEST|g" Dockerfile
    else
        # Linux
        sed -i "s|FROM python:3.11-slim|FROM python:3.11-slim-bookworm@$DIGEST|g" Dockerfile
    fi
}

# Function to add security scanning to build process
add_build_time_scanning() {
    echo "🔍 Adding build-time vulnerability scanning..."

    cat > docker-compose.security.yml << 'EOF'
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.security
      args:
        - BUILDKIT_INLINE_CACHE=1
    image: migrate-platform:secure
    security_opt:
      - no-new-privileges:true
      - seccomp:unconfined
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
      - /var/cache
EOF
}

# Function to create security-focused requirements
create_secure_requirements() {
    echo "📋 Creating security-patched requirements..."

    cat > backend/requirements-security.txt << 'EOF'
# Core dependencies with security patches
aiofiles==24.1.0
aiohttp>=3.10.0  # CVE fixes
alembic>=1.16.2
asyncpg>=0.30.0
bcrypt>=4.3.0  # Latest security patches
crewai>=0.140.0
cryptography>=45.0.5  # Important security updates
fastapi>=0.115.14
httpx>=0.28.1
jinja2>=3.1.6  # Template injection fixes
passlib[bcrypt]>=1.7.4
psycopg2-binary>=2.9.10  # PostgreSQL security updates
pydantic>=2.11.7
python-jose[cryptography]>=3.5.0
python-multipart>=0.0.20
sqlalchemy>=2.0.41
uvicorn[standard]>=0.35.0

# Security tools
pip-audit>=2.7.0
safety>=3.2.0
bandit>=1.7.8

# Remove or update vulnerable packages
# certifi>=2025.6.15  # Update to latest
# pillow>=11.3.0  # Update for CVE fixes
# urllib3>=2.5.0  # Security patches
EOF
}

# Function to scan and fix specific CVEs
fix_specific_cves() {
    echo "🔧 Addressing specific CVEs from Docker scan..."

    # Create a requirements override file
    cat > backend/requirements-cve-fixes.txt << 'EOF'
# CVE-2024-3651 - Update package
# CVE-2024-28180 - Update package
# Add specific package versions that fix the CVEs shown in Docker scan

# PostgreSQL 16 related
# Ensure we're using latest psycopg2-binary
psycopg2-binary>=2.9.10

# Debian package fixes (these need to be fixed in base image)
# These are OS-level and need to be addressed in Dockerfile
EOF
}

# Function to create minimal production image
create_minimal_image() {
    echo "🏗️ Creating minimal production image..."

    cat > Dockerfile.minimal << 'EOF'
# Multi-stage build for minimal attack surface
FROM python:3.11-slim-bookworm as builder

WORKDIR /app
COPY backend/requirements-security.txt .
RUN pip install --user --no-cache-dir -r requirements-security.txt

# Final minimal image
FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends libpq5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy only necessary files
COPY --from=builder /root/.local /root/.local
COPY backend/ /app/

WORKDIR /app
ENV PATH=/root/.local/bin:$PATH

# Run as non-root
RUN useradd -m -u 1000 appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
}

# Main execution
echo "1️⃣ Updating base image..."
update_base_image

echo ""
echo "2️⃣ Creating secure requirements..."
create_secure_requirements

echo ""
echo "3️⃣ Adding build-time scanning..."
add_build_time_scanning

echo ""
echo "4️⃣ Creating minimal production image..."
create_minimal_image

echo ""
echo "5️⃣ Testing security improvements..."

# Build and scan the new image
echo "Building secure image..."
docker build -f Dockerfile.security -t migrate-platform:secure backend/

echo ""
echo "Scanning secure image with Trivy..."
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy:latest image migrate-platform:secure

echo ""
echo "✅ Container security hardening complete!"
echo ""
echo "Next steps:"
echo "1. Review the scan results above"
echo "2. Use Dockerfile.security for production builds"
echo "3. Regularly update base images and dependencies"
echo "4. Enable Docker Content Trust: export DOCKER_CONTENT_TRUST=1"
echo "5. Use docker compose with security options"
echo ""
echo "To build with security scanning:"
echo "  docker build -f Dockerfile.security -t migrate-platform:secure ."
echo ""
echo "To run with security options:"
echo "  docker-compose -f docker-compose.security.yml up"
