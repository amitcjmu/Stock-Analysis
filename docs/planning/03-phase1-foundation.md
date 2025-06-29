# Implementation Plan: Part 3 - Phase 1: Foundation (Weeks 1-2)

## Overview
Phase 1 establishes the foundational infrastructure, core patterns, and development environment that will support all subsequent development phases.

## Week 1: Infrastructure and Core Setup

### Day 1-2: Development Environment Setup

#### Project Structure Creation
```
project-root/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── context.py
│   │   │   └── security.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── tenant.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   └── dependencies.py
│   │   ├── flows/
│   │   │   ├── __init__.py
│   │   │   └── base.py
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   └── base.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── base.py
│   │   └── tests/
│   ├── requirements/
│   │   ├── base.txt
│   │   ├── dev.txt
│   │   └── prod.txt
│   ├── alembic/
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── types/
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── Dockerfile
├── infrastructure/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── k8s/
│   └── terraform/
├── docs/
│   ├── api/
│   ├── architecture/
│   └── deployment/
├── scripts/
│   ├── setup.sh
│   ├── test.sh
│   └── deploy.sh
└── .github/
    └── workflows/
```

#### Core Dependencies Setup
```toml
# backend/pyproject.toml
[tool.poetry]
name = "ai-migration-platform"
version = "0.1.0"
description = "AI-powered cloud migration orchestration platform"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
pydantic = "^2.5.0"
sqlalchemy = {extras = ["asyncio"], version = "^2.0.0"}
alembic = "^1.13.0"
asyncpg = "^0.29.0"
redis = "^5.0.0"
crewai = "^0.40.0"
openai = "^1.3.0"
anthropic = "^0.7.0"
pgvector = "^0.2.0"
prometheus-client = "^0.19.0"
opentelemetry-api = "^1.21.0"
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
httpx = "^0.25.0"

[tool.poetry.group.dev.dependencies]
black = "^23.11.0"
isort = "^5.12.0"
mypy = "^1.7.0"
pytest-cov = "^4.1.0"
pre-commit = "^3.5.0"
```

```json
// frontend/package.json
{
  "name": "ai-migration-platform-ui",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "jest",
    "test:e2e": "playwright test"
  },
  "dependencies": {
    "next": "14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@tanstack/react-query": "^5.8.0",
    "zustand": "^4.4.0",
    "@radix-ui/react-*": "latest",
    "tailwindcss": "^3.3.0",
    "typescript": "^5.2.0",
    "zod": "^3.22.0",
    "react-hook-form": "^7.47.0",
    "@hookform/resolvers": "^3.3.0"
  },
  "devDependencies": {
    "@types/node": "^20.9.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "eslint": "^8.53.0",
    "eslint-config-next": "14.0.0",
    "@playwright/test": "^1.40.0",
    "jest": "^29.7.0",
    "@testing-library/react": "^13.4.0"
  }
}
```

#### Docker Configuration
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: migration_postgres
    environment:
      POSTGRES_DB: migration_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: migration_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: development
    container_name: migration_backend
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/migration_db
      - REDIS_URL=redis://redis:6379
      - ENVIRONMENT=development
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: development
    container_name: migration_frontend
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
    command: npm run dev

volumes:
  postgres_data:
  redis_data:
```

### Day 3-4: Core Framework Implementation

#### FastAPI Application Setup
```python
# backend/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.database import engine
from app.api.v1.router import api_router
from app.middleware.logging import LoggingMiddleware
from app.middleware.metrics import MetricsMiddleware
from app.middleware.tenant import TenantMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown

def create_application() -> FastAPI:
    app = FastAPI(
        title="AI Migration Platform API",
        description="Enterprise cloud migration orchestration platform",
        version="1.0.0",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan
    )

    # Security middleware
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware
    app.add_middleware(TenantMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(LoggingMiddleware)

    # Include routers
    app.include_router(api_router, prefix="/api/v1")

    return app

app = create_application()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4
    )
```

#### Configuration Management
```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "AI Migration Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # API
    API_V1_STR: str = "/api/v1"
    ALLOWED_HOSTS: List[str] = ["*"]
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # LLM
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    DEEPINFRA_API_KEY: Optional[str] = None
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Monitoring
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def database_url_async(self) -> str:
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

settings = Settings()
```

### Day 5: Database Foundation

#### Database Models and Migrations
```python
# backend/app/models/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, UUID
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

```python
# backend/app/models/tenant.py
from sqlalchemy import Column, String, JSON, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

class Tenant(BaseModel):
    __tablename__ = "tenants"
    
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    settings = Column(JSON, default={})
    is_active = Column(Boolean, default=True)
    
    # Relationships
    flows = relationship("Flow", back_populates="tenant", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="tenant", cascade="all, delete-orphan")
```

```sql
-- backend/sql/init.sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create initial tenant for development
INSERT INTO tenants (id, name, slug, settings, is_active) 
VALUES (
    uuid_generate_v4(),
    'Development Tenant',
    'dev-tenant',
    '{"max_flows": 1000, "features": ["all"]}',
    true
);
```

#### Async Database Setup
```python
# backend/app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.database_url_async,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    poolclass=NullPool if settings.ENVIRONMENT == "test" else None
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

## Week 2: Core Patterns and Multi-Tenancy

### Day 6-7: Multi-Tenant Context System

#### Tenant Context Management
```python
# backend/app/core/context.py
from contextvars import ContextVar
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class TenantContext(BaseModel):
    tenant_id: UUID
    user_id: Optional[UUID] = None
    permissions: List[str] = []

# Context variables
current_tenant: ContextVar[Optional[TenantContext]] = ContextVar('current_tenant', default=None)

