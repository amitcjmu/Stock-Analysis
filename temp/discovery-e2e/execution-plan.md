# Discovery Flow E2E Testing - Multi-Agent Execution Plan

## Executive Summary
This plan coordinates 5 specialized agents working in parallel to thoroughly test the Discovery flow, identifying issues across frontend, backend, and database layers.

## Agent Team Composition

### 1. Browser UI Agent
**Mission**: Navigate through the Discovery flow UI and interact with all elements
**Tools**: Playwright browser automation
**Key Responsibilities**:
- Login with demo@demo-corp.com / Demo123!
- Navigate to Discovery flow
- Upload CMDB CSV files
- Progress through all 5 phases
- Take screenshots at each step
- Report UI failures and blockers

**Success Metrics**:
- Complete navigation through all phases
- Document all UI elements that fail
- Capture visual evidence of issues

### 2. Console & Network Monitor Agent
**Mission**: Monitor browser console and network activity for errors
**Tools**: Playwright console API, network monitoring
**Key Responsibilities**:
- Capture all JavaScript console errors
- Monitor network requests/responses
- Track API call failures (4xx, 5xx)
- Identify CORS issues
- Monitor WebSocket connections
- Track performance metrics

**Success Metrics**:
- Zero untracked console errors
- Complete network request log
- Performance bottleneck identification

### 3. Backend Log Analyzer Agent
**Mission**: Monitor Docker backend logs for errors and warnings
**Tools**: Docker logs, grep, log parsing
**Key Responsibilities**:
- Stream backend logs in real-time
- Identify Python exceptions
- Track CrewAI flow execution
- Monitor database query errors
- Capture stack traces
- Identify memory/resource issues

**Success Metrics**:
- Complete error log with timestamps
- Stack trace collection
- Resource usage patterns

### 4. Database Validator Agent
**Mission**: Verify data persistence and integrity
**Tools**: PostgreSQL queries, Docker exec
**Key Responsibilities**:
- Verify flow records created
- Check master-child flow relationships
- Validate field mappings
- Ensure multi-tenant isolation
- Check data import records
- Verify asset creation

**Success Metrics**:
- Data integrity verification
- Relationship mapping validation
- No data leakage across tenants

### 5. API Test Agent
**Mission**: Test API endpoints directly for validation
**Tools**: curl/httpie, API testing
**Key Responsibilities**:
- Test discovery flow initialization
- Validate data import endpoints
- Check flow status endpoints
- Test with/without required headers
- Verify error responses
- Check API response times

**Success Metrics**:
- API endpoint coverage
- Response time benchmarks
- Error handling validation

## Execution Timeline

### Phase 1: Setup (T+0 minutes)
All agents initialize simultaneously:
- Browser UI Agent: Launch browser, navigate to app
- Console Monitor: Attach to browser instance
- Backend Log Agent: Start log streaming
- Database Validator: Connect to PostgreSQL
- API Test Agent: Prepare test requests

### Phase 2: Login & Flow Init (T+2 minutes)
- Browser UI: Perform login
- Console Monitor: Watch for auth errors
- Backend Log: Monitor auth flow
- Database: Check user session creation
- API Test: Test auth endpoints

### Phase 3: Data Import (T+5 minutes)
- Browser UI: Upload CMDB files
- Console Monitor: Track upload progress
- Backend Log: Monitor processing
- Database: Verify import records
- API Test: Test import endpoints

### Phase 4: Attribute Mapping (T+10 minutes)
- Browser UI: Configure mappings
- Console Monitor: Watch for UI errors
- Backend Log: Track mapping logic
- Database: Verify mapping storage
- API Test: Test mapping endpoints

### Phase 5: Data Cleansing (T+15 minutes)
- Browser UI: Apply cleansing rules
- Console Monitor: Monitor transformations
- Backend Log: Track cleansing process
- Database: Verify data updates
- API Test: Test cleansing endpoints

### Phase 6: Inventory & Dependencies (T+20 minutes)
- Browser UI: Validate inventory, map dependencies
- Console Monitor: Watch visualization
- Backend Log: Monitor asset creation
- Database: Verify relationships
- API Test: Test inventory endpoints

### Phase 7: Analysis & Reporting (T+25 minutes)
All agents compile findings and correlate issues

## Communication Protocol

### Real-time Issue Escalation
- **CRITICAL**: Flow completely blocked
- **HIGH**: Major functionality broken
- **MEDIUM**: Feature partially working
- **LOW**: Minor UI/UX issues

### Inter-Agent Communication
Agents will report findings to central coordinator for:
- Cross-layer issue correlation
- Root cause analysis
- Dependency tracking
- Resolution prioritization

## Expected Issue Categories

### Frontend Issues
- Incomplete flow blocking
- Session/Flow ID mismatches
- UI component failures
- Console errors
- Network timeouts

### Backend Issues
- CrewAI flow failures
- Database connection issues
- Multi-tenant violations
- Memory leaks
- Unhandled exceptions

### Integration Issues
- API/UI mismatches
- Data persistence failures
- Async operation failures
- WebSocket disconnections

## Success Criteria

1. **Complete Flow Execution**: At least one successful path through all phases
2. **Issue Documentation**: All blockers documented with reproduction steps
3. **Root Cause Analysis**: Issues traced to source code
4. **Performance Baseline**: Response times documented
5. **Data Integrity**: No data corruption or leakage

## Deliverables

1. **issues.md**: Comprehensive issue log
2. **resolution.md**: Root cause analysis and fixes
3. **progress-tracker.md**: Real-time status updates
4. **Screenshots**: Visual evidence of issues
5. **Performance Report**: Bottleneck analysis
6. **Recommendations**: Prioritized fix list

---

## Agent Instructions

Each agent will receive specific instructions and begin execution in parallel. The coordinator will monitor progress and facilitate inter-agent communication for issue correlation.
