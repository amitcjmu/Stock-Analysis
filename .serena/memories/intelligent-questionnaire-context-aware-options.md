# Intelligent Context-Aware Questionnaire Generation

**Session Date**: October 31, 2025
**Feature**: PR #890 - Intelligent questionnaire options with asset context threading

---

## Problem: Static Dropdown Options Don't Adapt to Asset Characteristics

**Context**: Questionnaire dropdowns showed same options for all assets, regardless of OS, EOL status, or business criticality. Users had to search through irrelevant options.

**Solution**: Context-aware intelligent option generation that reorders dropdowns based on asset attributes.

---

## Implementation Pattern: Asset Context Threading Pipeline

**Pipeline Flow**:
```
Asset Data → EOL Detection → Serialization → Gap Analysis → Intelligent Options → Questionnaire
```

### 1. EOL Detection (Runtime Pattern Matching)

**File**: `backend/app/api/v1/endpoints/collection_crud_questionnaires/utils.py`

```python
def _determine_eol_status(
    operating_system: str, os_version: str, technology_stack: List[str]
) -> str:
    """Detect EOL status from OS and tech stack patterns."""
    eol_os_patterns = {
        "AIX 7.1": "EOL_EXPIRED",
        "AIX 7.2": "EOL_EXPIRED",
        "Windows Server 2008": "EOL_EXPIRED",
        "Windows Server 2012": "EOL_EXPIRED",
        "RHEL 6": "EOL_EXPIRED",
        "RHEL 7": "EOL_SOON",
    }

    eol_tech_patterns = {
        "websphere_85": "EOL_EXPIRED",
        "jboss_6": "EOL_EXPIRED",
        "tomcat_7": "EOL_EXPIRED",
    }

    # Check OS first
    if operating_system and os_version:
        os_key = f"{operating_system} {os_version}".strip()
        for pattern, status in eol_os_patterns.items():
            if pattern in os_key:
                return status

    # Check tech stack
    if technology_stack and isinstance(technology_stack, list):
        for tech in technology_stack:
            if tech in eol_tech_patterns:
                return eol_tech_patterns[tech]

    return "CURRENT"
```

**Key Insight**: Runtime detection > Database field. Eliminates need for pre-population while maintaining accuracy.

---

### 2. Asset Serialization with EOL Context

**File**: `backend/app/api/v1/endpoints/collection_crud_questionnaires/utils.py`

```python
def _analyze_selected_assets(existing_assets: List[Asset]) -> Tuple[List[dict], dict]:
    """Serialize assets with EOL context for intelligent options."""
    selected_assets = []

    for asset in existing_assets:
        # Extract data for EOL detection
        operating_system = getattr(asset, "operating_system", None) or ""
        os_version = getattr(asset, "os_version", None) or ""
        technology_stack = getattr(asset, "technology_stack", [])

        # Runtime EOL determination
        eol_technology = _determine_eol_status(
            operating_system, os_version, technology_stack
        )

        selected_assets.append({
            "id": str(asset.id),  # CRITICAL: Use "id" not "asset_id"
            "operating_system": operating_system,
            "os_version": os_version,
            "technology_stack": technology_stack,
            "eol_technology": eol_technology,  # ← Added for intelligent options
            "criticality": getattr(asset, "criticality", "unknown"),
        })

    return selected_assets, asset_analysis
```

**Critical Detail**: `section_builders.py` expects `"id"` key, not `"asset_id"`. Wrong key breaks context lookup.

---

### 3. Intelligent Option Functions (Modular Pattern)

**File**: `backend/app/services/ai_analysis/questionnaire_generator/tools/intelligent_options/security_options.py`

```python
def get_security_vulnerabilities_options(
    asset_context: Dict,
) -> Optional[Tuple[str, List[Dict[str, str]]]]:
    """EOL-aware security vulnerability options."""
    eol_status = asset_context.get("eol_technology", "").upper()

    # EOL_EXPIRED → High Severity first (urgent)
    if "EOL_EXPIRED" in eol_status:
        options = [
            {"value": "high_severity", "label": "High Severity - Critical vulnerabilities exist"},
            {"value": "medium_severity", "label": "Medium Severity - Moderate risk"},
            {"value": "low_severity", "label": "Low Severity - Minor issues"},
            {"value": "none_known", "label": "None Known - No vulnerabilities identified"},
        ]
        logger.info(f"Providing high-risk options for EOL status: {eol_status}")
        return "select", options

    # CURRENT → None Known first (optimistic)
    elif "CURRENT" in eol_status:
        options = [
            {"value": "none_known", "label": "None Known - No vulnerabilities identified"},
            {"value": "low_severity", "label": "Low Severity - Minor issues"},
            {"value": "medium_severity", "label": "Medium Severity - Moderate risk"},
            {"value": "high_severity", "label": "High Severity - Critical vulnerabilities exist"},
        ]
        return "select", options

    return None  # Fallback to default options
```

**Pattern**: Return `None` for graceful fallback, not empty options.

---

### 4. Context-Aware Field Routing

**File**: `backend/app/services/ai_analysis/questionnaire_generator/tools/section_builders.py`

