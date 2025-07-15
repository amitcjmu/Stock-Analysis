# Discovery Flow E2E Testing Issues Log

## Overview
This document tracks all issues encountered during the end-to-end testing of the Discovery flow.

## Issue Format
- **Issue ID**: [DISC-XXX]
- **Phase**: [Data Import | Attribute Mapping | Data Cleansing | Inventory | Dependency Mapping]
- **Severity**: [Critical | High | Medium | Low]
- **Type**: [Frontend | Backend | Database | Integration]
- **Description**: Detailed description of the issue
- **Error Details**: Console errors, backend logs, stack traces
- **Impact**: How this affects the user experience or data integrity
- **Status**: [Open | In Progress | Resolved]

---

## Active Issues

### DISC-001 - 2025-01-15T10:30:00Z
- **Phase**: Data Import
- **Severity**: Critical
- **Type**: Backend
- **Description**: UUID JSON Serialization Error blocks all discovery flow creation
- **Error Details**: 
```
TypeError: Object of type UUID is not JSON serializable
Location: backend/app/services/crewai_flows/execution_engine.py:293
Failed SQL: UPDATE crewai_flow_state_extensions SET flow_persistence_data=$2::JSONB WHERE id=$1
```
- **Impact**: Complete blockage - no user can create new discovery flows
- **Status**: In Progress (Agent-6 implementing corrected fix)

---

### DISC-002 - 2025-01-15T10:31:00Z
- **Phase**: Data Import
- **Severity**: Critical
- **Type**: Frontend/Backend
- **Description**: Incomplete discovery flows blocking new data uploads
- **Error Details**: 
```
UI Message: "Upload Blocked: 2 incomplete discovery flows found. Complete or delete existing flows before uploading new data."
Stuck Flows:
- Flow 142698c8...: initialized | unknown | 0%
- Flow 0b639f54...: active | unknown | 0%
```
- **Impact**: Users cannot start new discovery processes
- **Status**: Open

---

### DISC-003 - 2025-01-15T10:32:00Z
- **Phase**: Data Import
- **Severity**: High
- **Type**: Database
- **Description**: Discovery flows not properly linked to master flows
- **Error Details**: 
```
Database Analysis:
- 19 out of 22 discovery flows (86%) have NULL master_flow_id
- 3 discovery flows reference non-existent master flows
```
- **Impact**: Flow state management broken, cannot track flow hierarchy
- **Status**: Open

---

### DISC-004 - 2025-01-15T10:33:00Z
- **Phase**: General
- **Severity**: High
- **Type**: Backend
- **Description**: Multi-tenant header violations causing API failures
- **Error Details**: 
```
Multiple endpoints missing X-Client-Account-Id header validation:
- /api/v1/unified-discovery/flow/initialize
- /api/v1/data-import/store-import
Returning 403 Forbidden when headers missing
```
- **Impact**: API calls fail without proper error messages
- **Status**: Resolved (Agent-6 verified configuration is correct)

---

### DISC-005 - 2025-01-15T10:34:00Z
- **Phase**: Inventory
- **Severity**: Critical
- **Type**: Database
- **Description**: No assets being generated from imported data
- **Error Details**: 
```
Database query results:
- 0 assets created in last 24 hours
- 94 raw import records exist
- 83 field mappings configured
- But no asset generation occurring
```
- **Impact**: Discovery flow cannot complete without asset creation
- **Status**: Open

---

### DISC-006 - 2025-01-15T10:35:00Z
- **Phase**: General
- **Severity**: High
- **Type**: Backend
- **Description**: High flow failure rate (60%+ flows not completing)
- **Error Details**: 
```
Master Flow Status Distribution:
- 43% cancelled (38/88)
- 19% failed (17/88)
- 30% completed (26/88)
- 8% running (7/88)
```
- **Impact**: Poor user experience, flows rarely complete successfully
- **Status**: Open (Solution designed by Agent-4)

---

### DISC-007 - 2025-01-15T10:36:00Z
- **Phase**: Data Import
- **Severity**: Medium
- **Type**: Frontend
- **Description**: Dialog system failure when attempting to delete flows
- **Error Details**: 
```
Browser dialog becomes stuck after clicking Delete button
Cannot dismiss or accept the confirmation dialog
All browser operations blocked until page refresh
```
- **Impact**: Users cannot clean up stuck flows through UI
- **Status**: Open (Solution designed by Agent-4)

---

### DISC-008 - 2025-01-15T10:37:00Z
- **Phase**: General
- **Severity**: Medium
- **Type**: Backend
- **Description**: Aggressive rate limiting affecting normal usage
- **Error Details**: 
```
Rate limit (429) triggered after just 5 rapid requests
Rate limit persists even after 5 second delay
Affects legitimate testing and user workflows
```
- **Impact**: API testing and automated workflows impacted
- **Status**: Open (Solution designed by Agent-4)

---

### DISC-009 - 2025-01-15T10:38:00Z
- **Phase**: Data Import
- **Severity**: Medium
- **Type**: Backend
- **Description**: User context issues preventing flow visibility
- **Error Details**: 
```
Error: Failed to get active flows for user: 'engagement_id'
Location: User service context creation
Users cannot see their active flows in UI
```
- **Impact**: Users lose visibility of their in-progress flows
- **Status**: Open (Solution designed by Agent-4)

---

### DISC-010 - 2025-01-15T10:39:00Z
- **Phase**: Data Import
- **Severity**: Medium
- **Type**: Backend
- **Description**: Data import validation too strict, missing documentation
- **Error Details**: 
```
POST /api/v1/data-import/store-import returns 422
Required fields not documented: file_data, metadata, upload_context
No clear error messages for missing fields
```
- **Impact**: Developers cannot integrate without proper API documentation
- **Status**: Open (Solution designed by Agent-4)

---

### DISC-011 - 2025-01-15T12:30:00Z
- **Phase**: All Phases
- **Severity**: Critical
- **Type**: Frontend
- **Description**: Browser native confirm dialog blocking ALL UI access on page load
- **Error Details**: 
```
Location: flowDeletionService.ts line 170
Code: const confirmed = window.confirm(...)
Triggered on page load with undefined flow data
Shows: "Unknown Flow" with all undefined values
Playwright cannot interact with native browser dialogs
```
- **Impact**: 100% UI blockage - no testing can proceed, no users can access the system
- **Status**: Resolved (Agent-6 replaced with React modal components)

---

### DISC-012 - 2025-01-15T13:00:00Z
- **Phase**: Data Import
- **Severity**: Critical
- **Type**: Frontend
- **Description**: Vite lazy loading failure preventing CMDBImport module from loading
- **Error Details**: 
```
TypeError: Failed to fetch dynamically imported module: 
http://localhost:8081/src/pages/discovery/CMDBImport.tsx?t=1752595262211

UI shows: "Failed to load Data Import"
Browser error: Module fetch failed with network error
```
- **Impact**: Cannot access Discovery flow data import page - blocks all testing
- **Status**: Resolved (Agent-4 cleared Vite cache and restarted frontend container)

---

## Summary Statistics
- **Total Issues**: 12
- **Critical**: 2 (DISC-002, DISC-005)
- **High**: 3
- **Medium**: 3
- **Low**: 0
- **Resolved**: 4 (DISC-001, DISC-004, DISC-011, DISC-012)
- **Blocking Issues**: 3 (DISC-002, DISC-003, DISC-005)