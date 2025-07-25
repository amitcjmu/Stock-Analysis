# Agent Validation Instructions

## Overview
This document provides specific instructions for each agent on how to perform original reporter validation for their assigned issues.

## Agent-1 (UI Testing Agent) - Validation Instructions

### Issues to Validate
- **DISC-007**: Dialog system improvements
- **DISC-011**: Browser dialog blocker (already resolved)
- **DISC-012**: Vite lazy loading failure (already resolved)
- Any UI-related issues identified during testing

### Validation Process for Agent-1
1. **Access the Discovery Flow UI**
   ```bash
   # Navigate to Discovery flow
   http://localhost:8081/discovery/cmdb-import
   ```

2. **Test Original Problem Scenario**
   - Recreate the exact conditions that caused the original issue
   - Verify the problematic behavior no longer occurs
   - Test edge cases that might trigger the original issue

3. **Validate End-to-End Flow**
   - Complete full Discovery flow from Data Import to Tech Debt Assessment
   - Ensure all UI interactions work smoothly
   - Verify no blocking dialogs or errors appear

4. **Browser Automation Testing**
   ```bash
   # Run Playwright tests to ensure automation works
   docker exec migration_frontend npm run test:e2e
   ```

5. **Validation Documentation Template**
   ```markdown
   ✅ VALIDATED by Agent-1 for {ISSUE_ID}:
   - **Original Issue**: {Brief description of original problem}
   - **Test Scenario**: {Specific test performed}
   - **Result**: {Confirmation that issue is resolved}
   - **Edge Cases Tested**: {Any additional scenarios tested}
   - **Automation Status**: {Playwright test results}
   - **User Experience**: {Overall UX improvement confirmation}
   ```

## Agent-2 (Backend Monitoring Agent) - Validation Instructions

### Issues to Validate
- **DISC-002**: Stuck flows root cause fix
- **DISC-006**: Retry logic and error handling
- **DISC-008**: Adaptive rate limiting
- **DISC-009**: User context service fix
- Any backend performance or error issues

### Validation Process for Agent-2
1. **Monitor Backend Logs**
   ```bash
   # Monitor backend logs for error patterns
   docker logs migration_backend -f | grep -i "error\|warning\|stuck\|timeout"
   ```

2. **Test API Endpoints**
   ```bash
   # Test specific endpoints related to the issue
   curl -X GET "http://localhost:8000/api/v1/health" \
     -H "X-Client-Account-ID: 1" \
     -H "X-Engagement-ID: 1"
   ```

3. **Database Monitoring**
   ```bash
   # Check database for stuck flows, timeouts, etc.
   docker exec migration_db psql -U postgres -d migration_db -c "
   SELECT id, status, progress_percentage, created_at, timeout_at
   FROM discovery_flows
   WHERE status IN ('active', 'initialized', 'running')
   ORDER BY created_at DESC LIMIT 10;"
   ```

4. **Performance Testing**
   - Test the specific performance issue that was reported
   - Verify retry logic works under failure conditions
   - Confirm rate limiting behaves correctly

5. **Validation Documentation Template**
   ```markdown
   ✅ VALIDATED by Agent-2 for {ISSUE_ID}:
   - **Original Issue**: {Backend error or performance problem}
   - **Log Analysis**: {Monitoring results showing resolution}
   - **API Testing**: {Endpoint test results}
   - **Database Validation**: {Database query results}
   - **Performance Metrics**: {Before/after performance data}
   - **Error Elimination**: {Confirmation errors no longer occur}
   ```

## Agent-3 (Database Validation Agent) - Validation Instructions

### Issues to Validate
- **DISC-003**: Master-child flow linkage with migration
- Any database integrity, migration, or data consistency issues

### Validation Process for Agent-3
1. **Database Schema Validation**
   ```bash
   # Check database schema changes
   docker exec migration_db psql -U postgres -d migration_db -c "
   \d+ discovery_flows"
   ```

2. **Data Integrity Checks**
   ```bash
   # Verify flow linkage integrity
   docker exec migration_db psql -U postgres -d migration_db -c "
   SELECT
     df.id,
     df.master_flow_id,
     cf.id as master_exists
   FROM discovery_flows df
   LEFT JOIN crewai_flows cf ON df.master_flow_id = cf.id
   WHERE df.master_flow_id IS NOT NULL
   LIMIT 10;"
   ```

3. **Migration Verification**
   ```bash
   # Check migration history
   docker exec migration_backend alembic history
   docker exec migration_backend alembic current
   ```

4. **Constraint Testing**
   - Test foreign key constraints
   - Verify cascade deletions work
   - Confirm data consistency rules

5. **Validation Documentation Template**
   ```markdown
   ✅ VALIDATED by Agent-3 for {ISSUE_ID}:
   - **Original Issue**: {Database or data integrity problem}
   - **Schema Changes**: {Database schema modifications verified}
   - **Data Integrity**: {Integrity check results}
   - **Migration Status**: {Migration application results}
   - **Constraint Testing**: {Foreign key and constraint validation}
   - **Data Consistency**: {Consistency verification results}
   ```

