# CLAUDE.md - CRITICAL INSTRUCTIONS FOR AI AGENTS

⚠️ **STOP! READ THIS ENTIRE FILE BEFORE WRITING ANY CODE** ⚠️

This file provides **MANDATORY** guidance to Claude Code (claude.ai/code) and all AI agents when working with code in this repository.

## 🛑 CRITICAL RULES - VIOLATIONS WILL BREAK THE APPLICATION

### 1. **NEVER RUN ANYTHING LOCALLY**
- ❌ **NEVER** run `npm install`, `pip install`, `python`, `node`, or ANY commands locally
- ✅ **ALWAYS** use Docker: `docker exec migration_backend <command>`
- ✅ **ALWAYS** use Docker: `docker exec migration_frontend <command>`

### 2. **NEVER USE LEGACY PATTERNS**
- ❌ **NEVER** use `DataImportRepository`, `FieldMappingRepository` - DELETED July 6, 2025
- ❌ **NEVER** use V3 API patterns - DELETED July 6, 2025
- ❌ **NEVER** use session_id - use flow_id
- ❌ **NEVER** create pseudo-agents - use real CrewAI patterns only
- ✅ **ALWAYS** use direct SQLAlchemy queries for data access
- ✅ **ALWAYS** use Master Flow Orchestrator for flow management

### 3. **CORRECT IMPORT PATHS**
- ❌ **NEVER** `from app.models.user import User`
- ✅ **ALWAYS** `from app.models.client_account import User`
- ❌ **NEVER** `from app.core.auth import get_current_user`
- ✅ **ALWAYS** `from app.api.v1.auth.auth_utils import get_current_user`

### 4. **UNDERSTAND THE ARCHITECTURE BEFORE CODING**
- 📖 **MUST READ**: `/docs/development/PLATFORM_EVOLUTION_AND_CURRENT_STATE.md`
- 📖 **MUST READ**: Architecture is Phase 5 Flow-Based (98% complete)
- 📖 **MUST KNOW**: All flows use Master Flow Orchestrator pattern
- 📖 **MUST KNOW**: Real CrewAI agents only - no pseudo-agents



## 🎉 Master Flow Orchestrator Implementation Complete

**Completion Date:** 2025-07-05 22:17:07 UTC  
**Implementation Status:** ✅ COMPLETED  
**All Tasks:** MFO-001 through MFO-114 completed successfully  

### What's New
- ✅ **Master Flow Orchestrator:** Complete unified flow management system
- ✅ **All Flow Types:** Discovery, Assessment, Planning, Execution, Modernize, FinOps, Observability, Decommission
- ✅ **Real CrewAI Integration:** True CrewAI agents and flows (no more pseudo-agents)
- ✅ **Production Ready:** Full deployment, testing, and cleanup completed
- ✅ **Legacy Code Archived:** All deprecated implementations safely archived

### Next Steps
- All development should use the Master Flow Orchestrator system
- Legacy implementations are archived in `/backend/archive/legacy/`
- See `/docs/implementation/MASTER_FLOW_ORCHESTRATOR_SUMMARY.md` for complete details

---

## 🚨 **CRITICAL PLATFORM CONTEXT**

**IMPORTANT**: This platform has evolved through 6 architectural phases and is currently in **active remediation**. Understanding the evolution journey is essential for effective development.

### **Required Reading Before Development**
- `docs/development/PLATFORM_EVOLUTION_AND_CURRENT_STATE.md` - **MUST READ** - Complete evolution journey and current state
- `docs/development/AI_Force_Migration_Platform_Summary_for_Coding_Agents.md` - Platform summary and development context  
- `docs/development/CrewAI_Development_Guide.md` - CrewAI implementation guide
- `docs/planning/REMEDIATION_SUMMARY.md` - Current remediation status and timeline
- `docs/planning/discovery-flow/master-flow-orchestration-analysis.md` - **CRITICAL** - Master flow orchestration system architecture and implementation gaps
- `docs/planning/production-blockers-resolution-report.md` - **NEW** - Production blocker fixes (Echo, Foxtrot, Golf teams)
- `backend/SECURITY_FIX_SUMMARY.md` - **NEW** - Security hardening implementation details

## Platform Overview

The AI Force Migration Platform is an enterprise-grade cloud migration orchestration platform that has evolved through multiple architectural phases. It is currently in **Phase 5 (Flow-Based Architecture) - Production Ready (98% complete)**.

