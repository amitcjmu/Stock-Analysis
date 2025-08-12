# Flow Routing Intelligence Test Suite

## Overview

This test suite validates the complete solution for the critical flow routing issue where Discovery Flow fails at attribute mapping when resuming from incomplete initialization phase. The solution implements backend flow routing intelligence with recovery API endpoints and frontend automatic recovery integration.

## Original Problem

- **Issue**: Discovery flow fails at attribute mapping when resuming from incomplete initialization phase
- **Symptoms**: Shows "Discovery Flow Error: HTTP 404: Not Found" with manual "Retry Analysis" button
- **Impact**: Flow gets stuck requiring manual intervention instead of self-healing

## Solution Implemented

### Backend Components
- ✅ **Flow Routing Intelligence**: `FlowRoutingAgent` in `backend/app/services/flow_orchestration/`
- ✅ **Flow State Detection**: `FlowStateDetector` for incomplete flow initialization detection
- ✅ **Recovery API Endpoints**: New endpoints in `backend/app/api/v1/endpoints/flow_recovery.py`
- ✅ **Status Management**: Enhanced flow status management with automatic recovery

### Frontend Components
- ✅ **Flow Recovery Service**: `src/services/flow-recovery.ts` for API integration
- ✅ **Automatic Recovery Integration**: Enhanced hooks and components for self-healing
- ✅ **Phase Transition Interception**: Prevents navigation to incomplete phases
- ✅ **Recovery Progress UI**: User-friendly progress indicators during recovery

## Test Files

### 1. Comprehensive Playwright Test Suite
**File**: `flow-routing-intelligence-comprehensive.spec.ts`

Contains 8 critical test scenarios that validate the complete solution:

#### Test 1: Original Failing Flow Recovery
- **Purpose**: Navigate to the original failing URL and verify automatic recovery
- **URL**: `http://localhost:8081/discovery/attribute-mapping/8793785a-549d-4c6d-81a9-76b1c2f63b7e`
- **Expected**: Should show automatic recovery instead of manual "Retry Analysis" button
- **Validates**: Core issue resolution

#### Test 2: Automatic Flow State Detection
- **Purpose**: Test flow state validation on page load with incomplete flows
- **Expected**: System should automatically validate flow state and trigger recovery
- **Validates**: Proactive flow state monitoring

#### Test 3: Phase Transition Interception
- **Purpose**: Test navigation interception with incomplete data import
- **Expected**: Should intercept navigation and redirect to appropriate phase
- **Validates**: Prevention of access to incomplete phases

#### Test 4: Self-Healing Flow Navigation
- **Purpose**: Test seamless navigation without manual intervention
- **Expected**: Should provide smooth navigation with automatic issue resolution
- **Validates**: User experience improvements

#### Test 5: Recovery Progress UI
- **Purpose**: Test progress indicators and user feedback during recovery
- **Expected**: Should show clear progress and status during recovery operations
- **Validates**: User interface enhancements

#### Test 6: Flow Recovery API Integration
- **Purpose**: Verify API calls to new recovery endpoints
- **Expected**: Should call validation, recovery, and interception endpoints
- **API Endpoints Tested**:
  - `/api/v1/unified-discovery/flow/validate/{flow_id}`
  - `/api/v1/unified-discovery/flow/recover/{flow_id}`
  - `/api/v1/unified-discovery/flow/intercept-transition`
  - `/api/v1/unified-discovery/flow/health`
- **Validates**: Backend integration

#### Test 7: Graceful Fallbacks
- **Purpose**: Test scenarios where automatic recovery fails
- **Expected**: Should provide helpful navigation options when recovery isn't possible
- **Validates**: Robustness and fallback handling

#### Test 8: Complete E2E Flow
- **Purpose**: Test complete discovery flow with automatic recovery at each phase
- **Expected**: Should work smoothly from data import → field mapping → asset creation
- **Validates**: End-to-end solution effectiveness

### 2. Backend Recovery System Test
**File**: `backend/test_flow_recovery_system.py`

Comprehensive backend validation that:
- Creates problematic flow states that match the original issue
- Tests flow detection and routing intelligence
- Validates recovery mechanisms
- Ensures API endpoints work correctly

### 3. Validation Scripts

#### Complete Validation Suite
**File**: `validate-flow-routing-intelligence.sh`
- Runs complete validation including backend and frontend tests
- Checks Docker services, API endpoints, and comprehensive test scenarios
- Provides detailed pass/fail reporting

#### Quick Test Runner
**File**: `run-flow-routing-tests.sh`
- Fast iteration testing for development
- Can run specific tests by name
- Provides immediate feedback

## How to Run Tests

### Prerequisites
1. **Docker Services Running**:
   ```bash
   cd /path/to/migrate-ui-orchestrator
   docker-compose up -d
   ```

2. **Services Accessible**:
   - Frontend: http://localhost:8081
   - Backend: http://localhost:8000

### Running Tests

#### Option 1: Complete Validation Suite
```bash
cd tests/e2e
./validate-flow-routing-intelligence.sh
```

#### Option 2: Quick Playwright Tests Only
```bash
cd tests/e2e
./run-flow-routing-tests.sh
```

#### Option 3: Specific Test
```bash
cd tests/e2e
./run-flow-routing-tests.sh "Test 1"
```

#### Option 4: Manual Playwright Execution
```bash
cd tests/e2e
npx playwright test flow-routing-intelligence-comprehensive.spec.ts --headed
```

