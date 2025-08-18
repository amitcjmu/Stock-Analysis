# PostgreSQL Development Guide

## Overview

This guide provides comprehensive instructions for working with PostgreSQL in the AI Modernize Migration Platform, including local development setup, schema understanding, and SQLAlchemy ORM usage patterns.

## Database Schema Overview

### Visual Schema Diagram

```mermaid
erDiagram
    CLIENT_ACCOUNTS ||--o{ ENGAGEMENTS : has
    CLIENT_ACCOUNTS ||--o{ USER_ACCOUNT_ASSOCIATIONS : has
    USERS ||--o{ USER_ACCOUNT_ASSOCIATIONS : belongs_to
    ENGAGEMENTS ||--o{ DISCOVERY_FLOWS : contains
    ENGAGEMENTS ||--o{ COLLECTION_FLOWS : contains
    ENGAGEMENTS ||--o{ ASSESSMENT_FLOWS : contains
    ENGAGEMENTS ||--o{ ASSETS : contains
    ENGAGEMENTS ||--o{ DATA_IMPORTS : contains

    CLIENT_ACCOUNTS {
        uuid id PK
        string name
        string slug UK
        jsonb settings
        jsonb agent_configuration
        jsonb business_objectives
        timestamp created_at
        boolean is_active
    }

    ENGAGEMENTS {
        uuid id PK
        uuid client_account_id FK
        string name
        string slug
        string status
        jsonb migration_scope
        timestamp start_date
        timestamp target_completion_date
        timestamp created_at
    }

    USERS {
        uuid id PK
        string email UK
        string password_hash
        string first_name
        string last_name
        boolean is_active
        uuid default_client_id FK
        timestamp created_at
    }

    CREWAI_FLOW_STATE_EXTENSIONS {
        uuid id PK
        uuid flow_id UK
        uuid client_account_id FK
        uuid engagement_id FK
        string flow_type
        string flow_status
        string current_phase
        jsonb flow_config
        jsonb performance_metrics
        timestamp created_at
    }

    DISCOVERY_FLOWS {
        uuid id PK
        uuid flow_id UK
        uuid master_flow_id FK
        uuid client_account_id FK
        uuid engagement_id FK
        string flow_name
        string status
        string current_phase
        jsonb analysis_results
        jsonb field_mappings
        timestamp created_at
    }

    ASSETS {
        uuid id PK
        uuid client_account_id FK
        uuid engagement_id FK
        string asset_name
        string asset_type
        string environment
        jsonb specifications
        jsonb dependencies
        string sixr_recommendation
        uuid discovery_flow_id FK
        timestamp created_at
    }

    DATA_IMPORTS {
        uuid id PK
        uuid client_account_id FK
        uuid engagement_id FK
        string filename
        string upload_status
        integer total_rows
        jsonb processed_data
        timestamp created_at
    }
```

## Local PostgreSQL Setup

### 1. Docker Development (Recommended)

The platform uses Docker for all development. PostgreSQL runs in a container with proper configuration.

#### Accessing the Database Container

```bash
# Connect to PostgreSQL container
docker exec -it migration_db psql -U migration_user -d migration_db

# Or use the shortcut
docker-compose exec db psql -U migration_user -d migration_db
```

#### Database Container Configuration

```yaml
# docker-compose.yml (excerpt)
services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: migration_db
      POSTGRES_USER: migration_user
      POSTGRES_PASSWORD: migration_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/sql:/docker-entrypoint-initdb.d
```

### 2. Database Connection Configuration

#### Environment Variables

```bash
# .env file
DATABASE_URL=postgresql+asyncpg://migration_user:migration_password@localhost:5432/migration_db

# For local development
DB_HOST=localhost
DB_PORT=5432
DB_NAME=migration_db
DB_USER=migration_user
DB_PASSWORD=migration_password
```

#### SQLAlchemy Engine Configuration

```python
# backend/app/db/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Production-grade connection configuration
SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://user:password@host:port/database"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,                    # Set to True for SQL debugging
    pool_size=20,                  # Number of connections in pool
    max_overflow=30,               # Additional connections allowed
    pool_timeout=30,               # Seconds to wait for connection
    pool_recycle=3600,             # Recycle connections every hour
    pool_pre_ping=True,            # Validate connections before use
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,        # Keep objects accessible after commit
    autoflush=False,               # Manual control over when to flush
)
```

