# Playwright Testing Patterns - January 2025

## Testing Discovery Flow with MCP Playwright

### Key Testing Steps
1. Navigate to http://localhost:8081
2. Authenticate with demo@demo-corp.com
3. Access existing flow or create new one
4. Progress through phases and verify state

### Database Validation During Tests
```python
# Check phase progression
SELECT flow_id, current_phase, field_mapping_completed
FROM migration.discovery_flows
WHERE flow_id = '<test_flow_id>';

# Verify master flow state
SELECT flow_id, status, current_phase
FROM migration.crewai_flow_state_extensions
WHERE flow_id = '<test_flow_id>';
```

### Common UI Elements to Verify
- Phase transition buttons: "Continue to Data Cleansing"
- Success notifications: "Flow Continued - Discovery flow is now continuing..."
- URL changes: `/discovery/attribute-mapping/` → `/discovery/data-cleansing/`
- Data displays: Quality scores, records processed, recommendations

### Error Patterns to Check
- 500 errors on bulk operations (non-critical)
- Console errors vs warnings
- API endpoint 404s (critical)

### Screenshot Capture Points
- Before phase transition
- After successful navigation
- On error states
- Final validation state
