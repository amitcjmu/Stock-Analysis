# Legacy Discovery Endpoints Audit

## Files Still Using `/api/v1/discovery/` Endpoints

### 1. **src/components/discovery/PlanVisualization.tsx**
- `/api/v1/discovery/flow/planning/intelligence/${flowId}`
- `/api/v1/discovery/flow/planning/optimize/${flowId}`

### 2. **src/components/discovery/UploadBlocker.tsx**
- `/api/v1/discovery/flow/${flow.flowId}/complete`

### 3. **src/components/FlowCrewAgentMonitor/hooks/useAgentMonitor.ts**
- `/api/v1/discovery/flow/crews/monitoring/${flow.flow_id}` (multiple occurrences)

### 4. **src/hooks/discovery/useAttributeMappingNavigation.ts**
- `/api/v1/discovery/flow/${flowId}/resume`

### 5. **src/hooks/discovery/useCrewEscalation.ts**
- `/api/v1/discovery/${flowId}/escalate/dependencies/think`
- `/api/v1/discovery/${flowId}/escalate/dependencies/ponder`
- `/api/v1/discovery/${flowId}/escalation/${escalationId}/status`
- `/api/v1/discovery/${flowId}/escalation/status`
- `/api/v1/discovery/${flowId}/escalation/${escalationId}`

### 6. **src/hooks/discovery/useDiscoveryFlowList.ts**
- `/api/v1/discovery/flows/active` (multiple occurrences)

### 7. **src/hooks/__tests__/useAttributeMappingLogic.test.ts**
- `/api/v1/discovery/field-mappings`
- `/api/v1/discovery/clarifications`

### 8. **src/hooks/useApplication.ts**
- `/api/v1/discovery/applications/${applicationId}` (multiple occurrences)

### 9. **src/pages/discovery/CMDBImport/index.tsx**
- `/api/v1/discovery/flow/status/${file.flow_id}`
- `/api/v1/discovery/flow/${file.flow_id}/processing-status`

### 10. **src/pages/discovery/EnhancedDiscoveryDashboard/services/dashboardService.ts**
- `/api/v1/discovery/flows/active`
- `/api/v1/discovery/flow/status?flow_id=${dataImport.id}`

### 11. **src/pages/discovery/components/CMDBImport/AgentOrchestrationPanel.tsx**
- `/api/v1/discovery/flow/collaboration/analytics/${flowState.flow_id}`
- `/api/v1/discovery/flow/planning/intelligence/${flowState.flow_id}`
- `/api/v1/discovery/flow/crews/monitoring/${flowState.flow_id}`

### 12. **src/pages/discovery/hooks/useCMDBImport.ts**
- `/api/v1/discovery/flow/run-redesigned` (multiple occurrences)
- `/api/v1/discovery/flow/agentic-analysis/status-public?flow_id=${flowId}`

### 13. **src/pages/discovery/inventory/index.tsx**
- `/api/v1/discovery/inventory`

## Additional Configuration Files

### **src/config/api.ts**
Contains discovery endpoint configurations under `API_CONFIG.ENDPOINTS.DISCOVERY` but these are relative paths that get prefixed with `/api/v1` by the `apiCall` function.

## Summary
- **13 active files** still using legacy `/api/v1/discovery/` endpoints
- Most are related to flow status, crew monitoring, and legacy discovery operations
- Test file also contains legacy endpoint references
- These need to be migrated to use the unified discovery flow endpoints (`/api/v1/unified-discovery/`)