### 3. Database Tools and Clients

#### Command Line Tools

```bash
# PostgreSQL CLI (inside container)
docker exec -it migration_db psql -U migration_user -d migration_db

# Database shell commands
\l          # List databases
\dt         # List tables
\d+ table   # Describe table structure
\du         # List users
\q          # Quit

# Backup and restore
docker exec migration_db pg_dump -U migration_user migration_db > backup.sql
docker exec -i migration_db psql -U migration_user migration_db < backup.sql
```

#### GUI Tools

**pgAdmin** (Web-based)
```bash
# Run pgAdmin in Docker
docker run -p 5050:80 \
  -e PGADMIN_DEFAULT_EMAIL=admin@example.com \
  -e PGADMIN_DEFAULT_PASSWORD=admin \
  dpage/pgadmin4

# Connect to database:
# Host: host.docker.internal (Mac) or 172.17.0.1 (Linux)
# Port: 5432
# Database: migration_db
# Username: migration_user
```

**DBeaver** (Desktop Application)
- Download from: https://dbeaver.io/
- Connection URL: `jdbc:postgresql://localhost:5432/migration_db`
- Driver: PostgreSQL
- User: migration_user

## SQLAlchemy ORM Usage Patterns

### 1. Model Definition Patterns

#### Base Model with Multi-Tenancy

```python
# backend/app/models/base.py
from sqlalchemy import Column, String, DateTime, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr
import uuid
from datetime import datetime

Base = declarative_base()

class TimestampMixin:
    """Add timestamp fields to models"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class TenantMixin:
    """Add multi-tenant fields to models"""
    client_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=False, index=True)

class BaseModel(Base, TimestampMixin):
    """Abstract base model with common fields"""
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    is_active = Column(Boolean, default=True, nullable=False)
    
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
```

#### Example Model Implementation

```python
# backend/app/models/discovery_flow.py
from sqlalchemy import Column, String, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel, TenantMixin

class DiscoveryFlow(BaseModel, TenantMixin):
    """Discovery flow model with proper multi-tenancy"""
    __tablename__ = "discovery_flows"
    
    # Primary identification
    flow_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    flow_name = Column(String(255), nullable=False)
    
    # Status and progress
    status = Column(String(50), default='active', nullable=False, index=True)
    current_phase = Column(String(100), default='data_import', index=True)
    progress_percentage = Column(Integer, default=0)
    
    # Phase completion tracking
    data_import_completed = Column(Boolean, default=False)
    field_mapping_completed = Column(Boolean, default=False)
    data_cleansing_completed = Column(Boolean, default=False)
    
    # JSON data storage
    analysis_results = Column(JSONB, default=dict)
    field_mappings = Column(JSONB, default=dict)
    crewai_state_data = Column(JSONB, default=dict)
    
    # Foreign key relationships
    data_import_id = Column(UUID(as_uuid=True), ForeignKey('data_imports.id'))
    master_flow_id = Column(UUID(as_uuid=True), ForeignKey('crewai_flow_state_extensions.flow_id'))
    
    # Relationships
    data_import = relationship("DataImport", back_populates="discovery_flows")
    assets = relationship("Asset", back_populates="discovery_flow")
    
    def __repr__(self):
        return f"<DiscoveryFlow(id={self.id}, name={self.flow_name}, status={self.status})>"
```

### 2. Repository Pattern Implementation

#### Base Repository