```python
def _check_context_aware_field(
    attr_name: str, asset_context: Dict
) -> Optional[Tuple[str, List]]:
    """Route field names to intelligent option handlers."""
    context_aware_handlers = {
        "security_vulnerabilities": get_security_vulnerabilities_options,
        "security_compliance_requirements": get_security_compliance_requirements_options,
        "eol_technology_assessment": get_eol_technology_assessment_options,
        "availability_requirements": get_availability_requirements_options,
    }

    handler = context_aware_handlers.get(attr_name)
    if handler:
        return handler(asset_context)
    return None

def determine_field_type_and_options(
    attr_name: str, asset_context: Optional[Dict] = None
) -> Tuple[str, List]:
    """Determine field type with context-aware precedence."""
    # CRITICAL: Check context-aware BEFORE static FIELD_OPTIONS
    if asset_context:
        result = _check_context_aware_field(attr_name, asset_context)
        if result:
            return result  # Early return for intelligent options

    # Fallback to static FIELD_OPTIONS
    if attr_name in FIELD_OPTIONS:
        return infer_field_type_from_config(attr_name, FIELD_OPTIONS[attr_name])

    # Final fallback to heuristics
    return get_fallback_field_type_and_options(attr_name)
```

**Key Insight**: Precedence order matters:
1. Context-aware intelligent options (highest priority)
2. Static FIELD_OPTIONS from config
3. Heuristic fallback (lowest priority)

---

## Critical Bug Fix: String Matching Edge Cases

**Problem**: Substring matching caused false positives
```python
# WRONG - matches "missionary", "submission", etc.
if "mission" in business_criticality:
```

**Solution**: Exact matching with normalized values
```python
# CORRECT - only matches intended values
business_criticality = (business_criticality_raw or "").strip().lower()
if business_criticality in ["mission_critical", "mission-critical", "critical", "mission"]:
    # ... mission critical options
```

**Files Fixed**:
- `intelligent_options/infrastructure_options.py`
- `intelligent_options/security_options.py`
- `intelligent_options/business_options.py`

---

## Testing Pattern: Mock Asset Context

**File**: `backend/tests/backend/services/ai_analysis/questionnaire_generator/tools/test_intelligent_options.py`

```python
def test_security_vulnerabilities_eol_expired():
    """Test EOL-expired assets show High Severity first."""
    context = {"eol_technology": "EOL_EXPIRED"}
    field_type, options = get_security_vulnerabilities_options(context)

    assert field_type == "select"
    assert len(options) == 5
    assert options[0]["value"] == "high_severity"  # First option
    assert options[-1]["value"] == "none_known"    # Last option

def test_security_vulnerabilities_current():
    """Test current assets show None Known first."""
    context = {"eol_technology": "CURRENT"}
    field_type, options = get_security_vulnerabilities_options(context)

    assert options[0]["value"] == "none_known"      # First option
    assert options[-1]["value"] == "high_severity"  # Last option
```

**Pattern**: Test option ordering, not just presence. First/last options validate intelligent reordering.

---

## Integration Test Pattern: End-to-End Context Threading

**File**: `backend/tests/backend/integration/test_intelligent_questionnaire_generation.py`

```python
@pytest.mark.asyncio
async def test_eol_expired_asset_context_threading(
    db_session: AsyncSession, test_client_account, test_engagement
):
    """Verify EOL_EXPIRED context flows through to intelligent options."""
    # Create EOL asset
    asset = Asset(
        id=uuid4(),
        operating_system="AIX",
        os_version="7.2",
        technology_stack=["WebSphere 8.5"],
    )
    db_session.add(asset)
    await db_session.commit()

    # Generate questionnaire
    questionnaire = await generate_questionnaire(
        asset_ids=[asset.id],
        db_session=db_session,
    )

    # Verify security vulnerabilities has EOL-aware ordering
    security_q = next(
        q for q in questionnaire["questions"]
        if q["field_id"] == "security_vulnerabilities"
    )
    assert security_q["field_type"] == "select"
    assert security_q["options"][0]["value"] == "high_severity"
```

**Key Insight**: Integration tests verify the entire pipeline, not just individual functions.

---

## Agent Warmup Prevention Pattern

**Problem**: Agent warmup autonomously calls tools with empty/zero assets, bypassing intelligent options.

**Solution**: Skip warmup for data-dependent agents

**File**: `backend/app/services/persistent_agents/config/manager.py`

```python
async def warmup_agent(self, agent_type: str, agent: Any):
    """Warmup agent - skip for data-dependent agents."""
    # Skip warmup for questionnaire_generator
    if agent_type == "questionnaire_generator":
        logger.info(
            f"{agent_type} agent warmup skipped - "
            "prevents autonomous tool execution with empty data"
        )
        return  # Early return

    # Normal warmup for other agents
    warmup_input = {"task": f"Verify {agent_type} agent ready"}
    await agent.execute_async(inputs=warmup_input)
```

**When to Apply**: Any agent with tools requiring real data (not synthetic warmup data).

---

## Usage Guidelines

### When to Use Context-Aware Options
1. **Asset characteristics matter** - OS, tech stack, criticality affect relevance
2. **Option ordering changes meaning** - First option = most likely/relevant
3. **Multiple asset types** - Different characteristics need different prioritization

### When NOT to Use
1. **Static taxonomies** - Compliance standards don't change per asset
2. **User preferences** - Personal choices not context-dependent
3. **Simple yes/no** - Binary choices don't need reordering

### Performance Considerations
- Pattern matching is O(n) where n = number of patterns
- Keep pattern dictionaries small (<20 entries)
- Use early returns to avoid unnecessary checks
- Cache normalized values (`.lower()`, `.strip()`) at function start

---

## Related Patterns
- **Fallback Chains**: Try context → static → heuristic
- **Early Returns**: Return `None` for graceful degradation
- **Exact Matching**: Normalize + exact match > substring matching
- **Modularization**: One function per field type (<200 lines)
