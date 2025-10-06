# Asset-Batched Gap Enhancement Implementation Plan (Revised)

**Date**: October 2025
**Status**: Pending Approval
**ADRs**: ADR-024 (TenantMemoryManager), ADR-010 (Docker-first)

---

## Executive Summary

Revert direct LLM bypass and implement proper asset-based batching with:
- ✅ Persistent TenantScoped agent reuse (no per-call Crew instantiation)
- ✅ **Sequential** asset processing (agent is single-threaded, not concurrency-safe)
- ✅ Redis distributed lock (prevents multiple workers processing same flow)
- ✅ Per-asset persistence with composite unique index (immediate upsert)
- ✅ HTTP polling for progress (no SSE per frontend policy)
- ✅ **Tenant-configurable** context filtering (allowlist + denylist, 8KB payload cap)
- ✅ TenantMemoryManager learning (fail-safe, non-blocking, ENGAGEMENT scope)
- ✅ Strict schema validation with structured error codes
- ✅ Per-asset timeout (30s) and circuit breaker (>50% failure rate)
- ✅ **Manual intervention only** (no auto-retry, user re-runs failed assets)

---

## Architecture Principles

### 1. Persistent Agent Reuse (TenantScoped)
- **ONE** TenantScoped agent instance per execution run
- Agent is tenant-isolated by design (client_account_id + engagement_id)
- **NO** per-asset Crew/Task instantiation
- Agent created once at method entry, reused sequentially across all assets
- `memory=False` (per ADR-024) with TenantMemoryManager for learning

### 2. Sequential Asset Processing (No Concurrency)
- Process assets **sequentially** (one at a time)
- TenantScoped agent is single-threaded by design
- No semaphore needed (agent is not concurrency-safe)
- Per-flow Redis lock prevents multiple workers processing same flow
- User preference: Manual intervention for failures, no auto-retry

### 3. Distributed Coordination
- **Redis per-flow lock** prevents multiple workers processing same flow
- Lock key: `gap_enhancement_lock:{flow_id}` with 15-minute TTL
- Acquire lock before processing, release on completion/failure
- If lock acquisition fails, return `409 Conflict` (another worker processing)

### 4. Progressive Persistence
- Upsert gaps to DB immediately after each asset (atomic transaction)
- Composite unique index: `(collection_flow_id, field_name, gap_type, asset_id)`
- Handle serialization conflicts with single retry
- Update progress metrics in Redis/DB
- Frontend polls status endpoint (HTTP only, no SSE)

### 5. Context Payload Control (Tenant-Configurable)
- **Allowlist + Denylist**: Per-tenant safe keys + global PII/secret patterns
- **String cap**: Max 500 chars per value, max 8KB total payload per asset
- **Redaction**: Keys matching `SECRET_PATTERNS` or PII patterns
- **Canonicalization**: Lowercase keys, trim whitespace
- **Default to global allowlist** if tenant config not set

### 6. Fail-Safe Learning (Non-Blocking)
- TenantMemoryManager operations wrapped in try/except
- Learning failures never block enhancement
- Log learning errors to telemetry, continue execution
- Learning scope: ENGAGEMENT (default), fallback to CLIENT if sparse
- TTL on learnings to prevent drift, cap history to 1000 patterns

### 7. Manual Intervention (No Auto-Retry)
- **No automatic retries** for failed assets
- Mark failed assets with structured error_code
- User can manually re-run AI analysis for specific gaps later
- Expose `/requeue-failed-assets` endpoint for manual retry

---

## Phase 1: Context Filtering & Payload Builder

### File: `backend/app/services/collection/gap_analysis/context_filter.py` (NEW)

