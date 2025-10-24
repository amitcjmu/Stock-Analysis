# GitHub Issue Parent-Child Relationships and Project Setup

## Overview
This document describes how to properly create parent-child relationships between GitHub issues (sub-issues), assign issues to projects, and apply appropriate labels and metadata.

## Parent-Child Issue Relationships (Sub-Issues)

### What Are Sub-Issues?
GitHub's sub-issues feature allows you to create hierarchical relationships between issues, where one issue (parent) contains multiple child issues (sub-issues). This is different from simply mentioning issues in the body text.

### Key Differences: References vs. Sub-Issues

**❌ INCORRECT - Just Mentioning in Body:**
```markdown
## Sub-Issues
- #769 Task 1
- #770 Task 2
- #771 Task 3
```
This only creates text references. GitHub does NOT track these as proper relationships.

**✅ CORRECT - Actual Sub-Issue Relationship:**
Uses GitHub's REST API to create formal parent-child links that GitHub tracks and displays.

### How to Create Sub-Issue Relationships

#### Prerequisites
1. Both parent and child issues must already exist
2. You need the **numeric issue ID** (not the issue number)
3. All issues must be in the same repository

#### Step 1: Get Issue IDs
```bash
# Get numeric ID for an issue (NOT the issue number)
gh api repos/{owner}/{repo}/issues/{issue_number} --jq '.id'

# Example for multiple issues
for i in {769..787}; do
  id=$(gh api "repos/CryptoYogiLLC/migrate-ui-orchestrator/issues/$i" --jq '.id')
  echo "$i: $id"
done
```

**Important:** The issue ID is a large number like `3547494093`, NOT the issue number like `769`.

#### Step 2: Add Sub-Issues to Parent
```bash
# Add a single sub-issue
gh api repos/{owner}/{repo}/issues/{parent_number}/sub_issues \
  --method POST \
  --header 'Accept: application/vnd.github+json' \
  --header 'X-GitHub-Api-Version: 2022-11-28' \
  --input - <<< '{"sub_issue_id": 3547494093}'

# Add multiple sub-issues (example script)
for issue_num in {769..787}; do
  issue_id=$(gh api "repos/{owner}/{repo}/issues/$issue_num" --jq '.id')

  gh api repos/{owner}/{repo}/issues/768/sub_issues \
    --method POST \
    --header 'Accept: application/vnd.github+json' \
    --header 'X-GitHub-Api-Version: 2022-11-28' \
    --input - <<< "{\"sub_issue_id\": $issue_id}"

  sleep 1  # Rate limiting protection
done
```

**Critical Notes:**
- The `sub_issue_id` must be an **integer** in JSON, not a string
- Use `<<<` for heredoc input with proper JSON formatting
- Add sleep between requests to avoid rate limiting

#### Step 3: Verify Parent-Child Relationships
```bash
# Check parent issue has sub-issues
gh api repos/{owner}/{repo}/issues/{parent_number} \
  --jq '.sub_issues_summary'

# Expected output:
# {"total": 19, "completed": 0, "percent_completed": 0}

# Verify child issue shows parent
gh api repos/{owner}/{repo}/issues/{child_number}/parent \
  --jq '{parent_issue: .number, parent_title: .title}'

# Expected output:
# {"parent_issue": 768, "parent_title": "Parent Issue Title"}
```

## Milestone Assignment

### List Available Milestones
```bash
gh api repos/{owner}/{repo}/milestones \
  --jq '.[] | {number: .number, title: .title}'
```

### Assign Issue to Milestone
```bash
# Single issue
gh issue edit {issue_number} --milestone "Milestone Title"

# Multiple issues
for i in {769..787}; do
  gh issue edit $i --milestone "Collection Flow Adaptive Questionnaire"
done
```

### Verify Milestone Assignment
```bash
gh issue view {issue_number} --json milestone \
  --jq '.milestone.title'
```

## Project Assignment

### List Available Projects
```bash
# List all projects for owner
gh project list --owner {owner} --format json

# Example output includes project number (e.g., 2 for "AI Force Assess Roadmap")
```

### Add Issues to Project

**Method 1: Using `gh issue edit` (Simple)**
```bash
gh issue edit {issue_number} --add-project "Project Name"

# Example:
gh issue edit 769 --add-project "AI Force Assess Roadmap"
```

**Method 2: Using `gh project item-add` (More Reliable)**
```bash
# Format: gh project item-add {project_number} --owner {owner} --url {issue_url}

gh project item-add 2 \
  --owner CryptoYogiLLC \
  --url https://github.com/{owner}/{repo}/issues/{issue_number}

# Bulk add script
for i in {769..787}; do
  gh project item-add 2 \
    --owner CryptoYogiLLC \
    --url "https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/$i"
  sleep 0.3
done
```

### Verify Project Assignment
```bash
gh issue view {issue_number} --json projectItems \
  --jq '.projectItems[] | {project: .project.title, status: .status.name}'
```

