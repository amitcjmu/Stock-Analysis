# Multi-Tenant Context Leak Pattern - Security Fix

## Problem
Background tasks that query database without tenant scoping create critical security vulnerability. Attackers who guess analysis/flow IDs could access cross-tenant data.

## Qodo Bot Detection
Qodo Bot flagged this as Suggestion #4 (Importance 9/10):
> "Background tasks query SixRAnalysis and Asset tables WITHOUT tenant scoping"

## Solution Pattern
**Always pass tenant context through entire background task chain:**

### Step 1: Update API Endpoint to Pass Context
```python
# backend/app/api/v1/endpoints/sixr_analysis.py
background_tasks.add_task(
    service.run_initial_analysis,
    analysis.id,
    parameters.dict(),
    "system",
    context.client_account_id,  # SECURITY: Pass tenant context
    context.engagement_id,       # SECURITY: Pass tenant context
)
```

### Step 2: Update Service Method Signature
```python
# backend/app/api/v1/endpoints/sixr_analysis_modular/services/analysis_service.py
async def run_initial_analysis(
    self,
    analysis_id: int,
    parameters: Dict[str, Any],
    user: str,
    client_account_id: Optional[int] = None,  # NEW
    engagement_id: Optional[int] = None,      # NEW
):
```

### Step 3: Add Tenant Scoping to ALL Queries
```python
# BEFORE (VULNERABLE):
query = select(SixRAnalysis).where(SixRAnalysis.id == analysis_id)

# AFTER (SECURE):
query = select(SixRAnalysis).where(SixRAnalysis.id == analysis_id)
if client_account_id is not None:
    query = query.where(SixRAnalysis.client_account_id == client_account_id)
if engagement_id is not None:
    query = query.where(SixRAnalysis.engagement_id == engagement_id)
```

### Step 4: Handle Query Failures Securely
```python
result = await db.execute(query)
analysis = result.scalar_one_or_none()
if not analysis:
    logger.error(
        f"Analysis {analysis_id} not found for tenant "
        f"(client={client_account_id}, engagement={engagement_id})"
    )
    return  # Fail silently - don't reveal if ID exists in another tenant
```

## Verification Checklist
- [ ] Background task accepts client_account_id and engagement_id
- [ ] All SELECT queries include tenant scoping
- [ ] Query failures logged with tenant context
- [ ] No error messages reveal cross-tenant data existence
- [ ] Comments added: "SECURITY: Pass tenant context (Qodo Bot)"

## Related Vulnerabilities
Same pattern applies to:
- Asset queries
- Engagement queries
- Client account queries
- Any multi-tenant table accessed in background tasks

## Impact
CRITICAL - Prevents unauthorized cross-tenant data access via ID guessing attacks.
