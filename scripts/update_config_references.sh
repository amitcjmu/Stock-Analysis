#!/bin/bash

# Update Configuration File References Script
# This script updates references to moved configuration files

set -e

PROJECT_ROOT="/Users/chocka/CursorProjects/migrate-ui-orchestrator"

echo "Updating configuration file references..."

# Update docker-compose file references in shell scripts
find "$PROJECT_ROOT" -name "*.sh" -type f -exec sed -i '' 's|docker-compose\.yml|config/docker/docker-compose.yml|g' {} \;
find "$PROJECT_ROOT" -name "*.sh" -type f -exec sed -i '' 's|docker-compose-|config/docker/docker-compose-|g' {} \;
find "$PROJECT_ROOT" -name "*.sh" -type f -exec sed -i '' 's|docker-compose\.\([a-z-]*\)\.yml|config/docker/docker-compose.\1.yml|g' {} \;

# Update vite config references
find "$PROJECT_ROOT" -name "*.ts" -type f -exec sed -i '' 's|vite\.config\.ts|config/tools/vite.config.ts|g' {} \;

# Update tailwind config references
find "$PROJECT_ROOT" -name "*.ts" -type f -exec sed -i '' 's|tailwind\.config\.ts|config/tools/tailwind.config.ts|g' {} \;

# Update eslint config references
find "$PROJECT_ROOT" -name "*.json" -type f -exec sed -i '' 's|eslint\.config\.js|config/tools/eslint.config.js|g' {} \;

# Update pytest.ini references
find "$PROJECT_ROOT" -name "*.py" -type f -exec sed -i '' 's|pytest\.ini|config/tools/pytest.ini|g' {} \;

# Update alembic.ini references
find "$PROJECT_ROOT" -name "*.py" -type f -exec sed -i '' 's|alembic\.ini|config/database/alembic.ini|g' {} \;

# Update pyproject.toml references
find "$PROJECT_ROOT" -name "*.py" -type f -exec sed -i '' 's|pyproject\.toml|config/tools/pyproject.toml|g' {} \;

echo "Configuration file references updated successfully."