### **Current State Reality Check - POST CLEANUP (July 2025)**
- ✅ **Major Legacy Cleanup Complete**: 30+ legacy files archived to `/backend/archive/legacy/`
- ✅ **V3 API Infrastructure Removed**: Legacy database abstraction layer eliminated
- ✅ **Pseudo-Agents Archived**: All pseudo-agent patterns moved to archive
- ✅ **Backend API Stable**: No critical import errors, health checks passing
- ✅ **PostgreSQL-only state management achieved**
- ✅ **CrewAI Flow patterns ready** (UnifiedDiscoveryFlow with real CrewAI imports)
- ✅ **Multi-tenant architecture working**
- ✅ **Master-Child Flow Linkage Fixed**: Discovery flows properly track parent master flows
- ✅ **Deletion Cascade Working**: Master flow deletion properly cascades to child flows
- ✅ **Production Blockers Resolved**: All critical security, execution, and error handling issues fixed
- ⚠️ **Remaining work**: Session ID cleanup, field mapping UI, assessment flow integration

## Current Architecture (In Remediation)

### **Phase 5 Flow-Based + Production Ready (98% Complete)**
```
Frontend (Vercel) → API v1 Only → UnifiedDiscoveryFlow → CrewAI Crews → True Agents
                                         ↓
                                   PostgreSQL State → Multi-Tenant Context
                                         ↓
                                   Event Bus → Flow Coordination
```

### **Key Components Status - POST CLEANUP**
- **UnifiedDiscoveryFlow**: ✅ CrewAI Flow with `@start/@listen` decorators - REAL AGENTS ENABLED
- **PostgreSQL-Only State**: ✅ SQLite eliminated, full PostgreSQL persistence
- **Multi-Tenant Context**: ✅ `client_account_id` → `engagement_id` → `user_id` hierarchy working
- **Event-Driven Coordination**: ✅ Implemented and stable
- **True CrewAI Agents**: ✅ Pseudo-agents archived, real CrewAI patterns ready
- **API v1 Only**: ✅ V3 legacy database abstraction removed
- **Backend Health**: ✅ All import errors resolved, API endpoints functional
- **Flow Execution**: ✅ CrewAI flows now properly execute with kickoff() integration
- **Security**: ✅ Multi-tenant isolation enforced, SQL injection prevention added
- **Error Handling**: ✅ Centralized error handling with proper logging and tracking

### **Remaining Issues - POST PRODUCTION FIXES (July 2025)**
- **Session ID Cleanup**: Some files may still reference session_id instead of flow_id
- **Assessment Flow Integration**: Assessment flows now properly integrated but need testing
- **Master Flow Dashboard**: No unified flow visibility across all flow types
- **Real CrewAI Implementation**: Discovery flows execute but need actual agent logic

## Development Commands

### **Docker Development (Required)**
```bash
# Start all services
docker-compose up -d --build

# View logs (essential for debugging remediation issues)
docker-compose logs -f backend frontend

# Backend debugging (for remediation work)
docker exec -it migration_backend python -c "your_test_code"
docker exec -it migration_backend python -m pytest tests/

# Frontend development (during API transition)
docker exec -it migration_frontend npm run build
docker exec -it migration_frontend npm run lint

# Database access (for cleanup verification)
docker exec -it migration_db psql -U postgres -d migration_db
```

### **Remediation-Specific Commands**
```bash
# Session ID cleanup audit
docker exec -it migration_backend grep -r "session_id" app/ --include="*.py"

# Flow context debugging
docker exec -it migration_backend python -c "
from app.services.crewai_flows.flow_state_manager import FlowStateManager
# Debug flow context issues
"

# Database migration status
docker exec -it migration_backend alembic history
docker exec -it migration_backend alembic current

# API version usage audit  
docker exec -it migration_frontend grep -r "/api/v" src/ --include="*.ts" --include="*.tsx"
```

### **Build & Test Commands**
```bash
# Frontend (during API transition period)
npm run dev          # Development server (in container)
npm run build        # Production build
npm run lint         # ESLint with TypeScript
npm run test:e2e     # Playwright E2E tests

# Backend (remediation testing)
python -m pytest     # Run tests (in container)
python -m pytest tests/remediation/  # Remediation-specific tests
alembic upgrade head # Database migrations

# Database initialization (IMPORTANT after DB changes)
docker exec -it migration_backend python -m app.core.database_initialization
docker exec -it migration_backend python scripts/setup_platform_admin.py
```

## Critical Technical Patterns

