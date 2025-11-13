# QA E2E Testing with Automated GitHub Issue Tagging

## Workflow Pattern
Comprehensive E2E testing + automatic bug documentation + GitHub project metadata tagging.

## Command Usage
```bash
/qa-test-flow [flow-type] [test-objectives]
```

**Flow Types**:
- `collection` - Collection flow only
- `assessment` - Assessment flow only
- `collection-assessment` - Collection → Assessment transition (default)
- `discovery` - Discovery flow
- `plan` - Plan flow
- `full` - Complete end-to-end workflow

## Workflow Phases

### Phase 1: QA Testing
Launch `qa-playwright-tester` agent with:
- Starting URL: http://localhost:8081/login
- Demo credentials: demo@demo-corp.com / Demo123!
- Complete flow walkthrough
- Evidence collection (screenshots, logs, console errors)

### Phase 2: Bug Documentation
Agent creates GitHub issues automatically with:
- Label: `bug` (mandatory)
- Screenshots saved to `.playwright-mcp/`
- Backend logs: `docker logs migration_backend --tail 50`
- Database state queries
- Reproduction steps

### Phase 3: Auto-Tagging
```bash
# Get bugs from last hour
gh issue list --label bug --state open --limit 50 --json number,title,createdAt --jq '
  .[] | select((.createdAt | fromdateiso8601) > (now - 3600))
'

# For each bug, apply project metadata
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
}'
```

## Project Field IDs (AI-Force Assess Roadmap #2)
```
Project ID: PVT_kwHOC9ukJs4A-zrv
Team: PVTSSF_lAHOC9ukJs4A-zrvzgyGaz0 (Dev Team: 9282166a)
Status: PVTSSF_lAHOC9ukJs4A-zrvzgyGaqY (Backlog: 38d5ba08)
Priority: PVTSSF_lAHOC9ukJs4A-zrvzgzVlog (P0: ea888c88, P1: 3e8eecb9)
Iteration: PVTIF_lAHOC9ukJs4A-zrvzgyGaz4
Quarter: PVTIF_lAHOC9ukJs4A-zrvzgyGaz8
```

## Milestone Mapping
```bash
case "$FLOW_TYPE" in
  collection*) MILESTONE="Collection Flow Ready" ;;
  assessment*) MILESTONE="Assessment Flow complete" ;;
  discovery*) MILESTONE="Discovery Flow ready - Phase 2" ;;
  plan*) MILESTONE="Plan Flow complete" ;;
  full*) MILESTONE="Client Demo" ;;
esac
```

## Priority Detection
```bash
SEVERITY=$(gh issue view $ISSUE_NUMBER --json labels --jq '.labels[].name' | grep -i 'critical\|high\|medium\|low')

case "${SEVERITY,,}" in
  *critical*) PRIORITY_ID="ea888c88" ;; # P0
  *high*)     PRIORITY_ID="ea888c88" ;; # P0
  *medium*)   PRIORITY_ID="3e8eecb9" ;; # P1
  *low*)      PRIORITY_ID="f027ec0f" ;; # P2
esac
```

## Example Output
```
QA E2E Testing Complete - Collection Flow
══════════════════════════════════════════

Bugs Discovered: 2
├── Critical (P0): 1 (#789 - Router not registered)
└── High (P1): 1 (#788 - Missing header)

Project Configuration Applied:
├── Project: AI-Force Assess Roadmap (#2)
├── Team: Dev Team
├── Status: Backlog
├── Iteration: Iteration 7
└── Quarter: Quarter 2
```

## When to Use
- Pre-release QA validation
- Feature completion testing
- Post-refactoring verification
- Regression testing after major changes

## Related Commands
```bash
# View all bugs for milestone
gh issue list --label bug --state open --milestone "Collection Flow Ready"

# Automated bug fixing
/fix-bugs execute 789  # Fix specific bug
/fix-bugs dry-run      # Analyze without fixing
```
