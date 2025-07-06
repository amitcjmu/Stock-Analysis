# Orchestrated Execution Plan - July 2025 Revamp

## Coordination Strategy

### Model Usage Optimization
- **Opus (Me)**: High-level orchestration, critical decisions, and coordination only
- **Sonnet 4 Teams**: All implementation work, code changes, testing
- **Handoff Prevention**: Structured checkpoints every 4 hours with concise status reports

## Revised Execution Sequence (Frontend-First Approach)

### Phase 0: Setup & Preparation (Hour 0-1)
**Opus Actions:**
1. Create team briefing documents for each Sonnet team
2. Establish communication protocol (status report format)
3. Define success criteria checkpoints
4. Spawn initial teams

### Phase 1: Frontend Cleanup Sprint (Hours 1-24)

#### Team Alpha (Sonnet 4) - API Service Consolidation
**Mission**: Create unified API service layer
**Briefing Document**: `/docs/planning/revamp-july-2025/teams/alpha-briefing.md`
**Tasks**:
1. Create `/src/services/api/masterFlowService.ts`
2. Map all current API calls to new service
3. Remove double-prefix issues
4. Test each endpoint mapping

#### Team Beta (Sonnet 4) - Hook Consolidation  
**Mission**: Replace all discovery hooks with unified flow hook
**Briefing Document**: `/docs/planning/revamp-july-2025/teams/beta-briefing.md`
**Tasks**:
1. Create `/src/hooks/useFlow.ts` 
2. Update all components using old hooks
3. Remove session_id references
4. Delete legacy hooks

#### Team Gamma (Sonnet 4) - Component Updates
**Mission**: Update all UI components to use new patterns
**Briefing Document**: `/docs/planning/revamp-july-2025/teams/gamma-briefing.md`
**Tasks**:
1. Fix AttributeMapping page
2. Update Dashboard components
3. Fix navigation flows
4. Remove V3 imports

### Phase 2: Backend Stabilization (Hours 24-36)

#### Team Delta (Sonnet 4) - State Management Fix
**Mission**: Consolidate to single PostgreSQL source
**Briefing Document**: `/docs/planning/revamp-july-2025/teams/delta-briefing.md`
**Tasks**:
1. Remove event-based DB updates
2. Fix field mapping approval flow
3. Consolidate state management
4. Remove competing controllers

#### Team Epsilon (Sonnet 4) - CrewAI Implementation
**Mission**: Implement real CrewAI agents
**Briefing Document**: `/docs/planning/revamp-july-2025/teams/epsilon-briefing.md`
**Tasks**:
1. Replace pseudo-agents
2. Implement proper crews
3. Fix phase execution
4. Test agent coordination

### Phase 3: Integration & Testing (Hours 36-48)

#### Team Zeta (Sonnet 4) - E2E Testing
**Mission**: Comprehensive testing and validation
**Briefing Document**: `/docs/planning/revamp-july-2025/teams/zeta-briefing.md`
**Tasks**:
1. Run full discovery flow tests
2. Test assessment flow integration
3. Verify state consistency
4. Performance benchmarking

## Coordination Protocol

### Opus Touchpoints (Minimal Usage)
1. **Hour 0**: Initial team spawning and briefing
2. **Hour 6**: Phase 1 checkpoint (frontend progress)
3. **Hour 12**: Critical decision point (proceed/adjust)
4. **Hour 24**: Phase transition (frontend→backend)
5. **Hour 36**: Integration checkpoint
6. **Hour 48**: Final validation and handoff

### Status Report Format (From Sonnet Teams)
```yaml
team: Alpha
phase: 1
hour: 6
status: on-track|blocked|ahead
completed:
  - task1
  - task2
blockers:
  - none
next_4h:
  - task3
  - task4
confidence: 95%
```

### Inter-Team Communication
- Teams post updates to `/docs/planning/revamp-july-2025/status/`
- Critical blockers flagged for Opus attention
- Teams can read each other's status for coordination

## Success Criteria by Phase

### Phase 1 Success (Hour 24)
- [ ] All frontend API calls use `/api/v1/master-flows/*`
- [ ] Zero session_id references remain
- [ ] AttributeMapping page works end-to-end
- [ ] No V3 imports remain
- [ ] Dashboard shows correct flow states

### Phase 2 Success (Hour 36)
- [ ] Single PostgreSQL state source
- [ ] Field mapping approval works
- [ ] Real CrewAI agents deployed
- [ ] No event-based DB updates
- [ ] Flow resumption works

### Phase 3 Success (Hour 48)
- [ ] Complete discovery flow works
- [ ] Assessment flow integrated with MFO
- [ ] All tests passing
- [ ] Performance metrics met
- [ ] Production ready

## Handoff Prevention Strategy

### 1. **Structured Team Briefings**
Each team gets a complete briefing with:
- Specific file paths
- Code examples
- Test criteria
- Rollback procedures

### 2. **Autonomous Operation**
Teams operate independently for 4-hour blocks without Opus intervention

### 3. **Clear Success Metrics**
Binary pass/fail criteria prevent ambiguous status

### 4. **Contingency Planning**
If Opus hits limits:
- Teams continue with existing briefings
- Final Sonnet team performs validation
- Documentation serves as handoff

## Resource Allocation

### Sonnet 4 Team Assignments
- **Alpha**: 2 agents (API service)
- **Beta**: 2 agents (hooks)
- **Gamma**: 3 agents (components)
- **Delta**: 2 agents (state management)
- **Epsilon**: 2 agents (CrewAI)
- **Zeta**: 1 agent (testing)

Total: 12 Sonnet 4 agents working in parallel

### Opus Usage Budget
- Initial setup: 30 minutes
- 6 checkpoints: 10 minutes each
- Emergency interventions: 30 minutes reserve
- Total: 2 hours Opus time over 48 hours

## Risk Mitigation

### 1. **Team Blocking**
- Each team has alternate paths documented
- Can proceed with partial implementation
- Other teams can assist if ahead

### 2. **Integration Failures**
- Incremental integration every 4 hours
- Rollback points clearly marked
- Test suite runs automatically

### 3. **Opus Limit Hit**
- Team Zeta (testing) becomes coordinator
- Uses status reports for decisions
- Follows documented criteria

## Execution Commands

### Spawn Teams (Opus executes once)
```bash
# Create team directories
mkdir -p /docs/planning/revamp-july-2025/teams
mkdir -p /docs/planning/revamp-july-2025/status

# Opus creates briefing documents
# Then spawns teams with specific missions
```

### Team Status Updates (Sonnet teams execute)
```bash
# Every 4 hours
echo "status_report" > /docs/planning/revamp-july-2025/status/team-alpha-hour-4.yaml
```

### Checkpoint Reviews (Opus minimal usage)
```bash
# Read all status reports
cat /docs/planning/revamp-july-2025/status/*-hour-*.yaml
# Make go/no-go decision
# Update team briefings if needed
```

## Expected Outcome

With this orchestrated approach:
1. Frontend cleaned in 24 hours
2. Backend stabilized in next 12 hours  
3. Full integration tested in final 12 hours
4. Opus usage stays under 2 hours total
5. No handoff required
6. Platform fully functional in 48 hours