def get_current_tenant() -> Optional[TenantContext]:
    return current_tenant.get()

def set_current_tenant(context: TenantContext):
    current_tenant.set(context)
```

#### Tenant Middleware
```python
# backend/app/middleware/tenant.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.context import set_current_tenant, TenantContext
from app.services.tenant import TenantService
import uuid

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract tenant information from headers
        tenant_id = request.headers.get("X-Tenant-ID")
        user_id = request.headers.get("X-User-ID")
        
        if tenant_id:
            try:
                tenant_uuid = uuid.UUID(tenant_id)
                user_uuid = uuid.UUID(user_id) if user_id else None
                
                # Verify tenant exists and is active
                tenant_service = TenantService()
                tenant = await tenant_service.get_by_id(tenant_uuid)
                
                if not tenant or not tenant.is_active:
                    raise HTTPException(status_code=403, detail="Invalid or inactive tenant")
                
                # Set context
                context = TenantContext(
                    tenant_id=tenant_uuid,
                    user_id=user_uuid,
                    permissions=[]  # Will be loaded from auth service
                )
                set_current_tenant(context)
                
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid tenant or user ID format")
        
        response = await call_next(request)
        return response
```

### Day 8-9: Repository Pattern Implementation

#### Base Repository with Tenant Scoping
```python
# backend/app/repositories/base.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import DeclarativeBase
from app.core.context import get_current_tenant
from uuid import UUID

ModelType = TypeVar("ModelType", bound=DeclarativeBase)

class BaseRepository(Generic[ModelType], ABC):
    def __init__(self, db: AsyncSession, model: type[ModelType]):
        self.db = db
        self.model = model
    
    def _get_tenant_query(self):
        """Apply tenant filtering to queries"""
        tenant = get_current_tenant()
        if not tenant:
            raise ValueError("No tenant context available")
        
        query = select(self.model)
        if hasattr(self.model, 'tenant_id'):
            query = query.where(self.model.tenant_id == tenant.tenant_id)
        
        return query
    
    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        query = self._get_tenant_query().where(self.model.id == id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        query = self._get_tenant_query().offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def create(self, obj_data: dict) -> ModelType:
        # Automatically add tenant_id
        tenant = get_current_tenant()
        if tenant and hasattr(self.model, 'tenant_id'):
            obj_data['tenant_id'] = tenant.tenant_id
        
        obj = self.model(**obj_data)
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj
    
    async def update(self, id: UUID, obj_data: dict) -> Optional[ModelType]:
        query = (
            update(self.model)
            .where(self.model.id == id)
            .values(**obj_data)
            .returning(self.model)
        )
        
        # Apply tenant filtering
        tenant = get_current_tenant()
        if tenant and hasattr(self.model, 'tenant_id'):
            query = query.where(self.model.tenant_id == tenant.tenant_id)
        
        result = await self.db.execute(query)
        await self.db.commit()
        return result.scalar_one_or_none()
```

### Day 10: Testing Foundation

#### Testing Infrastructure Setup
```python
# backend/tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import get_db, Base
from app.core.context import set_current_tenant, TenantContext
import uuid

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5433/test_db"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(test_engine):
    async with AsyncSession(test_engine) as session:
        yield session
        await session.rollback()

@pytest.fixture
def override_get_db(db_session):
    def _override_get_db():
        yield db_session
    return _override_get_db

@pytest.fixture
async def client(override_get_db):
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def tenant_context():
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    context = TenantContext(tenant_id=tenant_id, user_id=user_id)
    set_current_tenant(context)
    return context
```

#### Example Test Cases
```python
# backend/tests/test_tenant_isolation.py
import pytest
from uuid import uuid4
from app.models.tenant import Tenant
from app.repositories.tenant import TenantRepository

@pytest.mark.asyncio
class TestTenantIsolation:
    async def test_tenant_creation(self, db_session):
        repo = TenantRepository(db_session)
        
        tenant_data = {
            "name": "Test Tenant",
            "slug": "test-tenant",
            "settings": {"feature_flags": ["ai_agents"]}
        }
        
        tenant = await repo.create(tenant_data)
        
        assert tenant.id is not None
        assert tenant.name == "Test Tenant"
        assert tenant.slug == "test-tenant"
        assert tenant.is_active is True
    
    async def test_tenant_scoped_queries(self, db_session, tenant_context):
        repo = TenantRepository(db_session)
        
        # Create tenant should be scoped to current context
        tenant = await repo.create({
            "name": "Scoped Tenant",
            "slug": "scoped-tenant"
        })
        
        # Verify tenant is associated with current context
        assert tenant.tenant_id == tenant_context.tenant_id
```

## Deliverables for Phase 1

### Infrastructure Deliverables
1. **Complete Development Environment**: Docker Compose setup with all services
2. **CI/CD Pipeline**: GitHub Actions for testing and deployment
3. **Project Structure**: Clean, scalable project organization
4. **Configuration Management**: Environment-based configuration system

### Code Deliverables
1. **FastAPI Application**: Basic API framework with middleware
2. **Database Layer**: Async SQLAlchemy with migrations
3. **Multi-Tenant System**: Context management and repository pattern
4. **Testing Framework**: Pytest setup with fixtures and utilities

### Documentation Deliverables
1. **Setup Guide**: Complete development environment setup
2. **Architecture Documentation**: System design and patterns
3. **API Documentation**: OpenAPI specification
4. **Testing Guide**: Testing strategies and best practices

### Quality Gates
- [ ] All services start successfully in Docker
- [ ] Database migrations run without errors
- [ ] Tenant isolation is properly implemented
- [ ] Test suite runs with 100% pass rate
- [ ] Code coverage > 80%
- [ ] All linting and type checking passes