### **Current Flow-Based Patterns (Use These)**
```python
# Use flow_id as primary identifier
async def get_flow_status(flow_id: str):
    async with AsyncSessionLocal() as session:
        flow = await session.get(DiscoveryFlow, flow_id)

# Use proper CrewAI Flow patterns
from crewai import Flow

class UnifiedDiscoveryFlow(Flow):
    @start()
    def initialize_flow(self):
        # Proper flow initialization
        
    @listen(initialize_flow)
    def data_import_phase(self):
        # Event-driven flow steps
```

### **Multi-Tenant Repository Pattern (Working)**
```python
class YourRepository(ContextAwareRepository):
    def __init__(self, db: Session, client_account_id: int):
        super().__init__(db, client_account_id)
        
# Always include multi-tenant headers
headers = {
    'X-Client-Account-ID': client_account_id,
    'X-Engagement-ID': engagement_id
}
```

### **Database Patterns (PostgreSQL-Only)**
```python
# Always use AsyncSessionLocal for database operations
async with AsyncSessionLocal() as session:
    result = await session.execute(query)
    
# JSON serialization safety (still needed)
def safe_json_serialize(data):
    def convert_numeric(obj):
        if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
            return None
        return obj
    return json.dumps(data, default=convert_numeric)
```

### **⚠️ Avoid These Legacy Patterns**
```python
# DON'T USE - Session-based patterns (Phase 2 - Deprecated)
session_id = "disc_session_12345"  # Use flow_id instead
session_manager.create_session()   # Use flow creation

# DON'T USE - Pseudo-agent patterns (Phase 2-3)
class BaseDiscoveryAgent(ABC):  # Use true CrewAI agents
    def execute(self, data):    # Use CrewAI crew patterns

# DON'T USE - Dual persistence (Phase 3)  
@persist()  # PostgreSQL-only now, no SQLite

# DON'T USE - Creating flows without master registration
assessment_flow = create_assessment_flow()  # Missing master flow
# ALWAYS register with master flow system - see master flow doc
```

## 🗑️ DELETED CODE - DO NOT USE OR REFERENCE

### **These Classes/Modules Were PERMANENTLY DELETED on July 6, 2025:**
```python
# ❌ DELETED - Repository Pattern (replaced with direct queries)
from app.repositories.data_import_repository import DataImportRepository  # DOES NOT EXIST
from app.repositories.field_mapping_repository import FieldMappingRepository  # DOES NOT EXIST
from app.repositories.v3.* import *  # ALL V3 REPOSITORIES DELETED

# ❌ DELETED - V3 Services (replaced with V1 API)
from app.services.v3.* import *  # ALL V3 SERVICES DELETED

# ❌ DELETED - Pseudo-Agents (replaced with real CrewAI)
from app.services.agents.base_discovery_agent import BaseDiscoveryAgent  # DELETED
from app.services.agents.data_import_validation_agent import *  # DELETED
from app.services.agents.attribute_mapping_agent import *  # DELETED
```

### **Use These Patterns Instead:**
```python
# ✅ Direct Database Queries
from sqlalchemy import select
from app.models.data_import.core import DataImport
from app.models.data_import.mapping import ImportFieldMapping

data_imports = await db.execute(
    select(DataImport).where(DataImport.client_account_id == context.client_account_id)
)

# ✅ Real CrewAI Patterns
from crewai import Agent, Task, Crew
agent = Agent(role="Data Analyst", goal="Analyze data quality")
```

## Key API Endpoints

### **API Usage - POST CLEANUP**
✅ **Current Reality**: Backend uses **API v1 only** - V3 legacy database abstraction removed.

#### **API v1 (Primary and Only Backend API)**
- `POST /api/v1/unified-discovery/flow/initialize` - Initialize discovery flow
- `GET /api/v1/unified-discovery/flow/status/{flow_id}` - Flow status (flow_id supported)
- `POST /api/v1/data-import/store-import` - Data import endpoint
- `GET /api/v1/health` - System health check (requires tenant headers)
- `GET /api/v1/discovery/flows/active` - Get active discovery flows (no placeholder)
- `GET /api/v1/master-flows/active` - Get all active flows across types (discovery + assessment + etc)
- `DELETE /api/v1/master-flows/{flow_id}` - Delete any flow via master orchestration

#### **Archived/Removed APIs**
- ❌ **API v3**: Entire V3 infrastructure archived - was legacy database abstraction layer
- ❌ **V3 Services**: V3DiscoveryFlowService, V3DataImportService etc. all archived
- ❌ **Pseudo-Agent APIs**: All pseudo-agent endpoints archived

