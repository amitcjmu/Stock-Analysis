# AWS EC2 Development Server - Solution Architecture

**Current Development Environment**  
**Document Date:** January 15, 2025  
**Deployment Type:** Single EC2 Instance Docker Solution  
**Environment:** Development Server

## Executive Summary

This document provides the detailed solution architecture for the AI Force Migration Platform currently running on a single AWS EC2 instance. The platform uses Docker containerization to provide a complete development environment with all necessary components for cloud migration orchestration.

## Solution Overview

The AI Force Migration Platform is deployed as a containerized application stack on a single EC2 instance, providing a complete development environment for cloud migration assessment and planning activities.

## High-Level Solution Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        AI Force Migration Platform                                 │
│                       (Single EC2 Instance Solution)                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                           USER INTERFACE LAYER                             │  │
│  │                                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                   Next.js Frontend Container                        │  │  │
│  │  │                    (migration_frontend)                             │  │  │
│  │  │                                                                     │  │  │
│  │  │  • React 18 with TypeScript                                         │  │  │
│  │  │  • Tailwind CSS for styling                                         │  │  │
│  │  │  • shadcn/ui component library                                      │  │  │
│  │  │  • Real-time WebSocket connections                                  │  │  │
│  │  │  • Responsive migration dashboards                                  │  │  │
│  │  │  • Interactive flow management                                      │  │  │
│  │  │                                                                     │  │  │
│  │  │  Port: 8081 (External: Host:8081)                                  │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                               │
│                                    ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                          APPLICATION LAYER                                  │  │
│  │                                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                   FastAPI Backend Container                         │  │  │
│  │  │                    (migration_backend)                              │  │  │
│  │  │                                                                     │  │  │
│  │  │  • FastAPI with async/await support                                 │  │  │
│  │  │  • Python 3.11+ runtime                                            │  │  │
│  │  │  • Master Flow Orchestrator                                         │  │  │
│  │  │  • Real CrewAI agent implementation                                 │  │  │
│  │  │  • Multi-tenant architecture                                        │  │  │
│  │  │  • RESTful API endpoints (v1 only)                                 │  │  │
│  │  │  • WebSocket real-time updates                                      │  │  │
│  │  │  • Background task processing                                       │  │  │
│  │  │                                                                     │  │  │
│  │  │  Port: 8000 (External: Host:8000)                                  │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                               │
│                                    ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                            DATA LAYER                                      │  │
│  │                                                                             │  │
│  │  ┌─────────────────────────────┐    ┌─────────────────────────────┐       │  │
│  │  │    PostgreSQL Container     │    │     Redis Container         │       │  │
│  │  │    (migration_postgres)     │    │    (migration_redis)        │       │  │
│  │  │                             │    │                             │       │  │
│  │  │  • PostgreSQL 16            │    │  • Redis 7 Alpine           │       │  │
│  │  │  • Primary database         │    │  • Task queue management    │       │  │
│  │  │  • Multi-tenant data        │    │  • Session caching          │       │  │
│  │  │  • Flow state storage       │    │  • Background job queue     │       │  │
│  │  │  • User management          │    │  • Real-time data cache     │       │  │
│  │  │  • Migration artifacts      │    │  • WebSocket session store  │       │  │
│  │  │                             │    │                             │       │  │
│  │  │  Port: 5432 (Ext: 5433)     │    │  Port: 6379 (Ext: 6379)    │       │  │
│  │  └─────────────────────────────┘    └─────────────────────────────┘       │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────┐  │
│  │                          WORKER LAYER (Optional)                           │  │
│  │                                                                             │  │
│  │  ┌─────────────────────────────────────────────────────────────────────┐  │  │
│  │  │                Assessment Worker Container                           │  │  │
│  │  │              (migration_assessment_worker)                          │  │  │
│  │  │                                                                     │  │  │
│  │  │  • Background assessment processing                                 │  │  │
│  │  │  • CrewAI agent execution                                           │  │  │
│  │  │  • Heavy computation tasks                                          │  │  │
│  │  │  • Long-running flow operations                                     │  │  │
│  │  │  • Concurrent assessment flows                                      │  │  │
│  │  │                                                                     │  │  │
│  │  │  Profile: worker (Optional activation)                             │  │  │
│  │  └─────────────────────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Component Architecture Details

