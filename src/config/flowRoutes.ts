/**
 * Centralized flow routing configuration for all flow types
 * Mirrors the backend RouteDecisionTool mapping for consistency
 * Supports discovery, assessment, planning, execution, and future flows
 */

export type FlowType =
  | "discovery"
  | "collection"
  | "assessment"
  | "plan"
  | "execute"
  | "modernize"
  | "finops"
  | "observability"
  | "decommission";

/**
 * Route mapping for all flow types - matches backend RouteDecisionTool.ROUTE_MAPPING
 * Each flow type has its phases mapped to frontend routes
 */
export const FLOW_PHASE_ROUTES: Record<
  FlowType,
  Record<string, (flowId: string) => string>
> = {
  discovery: {
    // Initialization phases go to monitoring view
    initialization: (flowId: string) =>
      flowId ? `/discovery/monitor/${flowId}` : "/discovery/cmdb-import",
    data_import_validation: () => "/discovery/cmdb-import",
    data_import: () => "/discovery/cmdb-import",

    // Field mapping phases
    field_mapping: (flowId: string) =>
      flowId
        ? `/discovery/attribute-mapping/${flowId}`
        : "/discovery/cmdb-import",
    attribute_mapping: (flowId: string) =>
      flowId
        ? `/discovery/attribute-mapping/${flowId}`
        : "/discovery/cmdb-import",

    // Data cleansing phase
    data_cleansing: (flowId: string) =>
      flowId ? `/discovery/data-cleansing/${flowId}` : "/discovery/cmdb-import",

    // Asset inventory phases
    asset_inventory: (flowId: string) =>
      flowId ? `/discovery/inventory/${flowId}` : "/discovery/cmdb-import",
    inventory: (flowId: string) =>
      flowId ? `/discovery/inventory/${flowId}` : "/discovery/cmdb-import",

    // Dependency analysis phases
    dependency_analysis: (flowId: string) =>
      flowId ? `/discovery/dependencies/${flowId}` : "/discovery/cmdb-import",
    dependencies: (flowId: string) =>
      flowId ? `/discovery/dependencies/${flowId}` : "/discovery/cmdb-import",

    // Completed flow - moved tech debt to assessment
    completed: (flowId: string) =>
      flowId ? `/discovery/inventory/${flowId}` : "/discovery/cmdb-import",

    // Status-based routing
    waiting_for_user_approval: (flowId: string) =>
      flowId
        ? `/discovery/attribute-mapping/${flowId}`
        : "/discovery/cmdb-import",
    paused: (flowId: string) =>
      flowId
        ? `/discovery/attribute-mapping/${flowId}`
        : "/discovery/cmdb-import",
    pending_approval: (flowId: string) =>
      flowId
        ? `/discovery/attribute-mapping/${flowId}`
        : "/discovery/cmdb-import",

    // Error states - route to monitoring for error details
    failed: (flowId: string) =>
      flowId ? `/discovery/monitor/${flowId}` : "/discovery/cmdb-import",
    error: (flowId: string) =>
      flowId ? `/discovery/monitor/${flowId}` : "/discovery/cmdb-import",
    not_found: (flowId: string) =>
      flowId ? `/discovery/monitor/${flowId}` : "/discovery/cmdb-import",

    // Unknown/undefined states - route to monitoring
    unknown: (flowId: string) =>
      flowId ? `/discovery/monitor/${flowId}` : "/discovery/cmdb-import",
    undefined: (flowId: string) =>
      flowId ? `/discovery/monitor/${flowId}` : "/discovery/cmdb-import",
    current: (flowId: string) =>
      flowId ? `/discovery/monitor/${flowId}` : "/discovery/cmdb-import",
  },

  collection: {
    // Asset selection phase - FIRST STEP: select applications before gap analysis
    // NOTE: Replaces deprecated platform_detection and automated_collection phases
    asset_selection: (flowId: string) =>
      flowId
        ? `/collection/select-applications?flowId=${flowId}`
        : "/collection",

    // Gap analysis phase - AI-powered two-phase gap discovery
    gap_analysis: (flowId: string) =>
      flowId ? `/collection/gap-analysis/${flowId}` : "/collection",

    // Questionnaire generation phase - AI generates targeted questions
    questionnaire_generation: (flowId: string) =>
      flowId ? `/collection/questionnaire-generation/${flowId}` : "/collection",

    // Manual collection phase - Users interact with questionnaires (adaptive forms)
    // FIX BUG#801: Route to existing adaptive-forms page, not non-existent manual-collection page
    manual_collection: (flowId: string) =>
      flowId ? `/collection/adaptive-forms?flowId=${flowId}` : "/collection",

    // Synthesis phase - Final data compilation and validation
    synthesis: (flowId: string) =>
      flowId ? `/collection/synthesis/${flowId}` : "/collection",

    // Finalization phase - Maps to synthesis (backend child flow uses this)
    finalization: (flowId: string) =>
      flowId ? `/collection/synthesis/${flowId}` : "/collection",

    // Completed flow
    completed: (flowId: string) =>
      flowId ? `/collection/summary/${flowId}` : "/collection",

    // Error states
    failed: () => "/collection",
    error: () => "/collection",
    unknown: () => "/collection",
  },

  assessment: {
    migration_readiness: (flowId: string) =>
      flowId ? `/assess/migration-readiness/${flowId}` : "/assess",
    business_impact: (flowId: string) =>
      flowId ? `/assess/business-impact/${flowId}` : "/assess",
    technical_assessment: (flowId: string) =>
      flowId ? `/assess/technical-assessment/${flowId}` : "/assess",
    // Tech debt assessment phases (moved from discovery)
    tech_debt_assessment: (flowId: string) =>
      flowId ? `/assess/tech-debt/${flowId}` : "/assess",
    tech_debt_analysis: (flowId: string) =>
      flowId ? `/assess/tech-debt/${flowId}` : "/assess",
    tech_debt: (flowId: string) =>
      flowId ? `/assess/tech-debt/${flowId}` : "/assess",
    technical_debt: (flowId: string) =>
      flowId ? `/assess/tech-debt/${flowId}` : "/assess",
    completed: (flowId: string) =>
      flowId ? `/assess/summary/${flowId}` : "/assess",

    // Error states
    failed: () => "/assess",
    error: () => "/assess",
    unknown: () => "/assess",
  },

  plan: {
    wave_planning: (flowId: string) =>
      flowId ? `/plan/waveplanning/${flowId}` : "/plan",
    roadmap: (flowId: string) => (flowId ? `/plan/roadmap/${flowId}` : "/plan"),
    roadmap_planning: (flowId: string) =>
      flowId ? `/plan/roadmap/${flowId}` : "/plan",
    runbook_creation: (flowId: string) =>
      flowId ? `/plan/runbook-creation/${flowId}` : "/plan",
    resource_allocation: (flowId: string) =>
      flowId ? `/plan/resource-allocation/${flowId}` : "/plan",
    completed: (flowId: string) =>
      flowId ? `/plan/summary/${flowId}` : "/plan",

    // Error states
    failed: () => "/plan",
    error: () => "/plan",
    unknown: () => "/plan",
  },

  execute: {
    pre_migration: (flowId: string) =>
      flowId ? `/execute/pre-migration/${flowId}` : "/execute",
    migration_execution: (flowId: string) =>
      flowId ? `/execute/migration-execution/${flowId}` : "/execute",
    post_migration: (flowId: string) =>
      flowId ? `/execute/post-migration/${flowId}` : "/execute",
    completed: (flowId: string) =>
      flowId ? `/execute/summary/${flowId}` : "/execute",

    // Error states
    failed: () => "/execute",
    error: () => "/execute",
    unknown: () => "/execute",
  },

  modernize: {
    modernization_assessment: (flowId: string) =>
      flowId ? `/modernize/assessment/${flowId}` : "/modernize",
    architecture_design: (flowId: string) =>
      flowId ? `/modernize/architecture-design/${flowId}` : "/modernize",
    implementation_planning: (flowId: string) =>
      flowId ? `/modernize/implementation-planning/${flowId}` : "/modernize",
    completed: (flowId: string) =>
      flowId ? `/modernize/summary/${flowId}` : "/modernize",

    // Error states
    failed: () => "/modernize",
    error: () => "/modernize",
    unknown: () => "/modernize",
  },

  finops: {
    cost_analysis: (flowId: string) =>
      flowId ? `/finops/cost-analysis/${flowId}` : "/finops",
    budget_planning: (flowId: string) =>
      flowId ? `/finops/budget-planning/${flowId}` : "/finops",
    completed: (flowId: string) =>
      flowId ? `/finops/summary/${flowId}` : "/finops",

    // Error states
    failed: () => "/finops",
    error: () => "/finops",
    unknown: () => "/finops",
  },

  observability: {
    monitoring_setup: (flowId: string) =>
      flowId ? `/observability/monitoring-setup/${flowId}` : "/observability",
    performance_optimization: (flowId: string) =>
      flowId
        ? `/observability/performance-optimization/${flowId}`
        : "/observability",
    completed: (flowId: string) =>
      flowId ? `/observability/summary/${flowId}` : "/observability",

    // Error states
    failed: () => "/observability",
    error: () => "/observability",
    unknown: () => "/observability",
  },

  decommission: {
    decommission_planning: (flowId: string) =>
      flowId ? `/decommission/planning/${flowId}` : "/decommission",
    data_migration: (flowId: string) =>
      flowId ? `/decommission/data-migration/${flowId}` : "/decommission",
    system_shutdown: (flowId: string) =>
      flowId ? `/decommission/system-shutdown/${flowId}` : "/decommission",
    completed: (flowId: string) =>
      flowId ? `/decommission/summary/${flowId}` : "/decommission",

    // Error states
    failed: () => "/decommission",
    error: () => "/decommission",
    unknown: () => "/decommission",
  },
};

