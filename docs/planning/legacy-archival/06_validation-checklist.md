# Pre-Removal Validation Checklist

## Before Removing Any Legacy Code
1. [ ] Run full test suite with legacy guard enabled
2. [ ] Check Docker logs for any 410 responses
3. [ ] Grep for imports of component to be removed
4. [ ] Review recent git history for related changes
5. [ ] Test in staging environment
6. [ ] Document removal in CHANGELOG

## Post-Removal Validation
1. [ ] All tests pass
2. [ ] No TypeScript compilation errors
3. [ ] No Python import errors
4. [ ] Docker containers start successfully
5. [ ] Frontend loads without console errors
6. [ ] No 404 errors in browser network tab
7. [ ] API health check endpoints respond correctly

