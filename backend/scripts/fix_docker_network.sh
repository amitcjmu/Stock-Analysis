#!/bin/bash

# Docker Network Fix Script
# Attempts common fixes for Docker network connectivity issues
# Run as root in your staging environment

echo "========================================"
echo "Docker Network Fix Attempt"
echo "Date: $(date)"
echo "========================================"
echo ""

# 1. Restart Docker with clean network
echo "1. Restarting Docker service..."
systemctl stop docker
sleep 2
# Clean up any stale network interfaces
ip link delete docker0 2>/dev/null || true
systemctl start docker
sleep 5
echo "Docker restarted"
echo ""

# 2. Configure Docker DNS
echo "2. Configuring Docker DNS..."
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<EOF
{
  "dns": ["8.8.8.8", "8.8.4.4", "1.1.1.1"],
  "dns-search": [""],
  "dns-opts": ["ndots:0"],
  "mtu": 1400,
  "registry-mirrors": [],
  "insecure-registries": [],
  "debug": false,
  "experimental": false
}
EOF
echo "Docker daemon configuration updated"
echo ""

# 3. Reload Docker daemon
echo "3. Reloading Docker daemon..."
systemctl daemon-reload
systemctl restart docker
sleep 5
echo "Docker daemon reloaded"
echo ""

# 4. Test connectivity
echo "4. Testing connectivity..."
docker run --rm alpine:latest sh -c 'nslookup registry.npmjs.org && echo "✅ DNS working"'
docker run --rm alpine:latest sh -c 'wget --spider --timeout=5 https://registry.npmjs.org && echo "✅ HTTPS working"'
echo ""

# 5. If behind proxy, configure it
if [ ! -z "$HTTP_PROXY" ] || [ ! -z "$HTTPS_PROXY" ]; then
    echo "5. Configuring Docker proxy settings..."
    mkdir -p /etc/systemd/system/docker.service.d
    cat > /etc/systemd/system/docker.service.d/http-proxy.conf <<EOF
[Service]
Environment="HTTP_PROXY=${HTTP_PROXY}"
Environment="HTTPS_PROXY=${HTTPS_PROXY}"
Environment="NO_PROXY=${NO_PROXY},localhost,127.0.0.1,docker-registry.local"
EOF
    systemctl daemon-reload
    systemctl restart docker
    echo "Proxy configured for Docker"
else
    echo "5. No proxy detected, skipping proxy configuration"
fi
echo ""

# 6. Alternative: Use host network for build
echo "6. Alternative build command using host network:"
echo "-------------------------------------------"
echo "If network issues persist, try building with host network:"
echo ""
echo "docker build --network=host -f config/docker/Dockerfile.frontend -t migration_frontend ."
echo ""

echo "========================================"
echo "Fix attempt complete!"
echo "Now try: docker-compose up -d"
echo "========================================"
