import { useMemo } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import { useDiscoveryFlowList } from './useDiscoveryFlowList';
import SecureLogger from '../../utils/secureLogger';
import SecureStorage from '../../utils/secureStorage';

// TypeScript interfaces for proper type safety
interface DiscoveryFlow {
  id: string;
  flow_id?: string;
  status: string;
  current_phase?: string;
  next_phase?: string;
  phases?: Record<string, boolean>;
  data_import_completed?: boolean;
  field_mapping_completed?: boolean;
  data_cleansing_completed?: boolean;
  created_at?: string;
  updated_at?: string;
}

interface FlowAutoDetectionOptions {
  currentPhase?: string;
  preferredStatuses?: string[];
  fallbackToAnyRunning?: boolean;
}

interface FlowAutoDetectionResult {
  urlFlowId: string | undefined;
  autoDetectedFlowId: string | null;
  effectiveFlowId: string | null;
  flowList: DiscoveryFlow[] | undefined;
  isFlowListLoading: boolean;
  flowListError: Error | null;
  hasUrlFlowId: boolean;
  hasAutoDetectedFlow: boolean;
  hasEffectiveFlow: boolean;
  totalFlowsAvailable: number;
}

export const useDiscoveryFlowAutoDetection = (options: FlowAutoDetectionOptions = {}): FlowAutoDetectionResult => {
  // First try route params (e.g., /path/:flowId)
  const { flowId: routeFlowId } = useParams<{ flowId?: string }>();

  // Also check query params (e.g., ?flow_id=...)
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const queryFlowId = queryParams.get('flow_id');

  // Normalize and validate IDs before use (trim whitespace and validate format)
  const normalizeFlowId = (id: string | null | undefined): string | undefined => {
    if (!id) return undefined;
    const trimmed = id.trim();
    // Basic UUID format validation
    const uuidPattern = /^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
    return trimmed && uuidPattern.test(trimmed) ? trimmed : undefined;
  };

  // Use route param first, then query param as fallback, both normalized
  const urlFlowId = normalizeFlowId(routeFlowId) || normalizeFlowId(queryFlowId) || undefined;

  const { data: flowList, isLoading: isFlowListLoading, error: flowListError } = useDiscoveryFlowList();

  const {
    currentPhase,
    preferredStatuses = ['initialized', 'running', 'active', 'in_progress', 'waiting_for_approval'],
    fallbackToAnyRunning = true
  } = options;

  // Auto-detect the most relevant flow based on current page context
  const autoDetectedFlowId = useMemo(() => {
    if (!flowList || flowList.length === 0) {
      // Emergency fallback: try to extract flow ID from URL with validation
      const currentUrl = typeof window !== 'undefined' ? window.location.href : '';

      // Look for flow ID patterns in current URL with secure validation
      const flowIdPattern = /[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}/i;
      const urlMatch = currentUrl.match(flowIdPattern);

      if (urlMatch) {
        const rawFlowId = urlMatch[0];
        const validatedFlowId = SecureStorage.validateUrlFlowId(rawFlowId);
        if (validatedFlowId) {
          return validatedFlowId;
        }
      }

      return null;
    }

    // Flow detection for phase

    // Priority 1: Flow currently in the specified phase (next_phase matches or current_phase matches)
    if (currentPhase) {
      const currentPhaseFlow = flowList.find((flow: DiscoveryFlow) =>
        flow.next_phase === currentPhase || flow.current_phase === currentPhase
      );
      if (currentPhaseFlow) {
        const flowId = currentPhaseFlow.flow_id || currentPhaseFlow.id;
        return flowId;
      }
    }

    // Priority 1.5: For field_mapping, also check flows that completed data_import
    if (currentPhase === 'field_mapping') {
      const dataImportCompleteFlow = flowList.find((flow: DiscoveryFlow) => {
        // Check if data_import is completed
        const dataImportCompleted = flow.phases?.data_import === true ||
                                   flow.data_import_completed === true ||
                                   flow.current_phase === 'data_import';

        // Check if flow is in a suitable status
        const isPreferredStatus = preferredStatuses.includes(flow.status);

        // Check if field_mapping is not yet completed
        const fieldMappingNotCompleted = flow.phases?.field_mapping !== true &&
                                           flow.field_mapping_completed !== true;

        return dataImportCompleted && isPreferredStatus && fieldMappingNotCompleted;
      });

      if (dataImportCompleteFlow) {
        const flowId = dataImportCompleteFlow.flow_id || dataImportCompleteFlow.id;
        return flowId;
      }
    }

    // Priority 1.6: For data_cleansing, also check flows that completed field_mapping
    if (currentPhase === 'data_cleansing') {
      const fieldMappingCompleteFlow = flowList.find((flow: DiscoveryFlow) => {
        // Check if field_mapping is completed
        const fieldMappingCompleted = flow.phases?.field_mapping === true ||
                                     flow.field_mapping_completed === true ||
                                     flow.current_phase === 'field_mapping';

        // Check if flow is in a suitable status
        const isPreferredStatus = preferredStatuses.includes(flow.status);

        // Check if data_cleansing is not yet completed
        const dataCleansingNotCompleted = flow.phases?.data_cleansing !== true &&
                                        flow.data_cleansing_completed !== true;

        // Check flow readiness for data_cleansing

        return fieldMappingCompleted && isPreferredStatus && dataCleansingNotCompleted;
      });

      if (fieldMappingCompleteFlow) {
        const flowId = fieldMappingCompleteFlow.flow_id || fieldMappingCompleteFlow.id;
        return flowId;
      }
    }

    // Priority 2: Flow with specified phase completed but still in preferred status
    if (currentPhase) {
      const completedPhaseFlow = flowList.find((flow: DiscoveryFlow) => {
        // Check both direct field and phases object for completion status
        const directField = flow[`${currentPhase}_completed`];
        const phasesField = flow.phases?.[`${currentPhase}_completed`];
        const isPhaseCompleted = directField === true || phasesField === true;

        const isPreferredStatus = preferredStatuses.includes(flow.status);

        // Check flow completion

        return isPhaseCompleted && isPreferredStatus;
      });

      if (completedPhaseFlow) {
        const flowId = completedPhaseFlow.flow_id || completedPhaseFlow.id;
        return flowId;
      }
    }

    // Priority 3: Any flow in preferred status
    if (fallbackToAnyRunning) {
      const runningFlow = flowList.find((flow: DiscoveryFlow) =>
        preferredStatuses.includes(flow.status)
      );
      if (runningFlow) {
        const flowId = runningFlow.flow_id || runningFlow.id;
        return flowId;
      }
    }

    // Priority 4: Most recent flow (even if completed)
    const sortedFlows = [...flowList].sort((a: DiscoveryFlow, b: DiscoveryFlow) => {
      const dateA = new Date(a.updated_at || a.created_at || '1970-01-01').getTime();
      const dateB = new Date(b.updated_at || b.created_at || '1970-01-01').getTime();
      return dateB - dateA;
    });

    if (sortedFlows.length > 0) {
      const flowId = sortedFlows[0].flow_id || sortedFlows[0].id;
      return flowId;
    }

    // Priority 5: Any flow at all (last resort)
    if (flowList.length > 0) {
      const flowId = flowList[0].flow_id || flowList[0].id;
      return flowId;
    }

    return null;
  }, [flowList, currentPhase, preferredStatuses, fallbackToAnyRunning]);

  // Validate that the resolved flow ID is in the user's visible flows
  const validatedFlowId = useMemo(() => {
    const candidateFlowId = urlFlowId || autoDetectedFlowId;

    if (!candidateFlowId) {
      return candidateFlowId;
    }

    // CRITICAL FIX #326: Validate URL flow_id exists in flowList before trusting it
    // Backend now returns 404 when flow_id doesn't exist - frontend must validate first
    if (urlFlowId) {
      // Wait for flowList to load before validating
      if (!flowList) {
        console.log(`⏳ Waiting for flowList to validate URL flow ID: ${urlFlowId}`);
        return null; // Return null while loading - will trigger "No Active Flow" state
      }

      // Check if URL flow_id exists in user's flow list
      const flowExists = flowList.some((flow: DiscoveryFlow) => {
        const flowId = flow.flow_id || flow.id;
        return flowId === urlFlowId;
      });

      if (flowExists) {
        console.log(`✅ Using validated URL flow ID: ${urlFlowId}`);
        return urlFlowId;
      } else {
        console.warn(`❌ URL flow ID ${urlFlowId} not found in user's flow list - invalid flow`);
        return null; // Return null for invalid flow_id - will trigger error state
      }
    }

    // For auto-detected flows, validate against flow list
    if (!flowList) {
      return candidateFlowId;
    }

    // Check if the auto-detected flow ID exists in the user's flow list
    const flowExists = flowList.some((flow: DiscoveryFlow) => {
      const flowId = flow.flow_id || flow.id;
      return flowId === candidateFlowId;
    });

    if (!flowExists && autoDetectedFlowId) {
      console.warn(`⚠️ Auto-detected flow ID ${autoDetectedFlowId} not found in user's active flows. Using anyway.`);
      // Still use it - the flow list might be incomplete
    }

    return candidateFlowId;
  }, [urlFlowId, autoDetectedFlowId, flowList]);

  // Use validated flow ID as the effective flow ID
  const effectiveFlowId = validatedFlowId;

  // Flow detection completed

  return {
    // Flow IDs
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,

    // Flow list data
    flowList,
    isFlowListLoading,
    flowListError,

    // Debugging info
    hasUrlFlowId: !!urlFlowId,
    hasAutoDetectedFlow: !!autoDetectedFlowId,
    hasEffectiveFlow: !!effectiveFlowId,
    totalFlowsAvailable: flowList?.length || 0
  };
};

