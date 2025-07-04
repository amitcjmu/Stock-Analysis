import { useMemo } from 'react';
import { useParams } from 'react-router-dom';
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
    if (!flowList || flowList.length === 0) return null;
    
    console.log(`🔍 Auto-detecting flow for phase: ${currentPhase}`, {
      totalFlows: flowList.length,
      preferredStatuses,
      fallbackToAnyRunning,
      sampleFlow: flowList.length > 0 ? {
        flow_id: flowList[0].flow_id,
        status: flowList[0].status,
        next_phase: flowList[0].next_phase,
        phases: flowList[0].phases,
        [`${currentPhase}_completed`]: flowList[0][`${currentPhase}_completed`]
      } : null
    });
    
    // Priority 1: Flow currently in the specified phase (next_phase matches)
    if (currentPhase) {
      const currentPhaseFlow = flowList.find((flow: any) => 
        flow.next_phase === currentPhase
      );
      if (currentPhaseFlow) {
        console.log(`✅ Found flow needing ${currentPhase} phase:`, currentPhaseFlow.flow_id);
        return currentPhaseFlow.flow_id;
      }
    }
    
    // Priority 1.5: For attribute_mapping, also check flows that completed data_import
    if (currentPhase === 'attribute_mapping') {
      const dataImportCompleteFlow = flowList.find((flow: any) => {
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
        console.log(`✅ Found flow with completed data_import ready for attribute_mapping:`, dataImportCompleteFlow.flow_id);
        return dataImportCompleteFlow.flow_id;
      }
    }
    
    // Priority 2: Flow with specified phase completed but still in preferred status
    if (currentPhase) {
      const completedPhaseFlow = flowList.find((flow: any) => {
        // Check both direct field and phases object for completion status
        const directField = flow[`${currentPhase}_completed`];
        const phasesField = flow.phases?.[`${currentPhase}_completed`];
        const isPhaseCompleted = directField === true || phasesField === true;
        
        const isPreferredStatus = preferredStatuses.includes(flow.status);
        
        console.log(`🔍 Checking flow ${flow.flow_id} for completed ${currentPhase}:`, {
          directField,
          phasesField,
          isPhaseCompleted,
          status: flow.status,
          isPreferredStatus
        });
        
        return isPhaseCompleted && isPreferredStatus;
      });
      
      if (completedPhaseFlow) {
        console.log(`✅ Found flow with completed ${currentPhase} phase:`, completedPhaseFlow.flow_id);
        return completedPhaseFlow.flow_id;
      }
    }
    
    // Priority 3: Any flow in preferred status
    if (fallbackToAnyRunning) {
      const runningFlow = flowList.find((flow: any) => 
        preferredStatuses.includes(flow.status)
      );
      if (runningFlow) {
        console.log(`✅ Found flow in preferred status:`, runningFlow.flow_id);
        return runningFlow.flow_id;
      }
    }
    
    // Priority 4: Most recent flow (even if completed)
    const sortedFlows = [...flowList].sort((a: any, b: any) => 
      new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime()
    );
    
    if (sortedFlows.length > 0) {
      console.log(`✅ Using most recent flow:`, sortedFlows[0].flow_id);
      return sortedFlows[0].flow_id;
    }
    
    console.log('❌ No suitable flow found');
    return null;
  }, [flowList, currentPhase, preferredStatuses, fallbackToAnyRunning]);

  // Use URL flow ID if provided, otherwise use auto-detected flow ID
  const effectiveFlowId = urlFlowId || autoDetectedFlowId;
  
  console.log(`🎯 Flow detection result:`, {
    urlFlowId,
    autoDetectedFlowId,
    effectiveFlowId,
    currentPhase
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
    preferredStatuses: ['initialized', 'running', 'active', 'initializing', 'processing', 'paused', 'waiting_for_user_approval'],
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
