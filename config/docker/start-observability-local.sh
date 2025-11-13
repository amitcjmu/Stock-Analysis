#!/bin/bash
# Start Observability Stack - Local Development
# This script starts the full observability stack for macOS/Windows local development
# with proper Docker socket permissions

set -e

cd "$(dirname "$0")"

echo "🔍 Starting Observability Stack (Local Dev Mode)..."
echo ""

# Load environment variables
if [ ! -f .env.observability ]; then
    echo "❌ Error: .env.observability not found"
    echo "Please copy .env.observability.template and fill in required values"
    exit 1
fi

# Start stack with local overrides
docker-compose \
    -f docker-compose.yml \
    -f docker-compose.observability.yml \
    -f docker-compose.observability.local.yml \
    --env-file .env.observability \
    up -d

echo ""
echo "✅ Observability stack started!"
echo ""
echo "📊 Access Grafana:"
echo "   URL: http://localhost:9999"
echo "   Username: admin"
echo "   Password: (from .env.observability GRAFANA_ADMIN_PASSWORD)"
echo ""
echo "🔧 Other Services:"
echo "   Loki:       http://localhost:3100"
echo "   Tempo:      http://localhost:3200"
echo "   Prometheus: http://localhost:9090"
echo "   Alloy UI:   http://localhost:12345"
echo ""
echo "📝 Check container status:"
echo "   docker ps | grep migration_"
echo ""
echo "⚠️  Note: This uses LOCAL DEV configuration (Alloy runs as root for macOS Docker socket access)"
echo "    For Azure/Railway production, use docker-compose.yml + docker-compose.observability.yml only"
