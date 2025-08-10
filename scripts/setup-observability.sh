#!/bin/bash

# CrewAI Agent Observability Setup Script
# Sets up comprehensive monitoring for CrewAI agents and flows

set -e

echo "🔍 Setting up CrewAI Agent Observability Stack..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if main application is running
check_main_app() {
    print_status "Checking main application status..."

    if docker-compose ps | grep -q "migration_backend.*Up"; then
        print_success "Main application backend is running"
    else
        print_error "Main application backend is not running"
        print_status "Please start the main application first: docker-compose up -d"
        exit 1
    fi

    if docker-compose ps | grep -q "migration_frontend.*Up"; then
        print_success "Main application frontend is running"
    else
        print_warning "Main application frontend is not running"
    fi
}

# Test backend API endpoints
test_backend_apis() {
    print_status "Testing backend API endpoints..."

    # Test health endpoint
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "Backend health endpoint is accessible"
    else
        print_error "Backend health endpoint is not accessible"
        return 1
    fi

    # Test monitoring endpoints
    if curl -s http://localhost:8000/api/v1/monitoring/status > /dev/null; then
        print_success "Agent monitoring endpoint is accessible"
    else
        print_warning "Agent monitoring endpoint is not accessible"
    fi

    # Test CrewAI Flow monitoring
    if curl -s http://localhost:8000/api/v1/monitoring/crewai-flows > /dev/null; then
        print_success "CrewAI Flow monitoring endpoint is accessible"
    else
        print_warning "CrewAI Flow monitoring endpoint is not accessible"
    fi
}

# Create observability configuration files
create_config_files() {
    print_status "Creating observability configuration files..."

    # Create directories
    mkdir -p observability/grafana/{dashboards,datasources}

    # Create OpenTelemetry collector config
    cat > observability/otel-collector-config.yaml << 'EOF'
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024
  memory_limiter:
    limit_mib: 512

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true

  prometheus:
    endpoint: "0.0.0.0:8889"

  logging:
    loglevel: debug

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [jaeger, logging]

    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus, logging]
EOF

    print_success "OpenTelemetry collector configuration created"
}

# Start observability stack
start_observability() {
    print_status "Starting observability stack..."

    # Start the observability services
    docker-compose -f config/docker/docker-compose.observability.yml up -d

    print_status "Waiting for services to start..."
    sleep 10

    # Check if services are running
    if docker-compose -f config/docker/docker-compose.observability.yml ps | grep -q "Up"; then
        print_success "Observability services are starting up"
    else
        print_error "Failed to start observability services"
        return 1
    fi
}

# Test observability endpoints
test_observability() {
    print_status "Testing observability endpoints..."

    # Wait for services to be fully ready
    print_status "Waiting for services to be ready..."
    sleep 30

    # Test Jaeger UI
    if curl -s http://localhost:16686 > /dev/null; then
        print_success "Jaeger UI is accessible at http://localhost:16686"
    else
        print_warning "Jaeger UI is not yet accessible"
    fi

    # Test OpenTelemetry collector
    if curl -s http://localhost:8888/metrics > /dev/null; then
        print_success "OpenTelemetry collector metrics are accessible"
    else
        print_warning "OpenTelemetry collector metrics are not yet accessible"
    fi
}

# Display access information
show_access_info() {
    print_success "🎉 Observability stack setup complete!"
    echo ""
    echo "📊 Access Points:"
    echo "  • Main Application: http://localhost:8081"
    echo "  • Agent Monitoring: http://localhost:8081/observability/agent-monitoring"
    echo "  • Jaeger Tracing: http://localhost:16686"
    echo "  • Backend API: http://localhost:8000"
    echo ""
    echo "🔍 Monitoring Endpoints:"
    echo "  • Agent Status: http://localhost:8000/api/v1/monitoring/status"
    echo "  • CrewAI Flows: http://localhost:8000/api/v1/monitoring/crewai-flows"
    echo "  • Health Check: http://localhost:8000/health"
    echo ""
    echo "🐛 Debugging:"
    echo "  • View logs: docker-compose logs -f backend"
    echo "  • View observability logs: docker-compose -f config/docker/docker-compose.observability.yml logs -f"
    echo "  • Test CMDB import: Upload a CSV file at http://localhost:8081/discovery/import"
}

# Main execution
main() {
    echo "🚀 CrewAI Agent Observability Setup"
    echo "===================================="

    check_main_app
    test_backend_apis
    create_config_files
    start_observability
    test_observability
    show_access_info

    print_success "Setup complete! You can now monitor CrewAI agents and flows."
}

# Run main function
main "$@"
