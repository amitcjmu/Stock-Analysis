#!/bin/bash

# Docker Network Diagnostics Script
# This script identifies network connectivity issues preventing npm/Docker registry access
# Run as root in your staging environment

echo "========================================"
echo "Docker Network Diagnostic Report"
echo "Date: $(date)"
echo "Host: $(hostname)"
echo "========================================"
echo ""

# 1. Check Docker daemon status
echo "1. Docker Service Status:"
echo "------------------------"
systemctl status docker --no-pager | head -20
echo ""

# 2. Check host network connectivity
echo "2. Host Network Connectivity:"
echo "----------------------------"
echo "Testing DNS resolution from host..."
nslookup registry.npmjs.org 2>&1
nslookup registry.docker.io 2>&1
echo ""

echo "Testing HTTP/HTTPS connectivity from host..."
curl -I --connect-timeout 5 https://registry.npmjs.org 2>&1 | head -10
curl -I --connect-timeout 5 https://registry.docker.io 2>&1 | head -10
echo ""

# 3. Check Docker network configuration
echo "3. Docker Network Configuration:"
echo "--------------------------------"
docker network ls
echo ""
docker network inspect bridge 2>&1 | grep -A5 "IPAM\|Gateway"
echo ""

# 4. Test connectivity from within Docker container
echo "4. Container Network Tests:"
echo "--------------------------"
echo "Creating test container..."
docker run --rm --name network-test alpine:latest sh -c '
echo "Inside Docker container tests:"
echo ""
echo "DNS Resolution tests:"
nslookup registry.npmjs.org 2>&1
nslookup registry.docker.io 2>&1
nslookup google.com 2>&1
echo ""
echo "Ping tests (5 packets):"
ping -c 5 8.8.8.8 2>&1
echo ""
echo "HTTP connectivity tests:"
wget --spider --timeout=5 http://registry.npmjs.org 2>&1
wget --spider --timeout=5 https://registry.npmjs.org 2>&1
echo ""
echo "Checking resolv.conf:"
cat /etc/resolv.conf
echo ""
echo "Checking network interfaces:"
ip addr show
echo ""
echo "Checking routing table:"
ip route
'

# 5. Check for proxy settings
echo ""
echo "5. Proxy Configuration Check:"
echo "-----------------------------"
echo "System proxy settings:"
echo "HTTP_PROXY: ${HTTP_PROXY:-not set}"
echo "HTTPS_PROXY: ${HTTPS_PROXY:-not set}"
echo "NO_PROXY: ${NO_PROXY:-not set}"
echo ""

echo "Docker daemon proxy settings:"
if [ -f /etc/systemd/system/docker.service.d/http-proxy.conf ]; then
    cat /etc/systemd/system/docker.service.d/http-proxy.conf
else
    echo "No Docker daemon proxy configuration found"
fi
echo ""

# 6. Check firewall rules
echo "6. Firewall Configuration:"
echo "-------------------------"
if command -v iptables &> /dev/null; then
    echo "IPTables rules (Docker-related):"
    iptables -L -n | grep -E "DOCKER|Chain" | head -20
else
    echo "iptables not found"
fi

if command -v ufw &> /dev/null; then
    echo ""
    echo "UFW Status:"
    ufw status verbose 2>&1 | head -20
else
    echo "ufw not found"
fi
echo ""

# 7. Check Docker daemon configuration
echo "7. Docker Daemon Configuration:"
echo "-------------------------------"
if [ -f /etc/docker/daemon.json ]; then
    echo "Contents of /etc/docker/daemon.json:"
    cat /etc/docker/daemon.json
else
    echo "No daemon.json found"
fi
echo ""

# 8. Test specific npm registry endpoints
echo "8. NPM Registry Specific Tests:"
echo "-------------------------------"
echo "Testing npm registry API endpoints..."
curl -I --connect-timeout 5 https://registry.npmjs.org/-/ping 2>&1 | head -5
curl --connect-timeout 5 https://registry.npmjs.org/-/ping 2>&1
echo ""

# 9. Check MTU settings
echo "9. MTU Configuration:"
echo "--------------------"
echo "Host network interfaces MTU:"
ip link show | grep mtu
echo ""
echo "Docker bridge MTU:"
docker network inspect bridge 2>&1 | grep -i mtu
echo ""

# 10. Generate summary
echo "========================================"
echo "DIAGNOSTIC SUMMARY"
echo "========================================"
echo ""
echo "Issues Found:"
echo "-------------"

# Check for common issues
if ! nslookup registry.npmjs.org &>/dev/null; then
    echo "❌ DNS resolution failing on host"
fi

if ! curl -I --connect-timeout 5 https://registry.npmjs.org &>/dev/null; then
    echo "❌ HTTPS connectivity to npm registry failing from host"
fi

if docker run --rm alpine:latest nslookup registry.npmjs.org &>/dev/null; then
    echo "✅ DNS works inside containers"
else
    echo "❌ DNS resolution failing inside Docker containers"
fi

if docker run --rm alpine:latest wget --spider --timeout=5 https://registry.npmjs.org &>/dev/null; then
    echo "✅ HTTPS works inside containers"
else
    echo "❌ HTTPS connectivity failing inside Docker containers"
fi

echo ""
echo "Recommended Actions for Network Admin:"
echo "--------------------------------------"
echo "1. If DNS is failing: Check DNS server configuration and /etc/resolv.conf"
echo "2. If HTTPS is blocked: Open outbound ports 80/443 to:"
echo "   - registry.npmjs.org (104.16.0.0/12 IP range)"
echo "   - registry.docker.io (34.192.0.0/10 IP range)"
echo "3. If proxy is required: Configure Docker daemon with proxy settings"
echo "4. If MTU mismatch: Adjust Docker bridge MTU to match host network"
echo "5. If firewall blocking: Add rules to allow Docker bridge network (172.17.0.0/16)"
echo ""
echo "========================================"
echo "End of Diagnostic Report"
echo "========================================"