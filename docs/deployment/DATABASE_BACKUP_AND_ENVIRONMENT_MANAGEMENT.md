# Database Backup and Environment Management

## Overview

This document covers the comprehensive backup and environment management system for the AI Force Migration Platform, designed to prevent data loss and provide environment-specific configurations.

## 🛡️ Database Backup System

### Automatic Backup Script

The platform includes a comprehensive backup script that creates multiple backup types:

```bash
./scripts/backup_database.sh
```

#### Backup Types Created:
1. **Full Database Backup** - Complete database with schema and data
2. **Schema-Only Backup** - Database structure without data
3. **Data-Only Backup** - Data without schema structure
4. **Metadata File** - Backup information and Git context

#### Features:
- ✅ Automatic compression (tar.gz format)
- ✅ Metadata tracking with Git information
- ✅ Automatic cleanup (keeps last 10 backups)
- ✅ Size and table count reporting
- ✅ Health checks and validation

### Database Restore Script

Restore from any backup created by the backup script:

```bash
./scripts/restore_database.sh <backup_file.tar.gz>
```

#### Safety Features:
- ✅ Pre-restore backup creation
- ✅ Confirmation prompts
- ✅ Database connectivity testing
- ✅ Rollback capability
- ✅ Metadata display

### Usage Examples

```bash
# Create a backup before schema changes
./scripts/backup_database.sh

# List available backups
ls -la ./backups/migration_db_backup_*.tar.gz

# Restore from specific backup
./scripts/restore_database.sh ./backups/migration_db_backup_20250127_143022.tar.gz
```

## 🌍 Environment Management

### Environment-Specific Docker Compose Files

The platform supports three deployment environments:

#### 1. Development Environment
```bash
# Use development configuration
docker-compose -f docker-compose.dev.yml up -d
```

**Features:**
- Auto-seeding of demo data
- Debug logging enabled
- Hot reload for development
- Adminer database UI
- Redis for caching
- Different ports to avoid conflicts

#### 2. Production Environment
```bash
# Use production configuration
docker-compose -f docker-compose.prod.yml up -d
```

**Features:**
- Production security settings
- Nginx reverse proxy
- Automated backups
- Monitoring with Prometheus/Grafana
- Resource limits and health checks
- SSL/TLS support

#### 3. Current Environment (Default)
```bash
# Use current configuration
docker-compose up -d
```

**Features:**
- Backward compatibility
- Existing workflow support

### Environment Configuration Setup

Use the environment setup script to create configuration files:

```bash
# Create all environment files
./scripts/setup_environments.sh

# Create specific environment
./scripts/setup_environments.sh dev    # Development only
./scripts/setup_environments.sh prod   # Production template
```

#### Generated Files:
- `.env` - Current environment variables
- `.env.dev` - Development configuration
- `.env.prod.template` - Production template

### Environment Variables

#### Core Configuration
```bash
# Database
POSTGRES_DB=migration_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# Application
ENVIRONMENT=development|production
DEBUG=true|false
DEMO_DATA=true|false
AUTO_SEED_DATA=true|false

# Security
SECRET_KEY=your_32_character_secret_key
JWT_SECRET=your_32_character_jwt_secret
ALLOWED_ORIGINS=https://your-domain.com

# API Keys
DEEPINFRA_API_KEY=your_api_key
```

## 📊 Demo Data Management

### Automatic Data Seeding

The platform includes a comprehensive demo data population script:

```bash
# Run demo data seeding
docker exec -it migration_backend python scripts/populate_demo_data.py
```

#### Demo Data Includes:
- **Users:** Admin, Demo, and User accounts
- **Client Accounts:** Democorp, Acme Corporation, Marathon Petroleum
- **Engagements:** Cloud migration projects
- **Sessions:** Data import sessions
- **User Profiles:** RBAC configurations