```python
"""Context filtering utilities for gap analysis."""

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# Global defaults (fallback if tenant config not set)
DEFAULT_SAFE_KEYS = {
    "environment",
    "app_owner",
    "technology",
    "tech_stack",
    "framework",
    "language",
    "deployment_type",
    "region",
    "cost_center",
    "business_unit",
    "application_tier",
    "compliance_requirements",
    "backup_policy",
    "monitoring_enabled",
}

# Global denylist (PII and secrets)
DENYLIST_PATTERNS = [
    r"password",
    r"token",
    r"secret",
    r"api[_-]?key",
    r"credential",
    r"auth",
    r"private[_-]?key",
    r"ssn",
    r"social[_-]?security",
    r"credit[_-]?card",
    r"email",
    r"phone",
]

MAX_STRING_LENGTH = 500
MAX_PAYLOAD_SIZE = 8192  # 8KB total per asset


async def get_tenant_safe_keys(
    client_account_id: str, redis_client
) -> set:
    """Get tenant-specific safe keys from Redis cache.

    Args:
        client_account_id: Tenant identifier
        redis_client: Redis client instance

    Returns:
        Set of allowed custom_attribute keys for this tenant
    """
    cache_key = f"tenant_safe_keys:{client_account_id}"

    # Try cache first
    cached = await redis_client.get(cache_key)
    if cached:
        return set(json.loads(cached))

    # Fall back to default
    return DEFAULT_SAFE_KEYS


def is_denied_key(key: str) -> bool:
    """Check if key matches global denylist (PII/secrets)."""
    key_lower = key.lower()
    return any(re.search(pattern, key_lower) for pattern in DENYLIST_PATTERNS)


def filter_custom_attributes(
    custom_attrs: Dict[str, Any],
    allowed_keys: set,
    max_payload_size: int = MAX_PAYLOAD_SIZE
) -> Dict[str, Any]:
    """Filter custom_attributes with allowlist, denylist, and size caps.

    Args:
        custom_attrs: Raw custom_attributes from asset
        allowed_keys: Tenant-specific allowed keys
        max_payload_size: Maximum total payload size in bytes

    Returns:
        Filtered dict with redacted secrets, capped lengths, and bounded size
    """
    if not custom_attrs:
        return {}

    filtered = {}
    total_size = 0

    for key, value in custom_attrs.items():
        # Canonicalize key (lowercase, trim)
        key_canonical = key.strip().lower()

        # Check denylist first (PII/secrets)
        if is_denied_key(key_canonical):
            logger.debug(f"Redacted denied key: {key}")
            continue

        # Check allowlist
        if key_canonical not in allowed_keys:
            continue

        # Skip null/empty
        if value is None or value == "":
            continue

        # Cap string length
        if isinstance(value, str):
            value = value.strip()
            if len(value) > MAX_STRING_LENGTH:
                value = value[:MAX_STRING_LENGTH] + "..."
                logger.debug(f"Truncated {key} to {MAX_STRING_LENGTH} chars")

        # Check payload size
        value_size = len(json.dumps({key: value}))
        if total_size + value_size > max_payload_size:
            logger.warning(
                f"Payload size limit reached ({max_payload_size} bytes), "
                f"dropping {key} and remaining fields"
            )
            break

        filtered[key_canonical] = value
        total_size += value_size

    return filtered


def build_compact_asset_context(asset: Any) -> Dict[str, Any]:
    """Build compact asset context with only relevant fields.

    Args:
        asset: Asset model instance

    Returns:
        Compact dict with filtered fields
    """
    context = {
        "id": str(asset.id),
        "name": asset.name,
        "asset_type": asset.asset_type,
    }

    # Include only non-null standard fields
    optional_fields = [
        "description",
        "environment",
        "location",
        "discovery_source",
    ]

    for field in optional_fields:
        value = getattr(asset, field, None)
        if value is not None and value != "":
            context[field] = value

    # Filter custom_attributes
    if asset.custom_attributes:
        filtered_custom = filter_custom_attributes(asset.custom_attributes)
        if filtered_custom:
            context["custom_attributes"] = filtered_custom

    return context
```

---

## Phase 2: Task Builder with Filtered Context

### File: `backend/app/services/collection/gap_analysis/task_builder.py` (MODIFY)

**Add new function**:

