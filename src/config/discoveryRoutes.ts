/**
 * ⚠️ DEPRECATED: Centralized discovery flow routing configuration
 *
 * @deprecated Per ADR-027 v3.0.0 - Use useFlowPhases hook to get routes from FlowTypeConfig
 *
 * **WHY THIS FILE IS DEPRECATED:**
 * - Hardcoded routes can become out of sync with backend FlowTypeConfig
 * - Backend is the single source of truth for phase sequences and UI routes
 * - Dynamic configuration allows phase changes without frontend deployments
 * - FlowTypeConfig provides additional metadata (icons, help text, duration)
 *
 * **MIGRATION STATUS:**
 * - ✅ Sidebar.tsx: Migrated to useAllFlowPhases() (lines 82-151)
 * - ✅ usePhaseAwareFlowResolver.ts: Migrated to use getPhaseOrder()
 * - ✅ useFlowManagement.ts: Migrated to use getPhaseRoute()
 * - ⚠️ Legacy fallback routes maintained for backward compatibility
 *
 * **REMOVAL TIMELINE:**
 * - v3.x: This file deprecated but functional (current)
 * - v4.0.0: File will be removed entirely (planned)
 *
 * **MIGRATION GUIDE:**
 *
 * ### For Route Resolution:
 * ```tsx
 * // ❌ Old way - hardcoded routes:
 * import { DISCOVERY_PHASE_ROUTES_LEGACY, getDiscoveryPhaseRoute } from '@/config/discoveryRoutes';
 * const route = DISCOVERY_PHASE_ROUTES_LEGACY[phase](flowId);
 * // or
 * const route = getDiscoveryPhaseRoute(phase, flowId);
 *
 * // ✅ New way - dynamic routes from backend:
 * import { useFlowPhases, getPhaseRoute } from '@/hooks/useFlowPhases';
 *
 * const MyComponent = ({ phase, flowId }) => {
 *   const { data: discoveryPhases, isLoading } = useFlowPhases('discovery');
 *
 *   const handleNavigate = () => {
 *     if (discoveryPhases) {
 *       const route = getPhaseRoute(discoveryPhases, phase);
 *       navigate(route);
 *     }
 *   };
 *
 *   if (isLoading) return <Loading />;
 *   return <Button onClick={handleNavigate}>Go to Phase</Button>;
 * };
 * ```
 *
 * ### For Phase Ordering:
 * ```tsx
 * // ❌ Old way - hardcoded phase order:
 * const PHASE_ORDER = { data_import: 1, field_mapping: 2, ... };
 * const currentOrder = PHASE_ORDER[currentPhase];
 *
 * // ✅ New way - dynamic ordering:
 * import { useFlowPhases, getPhaseOrder } from '@/hooks/useFlowPhases';
 *
 * const { data: phases } = useFlowPhases('discovery');
 * const currentOrder = getPhaseOrder(phases, currentPhase);
 * ```
 *
 * ### For Sidebar Navigation:
 * ```tsx
 * // ❌ Old way - manual menu construction:
 * const submenu = [
 *   { name: 'Field Mapping', path: '/discovery/attribute-mapping' },
 *   { name: 'Data Cleansing', path: '/discovery/data-cleansing' }
 * ];
 *
 * // ✅ New way - API-driven menu (see Sidebar.tsx:101-122):
 * const { data: allFlowPhases } = useAllFlowPhases();
 * const submenu = allFlowPhases?.discovery.phase_details.map(phase => ({
 *   name: phase.ui_short_name || phase.display_name,
 *   path: phase.ui_route,
 *   icon: getIconForPhase(phase.name)
 * }));
 * ```
 *
 * **BENEFITS OF MIGRATION:**
 * - ✅ Single source of truth (backend FlowTypeConfig)
 * - ✅ No frontend deployment needed for phase changes
 * - ✅ Rich metadata (icons, help text, estimated duration)
 * - ✅ Version control for flow configurations
 * - ✅ A/B testing different phase sequences per tenant
 *
 * **REFERENCE FILES:**
 * - `/src/hooks/useFlowPhases.ts` - Hook implementation and helper functions
 * - `/src/components/layout/sidebar/Sidebar.tsx` - Example successful migration
 * - `/docs/adr/027-universal-flow-type-config.md` - Architectural decision
 * - `/backend/app/services/crewai_flows/flow_configs/` - Backend FlowTypeConfig definitions
 *
 * Maps backend phase names to frontend routes (LEGACY - DO NOT EXTEND)
 */
