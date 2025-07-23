import { useMemo } from 'react';
import type { useParams } from 'react-router-dom';
import { useDiscoveryFlowList } from './useDiscoveryFlowList';

interface FlowAutoDetectionOptions {
  currentPhase?: string;
  preferredStatuses?: string[];
  fallbackToAnyRunning?: boolean;
}

export const useDiscoveryFlowAutoDetection = (options: FlowAutoDetectionOptions = {}) => {
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
      console.log(`🔍 No flows available for auto-detection`, { flowList, length: flowList?.length });
      
      // Emergency fallback: try to extract flow ID from URL or other context
      const currentUrl = typeof window !== 'undefined' ? window.location.href : '';
      console.log('🔍 Checking for emergency flow ID fallback from URL:', currentUrl);
      
      // Look for flow ID patterns in current URL or context
      const flowIdPattern = /[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}/i;
      const urlMatch = currentUrl.match(flowIdPattern);
      
      if (urlMatch) {
        console.log('✅ Found emergency flow ID from URL:', urlMatch[0]);
        return urlMatch[0];
      }
      
      return null;
    }
    
    console.log(`🔍 Auto-detecting flow for phase: ${currentPhase}`, {
      totalFlows: flowList.length,
      preferredStatuses,
      fallbackToAnyRunning,
      allFlows: flowList.map(flow => ({
        flow_id: flow.flow_id || flow.id,
        status: flow.status,
        current_phase: flow.current_phase,
        next_phase: flow.next_phase,
        phases: flow.phases,
        data_import_completed: flow.data_import_completed,
        attribute_mapping_completed: flow.attribute_mapping_completed,
        [`${currentPhase}_completed`]: flow[`${currentPhase}_completed`]
      }))
    });
    
    // Priority 1: Flow currently in the specified phase (next_phase matches)
    if (currentPhase) {
      const currentPhaseFlow = flowList.find((flow: unknown) => 
        flow.next_phase === currentPhase
      );
      if (currentPhaseFlow) {
        const flowId = currentPhaseFlow.flow_id || currentPhaseFlow.id;
        console.log(`✅ Found flow needing ${currentPhase} phase:`, flowId);
        return flowId;
      }
    }
    
    // Priority 1.5: For attribute_mapping, also check flows that completed data_import
    if (currentPhase === 'attribute_mapping') {
      const dataImportCompleteFlow = flowList.find((flow: unknown) => {
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
        console.log(`✅ Found flow with completed data_import ready for attribute_mapping:`, flowId);
        return flowId;
      }
    }
    
    // Priority 2: Flow with specified phase completed but still in preferred status
    if (currentPhase) {
      const completedPhaseFlow = flowList.find((flow: unknown) => {
        // Check both direct field and phases object for completion status
        const directField = flow[`${currentPhase}_completed`];
        const phasesField = flow.phases?.[`${currentPhase}_completed`];
        const isPhaseCompleted = directField === true || phasesField === true;
        
        const isPreferredStatus = preferredStatuses.includes(flow.status);
        
        console.log(`🔍 Checking flow ${flow.id} for completed ${currentPhase}:`, {
          directField,
          phasesField,
          isPhaseCompleted,
          status: flow.status,
          isPreferredStatus
        });
        
        return isPhaseCompleted && isPreferredStatus;
      });
      
      if (completedPhaseFlow) {
        const flowId = completedPhaseFlow.flow_id || completedPhaseFlow.id;
        console.log(`✅ Found flow with completed ${currentPhase} phase:`, flowId);
        return flowId;
      }
    }
    
    // Priority 3: Any flow in preferred status
    if (fallbackToAnyRunning) {
      const runningFlow = flowList.find((flow: unknown) => 
        preferredStatuses.includes(flow.status)
      );
      if (runningFlow) {
        const flowId = runningFlow.flow_id || runningFlow.id;
        console.log(`✅ Found flow in preferred status:`, flowId);
        return flowId;
      }
    }
    
    // Priority 4: Most recent flow (even if completed)
    const sortedFlows = [...flowList].sort((a: unknown, b: unknown) => 
      new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime()
    );
    
    if (sortedFlows.length > 0) {
      const flowId = sortedFlows[0].flow_id || sortedFlows[0].id;
      console.log(`✅ Using most recent flow:`, flowId);
      return flowId;
    }
    
    // Priority 5: Any flow at all (last resort)
    if (flowList.length > 0) {
      const flowId = flowList[0].flow_id || flowList[0].id;
      console.log(`✅ Using first available flow as last resort:`, flowId);
      return flowId;
    }
    
    console.log('❌ No suitable flow found');
    return null;
  }, [flowList, currentPhase, preferredStatuses, fallbackToAnyRunning]);

  // Use URL flow ID if provided, otherwise use auto-detected flow ID
  const effectiveFlowId = urlFlowId || autoDetectedFlowId;
  
  console.log(`🎯 Flow detection result for ${currentPhase}:`, {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    currentPhase,
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
export const useDataImportFlowDetection = () => {
  return useDiscoveryFlowAutoDetection({
    currentPhase: 'data_import',
    preferredStatuses: ['running', 'active', 'pending'],
    fallbackToAnyRunning: true
  });
};

export const useAttributeMappingFlowDetection = () => {
  return useDiscoveryFlowAutoDetection({
    currentPhase: 'attribute_mapping',
    preferredStatuses: ['initialized', 'running', 'active', 'initializing', 'processing', 'paused', 'waiting_for_user_approval', 'waiting_for_approval'],
    fallbackToAnyRunning: true
  });
};

export const useDataCleansingFlowDetection = () => {
  return useDiscoveryFlowAutoDetection({
    currentPhase: 'data_cleansing',
    preferredStatuses: ['running', 'active'],
    fallbackToAnyRunning: true
  });
};

export const useInventoryFlowDetection = () => {
  return useDiscoveryFlowAutoDetection({
    currentPhase: 'inventory',
    preferredStatuses: ['running', 'active'],
    fallbackToAnyRunning: true
  });
};

export const useDependenciesFlowDetection = () => {
  return useDiscoveryFlowAutoDetection({
    currentPhase: 'dependencies',
    preferredStatuses: ['running', 'active'],
    fallbackToAnyRunning: true
  });
};

export const useTechDebtFlowDetection = () => {
  return useDiscoveryFlowAutoDetection({
    currentPhase: 'tech_debt',
    preferredStatuses: ['running', 'active'],
    fallbackToAnyRunning: true
  });
};

// Re-export useDiscoveryFlowList for components that need it
export { useDiscoveryFlowList } from './useDiscoveryFlowList';
