### Architecture Minimums and 6R Readiness

This document defines the minimum information needed to classify applications for 6R treatment and how to obtain it with the existing Collection flow and validators.

### Architecture minimums (per application)
- Identity: application name, owner/team, business criticality
- Topology: tier count and component list (web/app/db/cache/message), deployment model (VM, container, serverless)
- Dependencies: inbound/outbound services, databases, external integrations
- Platform/runtime: language, framework, runtime version, packaging (jar, war, node, python), OS
- Data: primary database type, size tier, sensitivity/classification
- Non-functionals: availability target, RTO/RPO tier, peak TPS/throughput band
- Constraints: vendor lock-ins, licensing, compliance constraints

Minimum signals for quick 6R triage
- Rehost likely: VM-based, low coupling, no proprietary PaaS features, moderate data sensitivity
- Replatform candidate: containerizable runtime, manageable dependencies, some infra modernization benefits
- Refactor/Rewrite: monolith with high tech debt, outdated runtime, high coupling, performance/scalability needs
- Rearchitect: distributed, requires cloud-native redesign for availability/scale; event-driven targets
- Retire/Retain: usage signals low or strategic decision to hold

### How to obtain data in the current system
- Discovery inventory provides initial assets and relationships.
- Collection ADCS phases fill gaps through questionnaires and automated hints.
- apply_resolved_gaps_to_assets writes back fields to Asset, including assessment_readiness.
- DataFlowValidator computes phase scores and can compute a readiness score threshold.

Proposed validator outputs (extend DataFlowValidator)
- architecture_minimums_present: boolean
- missing_fields: list of critical fields per app
- readiness_score: 0-100
- phase_scores: object with discovery and collection
- blocking_issues: list
 - confidence_scores: number (0–1) and/or per-domain confidences
 - ai_insights: short list of AI-generated observations driving readiness

Thresholds (configurable)
- architecture_minimums_present is true
- readiness_score at least 70

### Assessment initialization contract
- Query assets where assessment_readiness='ready' for the engagement.
- POST /api/v1/assessment-flow/initialize with the list of app ids and optional strategy hints.
- UnifiedAssessmentFlow then loads selected applications with DiscoveryFlowIntegration.get_applications_ready_for_assessment.

### UX guardrails
- Don’t allow navigating to /assessment/{flowId}/tech-debt until assessment flow is initialized and SSE is ready.
- On /assess/overview, show missing minimums per application with links to targeted questionnaires.

### Adaptive questionnaire enablement
- Use detected missing_fields to generate targeted questionnaires
- Gate heavy AI generation behind a feature flag; fall back to static templates if disabled


