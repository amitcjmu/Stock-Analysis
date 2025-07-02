# Assessment Flow - Browser Testing Guide

## 🎯 Overview
This guide provides step-by-step instructions for manually testing the Assessment Flow feature in a browser to verify all functionality is working correctly.

## 🚀 Quick Start

### 1. Start the Application
```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check health endpoints
curl http://localhost:8000/health
curl http://localhost:3000
```

### 2. Initialize Database
```bash
# Run migrations
docker exec migration_backend alembic upgrade head

# Initialize assessment data
docker exec migration_backend python -m app.core.database_initialization
```

## 📋 Test Scenarios

### Scenario 1: Initialize Assessment Flow

1. **Navigate to Inventory Page**
   - Open browser to `http://localhost:3000`
   - Login with test credentials
   - Click "Inventory" in the navigation

2. **Select Applications**
   - Check 2-3 applications marked as "Ready for Assessment"
   - Click "Assess Selected" button
   - Verify selection confirmation dialog

3. **Start Assessment**
   - Click "Start Assessment" button
   - Should redirect to `/assessment/{flow_id}/architecture`
   - Verify flow ID in URL

### Scenario 2: Architecture Standards Phase

1. **Template Selection**
   - Click "Select Template" dropdown
   - Choose "Financial Services" or "Healthcare" template
   - Verify standards populate automatically

2. **Custom Standards**
   - Click "Add Custom Standard"
   - Fill in:
     - Type: `custom_security`
     - Description: `Enhanced security requirements`
     - Mandatory: ✓ checked
   - Click "Add"

3. **Application Overrides**
   - Expand "Application-Specific Overrides"
   - Add exception for one application
   - Provide rationale

4. **Continue**
   - Click "Continue to Tech Debt Analysis"
   - Verify navigation to next phase

### Scenario 3: Tech Debt Analysis

1. **Component Discovery**
   - Verify components are displayed:
     - Frontend components
     - Backend services
     - Database layers
   - Check tech debt scores (0-10 scale)

2. **Filter and Sort**
   - Filter by severity: High
   - Sort by tech debt score
   - Verify filtering works

3. **Real-time Updates**
   - Look for "AI Agents Working..." indicator
   - Wait for analysis completion
   - Verify new components appear

4. **User Modifications**
   - Click on a component
   - Modify tech debt score
   - Add custom tech debt item
   - Save changes

### Scenario 4: 6R Strategy Review

1. **Component Strategies**
   - Verify each component has strategy dropdown
   - Options: Rewrite, ReArchitect, Refactor, Replatform, Rehost
   - Check overall application strategy (highest modernization)

2. **Compatibility Validation**
   - Change frontend to "Rewrite"
   - Change backend to "Retain"
   - Verify compatibility warning appears

3. **Bulk Operations**
   - Click "Bulk Edit"
   - Select multiple components
   - Apply "Replatform" to all
   - Verify changes

4. **Confidence Scores**
   - Check confidence indicators (0-100%)
   - Low confidence should flag for review

### Scenario 5: App-on-Page Review

1. **Comprehensive View**
   - Verify all sections present:
     - Application Summary
     - Component Breakdown
     - Technical Debt Analysis
     - 6R Decision Rationale
     - Architecture Exceptions
     - Dependencies
     - Business Impact

2. **Navigation**
   - Use "Previous/Next Application" buttons
   - Verify data changes for each app

3. **Export Functions**
   - Click "Export" button
   - Try PDF export
   - Try JSON export
   - Click "Print" for print preview

### Scenario 6: Assessment Summary

1. **Statistics Review**
   - Total applications assessed
   - Strategy distribution chart
   - Average confidence score
   - Tech debt overview

2. **Mark Ready for Planning**
   - Select applications ready for planning
   - Provide final notes
   - Click "Finalize Assessment"

3. **Complete Flow**
   - Verify "Assessment Complete" message
   - Click "Continue to Planning"
   - Should redirect to planning module

## 🔍 Verification Checklist

### Data Persistence
- [ ] Refresh page - data should persist
- [ ] Navigate away and return - progress saved
- [ ] Use browser back/forward - state maintained

### Multi-Tenant Isolation
- [ ] Switch client account - cannot access other flows
- [ ] Verify client account ID in API calls
- [ ] Check data isolation in responses

### Real-Time Updates
- [ ] SSE connection established (check Network tab)
- [ ] Agent progress messages appear
- [ ] UI updates without page refresh

### Error Handling
- [ ] Submit invalid data - proper error messages
- [ ] Disconnect network - graceful degradation
- [ ] API errors - user-friendly messages

### Performance
- [ ] Page loads < 3 seconds
- [ ] Filtering/sorting responsive
- [ ] No UI freezing during updates

## 🐛 Common Issues & Solutions

### Issue: "Access Denied" Error
**Solution**: Check authentication token and client account context

### Issue: Components Not Loading
**Solution**: Verify Discovery Flow has run and applications have metadata

### Issue: Real-time Updates Not Working
**Solution**: Check SSE connection in browser Network tab, verify API endpoint

### Issue: 6R Strategies Not Saving
**Solution**: Check browser console for API errors, verify multi-tenant headers

## 🛠️ Developer Tools

### Browser Console Commands
```javascript
// Check current flow state
console.log(window.__assessmentFlowState);

// Verify SSE connection
console.log(window.__sseConnection);

// Check authentication
console.log(localStorage.getItem('authToken'));

// Trigger manual save
window.__assessmentFlow.saveProgress();
```

### API Testing
```bash
# Get flow status
curl -H "X-Client-Account-ID: 1" \
     http://localhost:8000/api/v1/assessment-flow/{flow_id}/status

# Check SSE events
curl -H "X-Client-Account-ID: 1" \
     http://localhost:8000/api/v1/assessment-flow/{flow_id}/events
```

## ✅ Success Criteria

The Assessment Flow is working correctly when:
1. ✅ Can complete entire flow from start to finish
2. ✅ All data persists across page refreshes
3. ✅ Real-time updates appear during agent processing
4. ✅ Can modify and save all assessment data
5. ✅ Applications marked ready for planning
6. ✅ Multi-tenant isolation enforced
7. ✅ Export and print functions work
8. ✅ No console errors or warnings

## 📸 Screenshots

Take screenshots of:
1. Architecture Standards page with template loaded
2. Tech Debt Analysis with components
3. 6R Strategy matrix with treatments
4. App-on-Page comprehensive view
5. Assessment Summary with statistics

These will serve as visual verification that the UI is rendering correctly.