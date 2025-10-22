# Playwright E2E Testing & Debugging Checklist

## Common Workflow
1. Navigate to page
2. Wait for elements to load
3. Inspect page state with `browser_snapshot`
4. Interact with elements
5. Check network requests with `browser_network_requests`
6. Verify console logs for errors

## Key MCP Commands

### Navigation
```typescript
mcp__playwright__browser_navigate({ url: "http://localhost:8081/path" })
mcp__playwright__browser_wait_for({ time: 5 })  // seconds
```

### Inspection
```typescript
mcp__playwright__browser_snapshot()  // Better than screenshot
mcp__playwright__browser_console_messages({ onlyErrors: true })
mcp__playwright__browser_network_requests()
```

### Interaction
```typescript
// Click button
mcp__playwright__browser_click({
  element: "Button description",
  ref: "e123"  // from snapshot
})

// Type text
mcp__playwright__browser_type({
  element: "Email textbox",
  ref: "e456",
  text: "user@example.com"
})
```

## Login Pattern
```typescript
// 1. Navigate to login
await browser_navigate({ url: "http://localhost:8081/login" })
await browser_wait_for({ time: 3 })

// 2. Fill credentials
await browser_type({ element: "Email", ref: "e30", text: "demo@demo-corp.com" })
await browser_type({ element: "Password", ref: "e36", text: "Demo123!" })

// 3. Submit
await browser_click({ element: "Sign In button", ref: "e52" })
await browser_wait_for({ time: 3 })
```

## Debugging API Calls

### Check Network Requests
```typescript
const requests = await browser_network_requests()
// Look for POST/GET to specific endpoints
// Note: Cannot see request body directly from MCP
```

### Check Backend Logs
```bash
docker logs migration_backend --tail 100 | grep "endpoint_pattern"
```

### Verify Frontend State
```typescript
// Check console for state updates
await browser_console_messages()
// Look for log patterns like "🔍", "✅", "❌"
```

## Common Issues

### HMR Not Updating
**Symptom**: Code changes not reflected in browser
**Fix**:
```bash
docker-compose restart frontend
# OR hard refresh browser (Cmd+Shift+R)
```

### Element Not Found
**Symptom**: Click/type fails with element not found
**Fix**: Use `browser_snapshot()` to get current ref IDs

### Timing Issues
**Symptom**: Interaction fails because page not loaded
**Fix**: Add `browser_wait_for({ time: N })` before interaction

## Best Practices
1. Always `browser_snapshot()` before clicking to get correct refs
2. Use descriptive element names for better error messages
3. Check console messages for frontend errors
4. Check backend logs for API errors
5. Verify Docker containers are running: `docker ps`