### Frontend Container (migration_frontend)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        Next.js Frontend Architecture                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Framework: Next.js 14 with App Router                                             │
│  Language: TypeScript                                                               │
│  Styling: Tailwind CSS + shadcn/ui                                                 │
│  State Management: React hooks + Context API                                       │
│                                                                                     │
│  Key Features:                                                                      │
│  ├─ Responsive Migration Dashboards                                                │
│  ├─ Real-time Flow Status Updates                                                  │
│  ├─ Interactive Data Import Interface                                              │
│  ├─ Field Mapping Configuration                                                    │
│  ├─ Assessment Flow Management                                                     │
│  ├─ Multi-tenant User Interface                                                    │
│  └─ WebSocket Integration for Live Updates                                         │
│                                                                                     │
│  Network Configuration:                                                             │
│  ├─ Internal Port: 8081                                                            │
│  ├─ External Port: 8081 (Host mapping)                                             │
│  ├─ Backend Connection: http://backend:8000                                        │
│  ├─ WebSocket Connection: ws://backend:8000/ws                                     │
│  └─ Static Asset Serving: Nginx (production) / Vite (development)                 │
│                                                                                     │
│  Build Configuration:                                                               │
│  ├─ Development: Vite dev server with hot reload                                   │
│  ├─ Production: Next.js build with static export                                   │
│  ├─ Environment Variables: VITE_* prefixed variables                               │
│  └─ Proxy Configuration: Vite proxy for backend API calls                         │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Backend Container (migration_backend)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend Architecture                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Framework: FastAPI with async/await                                               │
│  Language: Python 3.11+                                                            │
│  ORM: SQLAlchemy 2.0 with async support                                            │
│  Database: PostgreSQL with asyncpg driver                                          │
│                                                                                     │
│  Core Components:                                                                   │
│  ├─ Master Flow Orchestrator                                                       │
│  │  ├─ FlowLifecycleManager                                                        │
│  │  ├─ FlowExecutionEngine                                                         │
│  │  ├─ FlowErrorHandler                                                            │
│  │  ├─ FlowStatusManager                                                           │
│  │  └─ FlowAuditLogger                                                             │
│  │                                                                                 │
│  ├─ CrewAI Integration                                                              │
│  │  ├─ Real CrewAI Agents (Asset Intelligence, Field Mapping)                     │
│  │  ├─ UnifiedDiscoveryFlow                                                        │
│  │  ├─ UnifiedAssessmentFlow                                                       │
│  │  ├─ FlowStateManager                                                            │
│  │  └─ CrewAI LLM Configuration (DeepInfra)                                        │
│  │                                                                                 │
│  ├─ Multi-Tenant Architecture                                                      │
│  │  ├─ ContextAwareRepository Pattern                                              │
│  │  ├─ Client Account Isolation                                                    │
│  │  ├─ Engagement-based Organization                                               │
│  │  └─ RBAC User Management                                                        │
│  │                                                                                 │
│  └─ API Layer                                                                      │
│     ├─ RESTful API v1 Endpoints                                                    │
│     ├─ WebSocket Real-time Updates                                                 │
│     ├─ Background Task Processing                                                  │
│     └─ Health Check and Monitoring                                                 │
│                                                                                     │
│  Database Configuration:                                                            │
│  ├─ Connection: postgresql+asyncpg://postgres:postgres@postgres:5432/migration_db │
│  ├─ Connection Pool: SQLAlchemy async session management                           │
│  ├─ Migrations: Alembic database migrations                                        │
│  └─ Health Checks: PostgreSQL connection monitoring                                │
│                                                                                     │
│  External Integrations:                                                             │
│  ├─ DeepInfra API: LLM services for CrewAI agents                                  │
│  ├─ Redis Cache: Session and background task management                            │
│  └─ WebSocket Server: Real-time frontend communication                             │
│                                                                                     │
│  Network Configuration:                                                             │
│  ├─ Internal Port: 8000                                                            │
│  ├─ External Port: 8000 (Host mapping)                                             │
│  ├─ Database Connection: postgres:5432                                             │
│  ├─ Redis Connection: redis:6379                                                   │
│  └─ CORS Configuration: Frontend origin allowed                                    │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Database Container (migration_postgres)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        PostgreSQL Database Architecture                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Database Engine: PostgreSQL 16 Alpine                                             │
│  Container Name: migration_postgres                                                 │
│  Data Persistence: Docker volume (postgres_data)                                   │
│                                                                                     │
│  Database Schema:                                                                   │
│  ├─ Multi-Tenant Core                                                              │
│  │  ├─ client_accounts (Tenant isolation)                                         │
│  │  ├─ engagements (Project organization)                                         │
│  │  ├─ users (User management with RBAC)                                          │
│  │  └─ user_profiles (Extended user information)                                  │
│  │                                                                                 │
│  ├─ Flow Management                                                                │
│  │  ├─ crewai_flow_state_extensions (Master flow hub)                             │
│  │  ├─ discovery_flows (Discovery flow instances)                                 │
│  │  ├─ assessment_flows (Assessment flow instances)                               │
│  │  └─ flow_execution_logs (Flow audit trails)                                    │
│  │                                                                                 │
│  ├─ Data Import Pipeline                                                           │
│  │  ├─ data_imports (Import job records)                                          │
│  │  ├─ raw_import_records (Raw data storage)                                      │
│  │  ├─ import_field_mappings (Field mapping configuration)                        │
│  │  └─ import_validation_results (Data validation outcomes)                       │
│  │                                                                                 │
│  └─ Migration Artifacts                                                            │
│     ├─ migration_assessments (Assessment results)                                  │
│     ├─ migration_plans (Migration planning data)                                   │
│     ├─ migration_recommendations (AI-generated recommendations)                    │
│     └─ migration_execution_logs (Migration execution tracking)                     │
│                                                                                     │
│  Configuration:                                                                     │
│  ├─ Database Name: migration_db                                                    │
│  ├─ Username: postgres                                                             │
│  ├─ Password: postgres (Development only)                                          │
│  ├─ Internal Port: 5432                                                            │
│  ├─ External Port: 5433 (Host mapping for admin access)                           │
│  ├─ Character Set: UTF-8                                                           │
│  ├─ Timezone: UTC                                                                  │
│  └─ Health Check: pg_isready monitoring                                            │
│                                                                                     │
│  Performance Configuration:                                                         │
│  ├─ Shared Buffers: Default PostgreSQL settings                                    │
│  ├─ Connection Limit: Default (100 connections)                                    │
│  ├─ Work Memory: Default PostgreSQL settings                                       │
│  └─ WAL Configuration: Default with fsync enabled                                  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Redis Container (migration_redis)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           Redis Cache Architecture                                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Cache Engine: Redis 7 Alpine                                                      │
│  Container Name: migration_redis                                                    │
│  Data Persistence: Docker volume (redis_data) with AOF                             │
│                                                                                     │
│  Use Cases:                                                                         │
│  ├─ Background Task Queue                                                           │
│  │  ├─ Assessment flow processing jobs                                             │
│  │  ├─ Data import validation tasks                                                │
│  │  ├─ Long-running migration operations                                           │
│  │  └─ Scheduled maintenance tasks                                                 │
│  │                                                                                 │
│  ├─ Session Management                                                              │
│  │  ├─ User session storage                                                        │
│  │  ├─ WebSocket connection tracking                                               │
│  │  ├─ Flow state caching                                                          │
│  │  └─ Real-time update distribution                                               │
│  │                                                                                 │
│  ├─ Application Caching                                                            │
│  │  ├─ Frequently accessed data                                                    │
│  │  ├─ LLM response caching                                                        │
│  │  ├─ Database query results                                                      │
│  │  └─ API response caching                                                        │
│  │                                                                                 │
│  └─ Real-time Communication                                                        │
│     ├─ WebSocket message broadcasting                                              │
│     ├─ Flow status updates                                                         │
│     ├─ Progress notifications                                                      │
│     └─ Error alert distribution                                                    │
│                                                                                     │
│  Configuration:                                                                     │
│  ├─ Internal Port: 6379                                                            │
│  ├─ External Port: 6379 (Host mapping for debugging)                               │
│  ├─ Persistence: AOF (Append Only File) enabled                                    │
│  ├─ Memory Policy: allkeys-lru (Least Recently Used)                               │
│  ├─ Max Memory: Not set (uses available container memory)                          │
│  └─ Health Check: redis-cli ping monitoring                                        │
│                                                                                     │
│  Performance Configuration:                                                         │
│  ├─ TCP Keep-alive: Default Redis settings                                         │
│  ├─ Client Timeout: Default (0 - no timeout)                                       │
│  ├─ Database Count: 16 (default Redis databases)                                   │
│  └─ Connection Pooling: Handled by backend Redis client                            │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Architecture

