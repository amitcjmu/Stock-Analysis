#!/bin/bash

# Update Configuration File References Script
# This script updates references to moved configuration files

set -e

PROJECT_ROOT="/Users/chocka/CursorProjects/migrate-ui-orchestrator"

echo "Updating configuration file references..."

# Update specific docker-compose file references in shell scripts (avoid recursive paths)
find "$PROJECT_ROOT" -name "*.sh" -type f \
  -not -path "*/node_modules/*" \
  -not -path "*/venv/*" \
  -not -path "*/.git/*" \
  -exec sed -i '' 's|docker-compose\.dev\.yml|config/docker/docker-compose.dev.yml|g' {} \;

find "$PROJECT_ROOT" -name "*.sh" -type f \
  -not -path "*/node_modules/*" \
  -not -path "*/venv/*" \
  -not -path "*/.git/*" \
  -exec sed -i '' 's|docker-compose\.test\.yml|config/docker/docker-compose.test.yml|g' {} \;

find "$PROJECT_ROOT" -name "*.sh" -type f \
  -not -path "*/node_modules/*" \
  -not -path "*/venv/*" \
  -not -path "*/.git/*" \
  -exec sed -i '' 's|docker-compose\.prod\.yml|config/docker/docker-compose.prod.yml|g' {} \;

# Update tool config references in TypeScript files
find "$PROJECT_ROOT/src" -name "*.ts" -type f \
  -exec sed -i '' 's|\./vite\.config\.ts|\./config/tools/vite.config.ts|g' {} \;

find "$PROJECT_ROOT/src" -name "*.ts" -type f \
  -exec sed -i '' 's|\./tailwind\.config\.ts|\./config/tools/tailwind.config.ts|g' {} \;

# Update database config references in Python files
find "$PROJECT_ROOT/backend" -name "*.py" -type f \
  -exec sed -i '' 's|alembic\.ini|config/database/alembic.ini|g' {} \;

# Update tool references in package.json and similar
find "$PROJECT_ROOT" -name "package.json" -type f \
  -exec sed -i '' 's|"vite\.config\.ts"|"config/tools/vite.config.ts"|g' {} \;

echo "Configuration file references updated successfully."
echo "NOTE: Main docker-compose.yml kept in root for Docker CLI compatibility."
