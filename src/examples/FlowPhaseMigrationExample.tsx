/**
 * FlowPhaseMigrationExample
 *
 * Example component demonstrating ADR-027 Phase 7 migration
 * Shows how to migrate from hardcoded PHASE_SEQUENCES to API-driven useFlowPhases hook
 *
 * This file serves as a reference for migrating existing components
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  useFlowPhases,
  getPhaseDisplayName,
  getPhaseRoute,
  isValidPhase,
  getNextPhase,
  canTransitionToPhase,
} from '@/hooks/useFlowPhases';

/**
 * BEFORE (Deprecated Pattern - DO NOT USE):
 *
 * ```tsx
 * import { PHASE_SEQUENCES, getNextPhase as getNextPhaseLegacy } from '@/config/flowRoutes';
 *
 * const phases = PHASE_SEQUENCES['discovery']; // Hardcoded
 * const nextPhase = getNextPhaseLegacy('discovery', currentPhase); // Hardcoded
 * ```
 *
 * AFTER (New Pattern - USE THIS):
 *
 * See implementation below
 */

interface FlowPhaseMigrationExampleProps {
  flowType: string;
  currentPhase: string;
  flowId: string;
}

export function FlowPhaseMigrationExample({
  flowType,
  currentPhase,
  flowId,
}: FlowPhaseMigrationExampleProps) {
  const navigate = useNavigate();

  // Step 1: Fetch phases from API using useFlowPhases hook
  const { data: phases, isLoading, error } = useFlowPhases(flowType);

  // Step 2: Handle loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        <span className="ml-3 text-gray-600">Loading phase information...</span>
      </div>
    );
  }

  // Step 3: Handle error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <h3 className="text-red-800 font-semibold">Failed to load phases</h3>
        <p className="text-red-600 text-sm mt-1">
          {error instanceof Error ? error.message : 'Unknown error'}
        </p>
      </div>
    );
  }

  // Step 4: Use helper functions with API data
  const displayName = getPhaseDisplayName(phases, currentPhase);
  const route = getPhaseRoute(phases, currentPhase);
  const valid = isValidPhase(phases, currentPhase);
  const nextPhase = getNextPhase(phases, currentPhase);

  // Step 5: Use phase data in UI
  return (
    <div className="space-y-6">
      {/* Flow Information */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold text-gray-900">
          {phases?.display_name} (v{phases?.version})
        </h2>
        <p className="text-gray-600 mt-2">
          Total Duration: {phases?.estimated_total_duration_minutes} minutes
        </p>
        <p className="text-gray-600">
          Phases: {phases?.phase_count}
        </p>
      </div>

      {/* Current Phase Status */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-blue-900 font-semibold">Current Phase</h3>
        <p className="text-blue-700 text-lg mt-1">{displayName}</p>
        <p className="text-blue-600 text-sm">
          Internal: {currentPhase} | Valid: {valid ? 'Yes' : 'No'}
        </p>
      </div>

      {/* Phase Progress */}
      <div className="space-y-2">
        <h3 className="font-semibold text-gray-900">Phase Progress</h3>
        {phases?.phase_details.map((phase, index) => {
          const isCurrent = phase.name === currentPhase;
          const isPast = index < (phases?.phases.indexOf(currentPhase) ?? 0);
          const canNavigate = canTransitionToPhase(phases, currentPhase, phase.name);

          return (
            <div
              key={phase.name}
              className={`
                flex items-center justify-between p-4 rounded-lg border
                ${isCurrent ? 'bg-blue-50 border-blue-300' : ''}
                ${isPast ? 'bg-green-50 border-green-300' : ''}
                ${!isCurrent && !isPast ? 'bg-gray-50 border-gray-200' : ''}
              `}
            >
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-900">
                    {phase.order + 1}. {phase.display_name}
                  </span>
                  {isCurrent && (
                    <span className="px-2 py-1 bg-blue-600 text-white text-xs rounded">
                      Current
                    </span>
                  )}
                  {isPast && (
                    <span className="px-2 py-1 bg-green-600 text-white text-xs rounded">
                      Completed
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-1">{phase.description}</p>
                <div className="flex gap-4 mt-2 text-xs text-gray-500">
                  <span>Duration: {phase.estimated_duration_minutes} min</span>
                  {phase.can_pause && <span>Can Pause</span>}
                  {phase.can_skip && <span>Can Skip</span>}
                </div>
              </div>

              {canNavigate && (
                <button
                  onClick={() => navigate(phase.ui_route)}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                  Go to Phase
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Navigation Actions */}
      <div className="flex gap-4">
        {nextPhase && (
          <button
            onClick={() => {
              const nextRoute = getPhaseRoute(phases, nextPhase);
              navigate(nextRoute);
            }}
            className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-semibold"
          >
            Continue to {getPhaseDisplayName(phases, nextPhase)}
          </button>
        )}

        <button
          onClick={() => navigate(route)}
          className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
        >
          Stay on Current Phase
        </button>
      </div>

      {/* Debug Information (Development Only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="bg-gray-100 rounded-lg p-4 mt-8">
          <h4 className="font-mono text-sm font-bold mb-2">Debug Info</h4>
          <pre className="text-xs overflow-auto">
            {JSON.stringify(
              {
                flowType,
                currentPhase,
                flowId,
                phases: phases?.phases,
                phaseCount: phases?.phase_count,
              },
              null,
              2
            )}
          </pre>
        </div>
      )}
    </div>
  );
}

/**
 * Key Migration Points:
 *
 * 1. Replace PHASE_SEQUENCES with useFlowPhases hook
 * 2. Handle loading and error states
 * 3. Use helper functions (getPhaseDisplayName, getPhaseRoute, etc.)
 * 4. Access phase data via phases?.phases and phases?.phase_details
 * 5. Use snake_case field names (phase.display_name, NOT phase.displayName)
 */

/**
 * TypeScript Type Reference:
 *
 * ```typescript
 * interface FlowPhases {
 *   flow_type: string;
 *   display_name: string;
 *   version: string;
 *   phases: string[];
 *   phase_details: PhaseDetail[];
 *   phase_count: number;
 *   estimated_total_duration_minutes: number;
 * }
 *
 * interface PhaseDetail {
 *   name: string;
 *   display_name: string;
 *   description: string;
 *   order: number;
 *   estimated_duration_minutes: number;
 *   can_pause: boolean;
 *   can_skip: boolean;
 *   ui_route: string;
 *   icon?: string;
 *   help_text?: string;
 * }
 * ```
 */
