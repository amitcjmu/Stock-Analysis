# Discovery Flow Remediation Plan

**Date**: June 24, 2025  
**Status**: Draft  
**Owner**: [To be assigned]  

## Overview
This document outlines the plan to consolidate and modernize the Discovery flow implementation, focusing on migrating from legacy implementations to the V2 CrewAI Flow architecture.

## Current State Analysis

### Active V2 Components
1. **API Endpoints** (`/backend/app/api/v1/discovery_flow_v2.py`)
   - Modern implementation using CrewAI Flow
   - Properly integrated with V2 services
   - Follows current architectural patterns

2. **Core Services**
   - `DiscoveryFlowService` (`/backend/app/services/discovery_flow_service.py`)
   - `DiscoveryFlowRepository` (`/backend/app/repositories/discovery_flow_repository.py`)
   - `UnifiedFlowManagement` (in CrewAI flows)

3. **Frontend Integration**
   - `useDiscoveryFlowV2` hook
   - Modern React components using the V2 API

### Legacy Components to Be Deprecated

1. **API Endpoints**
   - `/backend/app/api/v1/endpoints/discovery_flow_management.py`
   - `/backend/app/api/v1/endpoints/discovery_flow_management_enhanced.py`
   - Legacy endpoints in `/backend/app/api/v1/endpoints/discovery.py`

2. **Services**
   - `discovery_flow_cleanup_service.py` (replaced by V2 version)
   - Potentially redundant services that duplicate V2 functionality

## Remediation Tasks

### Phase 1: Code Analysis and Documentation (Week 1-2)

1. **Inventory All Discovery-Related Code**
   - [ ] Map all components using legacy discovery flow
   - [ ] Document data flows between components
   - [ ] Identify all database tables and models used by legacy code

2. **Create Test Coverage**
   - [ ] Add integration tests for V2 endpoints
   - [ ] Create migration tests for data consistency
   - [ ] Document test coverage gaps

### Phase 2: API Consolidation (Week 3-4)

1. **Migrate Remaining Endpoints**
   - [ ] Move remaining functionality from legacy endpoints to V2
   - [ ] Update request/response schemas to match V2 patterns
   - [ ] Implement proper error handling and logging

2. **Update API Documentation**
   - [ ] Document all V2 endpoints
   - [ ] Create migration guide for consumers
   - [ ] Add deprecation notices to legacy endpoints

### Phase 3: Service Layer Updates (Week 5-6)

1. **Consolidate Services**
   - [ ] Merge functionality from legacy services into V2 services
   - [ ] Update service interfaces to use V2 patterns
   - [ ] Remove deprecated service methods

2. **Data Access Layer**
   - [ ] Update repositories to use V2 models
   - [ ] Implement proper transaction management
   - [ ] Add data migration scripts if needed

### Phase 4: Frontend Updates (Week 7-8)

1. **Component Updates**
   - [ ] Update all components to use V2 hooks
   - [ ] Remove legacy API calls
   - [ ] Implement proper loading and error states

2. **State Management**
   - [ ] Consolidate state management using V2 patterns
   - [ ] Remove legacy state management code
   - [ ] Add proper type definitions

### Phase 5: Testing and Validation (Week 9-10)

1. **Integration Testing**
   - [ ] Test all discovery flow scenarios
   - [ ] Validate data consistency
   - [ ] Performance testing

2. **User Acceptance Testing**
   - [ ] Create test cases for all user flows
   - [ ] Validate with stakeholders
   - [ ] Document test results

## Detailed File Changes

### Files to Be Removed
1. `/backend/app/api/v1/endpoints/discovery_flow_management.py`
2. `/backend/app/api/v1/endpoints/discovery_flow_management_enhanced.py`
3. `/backend/app/services/discovery_flow_cleanup_service.py` (after migrating to V2)

### Files to Be Modified
1. `/backend/app/api/v1/endpoints/discovery.py`
   - Remove legacy endpoints
   - Update to use V2 services

2. `/backend/app/services/discovery_flow_service.py`
   - Add any missing functionality from legacy services
   - Update method signatures to match V2 patterns

3. Frontend hooks and components
   - Update to use V2 API endpoints
   - Remove legacy state management

## Risk Assessment

### High Risk Areas
1. **Data Migration**
   - Risk: Data loss during migration
   - Mitigation: Create backups and test migration scripts

