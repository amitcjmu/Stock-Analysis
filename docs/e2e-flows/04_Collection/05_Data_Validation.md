# Collection Flow: 05 - Data Validation

Data validation is a critical step that occurs after data has been collected, regardless of the method used. Its purpose is to ensure the quality, accuracy, and completeness of the data before it is used for assessment.

## 1. Validation Process

The data validation process involves several checks:

- **Completeness Check**: Verifies that all required data fields have been populated.
- **Accuracy Check**: Cross-references data points to ensure consistency and correctness. For example, it might check if an IP address is in a valid format.
- **Quality Scoring**: Assigns a quality score to the data based on its completeness and accuracy.

## 2. Technical Details

- **CrewAI Phase**: The `DATA_VALIDATION` phase in the `unified_collection_flow.py` is responsible for orchestrating the validation process.
- **Automated Rules**: The system uses a set of predefined rules to perform the validation checks.
- **Manual Review**: In cases where the automated validation fails or flags data for review, a user may be prompted to manually verify the information.

## 3. Outcome

The outcome of the validation process is a clean, reliable dataset that can be confidently used in the **Assessment** phase. Any data that fails validation is either corrected or flagged for further investigation.

## 4. Code References

- **CrewAI Flow**: `backend/app/services/crewai_flows/unified_collection_flow.py`