/**
 * @deprecated Use useFlowPhases hook instead
 *
 * This constant is kept for backward compatibility only.
 * New code should fetch phases from API using useFlowPhases.
 *
 * Will be removed in v4.0.0
 *
 * Per ADR-027: FlowTypeConfig is the single source of truth for phase sequences.
 * This hardcoded data can become out of sync with backend configuration.
 *
 * Migration guide:
 * - Old: const phases = PHASE_SEQUENCES_LEGACY[flowType];
 * - New: const { data: phases } = useFlowPhases(flowType); // then use phases?.phases
 *
 * Phase sequences for determining next phase - matches backend phase_sequences
 */
export const PHASE_SEQUENCES_LEGACY: Record<FlowType, string[]> = {
  discovery: [
    "data_import",
    "attribute_mapping",
    "data_cleansing",
    "inventory",
    "dependencies",
  ],
  collection: [
    "asset_selection",
    "gap_analysis",
    "questionnaire_generation",
    "manual_collection",
    "synthesis",
  ],
  assessment: [
    "initialization",
    "architecture_minimums",
    "tech_debt_analysis",
    "component_sixr_strategies",
    "app_on_page_generation",
    "finalization",
  ],
  plan: ["wave_planning", "roadmap", "runbook_creation", "resource_allocation"],
  execute: ["pre_migration", "migration_execution", "post_migration"],
  modernize: [
    "modernization_assessment",
    "architecture_design",
    "implementation_planning",
  ],
  finops: ["cost_analysis", "budget_planning"],
  observability: ["monitoring_setup", "performance_optimization"],
  decommission: ["decommission_planning", "data_migration", "system_shutdown"],
};

