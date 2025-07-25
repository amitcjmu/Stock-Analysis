# Database Setup Guide

This guide provides comprehensive instructions for setting up the AI Modernize Migration Platform database for development and deployment.

## 🚀 Quick Start (Recommended)

For new developers, this is the fastest way to get up and running:

```bash
# 1. Clone the repository
git clone <repository-url>
cd migrate-ui-orchestrator

# 2. Start the complete stack with Docker
docker-compose up -d --build

# 3. Wait for initialization (check logs)
docker-compose logs -f backend
```

The initialization script will automatically:
- ✅ Create the database with required extensions
- ✅ Run all migrations in correct order
- ✅ Seed demo data and platform admin account
- ✅ Validate the setup

## 📋 Prerequisites

### For Docker Development (Recommended)
- Docker Desktop
- Docker Compose
- Git

### For Local Development (Advanced)
- PostgreSQL 14+ with pgvector extension
- Python 3.11+
- Node.js 18+

## 🐳 Docker Setup (Recommended)

### Initial Setup

```bash
# Build and start all services
docker-compose up -d --build

# Check initialization progress
docker-compose logs -f backend

# Verify everything is working
docker-compose ps
```

### Database Management Commands

```bash
# Initialize database only
docker-compose exec backend python scripts/init_database.py

# Force reset database (destructive)
docker-compose exec backend python scripts/init_database.py --force

# Validate database state
docker-compose exec backend python scripts/init_database.py --validate-only

# Access PostgreSQL directly
docker-compose exec postgres psql -U postgres -d migration_db

# View backend logs
docker-compose logs -f backend

# Restart backend service
docker-compose restart backend
```

### Troubleshooting Docker Issues

```bash
# If containers fail to start
docker-compose down -v  # Remove volumes
docker-compose up -d --build --force-recreate

# If database initialization fails
docker-compose exec backend /entrypoint.sh init-only

# If you need to force reset everything
docker-compose down -v
docker system prune -f
docker-compose up -d --build
```

## 🔧 Manual Setup (Local Development)

### 1. PostgreSQL Setup

```bash
# Install PostgreSQL with pgvector (macOS)
brew install postgresql@14
brew install pgvector

# Install PostgreSQL with pgvector (Ubuntu)
sudo apt-get install postgresql-14 postgresql-14-pgvector

# Start PostgreSQL
brew services start postgresql@14  # macOS
sudo systemctl start postgresql    # Ubuntu
```

### 2. Create Database

```sql
-- Connect to PostgreSQL as superuser
psql -U postgres

-- Create database and user
CREATE DATABASE migration_db;
CREATE USER migration_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE migration_db TO migration_user;

-- Connect to the new database
\c migration_db

-- Install extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 3. Environment Configuration

Create `backend/.env`:

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://migration_user:your_password@localhost:5432/migration_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=migration_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=migration_db

# Application Configuration
ENVIRONMENT=development
DEBUG=true
DEEPINFRA_API_KEY=your_api_key

# Feature Flags
ASSESSMENT_FLOW_ENABLED=true
CREWAI_ASSESSMENT_AGENTS_ENABLED=true
```

### 4. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run database initialization
python scripts/init_database.py

# Start the backend
uvicorn main:app --reload --port 8000
```

### 5. Frontend Setup

```bash
# Install dependencies
npm install

# Configure environment
echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev
```

## 🚂 Railway Deployment

### Database Issues Fix

If you're experiencing database issues in Railway:

```bash
# Connect to Railway and run fix script
railway shell
python scripts/deployment/fix-railway-db.py

# Or force reset (destructive)
python scripts/deployment/fix-railway-db.py --force-reset
```

### Environment Variables for Railway

Set these in your Railway environment:

```bash
DATABASE_URL=<provided_by_railway>
DEEPINFRA_API_KEY=<your_key>
ENVIRONMENT=production
CREWAI_ENABLED=true
ASSESSMENT_FLOW_ENABLED=true
```

## 🔍 Database Schema Overview

The platform uses these main table groups:

### Core Tables
- `users` - User accounts
- `client_accounts` - Customer organizations
- `engagements` - Migration projects
- `user_profiles` - User profile and RBAC data

### Flow Management
- `discovery_flows` - Discovery process flows
- `assessment_flows` - Assessment process flows
- `crewai_flow_state_extensions` - Master flow orchestration
- `user_active_flows` - User flow associations

### Data & Analytics
- `data_import_sessions` - Data import tracking
- `component_*` - Application component data
- `tech_debt_analysis` - Technical debt analysis
- `llm_usage_tracking` - AI usage metrics

## 🔐 Default Accounts

After initialization, these accounts are available:

### Platform Administrator
- **Email**: chocka@gmail.com
- **Password**: Password123!
- **Access**: Full platform administration

### Demo Users
- **Demo User**: demo@demo-corp.com / Demo123!
- **Demo Manager**: manager@demo-corp.com / Demo123!
- **Demo Analyst**: analyst@demo-corp.com / Demo123!
- **Demo Viewer**: viewer@demo-corp.com / Demo123!

## 🛠️ Migration Management

### Alembic Commands

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Upgrade to latest migration
alembic upgrade head

# Downgrade one migration
alembic downgrade -1

# Show migration history
alembic history

# Show current version
alembic current
```

### Migration Best Practices

1. **Always backup** before running migrations in production
2. **Test migrations** in development first
3. **Use descriptive names** for migration files
4. **Review generated migrations** before applying
5. **Handle data migrations** separately when needed

## 🔍 Health Checks

### Database Health Check

```bash
# Using Docker
docker-compose exec backend python scripts/init_database.py --validate-only

# Local development
python scripts/init_database.py --validate-only

# Manual check
curl http://localhost:8000/health
```

### Expected Health Check Results

```
Database Validation Report
==========================
Overall Status: ✅ HEALTHY

Component Status:
  📊 Tables: ✅ (45+ found)
  🔌 Extensions: ✅
  👤 Platform Admin: ✅
  🎭 Demo Data: ✅

Data Summary:
  Users: 5+
  Clients: 1+
  Engagements: 1+
```

## 🚨 Common Issues & Solutions

### Issue: "Migration failed"
**Solution**:
```bash
# Reset and reinitialize
docker-compose exec backend python scripts/init_database.py --force
```

### Issue: "Account not approved"
**Solution**:
```bash
# Run data initialization
docker-compose exec backend python -m app.core.database_initialization
```

### Issue: "Import Error" for models
**Solution**:
```bash
# Ensure proper PYTHONPATH
export PYTHONPATH=/app
python scripts/init_database.py
```

### Issue: "Extension not available"
**Solution**:
```bash
# Install pgvector in PostgreSQL
docker-compose exec postgres psql -U postgres -d migration_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Issue: Railway deployment fails
**Solution**:
```bash
# Use Railway fix script
railway shell
python scripts/deployment/fix-railway-db.py --force-reset
```

## 📞 Support

If you continue to experience issues:

1. **Check the logs**: `docker-compose logs -f backend`
2. **Validate database**: `python scripts/init_database.py --validate-only`
3. **Reset if needed**: `python scripts/init_database.py --force`
4. **Open an issue** with logs and error messages

## 🔄 Reset Everything

If you need to completely start over:

```bash
# Docker setup
docker-compose down -v
docker system prune -f
docker-compose up -d --build

# Local setup
dropdb migration_db
createdb migration_db
python scripts/init_database.py --force
```

This should resolve all database setup issues and get you running quickly!
