# Collection Flow: 01 - Overview Page

This page serves as the entry point for the Collection flow, where users can select their desired data collection method.

## 1. User Interface

The UI presents the user with several options for data collection, each tailored to a different use case.

- **Adaptive Forms**: For manual data entry with intelligent, context-aware forms.
- **Bulk Upload**: For uploading data from spreadsheets.
- **Data Integration**: For connecting directly to data sources.
- **Progress Monitoring**: To view the status of ongoing collection tasks.

![Collection Overview Page](<image_placeholder.png>)

## 2. User Actions

- **Selecting a Collection Method**: The user clicks on one of the collection method cards to initiate that specific workflow.
- **Permissions**: The ability to start a collection flow is restricted by user role. Only users with the "analyst" role or higher can create new collection flows.

## 3. Backend Integration

- **API Endpoint**: When a user starts a collection workflow, a `POST` request is made to `/api/v1/collection/flows`.
- **Request Payload**: The request payload includes the `workflowId` (e.g., `adaptive-forms`), an `automation_tier`, and a `collection_config` object.
- **Orchestration**: The backend uses the `MasterFlowOrchestrator` to create and manage the new collection flow.

## 4. Code References

- **Frontend**: `src/pages/collection/Index.tsx`
- **Backend API**: `backend/app/api/v1/endpoints/collection.py`
- **Orchestration**: `backend/app/services/master_flow_orchestrator.py`
- **CrewAI Flow**: `backend/app/services/crewai_flows/unified_collection_flow.py`