**Note:** GitHub Projects V2 API can have delays. If `projectItems` shows null immediately after adding, check the project board directly in the web UI.

## Label Management

### List Available Labels
```bash
gh label list --json name,description \
  --jq '.[] | "\(.name) - \(.description)"'
```

### Add Labels to Issues

**Single Issue:**
```bash
gh issue edit {issue_number} --add-label "label1,label2,label3"
```

**Bulk Label Assignment by Issue Type:**
```bash
# Database issues
for i in 769 770; do
  gh issue edit $i --add-label "database,priority-critical,backend"
done

# Backend issues
for i in 771 772 773 774 775 776 777 786; do
  gh issue edit $i --add-label "backend,priority-critical"
done

# Frontend issues
for i in 778 779 780 781 782; do
  gh issue edit $i --add-label "frontend,priority-critical"
done

# Testing issues
for i in 783 784 785; do
  gh issue edit $i --add-label "testing,priority-critical"
done

# Add API label to specific backend issues
for i in 773 774; do
  gh issue edit $i --add-label "api"
done

# Add E2E label to E2E testing issue
gh issue edit 785 --add-label "e2e"
```

### Verify Labels
```bash
gh issue view {issue_number} --json labels \
  --jq '[.labels[].name] | join(", ")'
```

## Common Label Categories for This Project

### By Work Type
- `backend` - Backend implementation work
- `frontend` - Frontend/UI implementation work
- `database` - Database schema and migrations
- `api` - API endpoints and routes
- `testing` - Testing and QA work
- `e2e` - End-to-end testing

### By Priority
- `priority-critical` - Must complete immediately
- `priority-high` - Important but not blocking
- `priority-medium` - Standard priority
- `priority-low` - Nice to have

### By Flow/Feature Area
- `plan-flow` - Issues related to Plan Flow milestone
- `discovery-flow` - Discovery Flow features
- `assessment-flow` - Assessment Flow features
- `collection-flow` - Collection Flow features

## Complete Workflow Example

### Creating a Milestone with Sub-Issues

**Step 1: Create Parent Issue**
```bash
# Create via web UI or CLI
gh issue create \
  --title "Feature X - Milestone Definition" \
  --body "Epic overview with design doc reference..." \
  --milestone "Collection Flow Adaptive Questionnaire" \
  --label "Milestone Definition,priority-critical" \
  --assignee "@me"
```

**Step 2: Create Child Issues**
```bash
# Create 5 child issues for the milestone
gh issue create --title "[DB] Database Migration" --label "database,priority-critical"
gh issue create --title "[Backend] Service Implementation" --label "backend,priority-critical"
gh issue create --title "[Frontend] UI Component" --label "frontend,priority-critical"
gh issue create --title "[Testing] E2E Tests" --label "testing,e2e,priority-critical"
gh issue create --title "[Deploy] Staging Deployment" --label "backend,priority-critical"

# Note the issue numbers returned (e.g., #801-#805)
```

**Step 3: Link Child Issues to Parent**
```bash
# Get IDs for all child issues
for i in {801..805}; do
  id=$(gh api "repos/CryptoYogiLLC/migrate-ui-orchestrator/issues/$i" --jq '.id')
  echo "$i: $id"
done

# Add as sub-issues to parent (e.g., #800)
for i in {801..805}; do
  issue_id=$(gh api "repos/CryptoYogiLLC/migrate-ui-orchestrator/issues/$i" --jq '.id')

  gh api repos/CryptoYogiLLC/migrate-ui-orchestrator/issues/800/sub_issues \
    --method POST \
    --header 'Accept: application/vnd.github+json' \
    --header 'X-GitHub-Api-Version: 2022-11-28' \
    --input - <<< "{\"sub_issue_id\": $issue_id}"

  sleep 1
done
```

**Step 4: Assign All to Milestone**
```bash
for i in {801..805}; do
  gh issue edit $i --milestone "Collection Flow Adaptive Questionnaire"
done
```

**Step 5: Add All to Project**
```bash
for i in {800..805}; do
  gh project item-add 2 \
    --owner CryptoYogiLLC \
    --url "https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/$i"
  sleep 0.3
done
```

**Step 6: Verify Complete Setup**
```bash
# Check parent has all sub-issues
gh api repos/CryptoYogiLLC/migrate-ui-orchestrator/issues/800 \
  --jq '.sub_issues_summary'

# Verify one child shows parent
gh api repos/CryptoYogiLLC/migrate-ui-orchestrator/issues/801/parent \
  --jq '.number'

# Check milestone assignment
gh issue view 801 --json milestone --jq '.milestone.title'

# Check labels
gh issue view 801 --json labels --jq '[.labels[].name]'
```

## Troubleshooting