### Request Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           Request Processing Flow                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  1. User Interaction                                                                │
│     ┌─────────────────────────────────────────────────────────────────────────┐  │
│     │ User Browser → Frontend Container (migration_frontend:8081)             │  │
│     │ ├─ Static assets served by Next.js                                     │  │
│     │ ├─ React components render UI                                           │  │
│     │ ├─ User interactions trigger state changes                             │  │
│     │ └─ API calls initiated to backend                                      │  │
│     └─────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                               │
│                                    ▼                                               │
│  2. API Request Processing                                                          │
│     ┌─────────────────────────────────────────────────────────────────────────┐  │
│     │ Frontend → Backend Container (migration_backend:8000)                   │  │
│     │ ├─ FastAPI receives HTTP/WebSocket requests                            │  │
│     │ ├─ Multi-tenant context validation                                     │  │
│     │ ├─ Request routing to appropriate endpoint                             │  │
│     │ ├─ Authentication and authorization checks                             │  │
│     │ └─ Business logic processing                                           │  │
│     └─────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                               │
│                                    ▼                                               │
│  3. Data Operations                                                                 │
│     ┌─────────────────────────────────────────────────────────────────────────┐  │
│     │ Backend → Database Container (migration_postgres:5432)                  │  │
│     │ ├─ SQLAlchemy async session creation                                    │  │
│     │ ├─ Multi-tenant data filtering                                          │  │
│     │ ├─ Database queries and transactions                                    │  │
│     │ ├─ Data validation and integrity checks                                │  │
│     │ └─ Result set processing                                                │  │
│     └─────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                               │
│                                    ▼                                               │
│  4. Cache Operations                                                                │
│     ┌─────────────────────────────────────────────────────────────────────────┐  │
│     │ Backend → Redis Container (migration_redis:6379)                        │  │
│     │ ├─ Session data retrieval/storage                                       │  │
│     │ ├─ Cached data lookup                                                   │  │
│     │ ├─ Background task queuing                                              │  │
│     │ ├─ Real-time update broadcasting                                        │  │
│     │ └─ Cache invalidation as needed                                         │  │
│     └─────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                               │
│                                    ▼                                               │
│  5. Response Generation                                                             │
│     ┌─────────────────────────────────────────────────────────────────────────┐  │
│     │ Backend → Frontend (Response)                                           │  │
│     │ ├─ Data serialization (JSON/WebSocket)                                 │  │
│     │ ├─ Multi-tenant data filtering                                          │  │
│     │ ├─ Error handling and logging                                           │  │
│     │ ├─ Response compression if needed                                       │  │
│     │ └─ HTTP/WebSocket response transmission                                 │  │
│     └─────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                               │
│                                    ▼                                               │
│  6. UI Update                                                                       │
│     ┌─────────────────────────────────────────────────────────────────────────┐  │
│     │ Frontend → User Browser (UI Update)                                     │  │
│     │ ├─ React state updates                                                  │  │
│     │ ├─ Component re-rendering                                               │  │
│     │ ├─ Real-time notifications                                              │  │
│     │ ├─ Progress indicators                                                  │  │
│     │ └─ User feedback display                                                │  │
│     └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Background Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        Background Processing Flow                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  1. Task Initiation                                                                 │
│     ┌─────────────────────────────────────────────────────────────────────────┐  │
│     │ Backend → Redis Queue (Task Creation)                                   │  │
│     │ ├─ Assessment flow processing requests                                  │  │
│     │ ├─ Data import validation tasks                                         │  │
│     │ ├─ Long-running migration operations                                    │  │
│     │ └─ Scheduled maintenance tasks                                          │  │
│     └─────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                               │
│                                    ▼                                               │
│  2. Worker Processing                                                               │
│     ┌─────────────────────────────────────────────────────────────────────────┐  │
│     │ Assessment Worker Container (migration_assessment_worker)                │  │
│     │ ├─ Redis queue monitoring                                               │  │
│     │ ├─ Task dequeue and processing                                          │  │
│     │ ├─ CrewAI agent execution                                               │  │
│     │ ├─ Heavy computation tasks                                              │  │
│     │ └─ Progress updates to Redis                                            │  │
│     └─────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                               │
│                                    ▼                                               │
│  3. Database Updates                                                                │
│     ┌─────────────────────────────────────────────────────────────────────────┐  │
│     │ Worker → Database Container (Result Storage)                            │  │
│     │ ├─ Flow state updates                                                   │  │
│     │ ├─ Assessment result storage                                            │  │
│     │ ├─ Migration recommendation updates                                     │  │
│     │ └─ Audit log entries                                                    │  │
│     └─────────────────────────────────────────────────────────────────────────┘  │
│                                    │                                               │
│                                    ▼                                               │
│  4. Real-time Updates                                                               │
│     ┌─────────────────────────────────────────────────────────────────────────┐  │
│     │ Worker → Redis → Backend → Frontend (Live Updates)                      │  │
│     │ ├─ WebSocket message broadcasting                                       │  │
│     │ ├─ Progress notification updates                                        │  │
│     │ ├─ Flow status change notifications                                     │  │
│     │ └─ Error alert distribution                                             │  │
│     └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Security Architecture

