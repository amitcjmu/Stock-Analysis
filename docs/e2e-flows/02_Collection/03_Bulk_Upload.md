# Collection Flow: 03 - Bulk Upload

The Bulk Upload method provides a way to upload asset data from a spreadsheet. This is useful when the data has been collected offline or exported from another system.

## 1. User Journey

1.  **Select Method**: The user selects the "Bulk Upload" option from the Collection Overview page.
2.  **Download Template**: The user is prompted to download a spreadsheet template. This template contains the required columns for the asset data.
3.  **Populate Template**: The user fills in the template with their asset information.
4.  **Upload Spreadsheet**: The user uploads the completed spreadsheet.
5.  **Data Processing**: The system processes the spreadsheet, validates the data, and imports it into the asset inventory.

## 2. Backend Logic

- **File Parsing**: The backend receives the uploaded file and parses the spreadsheet data.
- **Data Validation**: Each row of the spreadsheet is validated to ensure data integrity. This is part of the `DATA_VALIDATION` phase in the CrewAI flow.
- **Asset Creation/Update**: The validated data is used to create new assets or update existing ones in the database.

## 3. Code References

- **Frontend**: `src/pages/collection/Index.tsx` (initiates the flow)
- **CrewAI Flow**: `backend/app/services/crewai_flows/unified_collection_flow.py` (handles data validation)
