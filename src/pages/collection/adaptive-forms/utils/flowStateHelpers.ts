/**
 * Flow State Helper Functions
 * Utility functions for flow state management
 * Extracted from AdaptiveForms.tsx
 */

interface CollectionFlowConfig {
  selected_application_ids?: string[];
  applications?: string[];
  application_ids?: string[];
  has_applications?: boolean;
}

interface CollectionFlow {
  flow_id?: string;
  id?: string;
  progress?: number;
  current_phase?: string;
  collection_config?: CollectionFlowConfig;
}

/**
 * Check if applications are selected in a collection flow
 */
export const hasApplicationsSelected = (collectionFlow: CollectionFlow | null): boolean => {
  if (!collectionFlow) return false;

  // Check collection_config for selected applications
  const config = collectionFlow.collection_config || {};
  const selectedApps =
    config.selected_application_ids ||
    config.applications ||
    config.application_ids ||
    [];

  // Check if applications are selected
  const hasApps = Array.isArray(selectedApps) && selectedApps.length > 0;

  // Also check if has_applications flag is set in config
  const hasAppsFlag = config.has_applications === true;

  // Return true if applications are selected either way
  return hasApps || hasAppsFlag;
};

/**
 * Normalize flow ID from different possible field names
 */
export const normalizeFlowId = (flow: CollectionFlow): string => {
  return String(flow.flow_id || flow.id || '');
};

/**
 * Filter blocking flows excluding the current flow
 */
export const filterBlockingFlows = (
  allFlows: CollectionFlow[],
  currentFlowId: string | null,
  deletingFlowIds: Set<string>
): CollectionFlow[] => {
  const normalizedCurrentId = String(currentFlowId || '');

  return allFlows.filter((flow) => {
    const flowId = normalizeFlowId(flow);

    // Don't block if this is the current flow
    if (currentFlowId && flowId === normalizedCurrentId) {
      return false;
    }

    // Don't block if flow is being deleted
    if (deletingFlowIds.has(flowId)) {
      return false;
    }

    return true;
  });
};
