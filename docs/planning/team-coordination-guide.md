# Team Coordination Guide for Discovery Flow Implementation

## Quick Reference for AI Agent Teams

### Team Alpha (Agent Decision Engine)
**Your Mission**: Make the Discovery flow truly autonomous by implementing intelligent agent decision-making.

**Key Files You Own**:
- `/backend/app/services/crewai_flows/agents/decision_agents.py` (create)
- `/backend/app/services/crewai_flows/agents/analysis_tools.py` (create)
- `/backend/app/services/crewai_flows/unified_discovery_flow/phases/field_mapping.py` (modify)

**Critical Success Factors**:
1. NO hardcoded thresholds (remove the 90% rule)
2. NO hardcoded field lists (agents determine what's critical)
3. Agents must provide clear reasoning for decisions
4. All decisions must be auditable

**Integration Points**:
- Your agents will be called by the MFO's FlowExecutionEngine
- You must emit decisions that Team Bravo can broadcast
- Team Delta needs your interfaces for testing

### Team Bravo (Real-Time Communication)
**Your Mission**: Connect the existing Agent-UI Bridge to enable real-time flow updates using SSE and smart polling.

**Key Files You Own**:
- `/backend/app/api/v1/endpoints/agent_events.py` (create)
- `/backend/app/services/agent_ui_bridge.py` (modify)
- `/backend/app/api/v1/endpoints/discovery_flows/query_endpoints.py` (add ETags)

**Critical Success Factors**:
1. SSE endpoint must work with HTTP/2
2. Smart polling with ETags for efficiency
3. All flow updates broadcast in real-time
4. Graceful fallback from SSE to polling

**Integration Points**:
- You consume events from Team Alpha's agents
- Team Charlie depends on your SSE endpoint
- Must integrate with existing agent_ui_bridge

### Team Charlie (Frontend Refactoring)
**Your Mission**: Transform the frontend from an orchestrator to a passive viewer of agent decisions using SSE with smart polling fallback.

**Key Files You Own**:
- `/src/hooks/useFlowUpdates.ts` (create)
- `/src/utils/smartPolling.ts` (create)
- `/src/components/discovery/AgentInsights.tsx` (create)
- `/src/hooks/useUnifiedDiscoveryFlow.ts` (modify - replace with SSE)
- `/src/hooks/discovery/attribute-mapping/useAttributeMappingActions.ts` (modify - remove hardcoded logic)

**Critical Success Factors**:
1. Implement SSE with automatic fallback to smart polling
2. Use ETags for efficient polling when needed
3. REMOVE all hardcoded business logic
4. REMOVE direct phase navigation
5. Display agent reasoning clearly

**Integration Points**:
- You depend on Team Bravo's SSE endpoint
- You implement smart polling with ETags
- You display decisions from Team Alpha's agents
- Team Delta will test your components

### Team Delta (Integration & Testing)
**Your Mission**: Ensure everything works together seamlessly with comprehensive testing.

**Key Files You Own**:
- `/backend/tests/test_agent_decisions.py` (create)
- `/backend/tests/test_discovery_flow_e2e.py` (create)
- `/backend/tests/test_websocket_performance.py` (create)
- Development environment setup

**Critical Success Factors**:
1. 100% coverage of agent decision paths
2. E2E tests cover all user scenarios
3. Performance benchmarks established
4. Integration points validated

**Integration Points**:
- Test all teams' components
- Validate cross-team contracts
- Performance test the full system

## Communication Protocol

### 1. Morning Sync (15 min)
```
Each team reports:
- Yesterday's progress
- Today's focus
- Blockers/dependencies
- Integration needs
```

### 2. API Contract Agreement
When teams need to integrate:
```python
# Team Alpha defines:
class AgentDecision:
    action: str  # "proceed", "pause", "skip"
    next_phase: str
    confidence: float
    reasoning: str
    metadata: Dict

# Team Bravo SSE event format:
data: {
    "type": "agent_decision",
    "flow_id": "xxx",
    "decision": AgentDecision,
    "timestamp": "ISO-8601",
    "version": 1
}
event: flow_update
id: 12345

# Team Bravo ETag response:
HTTP/1.1 200 OK
ETag: "686897696a7c876b7e"
Cache-Control: no-cache

# Team Charlie consumes:
// SSE
eventSource.addEventListener('flow_update', (e) => {
    const { decision } = JSON.parse(e.data);
    if (decision.action === "pause") {
        showAgentRecommendation(decision.reasoning);
    }
});

// Smart polling
if (response.status !== 304) {
    const data = await response.json();
    handleUpdate(data);
}
```

### 3. Blocker Resolution
```
1. Identify blocker in morning sync
2. Assign owner from blocking team
3. Set resolution deadline (max 4 hours)
4. Update all affected teams when resolved
```

## Key Coordination Checkpoints

### Checkpoint 1: Agent Interface Definition (Day 1, 4 PM)
- Team Alpha: Define AgentDecision interface
- All Teams: Review and approve
- Lock interface for implementation

### Checkpoint 2: SSE Event Protocol (Day 2, 2 PM)
- Team Bravo: Define SSE event formats
- Team Bravo: Implement ETag generation
- Team Charlie: Confirm EventSource compatibility
- Document SSE events and fallback strategy

### Checkpoint 3: First Integration (Day 3, 4 PM)
- Team Alpha: Agent making decisions
- Team Bravo: Broadcasting updates
- Team Charlie: Receiving and displaying
- Team Delta: Running integration tests

### Checkpoint 4: Full System Test (Day 5, 2 PM)
- All teams: Components integrated
- Team Delta: Run full E2E suite
- Identify and assign fixes

## Common Pitfalls to Avoid

### For Team Alpha:
❌ Don't create new orchestration logic - use existing MFO
❌ Don't hardcode any thresholds - everything must be dynamic
❌ Don't forget audit trails - every decision must be logged

### For Team Bravo:
❌ Don't create a new event system - use existing agent_ui_bridge
❌ Don't forget error handling - SSE connections can drop
❌ Don't implement WebSockets - use SSE/polling per strategy
❌ Don't broadcast sensitive data - filter appropriately

### For Team Charlie:
❌ Don't use old polling patterns - use SSE with smart fallback
❌ Don't make decisions - only display agent recommendations
❌ Don't forget loading states - SSE connection takes time
❌ Don't forget ETag headers in polling requests

### For Team Delta:
❌ Don't test in isolation - integration tests are key
❌ Don't ignore performance - load test SSE connections
❌ Test both SSE and polling paths - both must work
❌ Don't skip edge cases - test disconnections, errors, etc.

## Definition of Done

### Individual Task Done:
- [ ] Code complete and pushed
- [ ] Unit tests passing
- [ ] Integration points documented
- [ ] Code reviewed by peer
- [ ] No hardcoded values

### Integration Done:
- [ ] Cross-team integration tested
- [ ] API contracts validated
- [ ] Performance benchmarks met
- [ ] Error scenarios handled
- [ ] Documentation updated

### Phase Done:
- [ ] All tasks in phase complete
- [ ] Integration tests passing
- [ ] Performance acceptable
- [ ] No regressions
- [ ] Team Delta sign-off

## Emergency Procedures

### If Blocked > 4 Hours:
1. Escalate to coordinator
2. Consider temporary workaround
3. Document tech debt
4. Plan proper fix

### If Integration Fails:
1. Rollback to last working state
2. Debug with both teams
3. Fix and re-test
4. Update integration tests

### If Performance Degrades:
1. Profile to find bottleneck
2. Implement quick fix if possible
3. Plan optimization sprint
4. Consider feature flags

## Questions to Ask During Implementation

### Team Alpha Should Ask:
- "Is this decision better made by an agent or configuration?"
- "How will users understand this agent's reasoning?"
- "What happens if the agent makes a wrong decision?"

### Team Bravo Should Ask:
- "How many concurrent SSE connections must we support?"
- "What's the event rate we need to handle?"
- "When should clients fall back to polling?"
- "How do we generate consistent ETags?"

### Team Charlie Should Ask:
- "Is this logic better on frontend or backend?"
- "How do we show agent reasoning clearly?"
- "When should we retry SSE vs switch to polling?"
- "How do we handle ETag caching correctly?"

### Team Delta Should Ask:
- "Have we tested all integration points?"
- "What's our performance baseline?"
- "Are error paths covered?"

## Success Metrics Dashboard

Track these daily:
1. **Hardcoded Logic Removed**: ___/10 instances
2. **SSE Connection Success**: ___% 
3. **Smart Polling Efficiency**: ___% 304 responses
4. **Agent Decision Rate**: ___% automated
5. **Test Coverage**: ___%
6. **Integration Points Working**: ___/8

## Final Checklist

Before declaring success:
- [ ] Zero hardcoded business logic
- [ ] 100% event-driven (no polling)
- [ ] Agent decisions driving flow
- [ ] Real-time updates working
- [ ] All tests passing
- [ ] Performance targets met
- [ ] Documentation complete
- [ ] Team retrospective held