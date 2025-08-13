# E2E Flow: 04 - Collection

This document outlines the end-to-end user and data flow for the **Collection** phase of the migration process.

## 1. Objective

The primary objective of the Collection flow is to gather detailed information about the assets identified during the **Discovery** phase. This involves a combination of automated data collection, manual data entry through adaptive forms, and bulk data uploads. The goal is to enrich the asset inventory with the necessary details to perform a comprehensive assessment.

## 2. API Call Summary

| # | Method | Endpoint                              | Trigger                               | Description                                      |
|---|--------|---------------------------------------|---------------------------------------|--------------------------------------------------|
| 1 | `POST` | `/collection/flows`                   | User selects a collection method.     | Creates a new collection flow.                   |
| 2 | `GET`  | `/collection/flows`                   | Loading the collection progress page. | Fetches all collection flows.                    |
| 3 | `GET`  | `/collection/flows/{flow_id}`         | Viewing details of a specific flow.   | Fetches a single collection flow.                |
| 4 | `POST` | `/collection/flows/{flow_id}/start`   | User action to start a paused flow.   | Starts or resumes a collection flow.             |
| 5 | `POST` | `/collection/flows/{flow_id}/complete`| Automatic, upon flow completion.      | Marks a collection flow as complete.             |
| 6 | `GET`  | `/collection/questionnaires/{flow_id}`| Adaptive forms page loads.            | Fetches the questionnaire for a flow.            |
| 7 | `POST` | `/collection/questionnaires/{flow_id}`| User submits a form.                  | Submits answers to a questionnaire.              |

## 3. Directory Structure

The documentation for the Collection flow is organized as follows:

- **`00_Collection_Flow_Summary.md`**: This file.
- **`01_Overview_Page.md`**: Describes the main Collection dashboard and how users initiate the flow.
- **`02_Adaptive_Forms.md`**: Details the process of collecting data using dynamically generated forms.
- **`03_Bulk_Upload.md`**: Explains how to upload data in bulk using spreadsheets.
- **`04_Data_Integration.md`**: Covers direct integration with data sources for automated collection.
- **`05_Data_Validation.md`**: Describes the data validation and enrichment process.
- **`06_Handoff_to_Assess.md`**: Explains how the collected data is handed off to the Assessment flow.