/**
 * Alias for backward compatibility
 * @deprecated Use PHASE_SEQUENCES_LEGACY or preferably useFlowPhases hook
 */
export const PHASE_SEQUENCES = PHASE_SEQUENCES_LEGACY;

/**
 * Get the appropriate route for any flow type and phase
 * @param flowType - The type of flow (discovery, assess, etc.)
 * @param phase - The current phase of the flow
 * @param flowId - The flow ID
 * @returns The route to navigate to
 */
export function getFlowPhaseRoute(
  flowType: FlowType,
  phase: string,
  flowId: string,
): string {
  const flowRoutes = FLOW_PHASE_ROUTES[flowType];
  if (!flowRoutes) {
    console.warn(`Unknown flow type: ${flowType}, defaulting to home`);
    return "/";
  }

  const routeFunction = flowRoutes[phase];
  if (routeFunction) {
    return routeFunction(flowId);
  }

  // Default to flow type's error route
  const errorRoute = flowRoutes["unknown"] || flowRoutes["error"];
  if (errorRoute) {
    return errorRoute(flowId);
  }

  console.warn(`Unknown phase: ${phase} for flow type: ${flowType}`);
  return `/${flowType}`;
}

/**
 * Get discovery flow route (backward compatibility)
 * @param phase - The current phase of the discovery flow
 * @param flowId - The flow ID
 * @returns The route to navigate to
 */