#### Demo Credentials:
- **Admin:** admin@democorp.com / password
- **Demo:** demo@democorp.com / password  
- **User:** chocka@gmail.com / password123

### Data Seeding Features:
- ✅ Idempotent (safe to run multiple times)
- ✅ Fixed UUIDs for consistency
- ✅ Proper relationships and constraints
- ✅ RBAC and permissions setup

## 🔄 Workflow for Schema Updates

### Before Making Schema Changes:

1. **Create Backup**
   ```bash
   ./scripts/backup_database.sh
   ```

2. **Note the backup file name** for potential rollback

3. **Test in development environment first**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

### After Schema Changes:

1. **Run migrations**
   ```bash
   docker exec -it migration_backend python -m alembic upgrade head
   ```

2. **Reseed demo data if needed**
   ```bash
   docker exec -it migration_backend python scripts/populate_demo_data.py
   ```

3. **Verify functionality**

4. **Create post-update backup**
   ```bash
   ./scripts/backup_database.sh
   ```

## 🚨 Data Loss Prevention

### Root Causes of Previous Data Loss:

1. **Schema Evolution** - Database schema changed without migration
2. **Container Lifecycle** - Data not persisted in volumes
3. **Manual Changes** - Direct database modifications lost
4. **Missing Backups** - No backup strategy in place

### Prevention Measures:

1. **Regular Backups**
   - Automatic backup before schema changes
   - Scheduled daily backups in production
   - Version-controlled backup metadata

2. **Proper Volume Management**
   - Named volumes for data persistence
   - Environment-specific volume strategies
   - Volume backup integration

3. **Migration Strategy**
   - Alembic migrations for schema changes
   - Demo data seeding for consistency
   - Rollback procedures

4. **Environment Isolation**
   - Separate configurations per environment
   - Clear deployment procedures
   - Testing protocols

## 📋 Best Practices

### Development Workflow:
1. Always backup before major changes
2. Use development environment for testing
3. Seed demo data after schema changes
4. Test login functionality with all accounts
5. Verify data persistence across container restarts

### Production Deployment:
1. Create backup before deployment
2. Use production environment configuration
3. Monitor backup success
4. Verify health checks
5. Test rollback procedures

### Backup Management:
1. Keep multiple backup generations
2. Store backups in secure location
3. Test restore procedures regularly
4. Document backup metadata
5. Monitor backup file sizes

## 🔧 Troubleshooting

### Common Issues:

#### "Container not running"
```bash
# Check container status
docker-compose ps

# Start containers
docker-compose up -d
```

#### "Database connection failed"
```bash
# Check database health
docker exec -it migration_postgres psql -U postgres -d migration_db -c "SELECT 1;"

# Restart database
docker-compose restart postgres
```

#### "Login credentials not working"
```bash
# Reseed demo data
docker exec -it migration_backend python scripts/populate_demo_data.py

# Check user accounts
docker exec -it migration_postgres psql -U postgres -d migration_db -c "SELECT email, is_active FROM migration.users;"
```

#### "Backup restoration failed"
```bash
# Check backup file integrity
tar -tzf backup_file.tar.gz

# Try schema-only restore first
./scripts/restore_database.sh --schema-only backup_file.tar.gz
```

### Log Locations:
- **Application Logs:** `docker-compose logs -f backend`
- **Database Logs:** `docker-compose logs -f postgres`
- **Backup Logs:** Output from backup scripts

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)
- [Alembic Migration Documentation](https://alembic.sqlalchemy.org/)

---

## Quick Reference Commands

```bash
# Backup database
./scripts/backup_database.sh

# Restore database
./scripts/restore_database.sh <backup_file>

# Setup environments
./scripts/setup_environments.sh

# Development deployment
docker-compose -f docker-compose.dev.yml up -d

# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Seed demo data
docker exec -it migration_backend python scripts/populate_demo_data.py

# Check database status
docker exec -it migration_postgres psql -U postgres -d migration_db -c "SELECT version();"
``` 