#### **Development Guidance - POST CLEANUP**
- **All features**: Use API v1 only
- **Frontend**: Update to use v1 consistently, remove v3 references
- **Backend**: V3 routes completely removed from main.py
- **Testing**: Test v1 API only, ensure multi-tenant headers included

### **Admin & Monitoring**
- `GET /api/v1/observability/agents/status` - Agent health monitoring
- `GET /api/v1/admin/llm-usage/usage/report` - LLM usage analytics

## Active Agent Architecture

### **CrewAI Agents - POST CLEANUP**
**Pseudo-Agents Archived**: All pseudo-agent implementations moved to `/backend/archive/legacy/`

#### **Active Real CrewAI Agents**
1. **Asset Intelligence Agent** - ✅ True CrewAI agent (observability)
2. **Agent Health Monitor** - ✅ Performance monitoring working
3. **Performance Analytics Agent** - ✅ Optimization analysis working
4. **UnifiedDiscoveryFlow** - ✅ Real CrewAI Flow with @start/@listen decorators

#### **Archived Pseudo-Agents (moved to archive/legacy/)**
- ❌ **DataImportValidationAgent** - Pure Pydantic pseudo-agent
- ❌ **AttributeMappingAgent** - Pure Pydantic pseudo-agent  
- ❌ **DataCleansingAgent** - Pure Pydantic pseudo-agent
- ❌ **BaseDiscoveryAgent** - Pseudo-agent base class
- ❌ **DiscoveryAgentOrchestrator** - Orchestrator for pseudo-agents

#### **Next Steps**
- **Implement Real CrewAI Discovery Agents**: Replace archived pseudo-agents with true CrewAI implementations
- **Use UnifiedDiscoveryFlow**: Direct CrewAI Flow execution for discovery processes
- **No More Pseudo-Agents**: All new agent implementations must use real CrewAI patterns

## Important Development Rules

### **Post-Cleanup Development**
- **Clean State**: V3 APIs removed, pseudo-agents archived, backend stable
- **V1 API Only**: Use only v1 endpoints, no v3 references
- **Real CrewAI Only**: No pseudo-agent patterns, use true CrewAI flows
- **Session ID Cleanup**: Continue eliminating session_id references in favor of flow_id
- **Master Flow Registration**: ALL flow types MUST register with master orchestration system (see master flow doc)

### **Real CrewAI-First Development** 
- **NEVER** implement hard-coded rules or static logic
- **NEVER** create pseudo-agents (Pydantic-based) - all archived
- **ALWAYS** use real CrewAI agents with @start/@listen decorators
- **Use UnifiedDiscoveryFlow**: For discovery processes, use the real CrewAI Flow
- **Use Learning Systems**: Agents must learn from user feedback

### **Docker-First Development**
- **NEVER** run services locally (Python, PostgreSQL, Node.js)
- **ALWAYS** use Docker containers for all development
- **Use `docker exec`** for debugging and testing

### **Multi-Tenant Architecture**
- **All data access** must be client account scoped
- **Use `ContextAwareRepository`** pattern consistently
- **Include multi-tenant headers** in all API calls
- **Test tenant isolation** in all new features

## Environment Configuration

### **Production Deployment (Current)**
```bash
# Railway Backend
DATABASE_URL=postgresql://...
DEEPINFRA_API_KEY=your_key
CREWAI_ENABLED=true
ALLOWED_ORIGINS=https://your-app.vercel.app

# Post-Cleanup Feature Flags
ENABLE_FLOW_ID_PRIMARY=true
USE_POSTGRES_ONLY_STATE=true
API_V3_ENABLED=false  # V3 completely removed
CLEANUP_COMPLETE=true
REAL_CREWAI_ONLY=true

# Vercel Frontend
NEXT_PUBLIC_API_URL=https://your-railway-app.railway.app
NEXT_PUBLIC_API_V1_ONLY=true  # V3 removed
```

## 🔑 Database Initialization & Platform Admin Setup

### **CRITICAL: Authentication Requirements**
1. **ALL users MUST have UserProfile records with `status='active'` to login**
2. **Platform Admin**: chocka@gmail.com / Password123!
3. **Demo UUIDs use pattern**: XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX (DEFault/DEmo)
4. **NO demo client admin accounts** - only platform admin can create client admins

### **Database Initialization (Manual)**
⚠️ **IMPORTANT**: Database initialization is NOT automatic. Run it when:
- Setting up a new database
- After major schema changes
- If users report "Account not approved" errors
- When resetting demo data