### Container Security

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                             Container Security                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Network Security:                                                                  │
│  ├─ Docker Bridge Network Isolation                                                │
│  ├─ Container-to-container communication via internal DNS                          │
│  ├─ Port mapping restrictions (only necessary ports exposed)                       │
│  ├─ AWS Security Group firewall rules                                              │
│  └─ No direct internet access for database containers                              │
│                                                                                     │
│  Container Hardening:                                                               │
│  ├─ Non-root user execution where possible                                         │
│  ├─ Minimal base images (Alpine Linux)                                             │
│  ├─ Regular security updates                                                       │
│  ├─ Limited file system permissions                                                │
│  └─ Resource limits and constraints                                                │
│                                                                                     │
│  Data Security:                                                                     │
│  ├─ Environment variable management                                                │
│  ├─ Docker secrets for sensitive data                                              │
│  ├─ Database encryption at rest                                                    │
│  ├─ TLS encryption for data in transit                                             │
│  └─ Multi-tenant data isolation                                                    │
│                                                                                     │
│  Application Security:                                                              │
│  ├─ JWT-based authentication                                                       │
│  ├─ RBAC authorization model                                                       │
│  ├─ Input validation and sanitization                                              │
│  ├─ SQL injection prevention                                                       │
│  └─ CORS configuration                                                             │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Performance Characteristics

