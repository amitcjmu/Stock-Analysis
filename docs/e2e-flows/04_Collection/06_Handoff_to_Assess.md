# Collection Flow: 06 - Handoff to Assess

The handoff to the Assessment flow is the final step in the Collection process. It marks the completion of data gathering and the beginning of the analysis and planning stages.

## 1. Handoff Mechanism

- **Finalization Phase**: The `FINALIZATION` phase in the `unified_collection_flow.py` prepares the data for the handoff. This includes a final validation check and packaging the data in the required format.
- **Triggering Assessment Flow**: Once the finalization is complete, the system automatically triggers the start of the **Assessment** flow, passing the collected data as input.

## 2. Data Package

The data package that is handed off to the Assessment flow includes:

- **Enriched Asset Inventory**: The complete list of assets with all collected data.
- **Validation Reports**: Reports detailing the validation process and any issues that were found.
- **Collection Metadata**: Information about how the data was collected, including the methods used and timestamps.

## 3. User Notification

Upon successful handoff, the user is notified that the Collection flow is complete and that the Assessment flow has begun. They can then navigate to the Assessment dashboard to view the results.

## 4. Code References

- **CrewAI Flow**: `backend/app/services/crewai_flows/unified_collection_flow.py` (contains the `FINALIZATION` phase)
