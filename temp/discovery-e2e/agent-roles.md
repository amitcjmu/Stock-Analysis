# Agent Role Definitions & Instructions

## Agent-0: Orchestration Coordinator

### Primary Responsibilities
1. **Queue Management**
   - Maintain implementation queue priority
   - Assign work to available agents
   - Handle dependencies between issues

2. **User Interface**
   - Accept priority overrides from user
   - Process focus directives
   - Report system status

3. **Conflict Resolution**
   - Serialize conflicting changes
   - Manage resource allocation
   - Escalate blocked issues

### Key Files to Monitor
- `implementation-queue.json` (Read/Write)
- `agent-messages.jsonl` (Read/Write)
- `agent-status-dashboard.md` (Write)

### Decision Logic
```
IF new_issue AND priority == "P0-CRITICAL":
    push_to_front_of_queue()
    notify_implementation_agent()
ELIF user_override:
    reprioritize_queue()
ELIF agent_blocked:
    reassign_work()
```

---

## Agent-1: UI Testing Agent

### Primary Responsibilities
1. **Browser Automation**
   - Login to application
   - Navigate Discovery flow
   - Upload test CMDB files
   - Capture screenshots

2. **Error Detection**
   - Monitor console errors
   - Detect UI failures
   - Identify blocked workflows
   - Document exact steps

### Test Data Locations
- Servers: `/tests/e2e/discovery/test-data/servers-cmdb.csv`
- Applications: `/tests/e2e/discovery/test-data/applications-cmdb.csv`

### Credentials
- Email: `demo@demo-corp.com`
- Password: `Demo123!`

### Success Criteria
- Complete flow navigation
- All UI elements responsive
- No console errors
- Data successfully uploaded

---

## Agent-2: Backend Monitor Agent

### Primary Responsibilities
1. **Log Monitoring**
   ```bash
   docker logs -f migration_backend --since 1m
   ```

2. **Error Pattern Detection**
   - Python exceptions
   - Stack traces
   - Database errors
   - CrewAI failures

3. **Correlation**
   - Link errors to UI actions
   - Track error frequency
   - Identify error patterns

### Critical Patterns
- `ERROR` log level
- `TypeError: Object of type UUID`
- `CRITICAL` warnings
- `403 Forbidden`
- Database connection errors

---

## Agent-3: Database Validator Agent

### Primary Responsibilities
1. **Data Integrity Checks**
   ```sql
   -- Active flows check
   SELECT * FROM discovery_flows
   WHERE created_at > NOW() - INTERVAL '1 hour';

   -- Master flow linkage
   SELECT df.*, mf.id as master_id
   FROM discovery_flows df
   LEFT JOIN crewai_flow_state_extensions mf
   ON df.master_flow_id = mf.id;
   ```

2. **Validation Areas**
   - Flow record creation
   - Master-child relationships
   - Multi-tenant isolation
   - Asset generation

### Connection
```bash
docker exec -it migration_db psql -U postgres -d migration_db
```

---

## Agent-4: Solution Architect Agent

### Primary Responsibilities
1. **Solution Design**
   - Analyze issue root cause
   - Design technical fix
   - Consider alternatives
   - Assess implementation risk

2. **Documentation**
   - Update `solution-approach.md`
   - Provide clear implementation steps
   - Note dependencies
   - Estimate effort

### Design Principles
- Minimal code changes
- Use existing utilities
- Follow architecture patterns
- Consider rollback strategy

### Solution Template
```markdown
## DISC-XXX: [Issue Title]
### Proposed Solution
[Technical approach]

### Implementation Details
[Step-by-step guide]

### Risk Assessment
[Potential issues]

### Alternative Approaches
[Other options]
```

---

## Agent-5: Historical Analyst Agent

### Primary Responsibilities
1. **Git History Analysis**
   ```bash
   # Search for related changes
   git log --grep="UUID" --since="1 year ago"
   git log --grep="flow.*cleanup"

   # Check file history
   git log -p backend/app/services/crewai_flows/execution_engine.py
   ```

2. **Code Review**
   - Find existing utilities
   - Check for reverted fixes
   - Review architecture decisions
   - Analyze migration files

3. **Approval Decision**
   - APPROVED: Safe to implement
   - REJECTED: Would recreate issues
   - APPROVED_WITH_MODIFICATIONS: Needs changes

### Review Checklist
- [ ] No duplicate functionality
- [ ] Not previously reverted
- [ ] Follows architecture
- [ ] Has rollback plan

---

## Agent-6: Implementation Agent

### Primary Responsibilities
1. **Code Implementation**
   - Take approved fixes from queue
   - Implement minimal changes
   - Follow coding standards
   - Add appropriate comments

2. **Testing**
   - Run unit tests
   - Manual verification
   - Check for regressions
   - Document test results

### Implementation Rules
- One issue at a time
- Create before destroy
- Test before commit
- Document all changes

### Verification Steps
```bash
# Run tests
docker exec migration_backend python -m pytest

# Check specific functionality
docker exec migration_backend python -c "test_code"
```

---

## Agent-7: Verification Agent

### Primary Responsibilities
1. **Fix Verification**
   - Test implemented fixes
   - Run regression tests
   - Monitor for side effects
   - Validate resolution

2. **Documentation**
   - Update resolution.md
   - Record verification steps
   - Note any limitations
   - Close issue if verified

### Verification Checklist
- [ ] Original issue resolved
- [ ] No new errors introduced
- [ ] Performance acceptable
- [ ] Data integrity maintained
- [ ] Multi-tenant isolation preserved

---

## Inter-Agent Communication

### Message Protocol
```json
{
  "timestamp": "ISO-8601",
  "from": "Agent-X",
  "to": "Agent-Y | ALL | Coordinator",
  "type": "MESSAGE_TYPE",
  "payload": {
    "issue_id": "DISC-XXX",
    "details": {}
  }
}
```

### Handoff Procedures
1. Complete current work
2. Update status in queue
3. Send HANDOFF message
4. Wait for acknowledgment
5. Move to next task

---

## Priority Response Times

| Priority | Response Time | Escalation |
|----------|--------------|------------|
| P0-CRITICAL | < 5 minutes | Immediate |
| P1-HIGH | < 15 minutes | After 30 min |
| P2-MEDIUM | < 1 hour | After 2 hours |
| P3-LOW | < 4 hours | Next day |

---

## Success Metrics Per Agent

| Agent | Primary Metric | Target |
|-------|---------------|--------|
| Agent-1 | UI Test Coverage | 100% |
| Agent-2 | Error Detection Rate | 95% |
| Agent-3 | Data Validation Coverage | 100% |
| Agent-4 | Solution Quality | 90% approval |
| Agent-5 | Review Accuracy | 100% |
| Agent-6 | Implementation Success | 95% |
| Agent-7 | Verification Coverage | 100% |

---

*These role definitions ensure each agent has clear responsibilities and success criteria.*
