# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records for the AI Force Migration Platform. ADRs document important architectural decisions made during the project lifecycle.

## Index of ADRs

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](001-session-to-flow-migration.md) | Migrate from Session ID to Flow ID as Primary Identifier | Accepted | 2024-01-20 |
| [ADR-002](002-api-consolidation-strategy.md) | Consolidate APIs into Unified v3 Interface | Accepted | 2024-01-20 |
| [ADR-003](003-postgresql-only-state-management.md) | PostgreSQL-Only State Management for CrewAI Flows | Accepted | 2024-01-20 |
| [ADR-004](004-field-mapping-stabilization.md) | Field Mapping UI/UX Stabilization Strategy | Accepted | 2024-01-20 |
| [ADR-005](005-database-consolidation-architecture.md) | Database Consolidation Architecture | Accepted | 2025-06-27 |

## ADR Template

When creating new ADRs, use the following template:

```markdown
# ADR-XXX: [Title]

## Status
[Proposed | Accepted | Rejected | Deprecated | Superseded]

## Context
What is the issue that we're seeing that is motivating this decision or change?

## Decision
What is the change that we're proposing or have agreed to implement?

## Consequences
### Positive
What becomes easier or better as a result of this decision?

### Negative
What becomes more difficult or worse as a result of this decision?

### Risks
What are the risks and how will we mitigate them?

## Implementation
What needs to be done to implement this decision?

## Alternatives Considered
What other options were considered and why were they rejected?
```

## Reading Order

For new team members, we recommend reading ADRs in this order:
1. ADR-001 - Understand the identifier migration
2. ADR-003 - Understand state management architecture
3. ADR-005 - Understand database consolidation architecture
4. ADR-002 - Understand API consolidation
5. ADR-004 - Understand UI stabilization approach