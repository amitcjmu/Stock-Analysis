# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records for the AI Modernize Migration Platform. ADRs document important architectural decisions made during the project lifecycle.

## Index of ADRs

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](001-session-to-flow-migration.md) | Migrate from Session ID to Flow ID as Primary Identifier | Superseded | 2024-01-20 |
| [ADR-002](002-api-consolidation-strategy.md) | Consolidate APIs into Unified v3 Interface | Accepted | 2024-01-20 |
| [ADR-003](003-postgresql-only-state-management.md) | PostgreSQL-Only State Management for CrewAI Flows | Accepted | 2024-01-20 |
| [ADR-004](004-field-mapping-stabilization.md) | Field Mapping UI/UX Stabilization Strategy | Accepted | 2024-01-20 |
| [ADR-005](005-database-consolidation-architecture.md) | Database Consolidation Architecture | Accepted | 2025-06-27 |
| [ADR-006](006-master-flow-orchestrator.md) | Master Flow Orchestrator | Accepted | 2025 |
| [ADR-007](007-comprehensive-modularization-architecture.md) | Comprehensive Modularization Architecture | Accepted | 2025-07-11 |
| [ADR-008](008-agentic-intelligence-system-architecture.md) | Agentic Intelligence System Architecture | Accepted | 2025-07-12 |
| [ADR-009](009-multi-tenant-architecture.md) | Multi-Tenant Architecture | Accepted | 2024-2025 |
| [ADR-010](010-docker-first-development-mandate.md) | Docker-First Development Mandate | Accepted | 2024-2025 |
| [ADR-011](011-flow-based-architecture-evolution.md) | Flow-Based Architecture Evolution | Accepted | 2025 |
| [ADR-012](012-flow-status-management-separation.md) | Flow Status Management Separation | Accepted | 2025 |
| [ADR-013](013-adaptive-data-collection-integration.md) | Adaptive Data Collection System Integration | Accepted | 2025-07-19 |
| [ADR-014](014-on-premises-deployment-model.md) | On-Premises Deployment Model for Regulated Environments | Proposed | 2025-07-19 |
| [ADR-015](015-persistent-multi-tenant-agent-architecture.md) | Persistent Multi-Tenant Agent Architecture | Proposed | 2025-08-07 |
| [ADR-016](016-collection-flow-intelligent-data-enrichment.md) | Collection Flow for Intelligent Data Enrichment | Accepted | 2025-08-08 |
| [ADR-017](017-redis-backed-failure-journal-and-dlq.md) | Redis-Backed Failure Journal and DLQ | Accepted | 2025 |
| [ADR-018](018-service-registry-for-crewai-tools.md) | Service Registry for CrewAI Tools | Proposed | 2025-01-13 |
| [ADR-019](019-crewai-deepinfra-embeddings-monkey-patch.md) | CrewAI DeepInfra Embeddings Monkey Patch | Accepted | 2025 |
| [ADR-020](020-flow-type-aware-phase-transitions.md) | Flow-Type Aware Phase Transition Architecture | Proposed | 2025-08-22 |
| [ADR-021](021-flow-endpoint-plural-convention.md) | Flow Endpoint Plural Convention Consolidation | Accepted | 2025-08-29 |

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

### Foundation Architecture (Start Here)
1. **ADR-009** - Multi-Tenant Architecture - Core tenant isolation and security model
2. **ADR-010** - Docker-First Development Mandate - Development environment setup
3. **ADR-003** - PostgreSQL-Only State Management - Database architecture foundation

### Platform Evolution
4. **ADR-007** - Comprehensive Modularization Architecture - Codebase organization principles
5. **ADR-011** - Flow-Based Architecture Evolution - Core flow patterns (supersedes ADR-001)
6. **ADR-006** - Master Flow Orchestrator - Central orchestration system
7. **ADR-021** - Flow Endpoint Plural Convention Consolidation - Standardized endpoint patterns
8. **ADR-008** - Agentic Intelligence System - AI/ML integration patterns
9. **ADR-015** - Persistent Multi-Tenant Agent Architecture - Agent persistence and memory systems
10. **ADR-018** - Service Registry for CrewAI Tools - Service layer architecture for agent tools
11. **ADR-020** - Flow-Type Aware Phase Transition Architecture - Dynamic phase management across flow types
12. **ADR-013** - Adaptive Data Collection System Integration - Automated data collection capabilities
13. **ADR-016** - Collection Flow for Intelligent Data Enrichment - Bridge between Discovery and Assessment flows
14. **ADR-017** - Redis-Backed Failure Journal and DLQ - Failure recovery and dead letter queue
15. **ADR-014** - On-Premises Deployment Model - Regulated environment support (pending approval)

### Legacy Context
16. **ADR-005** - Database Consolidation Architecture - Historical database decisions
17. **ADR-002** - API Consolidation Strategy - API versioning and migration
18. **ADR-004** - Field Mapping UI/UX Stabilization - UI stabilization patterns
19. **ADR-001** - Session to Flow Migration - Original identifier migration (superseded by ADR-011)