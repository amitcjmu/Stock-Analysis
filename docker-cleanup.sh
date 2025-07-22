#!/bin/bash

echo "=== Docker and Application Cache Cleanup ==="
echo "Current disk usage:"
df -h | grep -E "/$|/System/Volumes/Data"

echo -e "\n=== Cleaning Application Caches ==="

# 1. Clean Playwright browsers cache (1.8GB)
echo -e "\n1. Cleaning Playwright browsers cache..."
rm -rf ~/Library/Caches/ms-playwright/*
echo "   Cleaned: ~/Library/Caches/ms-playwright"

# 2. Clean pip cache (495MB)
echo -e "\n2. Cleaning pip cache..."
rm -rf ~/Library/Caches/pip/*
pip cache purge 2>/dev/null || echo "   pip cache purge failed"

# 3. Clean npm/yarn caches
echo -e "\n3. Cleaning npm/yarn caches..."
npm cache clean --force 2>/dev/null
rm -rf ~/.npm/_cacache/*

# 4. Clean node-gyp cache
echo -e "\n4. Cleaning node-gyp cache..."
rm -rf ~/Library/Caches/node-gyp/*

# 5. Clean TypeScript cache
echo -e "\n5. Cleaning TypeScript cache..."
rm -rf ~/Library/Caches/typescript/*

# 6. Project-specific cleanup
echo -e "\n6. Cleaning project-specific items..."
# Clean test results
rm -rf ./test-results/*
# Clean temp files
rm -rf ./temp/*
# Clean dist if not needed
rm -rf ./dist/*

echo -e "\n=== Docker Cleanup (when Docker is responsive) ==="
echo "Attempting to clean Docker resources..."

# Check if Docker is running
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "Docker is running. Performing cleanup..."
    
    # Stop all containers
    docker stop $(docker ps -aq) 2>/dev/null || echo "No containers to stop"
    
    # Remove all stopped containers
    docker container prune -f
    
    # Remove all unused images
    docker image prune -a -f
    
    # Remove all unused volumes
    docker volume prune -f
    
    # Remove build cache
    docker builder prune -a -f
    
    # Full system prune
    docker system prune -a -f --volumes
    
    echo "Docker cleanup completed!"
else
    echo "Docker is not responsive. Here are manual steps:"
    echo "1. Quit Docker Desktop completely"
    echo "2. Delete Docker.raw file to reclaim space:"
    echo "   rm ~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw"
    echo "3. Restart Docker Desktop (it will recreate a smaller Docker.raw)"
fi

echo -e "\n=== Dockerfile Optimization for smaller images ==="
cat > Dockerfile.optimized << 'EOF'
# Example optimized Dockerfile for Node.js app
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
# Remove unnecessary files
RUN rm -rf .git .github docs tests *.md

# Example optimized Dockerfile for Python app
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
EOF

echo -e "\n=== Create .dockerignore file ==="
cat > .dockerignore << 'EOF'
# Version control
.git
.gitignore

# Dependencies
node_modules
venv
__pycache__
*.pyc

# IDE
.vscode
.idea

# Testing
coverage
.coverage
.pytest_cache
test-results

# Logs
*.log
logs

# OS
.DS_Store
Thumbs.db

# Build artifacts
dist
build
*.egg-info

# Documentation
docs
*.md

# Environment
.env
.env.*

# Temporary files
temp
tmp
*.tmp
EOF

echo -e "\n=== Space Saved Summary ==="
echo "Cleaned:"
echo "- Playwright browsers cache: ~1.8GB"
echo "- pip cache: ~495MB"
echo "- node-gyp cache: ~107MB"
echo "- TypeScript cache: ~103MB"
echo "- Project temp/test files: ~38MB"
echo "- Docker (if successful): up to 37GB"
echo ""
echo "New disk usage:"
df -h | grep -E "/$|/System/Volumes/Data"