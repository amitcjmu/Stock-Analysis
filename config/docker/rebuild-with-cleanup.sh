#!/bin/bash
# Docker Rebuild with Automatic Cleanup
# Prevents disk space issues by pruning unused Docker resources after rebuild

set -e  # Exit on error

echo "🐳 Starting Docker rebuild with cleanup..."
echo ""

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Step 1: Stop containers
echo "📦 Step 1/5: Stopping containers..."
docker-compose down
echo "✅ Containers stopped"
echo ""

# Step 2: Rebuild and start
echo "🔨 Step 2/5: Rebuilding and starting containers..."
docker-compose up --build -d
echo "✅ Containers rebuilt and started"
echo ""

# Step 3: Prune unused volumes (WARNING: Only removes UNUSED volumes)
echo "🗑️  Step 3/5: Pruning unused Docker volumes..."
docker volume prune -f
echo "✅ Unused volumes pruned"
echo ""

# Step 4: Prune build cache
echo "🗑️  Step 4/5: Pruning Docker build cache..."
docker builder prune -f
echo "✅ Build cache pruned"
echo ""

# Step 5: Remove dangling images
echo "🗑️  Step 5/5: Removing dangling images..."
docker image prune -f
echo "✅ Dangling images removed"
echo ""

# Show disk space saved
echo "💾 Docker disk usage summary:"
docker system df
echo ""

# Show running containers
echo "🚀 Running containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "✅ Docker rebuild with cleanup complete!"
echo ""
echo "📝 Note: This script only removes UNUSED Docker resources."
echo "   Active volumes and images are preserved."
