# Multi-Agent QA Testing with Automatic GitHub Project Tagging

## Use Case
Execute comprehensive E2E testing with automatic bug documentation and GitHub project metadata tagging, eliminating manual project management overhead.

## Workflow Pattern

### Phase 1: QA Testing with Playwright Agent
```bash
# Launch qa-playwright-tester with specific flow
/qa-test-flow collection "Complete end-to-end flow testing"
```

**Agent Task**:
- Execute full user journey tests
- Create GitHub issue for EVERY bug found (use `bug` label)
- Include comprehensive evidence:
  - Screenshots (`.playwright-mcp/`)
  - Browser console errors
  - Backend logs: `docker logs migration_backend --tail 50`
  - Database state queries

### Phase 2: Automatic GitHub Project Tagging

**For each bug issue created**:

```bash
# 1. Assign issue
gh issue edit $ISSUE_NUMBER --add-assignee CryptoYogiLLC

# 2. Set milestone based on flow type
gh issue edit $ISSUE_NUMBER --milestone "Collection Flow Ready"

# 3. Add to project
gh project item-add 2 --owner CryptoYogiLLC --url "https://github.com/.../issues/$ISSUE_NUMBER"

# 4. Get project item ID
ITEM_ID=$(gh api graphql -F query='...' | jq -r '.data.user.projectV2.items.nodes[] | select(.content.number == '$ISSUE_NUMBER') | .id')

# 5. Tag all project fields via GraphQL
gh api graphql -f query='
mutation {
  team: updateProjectV2ItemFieldValue(input: {
    projectId: "PVT_kwHOC9ukJs4A-zrv"
    itemId: "'$ITEM_ID'"
    fieldId: "PVTSSF_lAHOC9ukJs4A-zrvzgyGaz0"
    value: { singleSelectOptionId: "9282166a" }
  }) { projectV2Item { id } }

  status: updateProjectV2ItemFieldValue(input: {
    projectId: "PVT_kwHOC9ukJs4A-zrv"
    itemId: "'$ITEM_ID'"
    fieldId: "PVTSSF_lAHOC9ukJs4A-zrvzgyGaqY"
    value: { singleSelectOptionId: "38d5ba08" }
  }) { projectV2Item { id } }

  priority: updateProjectV2ItemFieldValue(input: {
    projectId: "PVT_kwHOC9ukJs4A-zrv"
    itemId: "'$ITEM_ID'"
    fieldId: "PVTSSF_lAHOC9ukJs4A-zrvzgzVlog"
    value: { singleSelectOptionId: "ea888c88" }
  }) { projectV2Item { id } }

  iteration: updateProjectV2ItemFieldValue(input: {
    projectId: "PVT_kwHOC9ukJs4A-zrv"
    itemId: "'$ITEM_ID'"
    fieldId: "PVTIF_lAHOC9ukJs4A-zrvzgyGaz4"
    value: { iterationId: "2cb0fdf4" }
  }) { projectV2Item { id } }

  quarter: updateProjectV2ItemFieldValue(input: {
    projectId: "PVT_kwHOC9ukJs4A-zrv"
    itemId: "'$ITEM_ID'"
    fieldId: "PVTIF_lAHOC9ukJs4A-zrvzgyGaz8"
    value: { iterationId: "b64ce631" }
  }) { projectV2Item { id } }
}'
```

**Field ID Extraction**:
```bash
# Get all field IDs once
gh api graphql -F query='
query {
  user(login: "CryptoYogiLLC") {
    projectV2(number: 2) {
      id
      fields(first: 30) {
        nodes {
          ... on ProjectV2SingleSelectField {
            id
            name
            options { id name }
          }
          ... on ProjectV2IterationField {
            id
            name
            configuration {
              iterations { id title startDate }
            }
          }
        }
      }
    }
  }
}' | jq
```

## Priority Mapping

**Based on severity labels**:
- `critical` → P0 (ea888c88)
- `high` → P0 (ea888c88)
- `medium` → P1 (3e8eecb9)
- `low` → P2 (f027ec0f)

## Milestone Mapping by Flow Type

```bash
case "$FLOW_TYPE" in
  collection*)
    MILESTONE="Collection Flow Ready"
    ;;
  assessment*)
    MILESTONE="Assessment Flow complete"
    ;;
  discovery*)
    MILESTONE="Discovery Flow ready - Phase 2"
    ;;
  plan*)
    MILESTONE="Plan Flow complete"
    ;;
  full*)
    MILESTONE="Client Demo"
    ;;
esac
```

## Complete Example Session

```bash
# Execute QA test
/qa-test-flow collection

# Agent creates issues #677, #678, #679

# Automatic tagging applied:
# - Team: Dev Team
# - Status: Backlog
# - Priority: P0 (Critical bugs)
# - Iteration: Current iteration (Iteration 7)
# - Quarter: Current quarter (Quarter 2)
# - Milestone: Collection Flow Ready

# Result: Zero manual project management needed
```

## Benefits

1. **Zero Manual Overhead**: Complete automation from testing to project tagging
2. **Consistent Metadata**: All bugs tagged identically with current iteration/quarter
3. **Comprehensive Evidence**: Every bug has screenshots, logs, and repro steps
4. **Immediate Visibility**: Bugs appear in project board instantly with full context

## Usage Notes

- Requires GitHub CLI (`gh`) configured with proper permissions
- Project number, field IDs, and option IDs are project-specific
- Run field ID extraction once per project to get current values
- Works with GitHub Projects v2 (GraphQL API)