```python
# Run manually via CLI:
docker exec migration_backend python -m app.core.database_initialization

# Or in code:
from app.core.database_initialization import initialize_database
from app.core.database import AsyncSessionLocal

async with AsyncSessionLocal() as db:
    await initialize_database(db)
```

### **Key Initialization Modules**
- `app/core/database_initialization.py` - Automated setup ensuring platform requirements
- `app/core/migration_hooks.py` - Alembic hooks for migrations
- `app/core/seed_data_config.py` - Centralized seed data configuration

### **In Alembic Migrations**
```python
from app.core.migration_hooks import MigrationHooks

def upgrade():
    # Your schema changes
    # Then ensure data consistency:
    MigrationHooks.run_all_hooks(op)
```

### **Manual Setup (if needed)**
```bash
# Clean and setup platform admin
docker exec migration_backend python scripts/clean_all_demo_data_fixed.py
docker exec migration_backend python scripts/setup_platform_admin.py
```

## Key Files & Directories

### **Backend Structure - POST CLEANUP**
```
backend/app/services/crewai_flows/
├── unified_discovery_flow.py         # ✅ Main CrewAI Flow (REAL AGENTS ENABLED)
├── flow_state_manager.py            # ✅ High-level state management
├── persistence/
│   ├── postgres_store.py            # ✅ PostgreSQL state store
│   ├── state_recovery.py            # ✅ Recovery mechanisms
│   └── state_migrator.py            # ✅ Session→flow migration tools
├── crews/                           # ✅ Real CrewAI agent implementations
└── tools/                           # ✅ Agent tools working

backend/app/core/
└── flow_state_validator.py         # ✅ State validation engine

backend/app/api/
├── v1/                              # ✅ Primary and ONLY API
│   ├── unified_discovery.py         # ✅ Main discovery endpoints
│   └── endpoints/                   # ✅ All functional endpoints
└── v2/discovery_flow_v2.py          # ❌ Deprecated (still exists)

backend/archive/legacy/              # 🗂️ ARCHIVED LEGACY CODE
├── app/services/v3/                 # ❌ Legacy database abstraction
├── app/services/agents/             # ❌ Pseudo-agent implementations
│   ├── base_discovery_agent.py     # ❌ Pseudo-agent base class
│   ├── data_import_validation_agent.py # ❌ Pseudo-agent
│   └── attribute_mapping_agent.py  # ❌ Pseudo-agent
└── app/api/v1/discovery_flow_new.py # ❌ Mixed v1/v3 implementation
```

### **Frontend Structure (Post January 2025 Cleanup)**
```
src/hooks/
├── useUnifiedDiscoveryFlow.ts     # ⚠️ Mixed v1/v3 API calls
└── discovery/
    └── useDiscoveryFlowStatus.ts  # ✅ NEW: Consolidated flow status hook (replaces duplicates)

src/pages/discovery/
├── CMDBImport.tsx                 # ✅ Uses v1 API, route fixed to /discovery/cmdb-import
└── AttributeMapping.tsx           # ⚠️ Field mapping UI issues

src/components/discovery/
└── SimplifiedFlowStatus.tsx       # ✅ Updated to use consolidated hook

src/config/
└── flowRoutes.ts                  # ✅ Centralized routing for all flow types

src/utils/migration/
└── sessionToFlow.ts               # ⚠️ Migration utilities still active

DELETED (January 2025 Cleanup):
- src/archive/hooks/discovery/useDiscoveryFlowV2.ts
- src/archive/hooks/discovery/useIncompleteFlowDetectionV2.ts
```

## Major Cleanup Status (98% Complete)

### **✅ Completed (Major Cleanup + Production Fixes January 2025)**
- ✅ **Legacy Code Archived**: 30+ files moved to `/backend/archive/legacy/`
- ✅ **V3 API Infrastructure Removed**: Legacy database abstraction eliminated
- ✅ **Pseudo-Agents Archived**: All Pydantic-based pseudo-agents removed
- ✅ **Backend Import Errors Fixed**: All critical import issues resolved
- ✅ **API Endpoints Functional**: Health checks passing, multi-tenant working
- ✅ **PostgreSQL-only state management**
- ✅ **CrewAI Flow framework ready** (UnifiedDiscoveryFlow with real CrewAI)
- ✅ **Multi-tenant architecture stable**
- ✅ **Flow Execution Fixed**: CrewAI flows now properly execute via kickoff()
- ✅ **Security Hardened**: Multi-tenant isolation, SQL injection prevention
- ✅ **Error Handling Centralized**: Proper error tracking and logging
- ✅ **Master-Child Flow Linkage**: Discovery flows properly linked to master flows
- ✅ **Deletion Cascade**: Master flow deletion cascades to all child flows
- ✅ **Frontend API Fixed**: Corrected endpoints for flow management
- ✅ **Discovery Flow Status Polling Fixed**: Consolidated duplicate implementations (January 2025)
- ✅ **Unused Discovery Endpoints Removed**: Cleaned up abort and processing-status endpoints
- ✅ **Frontend Hooks Consolidated**: Created useDiscoveryFlowStatus to replace 6 duplicate hooks