#### Option 5: Backend Tests Only
```bash
cd /path/to/migrate-ui-orchestrator
python3 backend/test_flow_recovery_system.py
```

## Test Results Interpretation

### Success Criteria
- ✅ All 8 Playwright tests pass
- ✅ Backend recovery system test passes
- ✅ No manual "Retry Analysis" buttons appear
- ✅ Automatic recovery indicators are visible
- ✅ HTTP 404 errors are eliminated
- ✅ Flow transitions work seamlessly

### Expected Outcomes

#### Before Fix (Original Problem)
- Manual "Retry Analysis" button appears
- HTTP 404 errors on attribute mapping page
- Flows get stuck requiring user intervention
- Poor user experience with manual recovery steps

#### After Fix (With Flow Routing Intelligence)
- Automatic recovery indicators appear
- No HTTP 404 errors on flow pages
- Seamless flow navigation without manual intervention
- Progress indicators during recovery operations
- Graceful fallbacks when recovery isn't possible

## API Endpoints Validated

The tests verify these new recovery API endpoints:

### Flow Validation
```http
GET /api/v1/unified-discovery/flow/validate/{flow_id}
```
Response:
```json
{
  "isValid": boolean,
  "canRecover": boolean,
  "recommendedAction": string,
  "redirectPath": string,
  "issues": string[],
  "metadata": object
}
```

### Flow Recovery
```http
POST /api/v1/unified-discovery/flow/recover/{flow_id}
```
Response:
```json
{
  "success": boolean,
  "message": string,
  "recoveredFlowId": string,
  "requiresUserAction": boolean,
  "metadata": object
}
```

### Transition Interception
```http
POST /api/v1/unified-discovery/flow/intercept-transition
```
Request:
```json
{
  "flowId": string,
  "fromPhase": string,
  "toPhase": string
}
```

Response:
```json
{
  "allowTransition": boolean,
  "redirectPath": string,
  "reason": string,
  "flowReadiness": {
    "dataImportComplete": boolean,
    "fieldMappingReady": boolean,
    "canProceedToAttributeMapping": boolean
  }
}
```

### Health Check
```http
GET /api/v1/unified-discovery/flow/health
```
Response:
```json
{
  "status": string,
  "services": {
    "flowValidation": boolean,
    "flowRecovery": boolean,
    "phaseTransition": boolean
  }
}
```

## Troubleshooting

### Common Issues

1. **Docker Services Not Running**
   ```bash
   docker-compose up -d
   # Wait for services to initialize
   ```

2. **Port Conflicts**
   - Frontend should be on port 8081
   - Backend should be on port 8000

3. **Test Failures**
   - Check test result logs in `tests/e2e/test-results/`
   - Review Docker container logs
   - Verify database state is clean

### Debug Mode
```bash
# Run with debug output
DEBUG=true npx playwright test flow-routing-intelligence-comprehensive.spec.ts --headed

# Take screenshots on failure
npx playwright test --screenshot=only-on-failure
```

## Success Metrics

### Key Performance Indicators (KPIs)
1. **Zero Manual Interventions**: No "Retry Analysis" buttons should appear
2. **Zero HTTP 404 Errors**: All flow URLs should resolve correctly
3. **Automatic Recovery Rate**: 100% of recoverable flows should auto-heal
4. **User Experience**: Seamless navigation without error states
5. **API Response Times**: Recovery operations should complete within 10 seconds

### Validation Checkpoints
- [ ] Original failing URL now works automatically
- [ ] Flow state detection happens on page load
- [ ] Phase transitions are intercepted properly
- [ ] Recovery progress is visible to users
- [ ] API endpoints respond correctly
- [ ] Fallback mechanisms work when needed
- [ ] Complete E2E flow works smoothly

## Implementation Notes

### Backend Intelligence
The flow routing intelligence is implemented through several coordinated services:
- **FlowStateDetector**: Identifies incomplete flow initialization states
- **FlowRoutingAgent**: Makes intelligent routing decisions
- **MasterFlowOrchestrator**: Orchestrates recovery operations
- **StatusManager**: Provides real-time flow status insights

### Frontend Self-Healing
The frontend self-healing is implemented through:
- **FlowRecoveryService**: Manages API interactions for recovery
- **useFlowDetection**: Hook for automatic flow state monitoring
- **ErrorAndStatusAlerts**: Components for recovery progress UI
- **Phase Transition Interception**: Navigation guards for incomplete flows

### Security Considerations
- All flow IDs are validated and sanitized
- Recovery operations require proper authentication
- Sensitive data is masked in logs
- Rate limiting is applied to recovery endpoints

## Future Enhancements

### Planned Improvements
1. **Predictive Recovery**: Machine learning to predict flow issues before they occur
2. **Advanced Metrics**: Detailed analytics on recovery success rates
3. **User Preferences**: Allow users to configure recovery behavior
4. **Cross-Flow Recovery**: Recover issues affecting multiple related flows

### Monitoring and Observability
- Flow recovery success/failure rates
- Time to recovery metrics
- User satisfaction with automatic recovery
- API endpoint performance monitoring

---

## Conclusion

This comprehensive test suite validates that the flow routing intelligence solution completely resolves the original HTTP 404 flow initialization errors. The tests ensure that:

1. **Users never see manual "Retry Analysis" buttons**
2. **Flows are automatically detected and recovered**
3. **Navigation is seamless and self-healing**
4. **Progress is clearly communicated to users**
5. **Fallbacks work when automatic recovery isn't possible**

The solution transforms the user experience from manual intervention to automatic self-healing, significantly improving the platform's reliability and usability.