2. **API Changes**
   - Risk: Breaking changes for API consumers
   - Mitigation: Maintain backward compatibility during transition

3. **Testing Coverage**
   - Risk: Incomplete test coverage leading to regressions
   - Mitigation: Implement comprehensive test suite

## Rollback Plan
1. Maintain V1 endpoints during transition
2. Use feature flags for gradual rollout
3. Keep database backups before major changes
4. Document rollback procedures for each phase

## Success Metrics
1. 100% of discovery functionality using V2 architecture
2. Zero regressions in functionality
3. Improved performance metrics
4. Reduced code complexity and maintenance burden

## Detailed Inventory Findings

### 1. Legacy Discovery Flow Components

#### Backend API Endpoints
- **File**: `/backend/app/api/v1/endpoints/discovery_flow_management.py`
  - **Status**: Legacy (to be deprecated)
  - **Key Functions**:
    - `get_incomplete_flows`: Retrieves incomplete discovery flows
    - `get_flow_details`: Gets details for a specific flow
    - `resume_discovery_flow`: Resumes an incomplete flow
    - `delete_discovery_flow`: Deletes a flow with cleanup
    - `bulk_flow_operations`: Performs bulk operations on flows

- **File**: `/backend/app/api/v1/endpoints/discovery_flow_management_enhanced.py`
  - **Status**: Legacy enhancement (to be deprecated)
  - **Purpose**: Extended functionality for flow management

#### Backend Services
- **File**: `/backend/app/services/asset_creation_bridge_service.py`
  - **Status**: Mixed (partially migrated to V2)
  - **Key Functions**:
    - `create_assets_from_discovery`: Creates assets from discovery flow
    - `_update_discovery_flow_completion`: Updates flow completion status

- **File**: `/backend/app/services/discovery_flow_completion_service.py`
  - **Status**: Mixed (partially migrated to V2)
  - **Key Functions**:
    - `validate_flow_completion_readiness`: Validates if flow can be completed
    - `get_assessment_ready_assets`: Gets assets ready for assessment
    - `generate_assessment_package`: Creates assessment package from flow

#### Database Models
- **File**: `/backend/app/models/discovery_flow.py`
  - **Status**: Legacy model (to be reviewed)
  - **Key Tables**:
    - `discovery_flows`: Main table for discovery flows
    - `discovery_assets`: Related assets for discovery flows
  - **Key Fields**:
    - `flow_id`: Primary identifier
    - `client_account_id`, `engagement_id`: Multi-tenancy fields
    - Phase tracking flags (`data_import_completed`, etc.)
    - CrewAI integration fields

### 2. Data Flows

#### Legacy Flow
1. **Initialization**:
   - Frontend calls legacy endpoints in `discovery_flow_management.py`
   - Service layer uses `DiscoveryFlowStateManager` for state handling
   - State stored in `discovery_flows` table

2. **Asset Creation**:
   - `AssetCreationBridgeService` creates assets from discovery
   - Updates flow completion status
   - Maintains relationship between discovery and asset data

3. **Completion Flow**:
   - `DiscoveryFlowCompletionService` validates completion
   - Generates assessment packages
   - Updates flow state

### 3. Frontend Components

#### Legacy Components
- **File**: `src/pages/Discovery.tsx`
  - **Status**: Legacy entry point
  - **Purpose**: Main discovery page

- **File**: `src/hooks/useDiscoveryDashboard.ts`
  - **Status**: Legacy hook
  - **Purpose**: Manages discovery dashboard state

#### V2 Components
- **File**: `src/pages/discovery/DiscoveryFlowV2.tsx`
  - **Status**: Current implementation
  - **Purpose**: Main V2 discovery flow component

- **File**: `src/hooks/discovery/useDiscoveryFlowV2.ts`
  - **Status**: Current implementation
  - **Purpose**: Manages V2 discovery flow state

### 4. Database Tables

#### Core Tables
1. `discovery_flows`
   - Stores flow metadata and state
   - Tracks phase completion
   - Maintains CrewAI integration data

2. `discovery_assets`
   - Stores assets discovered during flow
   - References `discovery_flows`
   - Contains asset metadata and state

3. `crewai_flow_state_extensions`
   - Extends CrewAI flow state
   - Stores additional metadata for discovery flows

## Next Steps
1. Assign owners to each task
2. Schedule kickoff meeting
3. Set up progress tracking
4. Begin Phase 1 implementation
