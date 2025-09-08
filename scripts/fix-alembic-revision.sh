#!/bin/bash

# Fix Alembic revision issue by clearing stale revision references
# This script addresses the "Can't locate revision identified by '67da5e784e40'" error

echo "🔧 Fixing Alembic revision references..."

# Connect to PostgreSQL and clear stale alembic version
docker exec -it migrate-ui-orchestrator-postgres-1 psql -U postgres -d migration_db << EOF
-- Clear any stale alembic version entries
DELETE FROM migration.alembic_version WHERE version_num = '67da5e784e40';

-- Show current alembic version state
SELECT * FROM migration.alembic_version;
EOF

echo "✅ Alembic revision references cleared"
echo "🔄 Now restart the backend container:"
echo "   docker compose restart backend"
