# Phase 1 Parallel Agent Tasks

This directory contains individual task files for Claude Code agents to execute Phase 1 of the remediation plan in parallel.

## Quick Start for Claude Code Agents

1. **Choose an agent role** from the available tasks below
2. **Open the corresponding task file** as your primary instruction set
3. **Begin work immediately** - no environment setup needed
4. **Follow the coordination guide** for integration points

## Available Agent Tasks

### Critical Path (Start First)
- [`AGENT_A1_BACKEND_SESSION_MIGRATION.md`](./AGENT_A1_BACKEND_SESSION_MIGRATION.md) - Backend session to flow migration
- [`AGENT_A2_FRONTEND_SESSION_MIGRATION.md`](./AGENT_A2_FRONTEND_SESSION_MIGRATION.md) - Frontend session to flow migration

### High Priority
- [`AGENT_B1_BACKEND_API_CONSOLIDATION.md`](./AGENT_B1_BACKEND_API_CONSOLIDATION.md) - Create unified v3 API
- [`AGENT_B2_FRONTEND_API_CLIENT.md`](./AGENT_B2_FRONTEND_API_CLIENT.md) - TypeScript client for v3 API
- [`AGENT_C1_STATE_MANAGEMENT_CLEANUP.md`](./AGENT_C1_STATE_MANAGEMENT_CLEANUP.md) - PostgreSQL-only state management

### User-Facing Fixes
- [`AGENT_D1_FIELD_MAPPING_FIXES.md`](./AGENT_D1_FIELD_MAPPING_FIXES.md) - Fix field mapping UI issues

### Quality & Documentation
- [`AGENT_E1_TEST_COVERAGE.md`](./AGENT_E1_TEST_COVERAGE.md) - Test coverage and automation
- [`AGENT_E2_DOCUMENTATION.md`](./AGENT_E2_DOCUMENTATION.md) - Documentation and ADRs

### Coordination
- [`PHASE1_COORDINATION_GUIDE.md`](./PHASE1_COORDINATION_GUIDE.md) - How agents work together

## For Human Coordinators

### Assigning Agents

When creating a new Claude Code conversation for each agent:

```
Please execute the Phase 1 remediation task defined in:
docs/planning/phase1-tasks/AGENT_[X]_[TASK].md

Follow the coordination guide at:
docs/planning/phase1-tasks/PHASE1_COORDINATION_GUIDE.md
```

### Monitoring Progress

Agents will:
1. Create feature branches following the naming convention
2. Make commits with proper tags
3. Open PRs when tasks are complete
4. Update their progress in PR descriptions

### Expected Timeline

- **Day 1**: All agents read tasks and begin implementation
- **Day 2-3**: Core implementation work
- **Day 4**: Integration testing
- **Day 5**: Final merge to develop branch

## Task File Structure

Each task file contains:
1. **Context** - Background and required reading
2. **Specific Tasks** - Detailed implementation steps
3. **Success Criteria** - Clear completion requirements
4. **Interfaces** - Integration points with other agents
5. **Implementation Guidelines** - Best practices and patterns
6. **Commands** - Useful commands for the task
7. **Definition of Done** - Checklist for completion

## Important Notes

- Agents can work **completely in parallel** with minimal dependencies
- The `PHASE1_COORDINATION_GUIDE.md` explains integration points
- Critical path agents (A1, A2) should start first
- All agents should follow the coding standards in `CLAUDE.md`
- Test everything in Docker environment, not locally

## Emergency Contact

If agents encounter blocking issues:
1. Add `blocking-phase1` label to PR
2. Document the issue clearly
3. Check if other agents can help
4. Escalate to human coordinator if needed

---

Ready to transform the platform! 🚀