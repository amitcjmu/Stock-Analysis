# Use Python 3.11 for better compatibility with CrewAI - with security updates
FROM python:3.11-slim-bookworm@sha256:139020233cc412efe4c8135b0efe1c7569dc8b28ddd88bddb109b764f8977e30

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Set work directory
WORKDIR /app

# Install system dependencies with security updates
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

# Copy requirements first for better caching
COPY requirements-docker.txt requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-docker.txt

# Copy application code
COPY . .

# Forcefully remove any Python cache files that might have been copied from the host
RUN find . -type d -name "__pycache__" -exec rm -r {} +
RUN find . -type f -name "*.pyc" -delete

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "app"] 