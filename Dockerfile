# AI Modernize Migration Platform - Railway Deployment Dockerfile
# This Dockerfile is specifically for Railway.com deployment

FROM python:3.11-slim-bookworm@sha256:139020233cc412efe4c8135b0efe1c7569dc8b28ddd88bddb109b764f8977e30

# Set working directory
WORKDIR /app

# Force cache invalidation - Updated 2025-07-29
ENV CACHE_BUST=2025-07-29-redis-fix

# Install system dependencies with security updates and version pinning
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        build-essential=12.9 \
        libpq-dev=15.9-0+deb12u1 \
        curl=7.88.1-10+deb12u8 \
        ca-certificates=20230311 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

# Copy backend requirements
COPY backend/requirements-docker.txt requirements.txt

# Install Python dependencies with version pinning
RUN pip install --no-cache-dir --upgrade pip==24.3.1 \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ .

# Copy startup scripts
COPY backend/scripts/deployment/start.sh .
COPY backend/entrypoint.sh .

# Make scripts executable
RUN chmod +x start.sh entrypoint.sh || true

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app \
    && chmod -R 755 /app

# Expose port (Railway will set the PORT environment variable)
EXPOSE 8000

# Health check (simplified for Railway compatibility)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; import os; port=os.getenv('PORT', '8000'); urllib.request.urlopen(f'http://localhost:{port}/health')" || exit 1

# Switch to non-root user
USER appuser

# Start command - use entrypoint.sh which handles migrations
CMD ["./entrypoint.sh"]