```python
def build_asset_enhancement_task(
    asset_gaps: List[Dict[str, Any]],
    asset_context: Dict[str, Any],
    previous_learnings: List[Dict] = None,
) -> str:
    """Build enhancement task for ONE asset with filtered context.

    Args:
        asset_gaps: 5-10 gaps for THIS asset only
        asset_context: Filtered asset context (from context_filter.build_compact_asset_context)
        previous_learnings: Similar patterns from TenantMemoryManager

    Returns:
        Task description string
    """
    learning_section = ""
    if previous_learnings and len(previous_learnings) > 0:
        learning_section = f"""
PREVIOUS LEARNINGS (similar {asset_context['asset_type']} assets):
{json.dumps([
    {
        "field": l.get("field_name"),
        "resolution": l.get("suggested_resolution"),
        "confidence": l.get("confidence_score")
    } for l in previous_learnings[:3]  # Limit to 3 most relevant
], indent=2)}
"""

    return f"""
TASK: Enhance {len(asset_gaps)} data gaps for ONE asset using available context.

ASSET CONTEXT (filtered, safe subset):
{json.dumps(asset_context, indent=2)}

{learning_section}

GAPS TO ENHANCE ({len(asset_gaps)} gaps):
{json.dumps(asset_gaps, indent=2)}

INSTRUCTIONS:
1. Use ONLY the provided asset context (standard fields + whitelisted custom_attributes)
2. Assign confidence_score (0.0-1.0) based on evidence strength:
   - 0.9-1.0: Strong evidence in asset context
   - 0.7-0.8: Moderate evidence, reasonable inference
   - 0.5-0.6: Weak evidence, speculative
   - 0.0-0.4: No evidence, best practice only
3. Provide 2-3 actionable ai_suggestions per gap
4. Set suggested_resolution to the single best action

CONFIDENCE EXAMPLES:
- Gap: "technology_stack" missing, custom_attributes has "tech_stack": "Node.js" → confidence=0.95
- Gap: "os" missing, custom_attributes has "environment": "linux-prod" → confidence=0.85
- Gap: "os" missing, no context → confidence=0.40 (generic suggestion)

RETURN VALID JSON (enhance ALL {len(asset_gaps)} gaps):
{{
    "gaps": {{
        "critical": [
            {{
                "asset_id": "EXACT_UUID_FROM_INPUT",
                "field_name": "EXACT_FIELD_FROM_INPUT",
                "gap_type": "missing_field",
                "gap_category": "infrastructure",
                "priority": 1,
                "confidence_score": 0.95,
                "ai_suggestions": [
                    "Check deployment manifests for OS details",
                    "Review infrastructure-as-code templates",
                    "Query asset owner for confirmation"
                ],
                "suggested_resolution": "Check deployment manifests for OS details"
            }}
        ],
        "high": [...],
        "medium": [...],
        "low": [...]
    }},
    "summary": {{
        "total_gaps": {len(asset_gaps)},
        "context_keys_used": ["custom_attributes.tech_stack", "environment"]
    }}
}}

CRITICAL: Return ONLY valid JSON, no markdown, no explanations.
"""
```

---

## Phase 3: Persistent Agent Executor with Bounded Concurrency

### File: `backend/app/services/collection/gap_analysis/service.py` (MAJOR REWRITE)