export const DISCOVERY_PHASE_ROUTES_LEGACY: Record<string, (flowId: string) => string> = {
  // ADR-027 v3.0.0: initialization phase removed from Discovery flow
  'data_import_validation': () => '/discovery/cmdb-import',
  'data_import': () => '/discovery/cmdb-import',

  // Data validation phase (ADR-038: intelligent data profiling)
  'data_validation': (flowId: string) => flowId ? `/discovery/data-validation/${flowId}` : '/discovery/cmdb-import',

  // Field mapping phases
  'field_mapping': (flowId: string) => flowId ? `/discovery/attribute-mapping/${flowId}` : '/discovery/cmdb-import',
  'attribute_mapping': (flowId: string) => flowId ? `/discovery/attribute-mapping/${flowId}` : '/discovery/cmdb-import',

  // Data cleansing phase
  'data_cleansing': (flowId: string) => flowId ? `/discovery/data-cleansing/${flowId}` : '/discovery/cmdb-import',

  // Asset inventory phases
  'asset_inventory': (flowId: string) => flowId ? `/discovery/inventory/${flowId}` : '/discovery/cmdb-import',
  'inventory': (flowId: string) => flowId ? `/discovery/inventory/${flowId}` : '/discovery/cmdb-import',

  // ADR-027 v3.0.0: dependency_analysis and tech_debt_assessment moved to Assessment flow
  // Legacy routes redirect to Assessment flow for backward compatibility
  'dependency_analysis': (flowId: string) => flowId ? `/assessment/dependency-analysis` : '/assess/overview',
  'dependencies': (flowId: string) => flowId ? `/assessment/dependency-analysis` : '/assess/overview',
  'tech_debt_assessment': (flowId: string) => flowId ? `/assessment/tech-debt` : '/assess/overview',
  'tech_debt_analysis': (flowId: string) => flowId ? `/assessment/tech-debt` : '/assess/overview',
  'tech_debt': (flowId: string) => flowId ? `/assessment/tech-debt` : '/assess/overview',
  'technical_debt': (flowId: string) => flowId ? `/assessment/tech-debt` : '/assess/overview',

  // Completed flow - route to inventory
  'completed': (flowId: string) => flowId ? `/discovery/inventory/${flowId}` : '/discovery/cmdb-import',

  // Status-based routing
  'waiting_for_user_approval': (flowId: string) => flowId ? `/discovery/attribute-mapping/${flowId}` : '/discovery/cmdb-import',
  'paused': (flowId: string) => flowId ? `/discovery/attribute-mapping/${flowId}` : '/discovery/cmdb-import',
  'pending_approval': (flowId: string) => flowId ? `/discovery/attribute-mapping/${flowId}` : '/discovery/cmdb-import',

  // Error states - route to monitoring for error details
  'failed': (flowId: string) => flowId ? `/discovery/monitor/${flowId}` : '/discovery/cmdb-import',
  'error': (flowId: string) => flowId ? `/discovery/monitor/${flowId}` : '/discovery/cmdb-import',
  'not_found': (flowId: string) => flowId ? `/discovery/monitor/${flowId}` : '/discovery/cmdb-import',

  // Unknown/undefined states - route to monitoring
  'unknown': (flowId: string) => flowId ? `/discovery/monitor/${flowId}` : '/discovery/cmdb-import',
  'undefined': (flowId: string) => flowId ? `/discovery/monitor/${flowId}` : '/discovery/cmdb-import',
  'current': (flowId: string) => flowId ? `/discovery/monitor/${flowId}` : '/discovery/cmdb-import',
};

/**
 * Alias for backward compatibility
 * @deprecated Use DISCOVERY_PHASE_ROUTES_LEGACY or preferably useFlowPhases hook
 */
export const DISCOVERY_PHASE_ROUTES = DISCOVERY_PHASE_ROUTES_LEGACY;

/**
 * Get the appropriate route for a discovery flow phase
 *
 * @deprecated Use getPhaseRoute from useFlowPhases hook instead
 *
 * Per ADR-027: Phase routes should come from API FlowTypeConfig, not hardcoded
 *
 * Migration guide:
 * ```tsx
 * // Old way:
 * const route = getDiscoveryPhaseRoute(phase, flowId);
 *
 * // New way:
 * const { data: phases } = useFlowPhases('discovery');
 * const route = getPhaseRoute(phases, phase); // from useFlowPhases hook
 * ```
 *
 * @param phase - The current phase of the flow
 * @param flowId - The flow ID
 * @returns The route to navigate to
 */
export function getDiscoveryPhaseRoute(phase: string, flowId: string): string {
  const routeFunction = DISCOVERY_PHASE_ROUTES_LEGACY[phase];
  if (routeFunction) {
    return routeFunction(flowId);
  }

  // Default to cmdb-import for unknown phases
  console.warn(`Unknown discovery phase: ${phase}, defaulting to cmdb-import`);
  return '/discovery/cmdb-import';
}

/**
 * Determine if a phase requires flowId in the URL
 * @param phase - The phase to check
 * @returns true if the phase requires flowId in URL
 */
export function phaseRequiresFlowId(phase: string): boolean {
  const noFlowIdPhases = [
    'data_import_validation',
    'data_import'
  ];

  return !noFlowIdPhases.includes(phase);
}
