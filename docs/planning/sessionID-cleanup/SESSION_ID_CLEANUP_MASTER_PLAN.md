# Session ID Final Cleanup - Master Plan

## 🎯 **Mission Statement**

**Goal**: Complete elimination of all session_id references from the codebase  
**Context**: The flow_id migration is 75% complete. Recent comprehensive audit reveals 246 total files with session_id references (originally estimated 132+).  
**Approach**: Staged cleanup with backend focus - maintain migration infrastructure during transition  
**Timeline**: 6-8 weeks with enhanced backend team allocation

## 🚨 **Critical Context**

### **This is NOT a migration - It's a cleanup**
- Migration already happened (flow_id is the primary identifier)
- We're removing leftover session_id code that's causing bugs
- No need for compatibility layers or gradual transitions

### **Active Bugs Being Caused by Residual session_id**
1. **Flow Context Sync Issues**: Data written to wrong tables due to context confusion
2. **Field Mapping UI Broken**: Shows "0 active flows" despite flows existing
3. **Navigation Breaks**: URLs still using sessionId parameters
4. **API Confusion**: Mixed v1/v3 calls with different identifiers

## 📊 **Scope of Work**

**Total Files Identified**: 246 files with session_id usage
- **216 Backend Files** (88%): Core systems, APIs, services, models, repositories
- **30 Frontend Files** (12%): Components, hooks, services (reduced due to modularization)
- **18 Critical Files**: Core system components (must fix first)
- **Modularization Progress**: Main components like CMDBImport.tsx successfully cleaned

## 👥 **Agent Assignments Overview**

| Agent | Focus Area | File Count | Priority Level | Notes |
|-------|------------|------------|----------------|-------|
| **Agent 1** | Core Backend Context | **15** | 🔥 CRITICAL | Expanded scope |
| **Agent 2** | Database Models & Repos | **60** | 🔥 CRITICAL | Major expansion |
| **Agent 3** | Backend APIs & Services | **80** | 🔥 CRITICAL | Massive expansion |
| **Agent 4** | Frontend Infrastructure | **8** | 🔴 HIGH | Preserve migration utils |
| **Agent 5** | Frontend Components | **15** | 🔴 HIGH | Focus on modular hooks |
| **Agent 6** | Backend Services & Testing | **68** | 🔥 CRITICAL | New backend focus |

## 🔄 **Execution Timeline**

### **Weeks 1-2: Critical Backend Foundation**
- **Days 1-3**: Agent 1 completes core context system (CRITICAL BLOCKER)
- **Days 4-7**: Agents 2-3-6 tackle database models, APIs, and core services
- **Days 8-14**: Continue massive backend cleanup (216 files)

### **Weeks 3-4: Backend Services & API Consolidation**
- **Days 15-21**: Complete backend service layer cleanup
- **Days 22-28**: API v3 cleanup and V1 deprecation

### **Weeks 5-6: Frontend & Testing**
- **Days 29-35**: Frontend infrastructure and component updates (30 files)
- **Days 36-42**: Comprehensive testing and final verification

### **Weeks 7-8: Buffer & Completion**
- **Days 43-49**: Bug fixes and integration issues
- **Days 50-56**: Final testing and documentation

## 🛠️ **Technical Patterns**

### **Backend Pattern - Remove session_id completely**
```python
# BEFORE (REMOVE)
class RequestContext:
    session_id: Optional[str] = None
    
async def get_flow_by_session_id(session_id: str):
    return query.filter(model.session_id == session_id)

# AFTER (KEEP)
class RequestContext:
    flow_id: Optional[str] = None
    
async def get_flow_by_flow_id(flow_id: str):
    return query.filter(model.flow_id == flow_id)
```

### **Frontend Pattern - Replace sessionId with flowId**
```typescript
// BEFORE (REMOVE)
const { sessionId } = useParams();
navigate(`/discovery/flow?sessionId=${sessionId}`);

// AFTER (KEEP)
const { flowId } = useParams();
navigate(`/discovery/flow?flowId=${flowId}`);
```

### **Database Pattern - Drop columns**
```sql
-- Final migration to run
ALTER TABLE discovery_flows DROP COLUMN IF EXISTS import_session_id CASCADE;
ALTER TABLE assets DROP COLUMN IF EXISTS session_id CASCADE;
DROP TABLE IF EXISTS data_import_sessions CASCADE;
```

## ✅ **Verification Commands**

Each agent should run these after completing their work:

