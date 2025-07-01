# Session ID Final Cleanup - Master Plan

## 🎯 **Mission Statement**

**Goal**: Complete elimination of all session_id references from the codebase  
**Context**: The flow_id migration is 75% complete. This is the FINAL CLEANUP to remove 132+ residual session_id references that are causing active bugs.  
**Approach**: Direct replacement - NO backward compatibility, NO deprecation warnings  
**Timeline**: 2-3 weeks with 6 parallel agents

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

**Total Files Identified**: 47 files with active session_id usage
- **18 Critical Files**: Core system components (must fix first)
- **15 High Priority Files**: Frontend components and services
- **14 Medium Priority Files**: Utilities and cleanup

## 👥 **Agent Assignments Overview**

| Agent | Focus Area | File Count | Priority Level |
|-------|------------|------------|----------------|
| Agent 1 | Core Backend Context | 6 | 🔥 CRITICAL |
| Agent 2 | Database Models & Repos | 8 | 🔥 CRITICAL |
| Agent 3 | APIs & Services | 10 | 🔥 CRITICAL |
| Agent 4 | Frontend Infrastructure | 8 | 🔴 HIGH |
| Agent 5 | Frontend Components | 10 | 🔴 HIGH |
| Agent 6 | Testing & Migrations | 5 | 🟡 MEDIUM |

## 🔄 **Execution Timeline**

### **Week 1 (Days 1-7)**
- **Days 1-2**: Agents 1-3 tackle critical backend files
- **Days 3-4**: Agent 4 starts frontend infrastructure (after Agent 1 completes context.py)
- **Days 5-7**: Agent 5 begins component updates, Agent 6 prepares migrations

### **Week 2 (Days 8-14)**
- **Days 8-10**: Complete all frontend work
- **Days 11-12**: Run database migrations, update all tests
- **Days 13-14**: Final verification and bug fixes

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
| Agent 1 | 0/6 | 6 | Not Started | - |
| Agent 2 | 0/8 | 8 | Not Started | - |
| Agent 3 | 0/10 | 10 | Not Started | - |
| Agent 4 | 0/8 | 8 | Not Started | - |
| Agent 5 | 0/10 | 10 | Not Started | - |
| Agent 6 | 0/5 | 5 | Not Started | - |

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
# Find backend session_id
grep -r "session_id" backend/app/ --include="*.py"

# Find frontend sessionId
grep -r "sessionId" src/ --include="*.ts" --include="*.tsx"

# Common replacements
session_id → flow_id
sessionId → flowId
import_session_id → flow_id
get_session_id → get_flow_id
by_session_id → by_flow_id
```

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

**Start Date**: [To be filled]  
**Target Completion**: 2-3 weeks from start  
**Daily Sync**: Update the Progress Tracker above