## Agent-4 (Solution Architect) - Validation Instructions

### Issues to Validate
- **DISC-005**: Asset generation pipeline investigation
- **DISC-010**: API documentation improvements
- Any architectural design or system integration issues

### Validation Process for Agent-4
1. **Architecture Review**
   - Review implementation against architectural patterns
   - Verify design decisions align with system architecture
   - Check integration points and dependencies

2. **Documentation Validation**
   ```bash
   # Check API documentation
   curl http://localhost:8000/docs
   curl http://localhost:8000/openapi.json
   ```

3. **Code Quality Assessment**
   - Review code for architectural compliance
   - Verify design patterns are followed
   - Check integration with existing systems

4. **System Integration Testing**
   - Test integration between components
   - Verify system boundaries are respected
   - Confirm architectural decisions implemented

5. **Validation Documentation Template**
   ```markdown
   ✅ VALIDATED by Agent-4 for {ISSUE_ID}:
   - **Original Issue**: {Architectural or design problem}
   - **Architecture Review**: {Architectural compliance verification}
   - **Design Validation**: {Design pattern implementation check}
   - **Integration Testing**: {Integration point validation}
   - **Documentation Quality**: {Documentation completeness and accuracy}
   - **System Compliance**: {Overall system architecture adherence}
   ```

## General Validation Guidelines

### Validation Quality Standards
- **Minimum 50 characters**: Validation details must be substantive
- **Specific testing**: Describe exact tests performed
- **Clear results**: State definitively whether issue is resolved
- **Evidence-based**: Provide concrete evidence of resolution

### Validation Failure Process
If validation fails:
1. **Document the failure**: Explain what still doesn't work
2. **Transition back to IMPLEMENTATION**: Use workflow system to move back
3. **Provide specific feedback**: Give implementation agent clear guidance
4. **Revalidate after fix**: Perform validation again after re-implementation

### Validation Success Process
If validation succeeds:
1. **Complete validation**: Call `mark_original_reporter_validation_complete()`
2. **Provide detailed feedback**: Document thorough validation results
3. **Approve completion**: Allow transition to COMPLETED state

## Workflow System Integration

### Validation Commands
```python
# Mark validation complete
enforcement_system.mark_original_reporter_validation_complete(
    issue_id="DISC-XXX",
    agent_id="agent-X",  # Must be original reporter
    validation_details="Detailed validation results here..."
)

# Transition to completion
enforcement_system.request_state_transition(
    issue_id="DISC-XXX",
    new_state=WorkflowState.COMPLETED,
    agent_id="agent-8"
)
```

### Validation State Checks
```python
# Check if ready for validation
issue = enforcement_system.issues["DISC-XXX"]
if issue.current_state == WorkflowState.ORIGINAL_REPORTER_VALIDATION:
    # Ready for original reporter validation

if issue.original_reporter_validated:
    # Can transition to COMPLETED
```

## Common Validation Scenarios

### Scenario 1: UI Issue (Agent-1)
- **Issue**: Button not working
- **Validation**: Click button, verify expected behavior
- **Evidence**: Screenshots, browser console logs
- **Automation**: Playwright test passes

### Scenario 2: Backend Issue (Agent-2)
- **Issue**: API returning 500 error
- **Validation**: API call returns 200 with correct data
- **Evidence**: API response logs, error log absence
- **Monitoring**: 1+ hour of error-free operation

### Scenario 3: Database Issue (Agent-3)
- **Issue**: Foreign key constraint missing
- **Validation**: Constraint exists and enforced
- **Evidence**: Database schema dump, constraint test
- **Integrity**: Data consistency verified

### Scenario 4: Architecture Issue (Agent-4)
- **Issue**: Design pattern not followed
- **Validation**: Pattern properly implemented
- **Evidence**: Code review, integration test
- **Compliance**: Architectural standards met

## Success Metrics

### Validation Quality Metrics
- **Validation Detail Length**: Average 200+ characters
- **Validation Success Rate**: 95%+ first-time validation success
- **Validation Time**: < 2 hours from verification to validation
- **Rework Rate**: < 10% requiring re-implementation

### Compliance Metrics
- **Original Reporter Validation**: 100% validated by correct agent
- **Validation Completeness**: 100% with proper validation details
- **Workflow Adherence**: 100% following complete workflow

## Conclusion

This validation process ensures:
- **Quality assurance**: Original reporters verify their issues are truly resolved
- **Accountability**: Each agent validates their own identified issues
- **Compliance**: Mandatory validation before issue closure
- **Continuous improvement**: Validation feedback improves future implementations

Each agent must follow their specific validation process to ensure proper issue resolution and maintain system quality standards.

---

**Implementation**: Follow validation instructions for your agent type
**Quality Standard**: Provide detailed, evidence-based validation
**Compliance**: Only original reporters can validate their issues
**Closure**: Issues complete only after successful validation
