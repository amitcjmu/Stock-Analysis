#!/bin/bash

# AI Modernize Migration Platform - Environment Setup Script
# Creates environment files for different deployment scenarios

set -e

echo "�� Setting up environment files..."

# Create development environment
cat > .env.dev << 'DEVEOF'
# Development Environment Configuration
POSTGRES_DB=migration_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DEEPINFRA_API_KEY=your_deepinfra_api_key_here
ENVIRONMENT=development
DEBUG=true
DEMO_DATA=true
AUTO_SEED_DATA=true
OTEL_SDK_DISABLED=true
DEVEOF

# Create production template
cat > .env.prod.template << 'PRODEOF'
# Production Environment Template
POSTGRES_DB=migration_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=CHANGE_THIS_SECURE_PASSWORD
DEEPINFRA_API_KEY=your_production_deepinfra_api_key
ENVIRONMENT=production
DEBUG=false
DEMO_DATA=false
AUTO_SEED_DATA=false
SECRET_KEY=generate_secure_32_character_secret_key
JWT_SECRET=generate_secure_32_character_jwt_secret
PRODEOF

echo "✅ Environment files created successfully!"
echo "📋 Files created:"
echo "  - .env.dev (Development)"
echo "  - .env.prod.template (Production template)"
