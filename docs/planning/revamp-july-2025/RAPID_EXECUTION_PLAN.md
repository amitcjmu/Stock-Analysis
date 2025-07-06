# Rapid Execution Plan - Complete Legacy Elimination

## Aggressive Timeline: 6 Hours Total

**Core Philosophy**: REMOVE, don't patch. Eliminate all legacy code causing split-brain issues.

### Hour 0-1: Parallel Frontend Blitz
**Teams Alpha + Beta + Gamma** (6 Sonnet agents working simultaneously)

**Team Alpha** - API Elimination (30 minutes):
- DELETE `/src/api/v3/` entirely 
- DELETE `/src/services/discoveryUnifiedService.ts`
- DELETE all `/api/v1/discovery/*` calls
- REPLACE with single `/api/v1/master-flows/*` pattern

**Team Beta** - Hook Purge (30 minutes):
- DELETE `/src/hooks/useDiscoveryFlow.ts`
- DELETE `/src/utils/migration/sessionToFlow.ts`
- REMOVE all session_id references (28 files)
- CREATE single `/src/hooks/useFlow.ts`

**Team Gamma** - Component Surgery (1 hour):
- FIX `/src/pages/discovery/AttributeMapping/index.tsx`
- UPDATE dashboard to use master flows only
- REMOVE all V3 imports
- STANDARDIZE on flow_id everywhere

### Hour 1-3: Backend State Consolidation
**Teams Delta + Epsilon** (4 Sonnet agents)

**Team Delta** - State Elimination (1 hour):
- REMOVE all event-based DB updates
- CONSOLIDATE to discovery_flows table only
- FIX field mapping approval flow
- DELETE competing state managers

**Team Epsilon** - CrewAI Completion (1 hour):
- IMPLEMENT missing real agents
- REMOVE remaining pseudo-agents
- COMPLETE phase execution pipeline
- TEST agent coordination

### Hour 3-6: Validation & Cleanup
**Team Zeta** - Using Existing Tests (2 hours):
- UPDATE existing `/tests` scripts
- RUN full test suite
- FIX any integration issues
- VALIDATE complete flows work

### Hour 6: Final Verification
**All Teams** - Production Readiness Check

## Dynamic Status Updates

### Real-Time Progress Tracking
Teams update status immediately when tasks complete:
```bash
# Task completion format
echo "COMPLETED: Delete V3 API - Team Alpha - $(date)" >> /docs/status.log
echo "BLOCKED: Missing endpoint - Team Beta - $(date)" >> /docs/status.log
```

### Opus Check-ins (15 minutes each)
- **Hour 0.5**: Frontend progress check
- **Hour 1.5**: Backend coordination 
- **Hour 3**: Integration status
- **Hour 5**: Final validation
- **As needed**: Blocker resolution

## Existing Test Infrastructure Usage

### Team Zeta Analysis of `/tests`
1. **Inventory existing tests**:
   ```bash
   find /tests -name "*.py" -o -name "*.js" -o -name "*.ts" | head -20
   ```

2. **Update test patterns**:
   - Fix API endpoint calls in tests
   - Update session_id to flow_id in test data
   - Ensure tests use master flows API

3. **Add missing coverage**:
   - End-to-end discovery flow test
   - Field mapping approval test
   - State consistency validation

## Aggressive Removal Strategy

### Files to DELETE Completely (No Patches)
```bash
# Frontend cleanup
rm -rf src/api/v3/
rm src/services/discoveryUnifiedService.ts
rm src/hooks/useDiscoveryFlow.ts
rm src/utils/migration/sessionToFlow.ts

# Backend cleanup  
rm -rf backend/app/services/agents/  # Pseudo-agents
rm backend/app/services/v3/  # Legacy V3 services
```

### Code Patterns to ELIMINATE
- All `session_id` references → `flow_id`
- All `/api/v1/discovery/*` calls → `/api/v1/master-flows/*`
- All pseudo-agent imports → Real CrewAI
- All dual state updates → Single PostgreSQL

## Success Criteria (Binary Pass/Fail)

### Hour 1 Checkpoint
- [ ] Zero V3 imports remain
- [ ] Zero session_id references  
- [ ] AttributeMapping page loads without errors
- [ ] All API calls use master-flows endpoint

### Hour 3 Checkpoint  
- [ ] Discovery flow creates successfully
- [ ] Field mapping approval works
- [ ] Flow state persists correctly
- [ ] No competing state updates

### Hour 6 Final
- [ ] Complete discovery flow works end-to-end
- [ ] All tests pass
- [ ] Zero legacy code remains
- [ ] Production deployment ready

## Blocker Resolution Protocol

### Common Expected Blockers
1. **Missing master-flows endpoints** → Create immediately
2. **Test failures** → Fix in place, don't skip
3. **State inconsistencies** → Choose PostgreSQL, delete others
4. **Component errors** → Remove broken features temporarily

### Escalation Process
- **Self-resolve**: Teams try for 15 minutes
- **Peer-assist**: Other teams help if available  
- **Opus intervention**: Flag for immediate attention
- **Temporary bypass**: Remove feature if blocking critical path

## Resource Allocation (Optimized)

### Parallel Execution
- **Hours 0-1**: 6 agents (frontend blitz)
- **Hours 1-3**: 4 agents (backend consolidation)  
- **Hours 3-6**: 2 agents (testing) + 4 agents (fixes)

### Opus Usage Budget
- Setup: 15 minutes
- 4 check-ins: 10 minutes each
- Blocker resolution: 30 minutes
- **Total: 1.25 hours over 6 hours**

## Zero Legacy Tolerance

### Definition of "Complete"
- No session_id anywhere in codebase
- No V3 API references  
- No pseudo-agents
- No competing state managers
- No `/api/v1/discovery/*` calls that bypass MFO
- Single API pattern throughout

### Validation Commands
```bash
# These must return ZERO results
grep -r "session_id" src/ 
grep -r "/api/v3" src/
grep -r "BaseDiscoveryAgent" backend/
grep -r "/api/v1/discovery/" src/ | grep -v master-flows
```

## Contingency Planning

### If Behind Schedule
- **Hour 2**: Cut non-essential features
- **Hour 4**: Focus on core discovery flow only
- **Hour 5**: Accept temporary UI issues for backend stability

### If Major Blocker
- **Document issue clearly**
- **Create workaround**  
- **Continue with reduced scope**
- **Never revert to legacy patterns**

## Expected Outcome

**End State (Hour 6)**:
- Platform works end-to-end
- Zero technical debt from legacy patterns
- Single API pattern (master-flows)
- Clean foundation for security/SSO
- Production deployment ready
- 90%+ reduction in codebase complexity

**Critical Success Factor**: COMPLETE elimination of legacy code, not partial fixes.