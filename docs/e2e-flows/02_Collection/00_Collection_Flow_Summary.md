# Collection Flow - Architecture Summary

**Last Updated:** 2025-12-08
**Purpose:** Comprehensive reference guide for understanding the Collection flow architecture before making code changes

## 🎯 Overview

The Collection flow is a multi-phase, AI-powered data gathering workflow that identifies missing asset information through intelligent gap analysis and generates adaptive questionnaires to collect it. It uses CrewAI agents orchestrated by the Master Flow Orchestrator (MFO) to process data through seven distinct phases, ensuring assets have complete data before assessment.

**Key Capabilities:**
- Two-phase gap analysis: Tier 1 programmatic scanning (instant) + Tier 2 AI enhancement (detailed insights)
- Intelligent questionnaire generation with context-aware MCQ questions per-asset, per-section based on TRUE gaps only
- Gap inheritance - already-resolved gaps from ANY previous collection flow are never re-asked
- Adaptive form system that adjusts dynamically based on asset data quality and existing answers
- Asset write-back - resolved questionnaire responses automatically populate asset fields
- Cross-section deduplication to prevent redundant questions across sections and assets
- Assessment readiness tracking with automatic status updates when collection completes

## Recent Updates

**Migration 076_remap_collection_flow_phases** has consolidated the Collection Flow from 8 phases to 7 phases:
- **Removed**: `platform_detection` and `automated_collection` phases
- **Added**: `asset_selection` phase (combines functionality of removed phases)
- **Benefit**: Improved efficiency and reduced complexity

## 1. Objective

The primary objective of the Collection flow is to gather detailed information about the assets identified during the **Discovery** phase. This involves a combination of automated asset identification, data collection, manual data entry through adaptive forms, and bulk data uploads. The goal is to enrich the asset inventory with the necessary details to perform a comprehensive assessment.

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
