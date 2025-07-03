#!/bin/bash
# Docker Cleanup Script - Remove old migrate-platform images
# This script safely removes old versions while keeping the latest

set -e

echo "🧹 Docker Image Cleanup for migrate-platform"
echo "==========================================="
echo ""

# Configuration
IMAGE_NAME="migrate-platform"
KEEP_LAST_N=2  # Number of recent images to keep

# Show current images
echo "📊 Current ${IMAGE_NAME} images:"
docker images | grep -E "REPOSITORY|${IMAGE_NAME}" || echo "No ${IMAGE_NAME} images found"
echo ""

# Get all image IDs for migrate-platform, sorted by creation date
echo "🔍 Analyzing images..."
IMAGE_DATA=$(docker images --format "table {{.ID}}\t{{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}\t{{.Size}}" | grep "${IMAGE_NAME}" | grep -v "<none>" || true)

if [ -z "$IMAGE_DATA" ]; then
    echo "No ${IMAGE_NAME} images found to clean up."
    exit 0
fi

# Count total images
TOTAL_IMAGES=$(echo "$IMAGE_DATA" | wc -l)
echo "Found $TOTAL_IMAGES ${IMAGE_NAME} images"

if [ $TOTAL_IMAGES -le $KEEP_LAST_N ]; then
    echo "Only $TOTAL_IMAGES images found. Keeping all (minimum to keep: $KEEP_LAST_N)"
    exit 0
fi

# Get images to remove (all except the most recent N)
IMAGES_TO_REMOVE=$(docker images --format "{{.ID}}\t{{.Repository}}:{{.Tag}}\t{{.CreatedAt}}" | grep "${IMAGE_NAME}" | sort -k3 -r | tail -n +$((KEEP_LAST_N + 1)) | awk '{print $1}')

if [ -z "$IMAGES_TO_REMOVE" ]; then
    echo "No old images to remove."
    exit 0
fi

# Show what will be removed
echo ""
echo "🗑️  Images to be removed (keeping the $KEEP_LAST_N most recent):"
for IMAGE_ID in $IMAGES_TO_REMOVE; do
    docker images | grep "$IMAGE_ID" || true
done

# Ask for confirmation
echo ""
echo "⚠️  This will remove $(echo "$IMAGES_TO_REMOVE" | wc -w) old image(s)."
echo "Continue? (y/N)"
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

# Remove old images
echo ""
echo "🔧 Removing old images..."
for IMAGE_ID in $IMAGES_TO_REMOVE; do
    echo "Removing image: $IMAGE_ID"
    docker rmi "$IMAGE_ID" 2>/dev/null || echo "  ⚠️  Could not remove $IMAGE_ID (may be in use)"
done

# Clean up dangling images
echo ""
echo "🧹 Removing dangling images..."
docker image prune -f

# Show final state
echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Remaining ${IMAGE_NAME} images:"
docker images | grep -E "REPOSITORY|${IMAGE_NAME}" || echo "No ${IMAGE_NAME} images found"

# Show disk space saved
echo ""
echo "💾 Docker disk usage:"
docker system df

# Option for aggressive cleanup
echo ""
echo "🔥 Run aggressive cleanup to remove ALL unused images? (y/N)"
echo "   Warning: This will remove all unused images, not just ${IMAGE_NAME}"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Running aggressive cleanup..."
    docker image prune -a -f
    echo "✅ Aggressive cleanup complete!"
fi