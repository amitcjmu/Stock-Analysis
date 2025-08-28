# Frontend Debugging Patterns

## React Event Handler Not Firing Checklist

### Systematic Debug Approach:
1. **Add console.log at button level** - Verify click reaches element
2. **Check button disabled state** - Ensure not disabled at render
3. **Verify prop passing chain** - Trace from hook → parent → child
4. **Check for stopPropagation** - Parent elements blocking events
5. **Inspect with React DevTools** - Verify handler is bound
6. **Add visual feedback** - Border/color change on hover/click
7. **Test with different button** - Rule out specific element issue

### Common React Button Issues:

#### Issue: Infinite Re-renders Block Events
```javascript
// BAD - Causes infinite loop
useEffect(() => {
  initializeFlow();
}, [initializeFlow]); // Function recreated each render

// GOOD - Stable function reference
const initializeFlow = useCallback(async () => {
  // logic
}, [dependencies]);
```

#### Issue: Handler Not Bound
```javascript
// Debug pattern
console.log('Component render:', {
  hasHandler: !!handleSave,
  handlerType: typeof handleSave,
  isFunction: typeof handleSave === 'function'
});
```

#### Issue: Conditional Rendering
```javascript
// Check if button is in DOM
{condition && (
  <Button onClick={handleSave}>Save</Button>
)}
```

## Performance Optimization Patterns

### Prevent Excessive Re-renders:
```javascript
// Use React.memo for expensive components
const ExpensiveComponent = React.memo(({ data }) => {
  // render logic
}, (prevProps, nextProps) => {
  // return true if props are equal
  return prevProps.data.id === nextProps.data.id;
});

// Conditional logging to avoid console spam
useEffect(() => {
  if (process.env.NODE_ENV === 'development' && props.debug) {
    console.log('Props changed:', props);
  }
}, [props]);
```

### State Update Patterns:
```javascript
// Batch multiple state updates
setState(prev => ({
  ...prev,
  field1: value1,
  field2: value2,
  field3: value3
}));

// Avoid separate setState calls
// BAD:
setState1(value1);
setState2(value2);
setState3(value3);
```

## Playwright Testing Patterns

### Form Interaction Testing:
```javascript
// Fill form and save
await page.getByRole('textbox', { name: 'Application name' }).fill('Test App');
await page.getByRole('button', { name: 'Save Progress' }).click();

// Wait for save confirmation
await page.waitForSelector('text=Progress Saved', { timeout: 5000 });

// Verify console logs
const consoleLogs = await page.evaluate(() => {
  return window.consoleLogs || [];
});
expect(consoleLogs).toContain('Save button clicked');
```

### API Call Verification:
```javascript
// Monitor network requests
page.on('request', request => {
  if (request.url().includes('/api/v1/collection')) {
    console.log('API called:', request.method(), request.url());
  }
});
```

## Multi-Agent Debugging Strategy

### Coordinated Agent Deployment:
1. **Frontend Agent**: Fix UI/React issues
2. **Backend Agent**: Verify API endpoints
3. **Database Agent**: Check schema/permissions
4. **QA Agent**: End-to-end testing
5. **SRE Agent**: Check runtime logs

### Handoff Pattern:
```
Frontend finds issue → Backend verifies API → Database checks data → QA validates flow
```

Each agent provides specific validation before passing to next stage.
