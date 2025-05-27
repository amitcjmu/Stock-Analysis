# AI Force Migration Platform - Railway Deployment Dockerfile
# This Dockerfile is specifically for Railway.com deployment

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements-docker.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/ .

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app

# Expose port (Railway will set the PORT environment variable)
EXPOSE 8000

# Health check (using python instead of curl for non-root user)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Switch to non-root user
USER appuser

# Start command (Railway will override this with the PORT variable)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 