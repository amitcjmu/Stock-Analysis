#!/bin/bash
# Docker Build with Automatic Cleanup Script
# Builds the image and removes old versions to save space

set -e

echo "🐳 Docker Build with Auto-Cleanup"
echo "================================"
echo ""

# Configuration
IMAGE_NAME="${IMAGE_NAME:-migrate-platform}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DOCKERFILE="${DOCKERFILE:-Dockerfile}"
BUILD_CONTEXT="${BUILD_CONTEXT:-.}"

# Get current image ID before build (if exists)
OLD_IMAGE_ID=$(docker images -q ${IMAGE_NAME}:${IMAGE_TAG} 2>/dev/null || true)

echo "📦 Current image info:"
if [ -n "$OLD_IMAGE_ID" ]; then
    docker images ${IMAGE_NAME}:${IMAGE_TAG}
    echo "Old image ID: $OLD_IMAGE_ID"
else
    echo "No existing image found for ${IMAGE_NAME}:${IMAGE_TAG}"
fi
echo ""

# Build new image
echo "🔨 Building new image..."
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "Dockerfile: ${DOCKERFILE}"
echo ""

docker build \
    -f "${DOCKERFILE}" \
    -t "${IMAGE_NAME}:${IMAGE_TAG}" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    "${BUILD_CONTEXT}"

# Get new image ID
NEW_IMAGE_ID=$(docker images -q ${IMAGE_NAME}:${IMAGE_TAG})
echo ""
echo "✅ Build completed successfully!"
echo "New image ID: $NEW_IMAGE_ID"

# No additional tags needed - keeping only latest for minimal setup
# Comment out to avoid creating extra tags
# echo ""
# echo "🏷️  Tagging image..."
# docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${IMAGE_NAME}:secure"
# docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${IMAGE_NAME}:$(date +%Y%m%d)"

# Clean up old images
echo ""
echo "🧹 Cleaning up old images..."

# Remove old image if it's different from the new one
if [ -n "$OLD_IMAGE_ID" ] && [ "$OLD_IMAGE_ID" != "$NEW_IMAGE_ID" ]; then
    echo "Removing old image: $OLD_IMAGE_ID"
    docker rmi "$OLD_IMAGE_ID" 2>/dev/null || echo "Note: Old image may be in use or already removed"
fi

# Remove dangling images (untagged)
echo "Removing dangling images..."
docker image prune -f

# Optional: Remove all unused images (commented out by default)
# echo "Remove ALL unused images? (y/N)"
# read -r response
# if [[ "$response" =~ ^[Yy]$ ]]; then
#     docker image prune -a -f
# fi

# Show final state
echo ""
echo "📊 Current Docker images:"
docker images | grep -E "REPOSITORY|${IMAGE_NAME}" | head -10

# Show disk usage
echo ""
echo "💾 Docker disk usage:"
docker system df

# Security scan option
echo ""
echo "🔒 Run security scan? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    if command -v docker scout &> /dev/null; then
        echo "Running Docker Scout security scan..."
        docker scout cves "${IMAGE_NAME}:${IMAGE_TAG}"
    else
        echo "Docker Scout not available. Install Docker Desktop for security scanning."
    fi
fi

echo ""
echo "✨ Build and cleanup complete!"
echo ""
echo "To use the new image:"
echo "  docker run -p 8000:8000 ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "To remove specific old images manually:"
echo "  docker images | grep ${IMAGE_NAME}"
echo "  docker rmi <image-id>"