### **⚠️ Remaining Work (1-2 weeks)**
- Session_id → flow_id cleanup in remaining files
- Master flow dashboard implementation
- Implement real CrewAI agent logic (flows execute but need business logic)
- Complete flow type coverage (Plan, Execute, Modernize, FinOps, etc)
- Performance optimization

### **🔧 Daily Development Impact - POST CLEANUP**
- **Backend is stable** - no critical import errors
- **Use V1 API only** - V3 completely removed
- **Multi-tenant headers required** - all API calls need X-Client-Account-Id and X-Engagement-Id
- **Real CrewAI patterns only** - no pseudo-agent implementations
- **UnifiedDiscoveryFlow ready** for implementing real CrewAI discovery processes

## Common Pitfalls - POST CLEANUP

1. **Referencing archived code** - Don't import from `/backend/archive/legacy/`
2. **Using V3 API patterns** - V3 infrastructure completely removed
3. **Creating pseudo-agents** - All agent implementations must use real CrewAI
4. **Ignoring multi-tenant headers** - All API calls require tenant context
5. **Not using UnifiedDiscoveryFlow** - Use real CrewAI flows for discovery processes
6. **Forgetting Docker** - All development must be containerized
7. **Hard-coding business rules** - Platform is real CrewAI-first by design
8. **Creating flows without master registration** - ALL flow types MUST register with CrewAIFlowStateExtensions
9. **Router prefix duplication** - API routers should NOT have their own prefix when included with prefix
10. **Creating duplicate flow status hooks** - Use useDiscoveryFlowStatus hook, don't create new polling logic
11. **Using removed discovery endpoints** - Check /docs/cleanup/active-discovery-endpoints.md for valid endpoints

## Documentation and Commit Guidelines
- **NEVER** reference Claude Code, Anthropic, or any AI coding assistant in git commit messages
- **NEVER** reference AI assistants in project documentation or code comments
- **Focus on technical changes and business value** in commit messages
- **Document remediation progress** when contributing to cleanup efforts

---

## 🚀 QUICK REFERENCE FOR AI AGENTS

### **Before Writing ANY Code:**
1. ✅ Read this entire CLAUDE.md file
2. ✅ Use Docker for ALL commands
3. ✅ Check if the class/module you're importing was DELETED
4. ✅ Use correct import paths from this guide
5. ✅ Understand Master Flow Orchestrator pattern

### **Common Mistakes AI Agents Make:**
- ❌ Using `DataImportRepository` (deleted July 6, 2025)
- ❌ Using `FieldMappingRepository` (deleted July 6, 2025)  
- ❌ Running commands locally instead of Docker
- ❌ Using old User import path
- ❌ Creating pseudo-agents instead of real CrewAI
- ❌ Using session_id instead of flow_id
- ❌ Creating duplicate flow polling logic (use useDiscoveryFlowStatus hook)
- ❌ Using `/api/v1/discovery/flow/{id}/abort` endpoint (removed January 2025)
- ❌ Using `/api/v1/discovery/flow/{id}/processing-status` endpoint (removed January 2025)

### **If You're Unsure:**
- 📖 Check `/docs/development/PLATFORM_EVOLUTION_AND_CURRENT_STATE.md`
- 🔍 Search for the pattern in this file's "DELETED CODE" section
- 🐳 Always use Docker: `docker exec migration_backend <command>`

---

**Current Platform State**: Phase 5 (Flow-Based Architecture) + Production Ready (98% complete)  
**Key Architecture Gap**: Real CrewAI agent logic needs implementation (flows execute but lack business logic)  
**Estimated Completion**: 1-2 weeks for agent logic implementation and remaining cleanup  
**Development Context**: Production-ready with all critical blockers resolved, flows properly linked  
**Last Updated**: January 14th 2025 - Added discovery flow cleanup documentation and consolidated hooks