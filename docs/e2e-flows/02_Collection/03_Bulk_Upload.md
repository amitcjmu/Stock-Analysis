# Collection Flow: 03 - Bulk Upload

This document provides a complete, end-to-end data flow analysis for the `Bulk Upload` page in the Collection phase of the AI Modernize Migration Platform.

**Analysis Date:** 2024-08-01

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
    *   `ProgressTracker`: Tracks the progress of the bulk upload process.

### API Call Summary

| # | Method | Endpoint                      | Trigger                           | Description                               |
|---|--------|-------------------------------|-----------------------------------|-------------------------------------------|
| 1 | `POST` | `/api/v1/data-import/store-import` | `handleBulkUpload` function       | Stores the imported data in the backend.  |

---

## 2. Backend, CrewAI, ORM, and Database Trace

The backend for the Bulk Upload page is primarily concerned with receiving and storing the uploaded data. The actual processing of the data is likely handled by a subsequent flow.

### API Endpoint: `POST /api/v1/data-import/store-import`

*   **FastAPI Route:** This route is likely located in `backend/app/api/v1/endpoints/data_import.py`.
*   **CrewAI Interaction:** This endpoint does not appear to directly trigger a CrewAI flow. It stores the raw data. It's likely that another process or a user action later on will trigger a CrewAI flow to process this imported data. The response from this endpoint does mention a `flow_id`, which suggests that a discovery flow might be initiated.
*   **ORM Layer:**
    *   **Operation:** Creates records to store the imported file and its data.
    *   **Models:** The specific models are not clear from the frontend code, but they are likely related to data import and staging.
*   **Database:**
    *   **Tables:** The tables used for storing the imported data are not specified in the frontend code. They are likely named `data_imports`, `imported_files`, or similar.
    *   **Query:** `INSERT INTO ...`

---

## 3. End-to-End Flow Sequence: Uploading Bulk Data

1.  **User Downloads Template:** The user clicks "Download Template" to get a CSV file with the required headers.
2.  **User Uploads File:** The user selects a populated CSV file to upload. The `handleBulkUpload` function is triggered.
3.  **Client-Side Parsing:** The frontend reads the file and parses the CSV data into a JSON format.
4.  **API Call:** A `POST` request is sent to `/api/v1/data-import/store-import` with the parsed data.
5.  **Backend Stores Data:** The backend stores the file and its content in the database.
6.  **Frontend Displays Data:** The uploaded data is displayed in the `BulkDataGrid` component.
7.  **User Proceeds:** The user can then review the data and proceed to the next step, which is likely data integration or validation.

---

## 4. Troubleshooting Breakpoints

| Breakpoint                        | Diagnostic Check                                                                                               | Platform-Specific Fix                                                                                             |
|-----------------------------------|----------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **File Upload Fails**             | Check the browser's console for errors in the `handleBulkUpload` function. An error message from the API might indicate a problem with the file format or the backend service. | Ensure the uploaded file is a valid CSV and that the `migration_backend` container is running and accessible. Check the backend logs for errors in the `data-import` service. |
| **Data is Not Displayed Correctly**| Verify that the client-side parsing logic in `handleBulkUpload` is correctly interpreting the CSV data. Check for any JavaScript errors during parsing. | The issue might be with the CSV file's format (e.g., delimiters, newlines). Ensure the file is a standard comma-separated CSV. If the problem persists, debug the parsing logic in `BulkUpload.tsx`. |
| **"Flow Creation Notice" warning**| This warning indicates that while the data was imported, a discovery flow could not be started, possibly due to an existing active flow. | This is not a critical error. The imported data is safe. The user will need to manually start a discovery or collection flow to process the data later. |