```python
import asyncio
from typing import Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)
from app.services.crewai_flows.memory.tenant_memory_manager import (
    TenantMemoryManager,
    LearningScope,
)
from .context_filter import build_compact_asset_context
from .task_builder import build_asset_enhancement_task
from .output_parser import parse_task_output
from .gap_persistence import persist_gaps
from .validation import validate_enhancement_output

logger = logging.getLogger(__name__)

# Per-asset timeout (30 seconds)
PER_ASSET_TIMEOUT = 30

# Circuit breaker threshold (abort if failure rate > 50%)
CIRCUIT_BREAKER_THRESHOLD = 0.5


async def _run_tier_2_ai_analysis_no_persist(
    self, assets: List, collection_flow_id: str, gaps: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Run tier_2 AI enhancement with persistent agent (sequential processing).

    Architecture:
    - ONE persistent TenantScoped agent for entire run (no per-asset Crew instantiation)
    - SEQUENTIAL asset processing (agent is single-threaded)
    - Redis lock prevents multiple workers processing same flow
    - Per-asset upsert to DB after each enhancement
    - TenantMemoryManager learning (fail-safe, non-blocking)
    - HTTP polling for progress (no SSE)
    - Manual intervention for failures (no auto-retry)
    """
    # Acquire distributed lock (prevent double-processing)
    lock_key = f"gap_enhancement_lock:{collection_flow_id}"
    lock_acquired = await redis_client.set(
        lock_key, "locked", nx=True, ex=900  # 15-minute TTL
    )

    if not lock_acquired:
        raise HTTPException(
            status_code=409,
            detail="Another worker is already processing this flow"
        )

    try:
        # Get single persistent agent for entire run
        logger.debug("🔧 Creating persistent gap_analysis_specialist agent")
        agent = await TenantScopedAgentPool.get_or_create_agent(
            client_id=self.client_account_id,
            engagement_id=self.engagement_id,
            agent_type="gap_analysis_specialist",
        )

    # Initialize memory manager (fail-safe wrapper below)
    memory_manager = TenantMemoryManager(
        crewai_service=crewai_service,
        database_session=db,
    )

    # Group gaps by asset
    gaps_by_asset = {}
    for gap in gaps:
        asset_id = gap.get("asset_id")
        if asset_id not in gaps_by_asset:
            gaps_by_asset[asset_id] = []
        gaps_by_asset[asset_id].append(gap)

    # Create asset lookup
    asset_lookup = {str(a.id): a for a in assets}

        # Progress tracking
        total_assets = len(gaps_by_asset)
        processed_count = 0
        failed_count = 0
        failed_assets = []  # Track for manual intervention
        all_enhanced_gaps = {"critical": [], "high": [], "medium": [], "low": []}

        # Get tenant safe keys for context filtering
        tenant_safe_keys = await get_tenant_safe_keys(
            self.client_account_id, redis_client
        )

        # Process assets SEQUENTIALLY (agent is not concurrency-safe)
        for asset_id, asset_gaps in gaps_by_asset.items():
            # Check circuit breaker
            if failed_count > 0:
                failure_rate = failed_count / max(processed_count + failed_count, 1)
                if failure_rate > CIRCUIT_BREAKER_THRESHOLD:
                    logger.error(
                        f"Circuit breaker triggered: {failure_rate:.0%} failure rate"
                    )
                    break

            asset = asset_lookup.get(asset_id)
            if not asset:
                logger.warning(f"Asset {asset_id} not found, skipping")
                failed_count += 1
                failed_assets.append({
                    "asset_id": asset_id,
                    "error_code": "asset_not_found"
                })
                continue

            try:
                logger.info(
                    f"🔄 Enhancing {len(asset_gaps)} gaps for {asset.name} "
                    f"({asset.asset_type}) - {processed_count + 1}/{total_assets}"
                )

                # Build filtered context
                asset_context = build_compact_asset_context(asset)

                # Retrieve learnings (fail-safe)
                previous_learnings = []
                try:
                    previous_learnings = await memory_manager.retrieve_similar_patterns(
                        client_account_id=self.client_account_id,
                        engagement_id=self.engagement_id,
                        scope=LearningScope.ENGAGEMENT,
                        pattern_type="gap_enhancement",
                        query_context={
                            "asset_type": asset.asset_type,
                            "gap_fields": [g.get("field_name") for g in asset_gaps],
                        },
                        limit=3,
                    )
                except Exception as e:
                    logger.error(f"Learning retrieval failed (non-blocking): {e}")

                # Build task
                task_description = build_asset_enhancement_task(
                    asset_gaps=asset_gaps,
                    asset_context=asset_context,
                    previous_learnings=previous_learnings,
                )

                # Execute agent (reuse persistent agent, no Crew creation)
                task_output = await self._execute_persistent_agent(
                    agent, task_description
                )

                # Parse and validate
                result_dict = parse_task_output(task_output)
                validation_errors = validate_enhancement_output(result_dict, asset_gaps)

                if validation_errors:
                    logger.warning(
                        f"Validation errors for {asset.name}: {validation_errors}"
                    )

                # Persist immediately (atomic per asset)
                gaps_persisted = await persist_gaps(
                    result_dict, [asset], db, collection_flow_id
                )

                # Store learning (fail-safe)
                try:
                    await memory_manager.store_learning(
                        client_account_id=self.client_account_id,
                        engagement_id=self.engagement_id,
                        scope=LearningScope.ENGAGEMENT,
                        pattern_type="gap_enhancement",
                        pattern_data={
                            "asset_id": asset_id,
                            "asset_type": asset.asset_type,
                            "gaps_enhanced": len(asset_gaps),
                            "context_keys": list(asset_context.get("custom_attributes", {}).keys()),
                            "avg_confidence": sum(
                                g.get("confidence_score", 0)
                                for gaps_list in result_dict["gaps"].values()
                                for g in gaps_list
                            ) / max(len(asset_gaps), 1),
                        },
                    )
                except Exception as e:
                    logger.error(f"Learning storage failed (non-blocking): {e}")

                # Update progress in Redis/DB
                await self._update_progress(
                    collection_flow_id,
                    processed=processed_count + 1,
                    total=total_assets,
                    current_asset=asset.name,
                )

                processed_count += 1

                return {
                    "success": True,
                    "gaps": result_dict["gaps"],
                    "gaps_persisted": gaps_persisted,
                }

            except Exception as e:
                logger.error(
                    f"Asset {asset.name} enhancement failed: {e}",
                    exc_info=True,
                )
                failed_count += 1
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }

    # Process all assets with bounded concurrency
    tasks = [
        process_single_asset(asset_id, asset_gaps)
        for asset_id, asset_gaps in gaps_by_asset.items()
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Aggregate results
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Task exception: {result}")
            failed_count += 1
            continue

        if result.get("success"):
            for priority in ["critical", "high", "medium", "low"]:
                all_enhanced_gaps[priority].extend(
                    result["gaps"].get(priority, [])
                )

    return {
        "gaps": all_enhanced_gaps,
        "questionnaire": {"sections": []},
        "summary": {
            "total_gaps": sum(len(v) for v in all_enhanced_gaps.values()),
            "assets_analyzed": processed_count,
            "assets_failed": failed_count,
            "gaps_persisted": sum(
                r.get("gaps_persisted", 0) for r in results if isinstance(r, dict)
            ),
        },
    }


async def _execute_persistent_agent(self, agent, task_description: str) -> Any:
    """Execute persistent agent WITHOUT creating new Crew/Task per call.

    Uses agent's internal execution method to avoid per-call Crew instantiation.
    Maintains max_iterations=1 (single-shot).
    """
    # Direct agent execution (no Crew creation)
    # Agent already configured with max_iterations=1 from TenantScopedAgentPool

    # If agent has execute_task method (direct execution)
    if hasattr(agent, "execute_task"):
        result = await agent.execute_task(task_description)
        return result

    # Otherwise, use minimal Task wrapper (reuse agent config)
    from crewai import Task

    task = Task(
        description=task_description,
        expected_output="JSON with enhanced gaps",
        agent=agent,
    )

    # Execute task directly on agent (agent already has max_iterations=1)
    result = await agent.execute_task_async(task)

    return result


async def _update_progress(
    self, flow_id: str, processed: int, total: int, current_asset: str
):
    """Update progress in Redis/DB for HTTP polling."""
    progress_key = f"gap_enhancement_progress:{flow_id}"

    progress_data = {
        "processed": processed,
        "total": total,
        "current_asset": current_asset,
        "percentage": int((processed / total) * 100),
        "updated_at": datetime.utcnow().isoformat(),
    }

    # Store in Redis with 1-hour TTL
    await redis_client.setex(
        progress_key,
        3600,
        json.dumps(progress_data),
    )
```

