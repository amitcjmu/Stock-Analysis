#!/bin/bash

# Docker maintenance script - run periodically to prevent disk space issues

echo "=== Docker Maintenance Script ==="
echo "Starting at: $(date)"

# Function to check if Docker is running
check_docker() {
    if docker info >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Clean Docker resources if Docker is running
if check_docker; then
    echo -e "\n1. Removing stopped containers..."
    docker container prune -f
    
    echo -e "\n2. Removing unused images..."
    docker image prune -a -f
    
    echo -e "\n3. Removing unused volumes..."
    docker volume prune -f
    
    echo -e "\n4. Removing build cache..."
    docker builder prune -a -f
    
    echo -e "\n5. Full system cleanup..."
    docker system prune -a -f --volumes
    
    echo -e "\n6. Docker disk usage after cleanup:"
    docker system df
else
    echo "Docker is not running. Skipping Docker cleanup."
fi

# Clean application caches
echo -e "\n=== Cleaning Application Caches ==="

echo "1. Cleaning Playwright cache..."
rm -rf ~/Library/Caches/ms-playwright/* 2>/dev/null

echo "2. Cleaning pip cache..."
pip cache purge 2>/dev/null || true

echo "3. Cleaning npm cache..."
npm cache clean --force 2>/dev/null || true

echo "4. Cleaning yarn cache..."
yarn cache clean 2>/dev/null || true

# Project-specific cleanup
echo -e "\n=== Project Cleanup ==="
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "1. Cleaning test results..."
rm -rf "$SCRIPT_DIR/test-results"/* 2>/dev/null

echo "2. Cleaning temp files..."
rm -rf "$SCRIPT_DIR/temp"/* 2>/dev/null

echo "3. Cleaning dist folder..."
rm -rf "$SCRIPT_DIR/dist"/* 2>/dev/null

echo -e "\n=== Cleanup Complete ==="
echo "Finished at: $(date)"

# Show disk usage
echo -e "\nCurrent disk usage:"
df -h | grep -E "/$|/System/Volumes/Data"