```bash
# Backend verification (should return 0)
docker exec -it migration_backend grep -r "session_id" app/ --include="*.py" | grep -v "__pycache__" | grep -v "alembic/versions" | wc -l

# Frontend verification (should return 0)
docker exec -it migration_frontend grep -r "sessionId" src/ --include="*.ts" --include="*.tsx" | wc -l

# Test execution
docker exec -it migration_backend pytest
docker exec -it migration_frontend npm test
```

## 📋 **Common Tracker Updates**

After completing each file, update this tracker:

### **Progress Tracker**

| Agent | Files Completed | Files Remaining | Status | Notes |
|-------|----------------|-----------------|---------|-------|
| Agent 1 | 4/15 | 11 | In Progress | Core Backend Context - context.py COMPLETED, sessions.py deleted |
| Agent 2 | 8/60 | 52 | In Progress | Models & repos cleaned, migration created |
| Agent 3 | 0/80 | 80 | Not Started | APIs & Services |
| Agent 4 | 0/8 | 8 | Not Started | Frontend Infrastructure |
| Agent 5 | 0/15 | 15 | Not Started | Frontend Components |
| Agent 6 | 9/68 | 59 | In Progress | Backend Services & Testing - Cleaning services and tests |

### **Blocker Log**

| Date | Agent | Blocker | Resolution |
|------|-------|---------|------------|
| - | - | - | - |

## 🚨 **Critical Dependencies**

1. **Agent 1 MUST complete `/backend/app/core/context.py` FIRST** - All other backend work depends on this
2. **Agent 2 MUST complete models BEFORE Agent 6 runs migrations**
3. **Agent 4 MUST complete hooks BEFORE Agent 5 updates components**

## 🎯 **Definition of Done**

The cleanup is complete when:

1. **Zero session_id references** in all code (except archived files and migration history)
2. **All tests passing** - No test failures due to missing session_id
3. **Manual testing confirms**:
   - ✅ Can create new discovery flow
   - ✅ Can import CMDB data
   - ✅ Field mapping shows active flows (bug fixed)
   - ✅ Can complete entire flow workflow
   - ✅ No console errors about session_id

## 📝 **Individual Agent Task Files**

Each agent has their own detailed task file:
- `SESSION_ID_CLEANUP_AGENT_1.md` - Core Backend Context
- `SESSION_ID_CLEANUP_AGENT_2.md` - Database Models & Repositories
- `SESSION_ID_CLEANUP_AGENT_3.md` - APIs & Services
- `SESSION_ID_CLEANUP_AGENT_4.md` - Frontend Infrastructure
- `SESSION_ID_CLEANUP_AGENT_5.md` - Frontend Components
- `SESSION_ID_CLEANUP_AGENT_6.md` - Testing & Migrations

## 🔧 **Quick Reference**

### **Search Patterns**
```bash
# Find backend session_id (216 files)
grep -r "session_id" backend/app/ --include="*.py"

# Find frontend sessionId (30 files)  
grep -r "sessionId" src/ --include="*.ts" --include="*.tsx"

# Count remaining files
grep -r "session_id" backend/ --include="*.py" | wc -l
grep -r "sessionId" src/ --include="*.ts" --include="*.tsx" | wc -l

# Common replacements
session_id → flow_id
sessionId → flowId
import_session_id → flow_id
get_session_id → get_flow_id
by_session_id → by_flow_id
```

### **⚠️ Modularization Notes**
- **CMDBImport.tsx**: Main component is now clean, focus on modular hooks
- **SessionToFlowMigration**: Preserve during transition (working infrastructure)
- **Repository patterns**: Check modularized subfolders (queries/, commands/)
- **Backend scope**: 88% of work is backend (216/246 files)

### **Git Branch Naming**
```bash
cleanup/session-id-agent-[number]-[component]
# Examples:
cleanup/session-id-agent-1-context
cleanup/session-id-agent-2-models
```

## 💪 **Final Notes**

- This is the LAST cleanup - be thorough
- Remove code, don't comment it out
- No backward compatibility needed
- Fix the bugs, don't work around them
- Ask in Slack if you find unexpected session_id usage

---

**Scope Update**: 246 files total (5x larger than originally estimated)  
**Backend Heavy**: 216 files (88%) require backend expertise  
**Target Completion**: 6-8 weeks from start  
**Modularization Impact**: Frontend main components successfully cleaned  
**Daily Sync**: Update the Progress Tracker above