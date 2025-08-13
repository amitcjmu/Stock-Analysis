# Collection Flow: 02 - Adaptive Forms

The Adaptive Forms method allows for manual data collection through a series of dynamically generated questionnaires. This method is ideal when direct integration is not possible and the data requirements are complex.

## 1. User Experience

After selecting the "Adaptive Forms" method, the user is guided through a series of forms. The questions in these forms are intelligently generated based on the information that is missing from the asset inventory.

- **Dynamic Questionnaires**: The forms are not static. They adapt to the information that has already been provided, ensuring that users are only asked for the information that is needed.
- **Progressive Disclosure**: The forms are presented in a logical sequence, guiding the user through the data collection process step-by-step.

## 2. Key Processes

- **Gap Analysis**: Before generating the questionnaires, the system performs a gap analysis to identify missing information. This is handled by the `GAP_ANALYSIS` phase of the CrewAI flow.
- **Questionnaire Generation**: Based on the gap analysis, the `QUESTIONNAIRE_GENERATION` phase creates the necessary forms and questions.
- **Manual Collection**: The user fills out the forms, providing the missing information. This corresponds to the `MANUAL_COLLECTION` phase.

## 3. Technical Implementation

- **CrewAI Phases**: The entire process is orchestrated by the `unified_collection_flow.py` CrewAI flow, specifically the `GAP_ANALYSIS`, `QUESTIONNAIRE_GENERATION`, and `MANUAL_COLLECTION` phases.
- **Data Storage**: The collected data is stored in the database and associated with the corresponding asset.

## 4. Code References

- **CrewAI Flow**: `backend/app/services/crewai_flows/unified_collection_flow.py`
