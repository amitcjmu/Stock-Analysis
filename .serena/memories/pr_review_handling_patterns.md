# PR Review Handling Patterns

## Complete Review Resolution Strategy

### Principle: Fix ALL Feedback in Same PR
Never defer to "follow-up PR" - reviewers expect complete resolution.

### Review Categories & Handling

#### Must-Fix Items (Blocking)
Handle immediately with focused fixes:
```python
# Example: Routing context preservation
def get_navigation_path(flow_type, phase_id, flow_id):
    if not phase_def:
        # FIXED: Always include flow_id
        return f"/{flow_type.value}/overview/{flow_id}"
```

#### High-Priority Items (Should Fix)
Include in same PR even if "non-blocking":

1. **Breaking Change Compatibility**
```python
# Add temporary routes during transition
api_router.include_router(router, prefix="/old-path", tags=["Deprecated"])
api_router.include_router(router, tags=["Current"])  # New path
```

2. **TypeScript Type Safety**
```typescript
// Before: Avoid this
const result = useQuery(...) as any;

// After: Proper typing
const result: UseQueryResult<DataType, Error> = useQuery<DataType, Error>(...);
```

3. **Pluggable Architecture**
```python
# Create extensible patterns
class LearnedPatternProvider(PatternProvider):
    async def get_patterns(self) -> Dict[str, List[str]]:
        # ML-based patterns in future
        return await self.fetch_learned_patterns()

class HeuristicPatternProvider(PatternProvider):
    async def get_patterns(self) -> Dict[str, List[str]]:
        # Current rule-based patterns
        return self.BASE_PATTERNS
```

4. **Comprehensive Testing**
```python
# Backend tests
async def test_data_cleansing_stats_success():
    response = await client.get(f"/flows/{flow_id}/data-cleansing/stats")
    assert response.status_code == 200

# Frontend tests
it('should fetch data when flowId provided', async () => {
    const { result } = renderHook(() => useDataCleansingStats('test-id'));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
});
```

### Response Template for Reviewers
```markdown
## ✅ ALL Review Items Addressed

### Must-Fix Items ✅
1. **Issue**: [Description]
   **Fixed**: [What was done]
   **File**: [path/to/file.py]

### High-Priority Items ✅
1. **Breaking Change Compatibility** ✅
   - Added temporary routes at old prefix
   - Documented migration path

2. **TypeScript Type Safety** ✅
   - Removed ALL 'any' casts
   - Exported proper interfaces

3. **Test Coverage** ✅
   - Added 13 backend tests
   - Added frontend hook tests

Ready for final review and merge! 🚀
```

## Bot-Specific Review Patterns

### Qodo Bot Reviews
Focus on security and code quality:
- **HIGH Priority**: Cross-tenant issues, memory leaks, security vulnerabilities
- **MEDIUM Priority**: Progress calculations, JSON serialization, error handling
- **LOW Priority**: Code style, documentation

Example fixes:
```python
# Memory leak fix
# WRONG: Cached by session
_service_cache[session_id] = DiscoveryFlowService()
# CORRECT: Fresh instance
return DiscoveryFlowService(db=db)

# Progress calculation fix
# WRONG: 0-based showing 0% initially
progress = int((current_index / total) * 100)
# CORRECT: 1-based
progress = int(((current_index + 1) / total) * 100)
```

### GPT5 Reviews
Focus on architecture and consistency:
- Router registration patterns
- Tag standardization
- API compatibility
- Documentation completeness

Example implementation:
```python
# Create fixes script for systematic resolution
def fix_all_review_items():
    fix_assessment_flow_tags()  # Use canonical tags
    fix_cross_tenant_caching()  # Security priority
    fix_api_health_tag_extraction()  # Consistency
    fix_error_response_structure()  # Standardization
    print("✅ All critical fixes applied!")
```

## Anti-Patterns to Avoid
- ❌ "Will address in follow-up PR"
- ❌ Partial fixes with TODOs
- ❌ Ignoring "high-priority" as optional
- ❌ No tests for new code
- ❌ Manual fixes without validation scripts

## Success Metrics
- Zero 'any' types in TypeScript
- All endpoints have tests
- Backward compatibility maintained
- Single PR resolves all feedback
- Validation scripts pass (check_api_tags.py, pre-commit)

## Qodo Bot Specific Patterns (Updated)

### Critical Learning: Update Existing PR
**NEVER create new branch/PR for review fixes** - Always update existing PR:
```bash
# WRONG: Creating new branch for fixes
git checkout -b fix/qodo-bot-suggestions  # ❌

# CORRECT: Stay on original branch
git checkout fix/bug-batch-20250820  # ✅
# Apply fixes
git add -A && git commit -m "fix: Apply Qodo Bot review suggestions"
git push origin fix/bug-batch-20250820
```

### Common Qodo Bot Suggestions & Fixes

#### 1. Function Signature Mismatches
```python
# Issue: Wrong parameter order
result = await execute_flow_phase(flow_id, next_phase, db, context)  # ❌

# Fix: Match actual function signature
result = await execute_flow_phase(flow_id, discovery_flow, context, db)  # ✅
```

#### 2. Database Query with Tenant Scoping
```python
# Issue: Using db.get() without tenant isolation
discovery_flow = await db.get(DiscoveryFlow, flow_id)  # ❌

# Fix: Proper filtered query with tenant scoping
stmt = select(DiscoveryFlow).where(
    and_(
        DiscoveryFlow.flow_id == flow_id,
        DiscoveryFlow.client_account_id == context.client_account_id,
        DiscoveryFlow.engagement_id == context.engagement_id,
    )
)
result = await db.execute(stmt)
discovery_flow = result.scalar_one_or_none()  # ✅
```

#### 3. Migration Enum Handling
```python
# Issue: Creating enums without checkfirst
enum.create(op.get_bind())  # ❌

# Fix: Idempotent creation
enum.create(op.get_bind(), checkfirst=True)  # ✅
```

#### 4. Table Existence Checks
```python
# Issue: Returning True on error masks failures
except Exception as e:
    return True  # ❌

# Fix: Return False to allow creation to proceed
except Exception as e:
    return False  # ✅
```