---

## Phase 4: Schema Validation

### File: `backend/app/services/collection/gap_analysis/validation.py` (NEW)

```python
"""Schema validation for gap enhancement outputs."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def validate_enhancement_output(
    result: Dict[str, Any], input_gaps: List[Dict]
) -> List[str]:
    """Validate enhancement output against strict schema.

    Args:
        result: Parsed output from agent
        input_gaps: Original input gaps

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Check top-level structure
    if "gaps" not in result:
        errors.append("Missing 'gaps' key in output")
        return errors

    gaps = result["gaps"]

    # Check priority keys
    for priority in ["critical", "high", "medium", "low"]:
        if priority not in gaps:
            errors.append(f"Missing '{priority}' priority in gaps")
        elif not isinstance(gaps[priority], list):
            errors.append(f"'{priority}' must be a list")

    # Validate each gap
    input_gap_ids = {g.get("asset_id") + g.get("field_name") for g in input_gaps}
    output_gap_count = 0

    for priority, gap_list in gaps.items():
        for idx, gap in enumerate(gap_list):
            output_gap_count += 1

            # Required fields
            required = ["asset_id", "field_name", "gap_type", "priority"]
            for field in required:
                if field not in gap:
                    errors.append(f"{priority}[{idx}]: Missing required field '{field}'")

            # Validate confidence_score
            if "confidence_score" in gap:
                score = gap["confidence_score"]
                if not isinstance(score, (int, float)):
                    errors.append(f"{priority}[{idx}]: confidence_score must be numeric")
                elif not (0.0 <= score <= 1.0):
                    errors.append(f"{priority}[{idx}]: confidence_score must be 0.0-1.0")

            # Validate ai_suggestions
            if "ai_suggestions" in gap:
                suggestions = gap["ai_suggestions"]
                if not isinstance(suggestions, list):
                    errors.append(f"{priority}[{idx}]: ai_suggestions must be a list")
                elif len(suggestions) == 0:
                    errors.append(f"{priority}[{idx}]: ai_suggestions cannot be empty")

    # Check gap count
    if output_gap_count != len(input_gaps):
        errors.append(
            f"Gap count mismatch: input={len(input_gaps)}, output={output_gap_count}"
        )

    return errors
```

