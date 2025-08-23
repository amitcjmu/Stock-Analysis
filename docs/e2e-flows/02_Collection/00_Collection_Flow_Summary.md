# E2E Flow: Collection Phase

This document outlines the end-to-end user and data flow for the **Collection** phase of the migration process, which is fully integrated with the Master Flow Orchestrator (MFO) architecture.

## 1. Objective

The primary objective of the Collection flow is to gather detailed information about the assets identified during the **Discovery** phase. This involves a combination of automated data collection, manual data entry through adaptive forms, and bulk data uploads. The goal is to enrich the asset inventory with the necessary details to perform a comprehensive assessment.

## 🏗️ MFO Integration Architecture

The Collection flow follows the **Master Flow Orchestrator** pattern:

- **Primary Identifier**: `master_flow_id` is used for ALL Collection operations
- **Unified Management**: ALL flow operations (create, resume, pause, delete) go through MFO
- **API Pattern**: Uses `/api/v1/master-flows/*` for flow lifecycle operations
- **Internal Implementation**: Collection-specific data stored in child tables but accessed via master_flow_id

## 2. API Call Summary (MFO-Aligned)

| # | Method | Endpoint                                           | Trigger                               | Description                                      |
|---|--------|----------------------------------------------------|---------------------------------------|--------------------------------------------------|
| 1 | `POST` | `/api/v1/master-flows`                            | User initiates collection flow.      | Creates a new collection flow via MFO.          |
| 2 | `GET`  | `/api/v1/master-flows/active?type=collection`     | Loading the collection progress page. | Fetches all active collection flows.            |
| 3 | `GET`  | `/api/v1/master-flows/{master_flow_id}`           | Viewing details of a specific flow.   | Fetches a single collection flow by master ID.  |
| 4 | `POST` | `/api/v1/master-flows/{master_flow_id}/resume`    | User action to start a paused flow.   | Resumes a collection flow via MFO.              |
| 5 | `POST` | `/api/v1/master-flows/{master_flow_id}/complete`  | Automatic, upon flow completion.      | Marks a collection flow as complete via MFO.    |
| 6 | `GET`  | `/api/v1/collection/questionnaires/{master_flow_id}` | Adaptive forms page loads.         | Fetches questionnaire using master_flow_id.     |
| 7 | `POST` | `/api/v1/collection/questionnaires/{master_flow_id}` | User submits a form.               | Submits answers using master_flow_id.           |

**Key Changes:**
- All flow lifecycle operations use `/api/v1/master-flows/*` endpoints
- Collection-specific operations use `master_flow_id` as the identifier
- No direct references to child flow IDs in public APIs

## 3. Directory Structure

The documentation for the Collection flow is organized as follows:

- **`00_Collection_Flow_Summary.md`**: This file.
- **`01_Overview_Page.md`**: Describes the main Collection dashboard and how users initiate the flow.
- **`02_Adaptive_Forms.md`**: Details the process of collecting data using dynamically generated forms.
- **`03_Bulk_Upload.md`**: Explains how to upload data in bulk using spreadsheets.
- **`04_Data_Integration.md`**: Covers direct integration with data sources for automated collection.
- **`05_Data_Validation.md`**: Describes the data validation and enrichment process.
- **`06_Handoff_to_Assess.md`**: Explains how the collected data is handed off to the Assessment flow.
