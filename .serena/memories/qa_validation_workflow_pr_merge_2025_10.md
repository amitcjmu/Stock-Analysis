# QA Validation Workflow After PR Merge

**Context**: Post-merge validation of Collection Flow Question Generation Fix (PR #659)
**Date**: October 2025
**Pattern**: Two-phase validation (manual + automated)

## Problem
After merging a major feature PR, need systematic validation to catch defects before production deployment.

## Solution Pattern

### Phase 1: Manual Browser Validation
**Purpose**: Quick smoke test to verify basic functionality

```bash
# 1. Verify Docker containers running
docker ps --filter "name=migration" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Expected: All 4 containers Up (frontend, backend, redis, postgres)
```

**Playwright Navigation Script**:
```javascript
// 1. Navigate to application
await page.goto('http://localhost:8081');

// 2. Login with demo credentials
await page.getByRole('textbox', { name: 'Email' }).fill('demo@demo-corp.com');
await page.getByRole('textbox', { name: 'Password' }).fill('Demo123!');
await page.getByRole('button', { name: 'Sign In' }).click();

// 3. Navigate to feature area
await page.locator('div').filter({ hasText: 'Collection' }).nth(4).click();
await page.getByRole('link', { name: 'Adaptive Forms' }).click();

// 4. Verify feature displays correctly
await page.getByRole('button', { name: 'View Details' }).click();
```

**Quick Checks**:
- ✅ No console errors
- ✅ Page loads successfully
- ✅ Navigation works
- ✅ Feature-specific elements visible

### Phase 2: Automated QA Agent Testing
**Purpose**: Comprehensive test coverage with defect reporting

```bash
# Invoke qa-playwright-tester agent with detailed test plan
Task subagent_type=qa-playwright-tester prompt="
IMPORTANT: First read:
1. /docs/analysis/Notes/coding-agent-guide.md
2. /.claude/agent_instructions.md

Test Areas:
1. Navigation & Access
2. Flow Status & Phase Progression
3. API Endpoint Testing
4. Error Scenarios
5. Performance & UX

Expected Outcomes:
✅ All pages load without 404 errors
✅ Flow phases display correctly
✅ No console errors
✅ API endpoints respond properly

Defect Reporting:
For ANY issues found:
1. Document exact reproduction steps
2. Include screenshots if UI-related
3. Copy exact error messages
4. Note expected vs actual behavior
5. Classify severity: Critical/High/Medium/Low
"
```

**Agent Deliverables**:
- Comprehensive QA test report (markdown)
- Defect log with reproduction steps
- Production readiness recommendation
- Test coverage metrics

## Pattern Application

**When to Use**:
- After merging major feature PRs
- Before production deployment
- For multi-phase implementations
- When changes span backend + frontend

**Benefits**:
1. **Fast feedback**: Manual validation in 5-10 minutes
2. **Comprehensive coverage**: Automated agent tests all scenarios
3. **Defect prevention**: Catches issues before production
4. **Documentation**: QA report for deployment sign-off

## Example Results - PR #659

**Manual Validation**: ✅ 5 minutes, no issues
- Login successful
- Collection flow navigation working
- Flow details display correctly
- No console errors

**Automated Testing**: ✅ 45 minutes, 11/11 passed
- Backend verification: PASS
- Frontend verification: PASS
- API integration: PASS (200+ requests)
- Phase configuration: PASS
- ADR compliance: PASS
- **Defects found**: ZERO

**Production Readiness**: ✅ APPROVED (95% confidence)

## Integration with Workflow

**Pre-commit** → **PR Review** → **Merge** → **QA Validation** → **Production Deploy**

This two-phase validation happens AFTER merge but BEFORE production deployment:
1. Run manual browser validation (5-10 min)
2. If manual passes → invoke qa-playwright-tester agent
3. If agent finds defects → create GitHub issues
4. If zero defects → approve for production

## Anti-Patterns to Avoid

❌ **Don't**: Skip validation assuming CI/CD covers everything
- CI/CD tests code, not user workflows

❌ **Don't**: Only test happy path scenarios
- Test error handling, edge cases, performance

❌ **Don't**: Deploy without QA report
- Report provides deployment sign-off documentation

## Commands Reference

```bash
# Start Docker if needed
cd config/docker && docker-compose up -d

# Check backend logs for errors
docker logs migration_backend --tail 100

# Open Playwright browser for manual testing
# (via MCP tools: browser_navigate, browser_click, etc.)

# Invoke QA agent
Task subagent_type=qa-playwright-tester prompt="[detailed test plan]"

# Check QA report
ls -lh QA_TEST_REPORT_*.md
```

**Key Takeaway**: Two-phase validation (manual + automated) catches defects before production while providing documented sign-off for deployment.