---

## Phase 5: Progress Polling Endpoint

### File: `backend/app/api/v1/endpoints/collection_gap_analysis/analysis_endpoints.py` (ADD)

```python
@router.get("/{flow_id}/enhancement-progress")
async def get_enhancement_progress(
    flow_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get current progress of gap enhancement (HTTP polling).

    Frontend polls this endpoint every 2-3 seconds during enhancement.
    """
    progress_key = f"gap_enhancement_progress:{flow_id}"

    progress_json = await redis_client.get(progress_key)

    if not progress_json:
        return {
            "status": "not_started",
            "processed": 0,
            "total": 0,
        }

    progress = json.loads(progress_json)

    return {
        "status": "in_progress" if progress["processed"] < progress["total"] else "completed",
        "processed": progress["processed"],
        "total": progress["total"],
        "current_asset": progress.get("current_asset"),
        "percentage": progress["percentage"],
        "updated_at": progress["updated_at"],
    }
```

---

## Security & Privacy

### Logging Policy
- ✅ Log: asset_id, asset_name, gap counts, durations, success/failure
- ❌ NEVER log: raw custom_attributes content, gap descriptions with PII
- Redact in error logs: `logger.error(f"Asset {asset.name} failed", exc_info=True)` (no asset data)

### Context Filtering
- Whitelist: `SAFE_CUSTOM_ATTRIBUTE_KEYS` (configurable per tenant)
- Redact: Keys matching `SECRET_PATTERNS`
- Cap: String values > 500 chars truncated