// Specific hooks for each Discovery page
export const useDataImportFlowDetection = (): FlowAutoDetectionResult => {
  return useDiscoveryFlowAutoDetection({
    currentPhase: 'data_import',
    preferredStatuses: ['running', 'active', 'pending'],
    fallbackToAnyRunning: true
  });
};

export const useFieldMappingFlowDetection = (): FlowAutoDetectionResult => {
  return useDiscoveryFlowAutoDetection({
    currentPhase: 'field_mapping',
    preferredStatuses: ['initialized', 'running', 'active', 'initializing', 'processing', 'paused', 'waiting_for_user_approval', 'waiting_for_approval'],
    fallbackToAnyRunning: true
  });
};

export const useDataCleansingFlowDetection = (): FlowAutoDetectionResult => {
  return useDiscoveryFlowAutoDetection({
    currentPhase: 'data_cleansing',
    preferredStatuses: ['initialized', 'running', 'active', 'in_progress', 'processing', 'paused', 'waiting_for_user_approval', 'waiting_for_approval'],
    fallbackToAnyRunning: true
  });
};

export const useInventoryFlowDetection = (): FlowAutoDetectionResult => {
  return useDiscoveryFlowAutoDetection({
    currentPhase: 'inventory',
    preferredStatuses: ['running', 'active'],
    fallbackToAnyRunning: true
  });
};

export const useDependenciesFlowDetection = (): FlowAutoDetectionResult => {
  return useDiscoveryFlowAutoDetection({
    currentPhase: 'dependencies',
    preferredStatuses: ['running', 'active'],
    fallbackToAnyRunning: true
  });
};

export const useTechDebtFlowDetection = (): FlowAutoDetectionResult => {
  return useDiscoveryFlowAutoDetection({
    currentPhase: 'tech_debt',
    preferredStatuses: ['running', 'active'],
    fallbackToAnyRunning: true
  });
};

// Re-export useDiscoveryFlowList for components that need it
export { useDiscoveryFlowList } from './useDiscoveryFlowList';
