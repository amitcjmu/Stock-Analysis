# Asset-Aware Questionnaire Generation Implementation

## Insight 1: Asset-Centric Collection Flow Architecture
**Problem**: Collection flows were allowing blank forms without asset selection, making gap analysis impossible
**Solution**: Enforce asset selection before questionnaire generation
**Code**:
```python
# Check for asset selection before generating questionnaires
selected_app_ids = flow.collection_config.get("selected_application_ids", [])
selected_asset_ids = flow.collection_config.get("selected_asset_ids", [])
if not selected_app_ids and not selected_asset_ids:
    logger.warning(f"No assets selected for collection flow {flow_id}")
    return [bootstrap_questionnaire_with_asset_selection_required()]
```
**Usage**: Always verify assets are selected before attempting gap-based questionnaire generation

## Insight 2: Comprehensive Asset Analysis for Gap Detection
**Problem**: Agent needed to understand unmapped attributes and failed mappings to generate relevant questions
**Solution**: Build comprehensive asset analysis including raw data inspection
**Code**:
```python
asset_analysis = {
    "unmapped_attributes": {},
    "failed_mappings": {},
    "missing_critical_fields": {},
    "data_quality_issues": {}
}

# Analyze unmapped attributes from raw data
raw_data = getattr(asset, "raw_data", {}) or {}
field_mappings = getattr(asset, "field_mappings_used", {}) or {}
mapped_fields = set(field_mappings.values()) if field_mappings else set()

for key, value in raw_data.items():
    if key not in mapped_fields and value:
        unmapped.append({
            "field": key,
            "value": str(value)[:100],
            "potential_mapping": _suggest_field_mapping(key)
        })

# Check critical fields
critical_fields = ["business_owner", "technical_owner", "six_r_strategy",
                  "migration_complexity", "dependencies", "operating_system"]
missing_fields = [f for f in critical_fields if not getattr(asset, f, None)]
```
**Usage**: Perform deep asset analysis before questionnaire generation to identify true gaps

## Insight 3: Tool-Based Agent Architecture (Not Heuristic)
**Problem**: Agents need tools to dynamically generate questionnaires, not static rules
**Solution**: Create specialized tools for agents to use
**Code**:
```python
# tools.py - Agent tools for dynamic generation
class QuestionnaireGenerationTool:
    def _run(self, asset_analysis, gap_type, asset_context):
        if gap_type == "missing_field":
            return self._generate_missing_field_question(asset_analysis, asset_context)
        elif gap_type == "unmapped_attribute":
            return self._generate_unmapped_attribute_question(asset_analysis, asset_context)
        # Dynamic generation based on gap type

# agents.py - Provide tools to agents
questionnaire_designer = Agent(
    role="Intelligent Questionnaire Designer",
    tools=[self.questionnaire_tool, self.gap_analysis_tool, self.asset_intelligence_tool]
)
```
**Usage**: Always provide agents with tools for dynamic behavior rather than hardcoded logic

## Insight 4: UUID to String Conversion for Foreign Keys
**Problem**: collection_flow_id expected string but got UUID type
**Solution**: Always convert UUIDs to strings when passing to Pydantic models
**Code**:
```python
# Convert UUID to string for FK fields
collection_flow_id=str(flow.id)  # NOT flow.flow_id
```
**Usage**: Use str() on UUID fields when passing to response models

## Insight 5: Persistent Multi-Tenant Agent Configuration
**Problem**: Need persistent agents for questionnaire generation per tenant
**Solution**: Add questionnaire_generator to agent pool constants
**Code**:
```python
# agent_pool_constants.py
"questionnaire_generator": {
    "role": "Adaptive Questionnaire Generation Agent",
    "goal": "Generate intelligent questionnaires based on gaps and asset types",
    "tools": ["questionnaire_generation", "gap_analysis", "asset_intelligence"],
    "max_retries": 3,
    "memory_enabled": True,
}
```
**Usage**: Configure persistent agents in agent_pool_constants for tenant-scoped operations