export function getDiscoveryPhaseRoute(phase: string, flowId: string): string {
  return getFlowPhaseRoute("discovery", phase, flowId);
}

/**
 * Determine if a phase requires flowId in the URL
 * @param flowType - The type of flow
 * @param phase - The phase to check
 * @returns true if the phase requires flowId in URL
 */
export function phaseRequiresFlowId(
  flowType: FlowType,
  phase: string,
): boolean {
  const noFlowIdPhases: Record<FlowType, string[]> = {
    discovery: ["data_import_validation", "data_import"],
    collection: ["failed", "error", "unknown"],
    assessment: ["failed", "error", "unknown"],
    plan: ["failed", "error", "unknown"],
    execute: ["failed", "error", "unknown"],
    modernize: ["failed", "error", "unknown"],
    finops: ["failed", "error", "unknown"],
    observability: ["failed", "error", "unknown"],
    decommission: ["failed", "error", "unknown"],
  };

  return !(noFlowIdPhases[flowType] || []).includes(phase);
}

/**
 * Get next phase for a flow
 *
 * @deprecated Use getNextPhase from useFlowPhases hook instead
 *
 * Per ADR-027: Phase sequences should come from API, not hardcoded constants
 *
 * Migration guide:
 * ```tsx
 * // Old way:
 * const nextPhase = getNextPhase(flowType, currentPhase);
 *
 * // New way:
 * const { data: phases } = useFlowPhases(flowType);
 * const nextPhase = getNextPhase(phases, currentPhase); // from useFlowPhases hook
 * ```
 *
 * @param flowType - The type of flow
 * @param currentPhase - The current phase
 * @returns The next phase or 'completed'
 */
export function getNextPhase(flowType: FlowType, currentPhase: string): string {
  const sequence = PHASE_SEQUENCES_LEGACY[flowType];
  if (!sequence) return "completed";

  const currentIndex = sequence.indexOf(currentPhase);
  if (currentIndex === -1 || currentIndex === sequence.length - 1) {
    return "completed";
  }

  return sequence[currentIndex + 1];
}

/**
 * Determine flow type from current path
 * @param pathname - The current pathname
 * @returns The flow type or null
 */
export function getFlowTypeFromPath(pathname: string): FlowType | null {
  if (pathname.includes("/discovery/")) return "discovery";
  if (pathname.includes("/collection/")) return "collection";
  if (pathname.includes("/assess/")) return "assessment";
  if (pathname.includes("/plan/")) return "plan";
  if (pathname.includes("/execute/")) return "execute";
  if (pathname.includes("/modernize/")) return "modernize";
  if (pathname.includes("/finops/")) return "finops";
  if (pathname.includes("/observability/")) return "observability";
  if (pathname.includes("/decommission/")) return "decommission";
  return null;
}

/**
 * Get flow information from the backend flow state
 * MFO-086: Updated to use Master Flow Orchestrator API
 * MIGRATED: Now uses masterFlowService instead of legacy FlowService
 */
export async function getFlowInfo(
  flowId: string,
): Promise<{ flowType: FlowType; currentPhase: string } | null> {
  try {
    // Use masterFlowService for unified flow API access
    const { masterFlowService } = await import(
      "../services/api/masterFlowService"
    );
    const { AuthService } = await import(
      "../contexts/AuthContext/services/authService"
    );

    // Get auth context for multi-tenant headers
    const authService = AuthService.getInstance();
    const context = authService.getAuthState();

    if (!context?.clientAccount?.id) {
      console.error("No client account context available for flow info");
      return null;
    }

    const flowStatus = await masterFlowService.getFlowStatus(
      flowId,
      context.clientAccount.id.toString(),
      context.engagement?.id?.toString(),
    );

    return {
      flowType: flowStatus.flowType as FlowType,
      currentPhase: flowStatus.currentPhase || "unknown",
    };
  } catch (error) {
    console.error("Failed to get flow info:", error);
    return null;
  }
}

/**
 * Master flow dashboard route
 * MFO-086: Add route for unified flow dashboard
 */
export const MASTER_FLOW_DASHBOARD_ROUTE = "/flows";

/**
 * Get dashboard route for a specific flow type
 * MFO-086: Support flow type specific dashboards
 */
export function getFlowDashboardRoute(flowType?: FlowType): string {
  if (!flowType) return MASTER_FLOW_DASHBOARD_ROUTE;
  return `/${flowType}`;
}