```python
# backend/app/repositories/base.py
from typing import TypeVar, Generic, Optional, List, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from uuid import UUID

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations"""
    
    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def get_by_id(self, id: UUID, tenant_context: Dict[str, UUID] = None) -> Optional[ModelType]:
        """Get entity by ID with optional tenant filtering"""
        query = select(self.model).where(self.model.id == id)
        
        if tenant_context and hasattr(self.model, 'client_account_id'):
            query = query.where(
                self.model.client_account_id == tenant_context['client_account_id']
            )
            if 'engagement_id' in tenant_context:
                query = query.where(
                    self.model.engagement_id == tenant_context['engagement_id']
                )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        tenant_context: Dict[str, UUID] = None,
        filters: Dict[str, Any] = None
    ) -> List[ModelType]:
        """Get multiple entities with pagination and filtering"""
        query = select(self.model)
        
        # Apply tenant filtering
        if tenant_context and hasattr(self.model, 'client_account_id'):
            query = query.where(
                self.model.client_account_id == tenant_context['client_account_id']
            )
            if 'engagement_id' in tenant_context:
                query = query.where(
                    self.model.engagement_id == tenant_context['engagement_id']
                )
        
        # Apply additional filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def create(self, obj_in: Dict[str, Any], tenant_context: Dict[str, UUID] = None) -> ModelType:
        """Create new entity with tenant context"""
        # Add tenant context if model supports it
        if tenant_context and hasattr(self.model, 'client_account_id'):
            obj_in.update(tenant_context)
        
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj
    
    async def update(
        self,
        id: UUID,
        obj_in: Dict[str, Any],
        tenant_context: Dict[str, UUID] = None
    ) -> Optional[ModelType]:
        """Update entity with tenant context validation"""
        query = update(self.model).where(self.model.id == id)
        
        # Apply tenant filtering to update
        if tenant_context and hasattr(self.model, 'client_account_id'):
            query = query.where(
                self.model.client_account_id == tenant_context['client_account_id']
            )
        
        query = query.values(**obj_in)
        await self.session.execute(query)
        await self.session.commit()
        
        return await self.get_by_id(id, tenant_context)
```

#### Specific Repository Implementation

```python
# backend/app/repositories/discovery_flow.py
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload
from .base import BaseRepository
from ..models.discovery_flow import DiscoveryFlow

class DiscoveryFlowRepository(BaseRepository[DiscoveryFlow]):
    """Repository for DiscoveryFlow operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(DiscoveryFlow, session)
    
    async def get_by_flow_id(
        self,
        flow_id: UUID,
        tenant_context: Dict[str, UUID]
    ) -> Optional[DiscoveryFlow]:
        """Get discovery flow by CrewAI flow ID"""
        query = select(self.model).where(
            self.model.flow_id == flow_id,
            self.model.client_account_id == tenant_context['client_account_id']
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_with_assets(
        self,
        flow_id: UUID,
        tenant_context: Dict[str, UUID]
    ) -> Optional[DiscoveryFlow]:
        """Get discovery flow with related assets"""
        query = select(self.model).options(
            selectinload(self.model.assets),
            joinedload(self.model.data_import)
        ).where(
            self.model.flow_id == flow_id,
            self.model.client_account_id == tenant_context['client_account_id']
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_active_flows(
        self,
        tenant_context: Dict[str, UUID]
    ) -> List[DiscoveryFlow]:
        """Get all active discovery flows for tenant"""
        query = select(self.model).where(
            self.model.status.in_(['active', 'running']),
            self.model.client_account_id == tenant_context['client_account_id'],
            self.model.engagement_id == tenant_context['engagement_id']
        ).order_by(self.model.created_at.desc())
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_progress(
        self,
        flow_id: UUID,
        phase: str,
        progress: int,
        tenant_context: Dict[str, UUID]
    ) -> Optional[DiscoveryFlow]:
        """Update flow progress and phase"""
        return await self.update(
            flow_id,
            {
                'current_phase': phase,
                'progress_percentage': progress,
                'last_phase_update': datetime.utcnow()
            },
            tenant_context
        )
```

### 3. Service Layer Patterns

#### Database Session Management

```python
# backend/app/services/base.py
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from ..db.database import AsyncSessionLocal

class BaseService:
    """Base service with database session management"""
    
    @asynccontextmanager
    async def get_session(self):
        """Context manager for database sessions"""
        async with AsyncSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def with_session(self, func, *args, **kwargs):
        """Execute function with database session"""
        async with self.get_session() as session:
            return await func(session, *args, **kwargs)
```

#### Service Implementation