### Issue: "Invalid property /sub_issue_id: is not of type integer"
**Cause:** Using `-f` flag which creates string values
**Solution:** Use `--input -` with heredoc and proper JSON formatting:
```bash
# ❌ WRONG
gh api ... -f sub_issue_id=3547494093

# ✅ CORRECT
gh api ... --input - <<< '{"sub_issue_id": 3547494093}'
```

### Issue: Project assignment doesn't show in `gh issue view`
**Cause:** GitHub Projects V2 API has propagation delays
**Solution:**
1. Check the project board directly in web UI
2. Use `gh project item-list {project_number}` to verify
3. Wait a few minutes and re-check

### Issue: Rate limiting errors
**Cause:** Too many rapid API calls
**Solution:** Add `sleep` between requests:
```bash
for i in {769..787}; do
  # ... API call ...
  sleep 1  # Add delay
done
```

## Reference: GitHub Sub-Issues API Documentation

**Endpoint:** `POST /repos/{owner}/{repo}/issues/{issue_number}/sub_issues`

**Request Body:**
```json
{
  "sub_issue_id": 3547494093,
  "replace_parent": false  // Optional: replace existing parent
}
```

**Response (201 Created):**
```json
{
  "message": "Created",
  "sub_issues_summary": {
    "total": 19,
    "completed": 0,
    "percent_completed": 0
  }
}
```

**Get Parent Issue:**
```bash
GET /repos/{owner}/{repo}/issues/{issue_number}/parent
```

## Best Practices

1. **Always use sub-issue API** instead of just text references in body
2. **Verify parent-child relationships** after creation
3. **Assign milestones** to both parent and child issues
4. **Use consistent labeling** based on issue type (backend, frontend, etc.)
5. **Add to project board** for tracking in "AI Force Assess Roadmap"
6. **Include priority labels** (`priority-critical`, etc.)
7. **Add sleep delays** in bulk operations to avoid rate limiting
8. **Use numeric issue IDs** (from API), not issue numbers, for sub-issues
9. **Verify in web UI** if CLI doesn't immediately reflect changes

## Repository-Specific Settings

### For migrate-ui-orchestrator Repository:
- **Owner:** CryptoYogiLLC
- **Repo:** migrate-ui-orchestrator
- **Primary Project:** "AI Force Assess Roadmap" (Project #2)
- **Common Milestones:**
  - "Collection Flow Ready"
  - "Collection Flow Adaptive Questionnaire"
  - "Discovery Flow ready _Phase 1"
  - "Plan Flow Complete - Technical Breakdown"

### Standard Label Set:
- Work Type: `backend`, `frontend`, `database`, `api`, `testing`, `e2e`
- Priority: `priority-critical`, `priority-high`, `priority-medium`, `priority-low`
- Flow: `plan-flow`, `discovery-flow`, `assessment-flow`, `collection-flow`
- Special: `Milestone Definition`, `bug`, `enhancement`

## Example Real-World Usage

**Context:** Issue #768 "Collection Flow Adaptive Questionnaire Enhancements"
- **Parent Issue:** #768
- **Child Issues:** #769-#787 (19 sub-issues)
- **Milestone:** "Collection Flow Adaptive Questionnaire"
- **Project:** "AI Force Assess Roadmap"

**Commands Used:**
```bash
# 1. Get all child issue IDs
for i in {769..787}; do
  id=$(gh api "repos/CryptoYogiLLC/migrate-ui-orchestrator/issues/$i" --jq '.id')
  echo "$i: $id"
done

# 2. Link all as sub-issues
for i in {769..787}; do
  issue_id=$(gh api "repos/CryptoYogiLLC/migrate-ui-orchestrator/issues/$i" --jq '.id')
  gh api repos/CryptoYogiLLC/migrate-ui-orchestrator/issues/768/sub_issues \
    --method POST \
    --header 'Accept: application/vnd.github+json' \
    --header 'X-GitHub-Api-Version: 2022-11-28' \
    --input - <<< "{\"sub_issue_id\": $issue_id}"
  sleep 1
done

# 3. Assign to milestone
for i in {769..787}; do
  gh issue edit $i --milestone "Collection Flow Adaptive Questionnaire"
done

# 4. Add labels by type
for i in 769 770; do
  gh issue edit $i --add-label "database,priority-critical,backend"
done

for i in 771 772 773 774 775 776 777 786; do
  gh issue edit $i --add-label "backend,priority-critical"
done

for i in 778 779 780 781 782; do
  gh issue edit $i --add-label "frontend,priority-critical"
done

# 5. Add to project
for i in {769..787}; do
  gh project item-add 2 --owner CryptoYogiLLC \
    --url "https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues/$i"
  sleep 0.3
done

# 6. Verify
gh api repos/CryptoYogiLLC/migrate-ui-orchestrator/issues/768 \
  --jq '.sub_issues_summary'
# Output: {"total": 19, "completed": 0, "percent_completed": 0}
```

**Result:** 19 properly linked sub-issues with correct milestone, labels, and project assignment.