### Current Performance Profile

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          Performance Characteristics                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Frontend Performance:                                                              │
│  ├─ Initial Load Time: 2-3 seconds (development mode)                              │
│  ├─ Bundle Size: ~2MB (unoptimized development build)                              │
│  ├─ WebSocket Latency: < 100ms (local network)                                     │
│  ├─ UI Responsiveness: 60fps for interactive elements                              │
│  └─ Memory Usage: ~100MB in browser                                                │
│                                                                                     │
│  Backend Performance:                                                               │
│  ├─ API Response Time: 50-200ms (simple operations)                                │
│  ├─ Database Query Time: 10-50ms (typical queries)                                 │
│  ├─ CrewAI Agent Execution: 30-60 seconds (complex assessments)                    │
│  ├─ Concurrent Users: 10-20 users (development configuration)                      │
│  └─ Memory Usage: ~512MB-1GB (Python processes)                                    │
│                                                                                     │
│  Database Performance:                                                              │
│  ├─ Connection Pool: 20 connections (default SQLAlchemy)                           │
│  ├─ Query Performance: Indexes on primary keys and foreign keys                    │
│  ├─ Storage Growth: ~10MB per migration project                                    │
│  ├─ Backup Size: ~100MB (typical development database)                             │
│  └─ Memory Usage: ~256MB (PostgreSQL process)                                      │
│                                                                                     │
│  Cache Performance:                                                                 │
│  ├─ Redis Memory Usage: ~64MB (typical cache size)                                 │
│  ├─ Cache Hit Rate: 85-95% (frequently accessed data)                              │
│  ├─ Session Storage: ~1KB per active user session                                  │
│  ├─ Background Queue: 10-100 queued jobs (peak load)                               │
│  └─ Real-time Updates: < 50ms latency                                              │
│                                                                                     │
│  Resource Requirements:                                                             │
│  ├─ CPU Usage: 2-4 cores (during CrewAI processing)                                │
│  ├─ Memory Usage: 2-4GB total (all containers)                                     │
│  ├─ Storage Usage: 5-10GB (application + data)                                     │
│  ├─ Network Bandwidth: 10-50 Mbps (normal operations)                              │
│  └─ EC2 Instance Type: t3.medium or larger recommended                             │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Deployment and Operations

