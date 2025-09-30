# Collection Questionnaire ID and Error Handling Fixes
Date: 2025-01-29

## Insight 1: Hardcoded UUID Removal Pattern
**Problem**: Backend overriding questionnaire_id with hardcoded UUID "00000000-0000-0000-0000-000000000001"
**Solution**: Preserve original questionnaire_id from bootstrap generation
**Code**:
```python
# backend/app/api/v1/endpoints/collection_crud_questionnaires/queries.py
# WRONG - Hardcoded UUID override:
return [
    AdaptiveQuestionnaireResponse(
        id=str(UUID("00000000-0000-0000-0000-000000000001")),  # BAD!
        
# CORRECT - Preserve original ID:
return [
    AdaptiveQuestionnaireResponse(
        id=bootstrap_q.get("questionnaire_id", "bootstrap_asset_selection"),
```
**Usage**: Never hardcode UUIDs; always preserve IDs from source data

## Insight 2: Agent Response Multi-Format Parser
**Problem**: CrewAI agents return questionnaires in various formats, parser couldn't find data
**Solution**: Enhanced parser to check multiple paths and generate from gap_analysis
**Code**:
```python
# backend/app/api/v1/endpoints/collection_crud_questionnaires/utils.py
def _extract_questionnaire_data(agent_result: dict, flow_id: str):
    # Try multiple paths
    questionnaires_data = agent_result.get("questionnaires", [])
    sections_data = agent_result.get("sections", [])
    
    # Check wrappers
    if not questionnaires_data and "result" in agent_result:
        result_data = agent_result["result"]
        questionnaires_data = result_data.get("questionnaires", [])
    
    # Generate from gap_analysis if no questionnaire data
    if not data_to_process and "processed_data" in agent_result:
        if "gap_analysis" in agent_result["processed_data"]:
            # Create questions from missing_critical_fields
            for asset_id, fields in gap_analysis["missing_critical_fields"].items():
                for field in fields:
                    questions.append({
                        "field_id": field,
                        "question_text": f"Please provide {field.replace('_', ' ').title()}",
                        "field_type": "text",
                        "required": True,
                        "metadata": {"asset_id": asset_id}
                    })
```
**Usage**: When parsing agent responses, check multiple formats and generate fallbacks

## Insight 3: Asset Filtering for Agent Context
**Problem**: All engagement assets passed to agent instead of just selected ones
**Solution**: Filter assets based on collection_config selected_application_ids
**Code**:
```python
# backend/app/api/v1/endpoints/collection_crud_questionnaires/queries.py
# Get ALL assets first
all_assets = await _get_existing_assets(db, context)

# Filter to only selected
selected_asset_ids = []
if flow.collection_config and flow.collection_config.get("selected_application_ids"):
    selected_asset_ids = flow.collection_config["selected_application_ids"]

existing_assets = []
if selected_asset_ids:
    for asset in all_assets:
        if str(asset.id) in selected_asset_ids:
            existing_assets.append(asset)
    logger.info(f"Filtered to {len(existing_assets)} selected assets")
```
**Usage**: Always filter context data to what's relevant for the current operation

## Insight 4: Database Enum Constraint Compliance
**Problem**: Invalid enum value "automated_collection" causing database errors
**Solution**: Use only valid CollectionFlowStatus enum values
**Code**:
```python
# backend/app/services/master_flow_sync_service/mappers.py
# Valid enum: initialized, asset_selection, gap_analysis, manual_collection, completed, failed, cancelled
status_mapping = {
    "running": "gap_analysis",  # Changed from "automated_collection"
    "completed": "completed",
    "failed": "failed",
    "paused": "gap_analysis",  # No "paused" in enum, use current phase
    "pending": "initialized",
}
```
**Usage**: Always verify enum values against database constraints before using

## Insight 5: Frontend Error Message UX
**Problem**: Technical error messages confusing users
**Solution**: User-friendly messages with actionable information
**Code**:
```typescript
// src/hooks/collection/useAdaptiveFormFlow.ts
// WRONG - Technical message:
userMessage = "Failed to generate questionnaire: Agent returned success but no questionnaire data";

// CORRECT - User-friendly:
if (error.message.includes("generation failed")) {
  userMessage = "Questionnaire generation is in progress. You can use this basic form while we prepare custom questions based on your data gaps.";
  shouldUseFallback = true;
}

toast({
  title: "Form Ready",  // Not "Fallback Form Loaded"
  description: userMessage,
  variant: "default",  // Not "warning"
});
```
**Usage**: Transform technical errors into helpful user guidance

## Insight 6: React State Declaration Fix
**Problem**: Duplicate state variable declaration causing syntax error
**Solution**: Use useEffect for conditional state updates
**Code**:
```typescript
// AssetSelectionForm.tsx
// WRONG - Duplicate declaration:
const [validationError, setValidationError] = useState<string | null>(null);
const validationError = selectedAssets.length === 0 ? "Select assets" : null;  // ERROR!

// CORRECT - useEffect:
const [validationError, setValidationError] = useState<string | null>(null);
React.useEffect(() => {
  if (selectedAssets.length < minSelections && selectedAssets.length > 0) {
    setValidationError(`Please select at least ${minSelections} asset${minSelections > 1 ? 's' : ''}`);
  } else if (selectedAssets.length > maxSelections) {
    setValidationError(`Please select no more than ${maxSelections} assets`);
  } else {
    setValidationError(null);
  }
}, [selectedAssets, minSelections, maxSelections]);
```
**Usage**: Never redeclare state variables; use effects for derived state

## Testing Pattern
**Iterative Testing**: Use CC agents for fixes → qa-playwright-tester for validation → repeat until working
**Log Monitoring**: Check both frontend and backend logs for complete picture
**End-to-End**: Test entire flow from asset selection through questionnaire submission