### Error Handling
- Structured error codes: `asset_not_found`, `validation_failed`, `agent_timeout`
- No raw exceptions exposed to frontend
- Telemetry includes error types, not error messages with data

---

## Testing Strategy

### Unit Tests
1. `test_context_filter.py`
   - Verify secret redaction
   - Verify string truncation
   - Verify whitelist filtering

2. `test_validation.py`
   - Valid output passes
   - Missing required fields detected
   - Invalid confidence_score detected

### Integration Tests
1. Single asset enhancement (5 gaps)
2. Multi-asset enhancement (10 assets, 60 gaps)
3. Learning retrieval and storage
4. Concurrent execution (3 assets in parallel)
5. Failure recovery (1 asset fails, others succeed)

### Performance Tests
- 60 gaps across 10 assets: < 60 seconds total
- Per-asset latency: < 10 seconds
- Memory usage: < 500MB

---

## Rollout Plan

### Phase 1: Backend Changes
1. Create `context_filter.py`
2. Add `build_asset_enhancement_task()` to `task_builder.py`
3. Rewrite `_run_tier_2_ai_analysis_no_persist()` in `service.py`
4. Add `validation.py`
5. Add progress endpoint to `analysis_endpoints.py`

### Phase 2: Testing
1. Unit tests for filtering and validation
2. Integration test with 10 assets
3. Load test with 60 gaps

### Phase 3: Deployment
1. Deploy to staging
2. Test with real collection flow
3. Monitor: token usage, latency, error rates
4. Deploy to production with feature flag

---

## Monitoring & Observability

### Metrics to Track
- Per-asset enhancement duration (p50, p95, p99)
- Token consumption per asset
- Enhancement success rate
- Learning storage success rate
- Concurrent asset count (peak)

### Alerts
- Enhancement failure rate > 10%
- Per-asset latency > 15 seconds
- Learning storage failure rate > 5%

---

## Rollback Plan

If issues arise:
1. Feature flag off (fall back to tier_1 programmatic scan only)
2. Revert service.py to previous commit
3. No data loss (gaps already persisted per-asset)

---

## Approval Checklist

- [ ] Persistent agent reuse (no per-call Crew creation)
- [ ] Bounded concurrency with semaphore (MAX_CONCURRENT_ASSETS=3)
- [ ] Per-asset persistence (immediate upsert)
- [ ] HTTP polling for progress (no SSE)
- [ ] Context filtering (whitelist, redact secrets, cap lengths)
- [ ] Fail-safe learning (non-blocking)
- [ ] Strict validation with structured errors
- [ ] Security: no raw custom_attributes in logs
- [ ] Testing: unit + integration + performance
- [ ] Monitoring: metrics + alerts defined

---

## Answered Questions (per GPT5 feedback)

1. **Should `SAFE_CUSTOM_ATTRIBUTE_KEYS` be configurable per tenant?**
   - ✅ YES - Store per-tenant allowlist in Redis (with global default)
   - Global denylist for PII/secrets applies to all tenants
   - Cache in Redis, expose admin endpoint to manage

2. **Should learning scope be CLIENT or ENGAGEMENT for gap enhancement?**
   - ✅ ENGAGEMENT (default)
   - Fallback to CLIENT when engagement data is sparse
   - Namespace by asset_type for better pattern matching
   - Add TTL and cap history to 1000 patterns per scope

3. **Should we expose per-asset progress in API?**
   - ✅ Aggregate progress by default (processed/total)
   - Optionally provide per-asset status via paginated endpoint
   - Keep HTTP polling (no SSE/WebSockets)

4. **Should failed assets be retried automatically or require manual intervention?**
   - ✅ NO auto-retry (user preference)
   - Mark failed assets with structured error_code
   - User manually re-runs AI analysis for specific gaps later
   - Expose `/requeue-failed-assets` endpoint for manual retry

---

**Next Steps**: Await approval, then implement Phase 1 → Phase 2 → Phase 3.