```python
# backend/app/services/discovery_flow_service.py
from typing import List, Optional, Dict, Any
from uuid import UUID
from ..repositories.discovery_flow import DiscoveryFlowRepository
from ..schemas.discovery_flow import DiscoveryFlowCreate, DiscoveryFlowUpdate
from .base import BaseService

class DiscoveryFlowService(BaseService):
    """Service for discovery flow operations"""
    
    async def create_flow(
        self,
        flow_data: DiscoveryFlowCreate,
        tenant_context: Dict[str, UUID]
    ) -> DiscoveryFlow:
        """Create new discovery flow"""
        async with self.get_session() as session:
            repo = DiscoveryFlowRepository(session)
            return await repo.create(flow_data.dict(), tenant_context)
    
    async def get_flow_by_id(
        self,
        flow_id: UUID,
        tenant_context: Dict[str, UUID]
    ) -> Optional[DiscoveryFlow]:
        """Get discovery flow by ID"""
        async with self.get_session() as session:
            repo = DiscoveryFlowRepository(session)
            return await repo.get_by_flow_id(flow_id, tenant_context)
    
    async def update_flow_progress(
        self,
        flow_id: UUID,
        phase: str,
        progress: int,
        tenant_context: Dict[str, UUID]
    ) -> Optional[DiscoveryFlow]:
        """Update flow progress"""
        async with self.get_session() as session:
            repo = DiscoveryFlowRepository(session)
            return await repo.update_progress(flow_id, phase, progress, tenant_context)
    
    async def get_tenant_flows(
        self,
        tenant_context: Dict[str, UUID],
        skip: int = 0,
        limit: int = 100
    ) -> List[DiscoveryFlow]:
        """Get flows for tenant with pagination"""
        async with self.get_session() as session:
            repo = DiscoveryFlowRepository(session)
            return await repo.get_multi(skip, limit, tenant_context)
```

### 4. Migration Patterns

#### Alembic Configuration

```python
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.models.base import Base
from app.core.config import settings

# Import all models to ensure they're registered
from app.models import *

target_metadata = Base.metadata

def run_migrations_online():
    """Run migrations in 'online' mode"""
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = settings.DATABASE_URL
    
    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True
        )

        with context.begin_transaction():
            context.run_migrations()
```

#### Migration Example

```python
# alembic/versions/001_create_discovery_flows.py
"""Create discovery flows table

Revision ID: 001_discovery_flows
Revises: 
Create Date: 2025-01-18 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_discovery_flows'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create discovery_flows table
    op.create_table(
        'discovery_flows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('flow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('engagement_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('flow_name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('current_phase', sa.String(100), nullable=True),
        sa.Column('progress_percentage', sa.Integer(), nullable=True),
        sa.Column('analysis_results', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('field_mappings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('flow_id')
    )
    
    # Create indexes
    op.create_index('idx_discovery_flows_client', 'discovery_flows', ['client_account_id'])
    op.create_index('idx_discovery_flows_engagement', 'discovery_flows', ['engagement_id'])
    op.create_index('idx_discovery_flows_status', 'discovery_flows', ['status'])
    op.create_index('idx_discovery_flows_phase', 'discovery_flows', ['current_phase'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_discovery_flows_phase', table_name='discovery_flows')
    op.drop_index('idx_discovery_flows_status', table_name='discovery_flows')
    op.drop_index('idx_discovery_flows_engagement', table_name='discovery_flows')
    op.drop_index('idx_discovery_flows_client', table_name='discovery_flows')
    
    # Drop table
    op.drop_table('discovery_flows')
```

### 5. Query Optimization Patterns

#### Efficient Querying

