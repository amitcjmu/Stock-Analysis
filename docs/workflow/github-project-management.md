# GitHub Project Management Guide

## Overview

The AI Modernize Migration Platform uses GitHub Projects for comprehensive task tracking, issue management, and team coordination. This guide explains how to effectively use our project boards for development activities.

## GitHub Projects Board

**Main Board**: [https://github.com/users/CryptoYogiLLC/projects/2/views/3](https://github.com/users/CryptoYogiLLC/projects/2/views/3)

### Available Views

1. **Board View** (Default): Kanban-style task board
2. **Table View**: Detailed list with all metadata
3. **Timeline View**: Gantt chart for planning
4. **Roadmap View**: High-level milestone tracking

## Task Management Workflow

### 1. Creating Issues and Tasks

All development activities must be tracked as either:
- **Issues**: Bugs, feature requests, or problems
- **Sub-issues**: Tasks that are part of a larger issue or epic

#### Issue Creation Template
```markdown
## Description
Brief description of the task/issue

## Acceptance Criteria
- [ ] Criteria 1
- [ ] Criteria 2
- [ ] Criteria 3

## Technical Notes
- Implementation approach
- Dependencies
- Potential risks

## Labels
- bug/enhancement/feature
- priority: high/medium/low
- area: frontend/backend/db/docs
```

### 2. Issue Classification

#### Labels
- **Type**: `bug`, `enhancement`, `feature`, `documentation`, `technical-debt`
- **Priority**: `priority:high`, `priority:medium`, `priority:low`
- **Area**: `frontend`, `backend`, `database`, `devops`, `ai-agents`
- **Size**: `size:S`, `size:M`, `size:L`, `size:XL`
- **Status**: `status:blocked`, `status:in-review`, `status:ready`

#### Size Estimation
- **S (Small)**: 1-4 hours
- **M (Medium)**: 4-8 hours (half day)
- **L (Large)**: 1-2 days
- **XL (Extra Large)**: 2+ days (needs breakdown)

### 3. Board Columns

#### Column Definitions
1. **Backlog**: New issues awaiting triage
2. **Ready**: Triaged and ready for development
3. **In Progress**: Currently being worked on
4. **In Review**: Code complete, awaiting review
5. **Testing**: Being tested/validated
6. **Done**: Completed and deployed

#### Column Limits
- **In Progress**: Max 3 items per developer
- **In Review**: Max 5 items total
- **Testing**: Max 8 items total

### 4. Assignment and Ownership

#### Assignment Rules
- Assign yourself when moving to "In Progress"
- Only assign to others with their consent
- Unassign when moving back to "Ready"

#### Team Assignments
- **@frontend-team**: UI/UX related tasks
- **@backend-team**: API and business logic
- **@ai-team**: CrewAI agents and learning systems
- **@devops-team**: Infrastructure and deployment

### 5. Sub-issue Management

#### Creating Sub-issues
1. Create main issue for the feature/epic
2. Break down into smaller sub-issues
3. Link sub-issues to parent using "Part of #XXX"
4. Track completion percentage on parent issue

#### Sub-issue Example
```markdown
## Parent Issue: Implement Redis Caching (#123)

### Sub-issues:
- [ ] Setup Redis configuration (#124)
- [ ] Implement cache middleware (#125)
- [ ] Add cache invalidation (#126)
- [ ] Update documentation (#127)
- [ ] Add monitoring (#128)
```

## Development Workflow Integration

### 1. Branch Naming
```bash
# Format: type/issue-number-short-description
git checkout -b feature/123-redis-caching
git checkout -b fix/456-auth-bug
git checkout -b docs/789-api-documentation
```

### 2. Commit Messages
```bash
# Reference issue numbers in commits
git commit -m "feat: implement Redis caching middleware (#123)

- Add RedisCache service with TTL support
- Integrate with existing API endpoints
- Include error handling and fallback logic

Closes #123"
```

### 3. Pull Request Integration
```markdown
## Pull Request Template

### Description
Brief description of changes

### Related Issues
- Closes #123
- Part of #456
- Related to #789

### Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

### Checklist
- [ ] Code follows project standards
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

## Project Views and Filters

### 1. Developer View
Filter by:
- Assignee: `@your-username`
- Status: `In Progress`, `In Review`
- Labels: Your area of expertise

### 2. Sprint Planning View
Filter by:
- Milestone: Current sprint
- Priority: High and Medium
- Status: Ready, In Progress

### 3. Bug Triage View
Filter by:
- Type: Bug
- Priority: All
- Status: Backlog, Ready

### 4. Technical Debt View
Filter by:
- Labels: `technical-debt`
- Sort by: Priority, Age

## Automation and Integrations

### 1. Automated Workflows
- **Issue Creation**: Auto-label based on repository
- **PR Links**: Auto-link PRs to issues
- **Status Updates**: Auto-move issues when PR merged
- **Notifications**: Slack integration for team updates

### 2. GitHub Actions Integration
```yaml
# .github/workflows/project-automation.yml
name: Project Board Automation

on:
  issues:
    types: [opened, closed]
  pull_request:
    types: [opened, merged, closed]

jobs:
  update-project:
    runs-on: ubuntu-latest
    steps:
      - name: Move issue to In Progress
        uses: alex-page/github-project-automation-plus@v0.8.1
        with:
          project: 2
          column: In Progress
          repo-token: ${{ secrets.GITHUB_TOKEN }}
```

## Reporting and Analytics

### 1. Sprint Reports
- **Velocity**: Issues completed per sprint
- **Burn-down**: Progress over time
- **Cycle Time**: Time from start to completion

### 2. Team Metrics
- **Throughput**: Issues per developer per week
- **Work Distribution**: Balance across team members
- **Blocking Issues**: Items stuck in review/testing

### 3. Quality Metrics
- **Bug Rate**: New bugs vs features delivered
- **Rework Rate**: Issues returning to development
- **Review Time**: Time spent in code review

## Best Practices

### 1. Daily Operations
- **Morning**: Check assigned issues and board updates
- **During Work**: Update issue status as you progress
- **EOD**: Move completed work to appropriate columns

### 2. Issue Management
- **Be Specific**: Clear, actionable descriptions
- **Size Appropriately**: Break down large tasks
- **Link Dependencies**: Use "depends on" and "blocks" relationships
- **Update Regularly**: Keep status and comments current

### 3. Communication
- **Use Comments**: Document decisions and progress
- **Tag Stakeholders**: Notify relevant team members
- **Link Related Work**: Connect issues, PRs, and discussions

### 4. Planning
- **Regular Grooming**: Weekly backlog refinement
- **Estimation**: Size all issues before sprint planning
- **Capacity Planning**: Don't overcommit team bandwidth

## Troubleshooting

### Common Issues

#### Issue Not Moving Between Columns
- Check if automation is enabled
- Verify PR is properly linked to issue
- Ensure proper labels are applied

#### Missing Issues in Board
- Check if issue is in correct repository
- Verify project filters are not hiding the issue
- Check if issue is archived

#### Automation Not Working
- Verify GitHub Actions are enabled
- Check repository permissions
- Review workflow configuration

### Getting Help

1. **Documentation**: Check GitHub Projects help docs
2. **Team Lead**: Contact your team lead for workflow questions
3. **DevOps Team**: For automation and integration issues
4. **Admin Support**: For permissions and access issues

## Quick Reference

### Keyboard Shortcuts
- `c`: Create new issue
- `t`: Filter by label
- `u`: Filter by user
- `/`: Open command palette
- `?`: Show all shortcuts

### Useful Links
- [Main Project Board](https://github.com/users/CryptoYogiLLC/projects/2/views/3)
- [Repository Issues](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/issues)
- [Team Discussions](https://github.com/CryptoYogiLLC/migrate-ui-orchestrator/discussions)
- [Project Settings](https://github.com/users/CryptoYogiLLC/projects/2/settings)

---

**Remember**: Consistent use of the project board is essential for team coordination and project visibility. When in doubt, create an issue and track your work!

*Last Updated: 2025-01-18*