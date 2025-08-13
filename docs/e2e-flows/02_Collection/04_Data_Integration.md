# Collection Flow: 04 - Data Integration

The Data Integration method is the most advanced collection option, providing automated data gathering from various sources. This method is suitable for modern environments where APIs and other integration points are available.

## 1. Process Overview

1.  **Platform Detection**: The flow begins by detecting the platforms in the user's environment (e.g., AWS, Azure, GCP). This is the `PLATFORM_DETECTION` phase.
2.  **Automated Collection**: Once the platforms are identified, the system uses platform-specific adapters to collect data automatically. This corresponds to the `AUTOMATED_COLLECTION` phase.
3.  **Data Synthesis**: The collected data from various sources is synthesized and normalized.

## 2. Key Technologies

- **Platform Adapters**: The system uses a set of adapters, each designed to communicate with a specific platform's API.
- **CrewAI Orchestration**: The `unified_collection_flow.py` orchestrates the entire process, from platform detection to data collection and validation.

## 3. Benefits

- **Speed and Efficiency**: Automating the data collection process significantly reduces the time and effort required.
- **Accuracy**: Collecting data directly from the source ensures a high degree of accuracy.
- **Comprehensive Coverage**: This method can gather a wide range of data that might be difficult to collect manually.

## 4. Code References

- **Frontend**: `src/pages/collection/Index.tsx` (initiates the flow)
- **CrewAI Flow**: `backend/app/services/crewai_flows/unified_collection_flow.py` (defines the `PLATFORM_DETECTION` and `AUTOMATED_COLLECTION` phases)