```python
# Efficient pagination with cursor-based pagination
async def get_flows_paginated(
    session: AsyncSession,
    tenant_context: Dict[str, UUID],
    cursor: Optional[UUID] = None,
    limit: int = 20
) -> List[DiscoveryFlow]:
    """Cursor-based pagination for better performance"""
    query = select(DiscoveryFlow).where(
        DiscoveryFlow.client_account_id == tenant_context['client_account_id']
    )
    
    if cursor:
        query = query.where(DiscoveryFlow.id > cursor)
    
    query = query.order_by(DiscoveryFlow.id).limit(limit)
    
    result = await session.execute(query)
    return result.scalars().all()

# Efficient relationship loading
async def get_flow_with_relationships(
    session: AsyncSession,
    flow_id: UUID,
    tenant_context: Dict[str, UUID]
) -> Optional[DiscoveryFlow]:
    """Load flow with all relationships in single query"""
    query = select(DiscoveryFlow).options(
        selectinload(DiscoveryFlow.assets).selectinload(Asset.sixr_analysis),
        joinedload(DiscoveryFlow.data_import),
        selectinload(DiscoveryFlow.collection_flows)
    ).where(
        DiscoveryFlow.flow_id == flow_id,
        DiscoveryFlow.client_account_id == tenant_context['client_account_id']
    )
    
    result = await session.execute(query)
    return result.scalar_one_or_none()

# Aggregation queries
async def get_engagement_statistics(
    session: AsyncSession,
    engagement_id: UUID,
    client_account_id: UUID
) -> Dict[str, Any]:
    """Get aggregated statistics for engagement"""
    flows_count = await session.scalar(
        select(func.count(DiscoveryFlow.id)).where(
            DiscoveryFlow.engagement_id == engagement_id,
            DiscoveryFlow.client_account_id == client_account_id
        )
    )
    
    completed_flows = await session.scalar(
        select(func.count(DiscoveryFlow.id)).where(
            DiscoveryFlow.engagement_id == engagement_id,
            DiscoveryFlow.client_account_id == client_account_id,
            DiscoveryFlow.status == 'completed'
        )
    )
    
    avg_progress = await session.scalar(
        select(func.avg(DiscoveryFlow.progress_percentage)).where(
            DiscoveryFlow.engagement_id == engagement_id,
            DiscoveryFlow.client_account_id == client_account_id,
            DiscoveryFlow.status.in_(['active', 'running'])
        )
    )
    
    return {
        'total_flows': flows_count or 0,
        'completed_flows': completed_flows or 0,
        'average_progress': float(avg_progress or 0),
        'completion_rate': (completed_flows / flows_count * 100) if flows_count else 0
    }
```

## Database Management Commands

### Development Commands

```bash
# Run migrations
docker exec migration_backend alembic upgrade head

# Create new migration
docker exec migration_backend alembic revision --autogenerate -m "description"

# Downgrade migration
docker exec migration_backend alembic downgrade -1

# Show migration history
docker exec migration_backend alembic history

# Show current migration
docker exec migration_backend alembic current
```

### Data Management

```bash
# Seed database with test data
docker exec migration_backend python -m scripts.seed_database

# Reset database (development only)
docker exec migration_backend python -m scripts.reset_database

# Backup database
docker exec migration_db pg_dump -U migration_user migration_db > backup_$(date +%Y%m%d).sql

# Restore database
docker exec -i migration_db psql -U migration_user migration_db < backup_20250118.sql
```

## Best Practices

### 1. Query Performance
- Always include tenant filtering in queries
- Use appropriate indexes for common query patterns
- Prefer `selectinload` over `joinedload` for one-to-many relationships
- Use cursor-based pagination for large datasets
- Monitor query performance with `echo=True` in development

### 2. Data Integrity
- Use foreign key constraints to maintain referential integrity
- Implement proper validation in SQLAlchemy models
- Use database transactions for multi-step operations
- Implement soft deletes with `is_active` flags

### 3. Security
- Always validate tenant context in repositories
- Use parameterized queries to prevent SQL injection
- Implement row-level security for additional protection
- Encrypt sensitive data at rest

### 4. Maintenance
- Regular backup schedules for production data
- Monitor database performance metrics
- Keep migration files clean and well-documented
- Test migrations in staging before production

## Troubleshooting

### Common Issues

#### Connection Pool Exhaustion
```python
# Monitor connection pool status
from app.db.database import engine
print(f"Pool size: {engine.pool.size()}")
print(f"Checked in: {engine.pool.checkedin()}")
print(f"Checked out: {engine.pool.checkedout()}")
```

#### Migration Conflicts
```bash
# Resolve migration conflicts
docker exec migration_backend alembic merge heads -m "merge migrations"
```

#### Performance Issues
```sql
-- Find slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC;

-- Analyze table statistics
ANALYZE discovery_flows;
```

---

*Last Updated: 2025-01-18*