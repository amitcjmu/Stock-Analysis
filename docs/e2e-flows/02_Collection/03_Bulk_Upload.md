# Collection Flow: 03 - Bulk Upload

This document provides a complete, end-to-end data flow analysis for the `Bulk Upload` page in the Collection phase of the AI Modernize Migration Platform.

**Analysis Date:** 2024-08-01 (Updated)

**Assumptions:**
*   The analysis focuses on the `src/pages/collection/BulkUpload.tsx` page.
*   The platform operates entirely within a Docker environment.
*   All API calls require authentication and multi-tenant context headers.

---

## 1. Frontend: Components and API Calls

The Bulk Upload page allows users to upload a large number of applications at once using a CSV template. The page handles file parsing, data display, and submission to the backend.

### Key Components & Hooks
*   **Page Component:** `src/pages/collection/BulkUpload.tsx`
*   **UI Components:**
    *   `BulkDataGrid`: A data grid for displaying and editing the uploaded application data.
    *   `ValidationDisplay`: Shows the results of data validation.
    *   `ProgressTracker`: Tracks the progress of the bulk upload process. **Note:** The fix plan indicates that the progress tracking on the frontend has been improved.

### API Call Summary

| # | Method | Endpoint                      | Trigger                           | Description                               |
|---|--------|-------------------------------|-----------------------------------|-------------------------------------------|
| 1 | `POST` | `/api/v1/data-import/store-import` | `handleBulkUpload` function       | Stores the imported data in the backend.  |

---

## 2. Backend, CrewAI, ORM, and Database Trace

The backend for the Bulk Upload page is primarily concerned with receiving and storing the uploaded data. The processing of this data is handled by a Discovery flow, which is initiated by the `store-import` endpoint.

### API Endpoint: `POST /api/v1/data-import/store-import`

*   **FastAPI Route:** This route is likely located in `backend/app/api/v1/endpoints/data_import.py`.
*   **CrewAI Interaction:** This endpoint initiates a new Discovery flow to process the uploaded data. This is a key difference from the other collection methods, which are part of a Collection flow.
*   **ORM Layer:**
    *   **Operation:** Creates records to store the imported file and its data, and a new `DiscoveryFlow` record.
    *   **Models:** `DataImport`, `ImportedFile` (inferred), `DiscoveryFlow`.
*   **Database:**
    *   **Tables:** `data_imports`, `imported_files` (inferred), `discovery_flows`.
    *   **Query:** `INSERT INTO ...`

---

## 3. End-to-End Flow Sequence: Uploading Bulk Data

1.  **User Downloads Template:** The user clicks "Download Template" to get a CSV file with the required headers.
2.  **User Uploads File:** The user selects a populated CSV file to upload, triggering the `handleBulkUpload` function.
3.  **Client-Side Parsing:** The frontend reads and parses the CSV data into a JSON format.
4.  **API Call:** A `POST` request is sent to `/api/v1/data-import/store-import` with the parsed data.
5.  **Backend Stores Data and Starts Flow:** The backend stores the data and starts a new Discovery flow to process it in the background.
6.  **Frontend Displays Data:** The uploaded data is displayed in the `BulkDataGrid` component, and the user receives a notification that the process has started.

---

## 4. Troubleshooting Breakpoints

| Breakpoint                        | Diagnostic Check                                                                                               | Platform-Specific Fix                                                                                             |
|-----------------------------------|----------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **File Upload Fails**             | Check the browser's console for errors in the `handleBulkUpload` function. An error message from the API might indicate a problem with the file format or the backend service. | Ensure the uploaded file is a valid CSV and that the `migration_backend` container is running and accessible. Check the backend logs for errors in the `data-import` service. |
| **Data is Not Displayed Correctly**| Verify that the client-side parsing logic in `handleBulkUpload` is correctly interpreting the CSV data. Check for any JavaScript errors during parsing. | The issue might be with the CSV file's format (e.g., delimiters, newlines). Ensure the file is a standard comma-separated CSV. If the problem persists, debug the parsing logic in `BulkUpload.tsx`. |
| **Discovery Flow Doesn't Start**  | The API response from `store-import` should indicate if a flow was started. If not, there might be an issue with the Discovery flow creation logic. | Check the backend logs for errors related to the `DiscoveryFlow` creation after a bulk upload. There might be a misconfiguration in the `data-import` service. |
