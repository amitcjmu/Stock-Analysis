# QA Playwright Testing Patterns

## Effective Testing Workflow
Use QA Playwright agent for thorough testing before pushing changes:
1. Deploy agent with specific test scenarios
2. Agent tests actual browser interactions
3. Provides screenshots and detailed reports
4. Catches routing errors, performance issues, and UX problems

## Example Test Scenario
```
Test scenario:
1. Navigate to http://localhost:8081
2. Login if needed
3. Click "Continue Flow" on flow ID: {specific-id}
4. Verify:
   - Response time (should be < 1 second)
   - No JavaScript errors in console
   - Navigation works (no 404 errors)
   - User guidance displayed properly
```

## Common Issues Found by QA Agent
1. **404 Routing Errors**: Routes in backend don't match frontend
2. **Performance Issues**: Identifies operations taking > 1 second
3. **Missing UI Elements**: Catches when expected elements don't render
4. **Console Errors**: Detects JavaScript errors users might miss

## Testing Commands
```bash
# Deploy QA agent for specific feature
Task tool with subagent_type: qa-playwright-tester

# Provide clear test instructions:
- What to test (specific flows/buttons)
- Expected behavior
- Known issues to watch for
- Metrics to measure (response times, error rates)
```

## QA Agent Capabilities
- Takes screenshots at key points
- Measures response times
- Checks console for errors
- Verifies element presence
- Tests navigation flows
- Validates data persistence

## Best Practices
1. Test after every major fix
2. Include both happy path and error cases
3. Verify fixes don't break other features
4. Check performance metrics
5. Validate across different flow types
