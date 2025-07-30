import { useMemo } from 'react';
import { useParams } from 'react-router-dom';
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
  attribute_mapping_completed?: boolean;
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
  const { flowId: urlFlowId } = useParams<{ flowId?: string }>();
  const { data: flowList, isLoading: isFlowListLoading, error: flowListError } = useDiscoveryFlowList();

  const {
    currentPhase,
    preferredStatuses = ['initialized', 'running', 'active', 'in_progress'],
    fallbackToAnyRunning = true
  } = options;

  // Auto-detect the most relevant flow based on current page context
  const autoDetectedFlowId = useMemo(() => {
    if (!flowList || flowList.length === 0) {
      SecureLogger.debug('No flows available for auto-detection', { flowListLength: flowList?.length });

      // Emergency fallback: try to extract flow ID from URL with validation
      const currentUrl = typeof window !== 'undefined' ? window.location.href : '';
      SecureLogger.debug('Checking for emergency flow ID fallback from URL');

      // Look for flow ID patterns in current URL with secure validation
      const flowIdPattern = /[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}/i;
      const urlMatch = currentUrl.match(flowIdPattern);

      if (urlMatch) {
        const rawFlowId = urlMatch[0];
        const validatedFlowId = SecureStorage.validateUrlFlowId(rawFlowId);
        if (validatedFlowId) {
          SecureLogger.debug('Found emergency flow ID from URL pattern');
          return validatedFlowId;
        }
      }

      return null;
    }

    SecureLogger.debug(`Auto-detecting flow for phase: ${currentPhase}`, {
      totalFlows: flowList.length,
      preferredStatuses,
      fallbackToAnyRunning
    });

    // Priority 1: Flow currently in the specified phase (next_phase matches or current_phase matches)
    if (currentPhase) {
      const currentPhaseFlow = flowList.find((flow: DiscoveryFlow) =>
        flow.next_phase === currentPhase || flow.current_phase === currentPhase
      );
      if (currentPhaseFlow) {
        const flowId = currentPhaseFlow.flow_id || currentPhaseFlow.id;
        SecureLogger.debug(`Found flow needing ${currentPhase} phase`);
        return flowId;
      }
    }

    // Priority 1.5: For attribute_mapping, also check flows that completed data_import
    if (currentPhase === 'attribute_mapping') {
      const dataImportCompleteFlow = flowList.find((flow: DiscoveryFlow) => {
        // Check if data_import is completed
        const dataImportCompleted = flow.phases?.data_import === true ||
                                   flow.data_import_completed === true ||
                                   flow.current_phase === 'data_import';

        // Check if flow is in a suitable status
        const isPreferredStatus = preferredStatuses.includes(flow.status);

        // Check if attribute_mapping is not yet completed
        const attributeMappingNotCompleted = flow.phases?.attribute_mapping !== true &&
                                           flow.attribute_mapping_completed !== true;

        return dataImportCompleted && isPreferredStatus && attributeMappingNotCompleted;
      });

      if (dataImportCompleteFlow) {
        const flowId = dataImportCompleteFlow.flow_id || dataImportCompleteFlow.id;
        SecureLogger.debug('Found flow with completed data_import ready for attribute_mapping');
        return flowId;
      }
    }

    // Priority 1.6: For data_cleansing, also check flows that completed field_mapping/attribute_mapping
    if (currentPhase === 'data_cleansing') {
      const fieldMappingCompleteFlow = flowList.find((flow: DiscoveryFlow) => {
        // Check if field_mapping or attribute_mapping is completed
        const fieldMappingCompleted = flow.phases?.field_mapping === true ||
                                     flow.field_mapping_completed === true ||
                                     flow.phases?.attribute_mapping === true ||
                                     flow.attribute_mapping_completed === true ||
                                     flow.current_phase === 'field_mapping' ||
                                     flow.current_phase === 'attribute_mapping';

        // Check if flow is in a suitable status
        const isPreferredStatus = preferredStatuses.includes(flow.status);

        // Check if data_cleansing is not yet completed
        const dataCleansingNotCompleted = flow.phases?.data_cleansing !== true &&
                                        flow.data_cleansing_completed !== true;

        SecureLogger.debug(`Checking flow readiness for data_cleansing`, {
          fieldMappingCompleted,
          isPreferredStatus,
          dataCleansingNotCompleted
        });

        return fieldMappingCompleted && isPreferredStatus && dataCleansingNotCompleted;
      });

      if (fieldMappingCompleteFlow) {
        const flowId = fieldMappingCompleteFlow.flow_id || fieldMappingCompleteFlow.id;
        SecureLogger.debug('Found flow with completed field_mapping ready for data_cleansing');
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

        SecureLogger.debug(`Checking flow completion for ${currentPhase}`, {
          isPhaseCompleted,
          isPreferredStatus
        });

        return isPhaseCompleted && isPreferredStatus;
      });

      if (completedPhaseFlow) {
        const flowId = completedPhaseFlow.flow_id || completedPhaseFlow.id;
        SecureLogger.debug(`Found flow with completed ${currentPhase} phase`);
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
        SecureLogger.debug('Found flow in preferred status');
        return flowId;
      }
    }

    // Priority 4: Most recent flow (even if completed)
    const sortedFlows = [...flowList].sort((a: DiscoveryFlow, b: DiscoveryFlow) =>
      new Date(b.updated_at || b.created_at || '').getTime() - new Date(a.updated_at || a.created_at || '').getTime()
    );

    if (sortedFlows.length > 0) {
      const flowId = sortedFlows[0].flow_id || sortedFlows[0].id;
      SecureLogger.debug('Using most recent flow');
      return flowId;
    }

    // Priority 5: Any flow at all (last resort)
    if (flowList.length > 0) {
      const flowId = flowList[0].flow_id || flowList[0].id;
      SecureLogger.debug('Using first available flow as last resort');
      return flowId;
    }

    SecureLogger.warn('No suitable flow found for auto-detection');
    return null;
  }, [flowList, currentPhase, preferredStatuses, fallbackToAnyRunning]);

  // Use URL flow ID if provided, otherwise use auto-detected flow ID
  const effectiveFlowId = urlFlowId || autoDetectedFlowId;

  SecureLogger.debug(`Flow detection result for ${currentPhase}`, {
    hasUrlFlowId: !!urlFlowId,
    hasAutoDetectedFlowId: !!autoDetectedFlowId,
    hasEffectiveFlowId: !!effectiveFlowId,
    flowListLength: flowList?.length || 0,
    isFlowListLoading,
    hasFlowListError: !!flowListError
  });

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

export const useAttributeMappingFlowDetection = (): FlowAutoDetectionResult => {
  return useDiscoveryFlowAutoDetection({
    currentPhase: 'attribute_mapping',
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