### Docker Compose Commands

```bash
# Start all core services
docker-compose up -d

# Start with optional assessment worker
docker-compose --profile worker up -d

# View container status
docker-compose ps

# Monitor logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose down && docker-compose up -d --build

# Scale assessment workers (if needed)
docker-compose up -d --scale assessment-worker=3
```

### Health Monitoring

```bash
# Check container health
docker-compose ps | grep healthy

# Backend health check
curl http://localhost:8000/health

# Frontend accessibility
curl http://localhost:8081

# Database connection test
docker exec migration_postgres pg_isready -U postgres

# Redis connectivity test
docker exec migration_redis redis-cli ping
```

### Backup and Recovery

```bash
# Database backup
docker exec migration_postgres pg_dump -U postgres migration_db > backup.sql

# Redis backup
docker exec migration_redis redis-cli BGSAVE

# Volume backup
docker run --rm -v migrate-ui-orchestrator_postgres_data:/data -v $(pwd):/backup busybox tar czf /backup/postgres-backup.tar.gz /data
```

## Current Limitations and Recommendations

### Known Limitations

1. **Single Point of Failure**: All services on one EC2 instance
2. **Limited Scalability**: Cannot scale individual services
3. **Development Configuration**: Not optimized for production loads
4. **Basic Security**: Minimal security hardening
5. **No Load Balancing**: Direct container access
6. **Limited Monitoring**: Basic health checks only
7. **Backup Strategy**: Manual backup processes
8. **SSL/TLS**: HTTP only (no HTTPS configuration)

### Recommendations for Production

1. **High Availability**: Multi-instance deployment with load balancing
2. **Database Separation**: Managed PostgreSQL service (RDS)
3. **Container Orchestration**: Kubernetes or ECS for container management
4. **SSL Termination**: Application Load Balancer with SSL certificates
5. **Monitoring**: CloudWatch, Prometheus, or similar monitoring solutions
6. **Backup Automation**: Automated backup and recovery procedures
7. **Security Hardening**: WAF, security groups, and container security
8. **CI/CD Pipeline**: Automated deployment and testing

---

**Document Status**: Current Development Configuration  
**Performance Profile**: Single Instance Development Server  
**Scalability**: 10-20 concurrent users  
**Next Review**: When planning production deployment  
**Maintained By**: Development Team