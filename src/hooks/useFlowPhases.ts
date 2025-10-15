/**
 * useFlowPhases Hook
 *
 * Fetches authoritative phase sequences from backend FlowTypeConfig.
 *
 * Per ADR-027: Replaces hardcoded PHASE_SEQUENCES with API-driven configuration.
 * This ensures single source of truth for phase information.
 *
 * Backend API: /api/v1/flow-metadata/phases/{flow_type}
 */

import { useQuery } from '@tanstack/react-query';
import { apiCall } from '@/services/api';

/**
 * Phase detail metadata from FlowTypeConfig
 *
 * CRITICAL: Uses snake_case to match backend exactly (no camelCase conversion)
 */
export interface PhaseDetail {
  name: string;
  display_name: string;
  description: string;
  order: number;
  estimated_duration_minutes: number;
  can_pause: boolean;
  can_skip: boolean;
  ui_route: string;
  ui_short_name?: string;  // Compact name for sidebar navigation (ADR-027)
  icon?: string;
  help_text?: string;
}

/**
 * Complete flow phase configuration from backend
 *
 * CRITICAL: Uses snake_case to match backend exactly (no camelCase conversion)
 */
export interface FlowPhases {
  flow_type: string;
  display_name: string;
  version: string;
  phases: string[];
  phase_details: PhaseDetail[];
  phase_count: number;
  estimated_total_duration_minutes: number;
}

/**
 * Fetch authoritative phase sequence for a specific flow type
 *
 * Per ADR-027: Replaces hardcoded PHASE_SEQUENCES
 *
 * @param flowType - Flow type (discovery, assessment, collection, etc.)
 * @returns React Query result with FlowPhases data
 *
 * @example
 * ```tsx
 * const { data: phases, isLoading, error } = useFlowPhases('discovery');
 * if (phases) {
 *   console.log(phases.phases); // ['data_import', 'field_mapping', ...]
 * }
 * ```
 */
export function useFlowPhases(flowType: string) {
  return useQuery<FlowPhases>({
    queryKey: ['flow-phases', flowType],
    queryFn: async () => {
      const response = await apiCall(`/flow-metadata/phases/${flowType}`, {
        method: 'GET',
      });
      return response as FlowPhases;
    },
    staleTime: 30 * 60 * 1000, // 30 minutes - phases rarely change
    gcTime: 60 * 60 * 1000,     // 1 hour (renamed from cacheTime in TanStack Query v5)
    retry: 3,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
}

/**
 * Fetch all flow phases (all flow types)
 *
 * Useful for global navigation and flow type selection
 *
 * @returns React Query result with all FlowPhases data keyed by flow_type
 *
 * @example
 * ```tsx
 * const { data: allPhases } = useAllFlowPhases();
 * Object.entries(allPhases || {}).map(([flowType, phaseInfo]) => (
 *   <NavItem key={flowType} label={phaseInfo.display_name} />
 * ))
 * ```
 */
export function useAllFlowPhases() {
  return useQuery<Record<string, FlowPhases>>({
    queryKey: ['flow-phases-all'],
    queryFn: async () => {
      const response = await apiCall('/flow-metadata/phases', {
        method: 'GET',
      });
      return response as Record<string, FlowPhases>;
    },
    staleTime: 30 * 60 * 1000,
    gcTime: 60 * 60 * 1000,
    retry: 3,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
  });
}

/**
 * Get phase display name from phase detail
 *
 * Helper function for rendering phase names in UI
 *
 * @param phases - FlowPhases data from useFlowPhases hook
 * @param phaseName - Internal phase name (e.g., 'field_mapping')
 * @returns Display name (e.g., 'Field Mapping & Transformation') or phaseName if not found
 */
export function getPhaseDisplayName(
  phases: FlowPhases | undefined,
  phaseName: string
): string {
  if (!phases) return phaseName;

  const phase = phases.phase_details.find(p => p.name === phaseName);
  return phase?.display_name || phaseName;
}

/**
 * Get phase route from phase detail
 *
 * Helper function for phase navigation
 *
 * @param phases - FlowPhases data from useFlowPhases hook
 * @param phaseName - Internal phase name
 * @returns UI route for phase (e.g., '/discovery/field-mapping') or '/' if not found
 */
export function getPhaseRoute(
  phases: FlowPhases | undefined,
  phaseName: string
): string {
  if (!phases) return '/';

  const phase = phases.phase_details.find(p => p.name === phaseName);
  return phase?.ui_route || '/';
}

/**
 * Check if phase is valid for flow type
 *
 * Helper function for phase validation
 *
 * @param phases - FlowPhases data from useFlowPhases hook
 * @param phaseName - Internal phase name to validate
 * @returns true if phase exists in flow's phase sequence
 */
export function isValidPhase(
  phases: FlowPhases | undefined,
  phaseName: string
): boolean {
  if (!phases) return false;
  return phases.phases.includes(phaseName);
}

/**
 * Get next phase in sequence
 *
 * Helper function for phase transitions
 *
 * @param phases - FlowPhases data from useFlowPhases hook
 * @param currentPhase - Current phase name
 * @returns Next phase name or null if at end
 */
export function getNextPhase(
  phases: FlowPhases | undefined,
  currentPhase: string
): string | null {
  if (!phases) return null;

  const phaseList = phases.phases;
  const currentIndex = phaseList.indexOf(currentPhase);

  if (currentIndex === -1 || currentIndex === phaseList.length - 1) {
    return null;
  }

  return phaseList[currentIndex + 1];
}

/**
 * Get previous phase in sequence
 *
 * Helper function for backward navigation
 *
 * @param phases - FlowPhases data from useFlowPhases hook
 * @param currentPhase - Current phase name
 * @returns Previous phase name or null if at beginning
 */
export function getPreviousPhase(
  phases: FlowPhases | undefined,
  currentPhase: string
): string | null {
  if (!phases) return null;

  const phaseList = phases.phases;
  const currentIndex = phaseList.indexOf(currentPhase);

  if (currentIndex <= 0) {
    return null;
  }

  return phaseList[currentIndex - 1];
}

/**
 * Get phase order/index
 *
 * Helper function to determine phase position in sequence
 *
 * @param phases - FlowPhases data from useFlowPhases hook
 * @param phaseName - Phase name to get order for
 * @returns Phase order (0-indexed) or -1 if not found
 */
export function getPhaseOrder(
  phases: FlowPhases | undefined,
  phaseName: string
): number {
  if (!phases) return -1;
  return phases.phases.indexOf(phaseName);
}

/**
 * Check if can transition to target phase
 *
 * Validates phase transitions based on sequence order
 *
 * @param phases - FlowPhases data from useFlowPhases hook
 * @param currentPhase - Current phase name
 * @param targetPhase - Target phase name
 * @returns true if transition is allowed (forward or same phase)
 */
export function canTransitionToPhase(
  phases: FlowPhases | undefined,
  currentPhase: string,
  targetPhase: string
): boolean {
  if (!phases) return false;

  const currentIndex = getPhaseOrder(phases, currentPhase);
  const targetIndex = getPhaseOrder(phases, targetPhase);

  // Invalid phases
  if (currentIndex === -1 || targetIndex === -1) {
    return false;
  }

  // Can move forward or stay on same phase
  return targetIndex >= currentIndex;
}
